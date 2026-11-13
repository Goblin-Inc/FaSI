#!/usr/bin/python3
import os, sys
try:
    import PyQt6
except ImportError:
    if os.path.exists("/usr/bin/python3") and os.path.realpath(sys.executable) != os.path.realpath("/usr/bin/python3"):
        os.execv("/usr/bin/python3", ["/usr/bin/python3", *sys.argv])
import os
import signal
import sys
from pathlib import Path
from PyQt6.QtCore import QSocketNotifier
from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


PID_FILE = Path("/tmp/fasi_app.pid")


def try_toggle_existing_instance() -> bool:
    """Если FaSI уже запущен, отправляет ему SIGUSR1 для мгновенного переключения окна."""
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        os.kill(pid, signal.SIGUSR1)
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        return False


def main():
    if "--toggle" in sys.argv:
        if try_toggle_existing_instance():
            sys.exit(0)

    if sys.platform.startswith("linux"):
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            print("Ошибка: требуется графический сеанс Linux (X11/Wayland).")
            sys.exit(1)

    # Если уже запущен другой экземпляр — просто переключаем его видимость
    if try_toggle_existing_instance():
        sys.exit(0)

    try:
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("FaSI")
    app.setDesktopFileName("fasi")
    app.setStyle("Fusion")
    window = MainWindow()

    # Настраиваем безопасную обработку SIGUSR1 через сокет-пару Qt
    r_fd, w_fd = os.pipe()
    os.set_blocking(r_fd, False)
    os.set_blocking(w_fd, False)

    def _sigusr1_handler(_signum, _frame):
        try:
            os.write(w_fd, b"1")
        except OSError:
            pass

    signal.signal(signal.SIGUSR1, _sigusr1_handler)
    notifier = QSocketNotifier(r_fd, QSocketNotifier.Type.Read, window)

    def _on_sigusr1_activated():
        try:
            os.read(r_fd, 64)
        except OSError:
            pass
        window.toggle_visibility()

    notifier.activated.connect(_on_sigusr1_activated)

    window.show()
    exit_code = app.exec()
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
