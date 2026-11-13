import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.json"

DEFAULT_CONFIG = {
    "default_provider": "yandex",
    "results_per_page": 20,
    "download_path": str(Path.home() / "Pictures" / "FASI"),
    "ask_save_path": False,
    "hotkey": "Alt+Space",
    "timeout": 10
}


class ConfigManager:
    def __init__(self):
        self.data = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                print(f"[Config] Ошибка чтения config.json: {e}")
        else:
            self.save()

    def save(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Ошибка записи config.json: {e}")

    def get(self, key, default=None):
        val = self.data.get(key, default)
        if key == "download_path" and isinstance(val, str):
            expanded = os.path.expanduser(val)
            os.makedirs(expanded, exist_ok=True)
            return expanded
        return val

    def set(self, key, value):
        self.data[key] = value
        self.save()


config = ConfigManager()