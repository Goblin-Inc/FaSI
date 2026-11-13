import ctypes
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

from .config import config


class HotkeyManager(QObject):
    activated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lib = None
        self._cb_ref = None
        self._load_cpp_bridge()

    def _load_cpp_bridge(self):
        root_dir = Path(__file__).resolve().parent.parent.parent
        candidates = [
            root_dir / "core_cpp" / "build" / "libfasi_core.so",
            root_dir / "core_cpp" / "libfasi_core.so",
        ]
        for so_path in candidates:
            if so_path.exists():
                try:
                    lib = ctypes.CDLL(str(so_path))
                    cb_type = ctypes.CFUNCTYPE(None)
                    self._cb_ref = cb_type(self._on_native_hotkey)
                    lib.fasi_hotkey_start.argtypes = [ctypes.c_char_p, cb_type]
                    lib.fasi_hotkey_start.restype = ctypes.c_bool
                    lib.fasi_hotkey_stop.argtypes = []
                    lib.fasi_hotkey_stop.restype = None
                    self._lib = lib
                    break
                except Exception as e:
                    print(f"[HotkeyManager] Не удалось загрузить C++ модуль {so_path}: {e}")

    def _on_native_hotkey(self):
        self.activated.emit()

    def start(self) -> bool:
        if not self._lib:
            return False
        hotkey_str = config.get("hotkey", "Alt+Space").encode("utf-8")
        return bool(self._lib.fasi_hotkey_start(hotkey_str, self._cb_ref))

    def stop(self):
        if self._lib:
            try:
                self._lib.fasi_hotkey_stop()
            except Exception:
                pass
