import configparser
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI

from shanbei_api import ShanbayAPI


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


app = FastAPI()


async def download_word(api: ShanbayAPI):
    book = await api.get_default_material_book()
    try:
        if book:
            print(f"当前教材 ID: {book}")

            new_words = await api.get_words_all(book, "NEW")
            print(f"今日新词总数: {len(new_words)}")

            review_words = await api.get_words_all(book, "REVIEW")
            print(f"今日复习词总数: {len(review_words)}")
    finally:
        await api.close()


@app.get("/")
async def root(background_tasks: BackgroundTasks):
    cookie_manager = CookieManager()
    cookie = cookie_manager.get_cookie("COOKIE")
    api = ShanbayAPI(cookie)
    background_tasks.add_task(download_word, api)
    return {"message": "Hello, FastAPI"}
