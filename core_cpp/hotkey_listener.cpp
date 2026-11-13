#include "hotkey_listener.hpp"
#include <chrono>

#ifdef HAVE_X11
#include <X11/Xlib.h>
#include <X11/keysym.h>
#endif

namespace fasi {

HotkeyListener::HotkeyListener() = default;

HotkeyListener::~HotkeyListener() {
    stop();
}

bool HotkeyListener::start(const std::string& hotkey_str, Callback callback) {
    if (running_.load()) {
        return false;
    }
    callback_ = callback;
    running_.store(true);
    worker_ = std::thread(&HotkeyListener::listen_loop, this, hotkey_str);
    return true;
}

void HotkeyListener::stop() {
    running_.store(false);
    if (worker_.joinable()) {
        worker_.join();
    }
}

bool HotkeyListener::is_running() const {
    return running_.load();
}

void HotkeyListener::listen_loop(std::string /*hotkey_str*/) {
#ifdef HAVE_X11
    Display* dpy = XOpenDisplay(nullptr);
    if (!dpy) {
        running_.store(false);
        return;
    }

    Window root = DefaultRootWindow(dpy);
    KeyCode keycode = XKeysymToKeycode(dpy, XK_space);
    unsigned int modifiers = Mod1Mask; // Alt + Space

    XGrabKey(dpy, keycode, modifiers, root, True, GrabModeAsync, GrabModeAsync);
    XGrabKey(dpy, keycode, modifiers | Mod2Mask, root, True, GrabModeAsync, GrabModeAsync); // NumLock

    XSelectInput(dpy, root, KeyPressMask);

    while (running_.load()) {
        while (XPending(dpy) > 0) {
            XEvent ev;
            XNextEvent(dpy, &ev);
            if (ev.type == KeyPress && callback_) {
                callback_();
            }
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(25));
    }

    XUngrabKey(dpy, keycode, modifiers, root);
    XUngrabKey(dpy, keycode, modifiers | Mod2Mask, root);
    XCloseDisplay(dpy);
#else
    while (running_.load()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
#endif
}

} // namespace fasi
