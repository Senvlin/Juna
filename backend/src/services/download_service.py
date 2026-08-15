import configparser
from pathlib import Path

# 配置文件固定放在 backend/config.ini，避免因启动目录不同而找不到
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.ini"


class CookieManager:
    def __init__(self, filename: str | Path | None = None):
        self.filename = DEFAULT_CONFIG_PATH if filename is None else Path(filename)

        self.config = configparser.ConfigParser(interpolation=None)
        self._load()

    def _load(self):
        if self.filename.exists():
            self.config.read(self.filename, encoding="utf-8")
        else:
            if "Cookie" not in self.config:
                self.config["Cookie"] = {}

    def save_cookie(self, key, value):
        self.config["Cookie"][key] = value
        self._save()
        print(f"[OK] Cookie saved: {key} (length={len(value)})")

    def get_cookie(self, key, fallback=None) -> str:
        if cookie := self.config.get("Cookie", key, fallback=fallback):
            return cookie
        else:
            raise RuntimeError(
                f"[ERROR] Cookie not found: {key}, please fill it in config.ini"
            )

    def _save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            self.config.write(f)
