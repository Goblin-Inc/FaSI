#include "hotkey_listener.hpp"

static fasi::HotkeyListener g_listener;

extern "C" {

bool fasi_hotkey_start(const char* hotkey_str, fasi::HotkeyListener::Callback cb) {
    return g_listener.start(hotkey_str ? hotkey_str : "Alt+Space", cb);
}

void fasi_hotkey_stop() {
    g_listener.stop();
}

bool fasi_hotkey_is_running() {
    return g_listener.is_running();
}

}
