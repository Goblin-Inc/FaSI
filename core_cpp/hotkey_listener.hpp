#pragma once

#include <atomic>
#include <functional>
#include <string>
#include <thread>

namespace fasi {

class HotkeyListener {
public:
    using Callback = void(*)();

    HotkeyListener();
    ~HotkeyListener();

    bool start(const std::string& hotkey_str, Callback callback);
    void stop();
    bool is_running() const;

private:
    void listen_loop(std::string hotkey_str);

    std::atomic<bool> running_{false};
    std::thread worker_;
    Callback callback_{nullptr};
};

} // namespace fasi
