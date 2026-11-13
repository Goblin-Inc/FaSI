import shutil
import subprocess
from PyQt6.QtCore import QBuffer, QIODevice
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication


def copy_image_to_clipboard(image: QImage) -> bool:
    """Копирует само изображение (пиксели) в системный буфер обмена (Qt + Wayland/X11)."""
    if image is None or image.isNull():
        return False

    # 1. Стандартный буфер обмена Qt
    clipboard = QApplication.clipboard()
    clipboard.setImage(image)

    # 2. На Wayland / X11 дополнительно передаем PNG в wl-copy или xclip,
    # чтобы буфер обмена сохранялся даже после закрытия окна приложения
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buf, "PNG")
    png_bytes = bytes(buf.data())
    buf.close()

    if shutil.which("wl-copy"):
        try:
            proc = subprocess.Popen(
                ["wl-copy", "--type", "image/png"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.communicate(input=png_bytes, timeout=3)
            return True
        except Exception:
            pass

    if shutil.which("xclip"):
        try:
            proc = subprocess.Popen(
                ["xclip", "-selection", "clipboard", "-t", "image/png", "-i"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.communicate(input=png_bytes, timeout=3)
            return True
        except Exception:
            pass

    return True
