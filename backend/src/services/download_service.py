import configparser
from pathlib import Path


class CookieManager:
    def __init__(self, filename="../config.ini"):
        self.filename = Path(filename)
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
        print(f"✅ 已保存 Cookie: {key} = {value}")

    def get_cookie(self, key, fallback=None) -> str:
        if cookie := self.config.get("Cookie", key, fallback=fallback):
            return cookie
        else:
            raise RuntimeError(
                f"❌ 未找到 Cookie: {key}, 请在config.ini中填写自己的cookie"
            )

    def _save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            self.config.write(f)
