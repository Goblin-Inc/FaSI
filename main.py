import os
import sys
from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow


def main():
    if sys.platform.startswith("linux"):
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            print("Ошибка: требуется графический сеанс Linux (X11/Wayland).")
            sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
