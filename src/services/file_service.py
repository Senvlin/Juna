import configparser
from pathlib import Path


def get_download_dir():  # TODO: 将下载保存放入另一个文件中集中管理
    try:
        from winreg import HKEY_CURRENT_USER, OpenKey, QueryValueEx

        key = OpenKey(
            HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        )
        download_path, _ = QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")
        return Path(download_path)
    except Exception:
        # 如果读取注册表失败，回退到默认路径
        return Path.home() / "Downloads"


DOWNLOAD_DIR = get_download_dir()


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
