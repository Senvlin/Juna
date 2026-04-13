import asyncio
import configparser
import json
import math
from pathlib import Path

import httpx

from decode import Decoder
from items import Material_book, Word


class CookieManager:
    def __init__(self, filename="config.ini"):
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


class ShanbayAPI:
    def __init__(self, cookie):
        """
        初始化 API 客户端
        :param cookie: 扇贝网站的 Cookie 字符串, 用于身份验证
        """
        self.cookie = cookie
        self.base_url = "https://apiv3.shanbay.com"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=self._parse_cookies(cookie),
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Windows; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"  # TODO: 以后会写随机User-Agent的
            },
        )

    def _parse_cookies(self, cookie_str) -> dict:
        """
        将 cookie 字符串转换为字典, 方便 httpx 处理
        """
        cookies = {}
        if not cookie_str:
            return cookies
        for item in cookie_str.split(";"):
            if "=" in item:
                key, value = item.split("=", 1)
                cookies[key.strip()] = value.strip()
        return cookies

    def _parse_material_book(self, data) -> Material_book:
        material_book = data["materialbook"]
        book = Material_book(
            id=data.get("materialbook_id"),
            description=material_book.get("description"),
            icon_url=material_book.get("icon_url"),
            name=material_book.get("name"),
            tag_ids=material_book.get("tag_ids"),
            total_count=material_book.get("total_count"),
            new_count=data.get("new_count"),
            review_count=data.get("review_count"),
        )
        return book

    async def get_default_material_book(self) -> Material_book | None:
        """
        获取用户当前学习的教材
        """
        url = "/wordsapp/user_material_books/current"

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("materialbook_id"):
                book = self._parse_material_book(data)
                return book
            else:
                print("未找到教材 ID，请检查 API 返回结构")
                return None

        except httpx.HTTPError as e:
            print(f"请求教材 ID 失败: {e}")
            return None

    async def get_words_in_page(self, material_book_id, page, words_type) -> dict | str:
        """
        获取指定页码的单词
        :param words_type: 'NEW'(新词)或'REVIEW'(复习)
        """
        url = f"/wordsapp/user_material_books/{material_book_id}/learning/words/today_learning_items"
        params = {
            "page": page,
            "ipp": 10,
            "type_of": words_type,
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            raw_words = data.get("data", {})
            decoded_words = Decoder.decode(raw_words)
            with open(f"words_{page}_{words_type}.json", "w", encoding="utf-8") as f:
                json.dump(decoded_words, f, ensure_ascii=False, indent=4)
            return decoded_words

        except httpx.HTTPError as e:
            print(f"请求单词列表失败: {e}")
            return ""

    def _parse_words(self, current_page_words) -> list[Word]:
        all_words = []
        for raw_word in current_page_words:
            vocab_with_senses = raw_word["vocab_with_senses"]
            sound = vocab_with_senses["sound"]
            word = Word(
                type_of=raw_word.get("type_of"),
                id=vocab_with_senses.get("id"),
                audio_uk_url=sound.get("audio_uk_urls")[0],
                audio_us_url=sound.get("audio_us_urls")[0],
                ipa_uk=sound.get("ipa_uk"),
                ipa_us=sound.get("ipa_us"),
                word=vocab_with_senses.get("word"),
                senses=vocab_with_senses.get("senses", []),
                updated_at=vocab_with_senses.get("updated_at"),
            )
            all_words.append(word)
        return all_words

    async def get_words_all(
        self, material_book: Material_book, words_type
    ) -> list[Word]:
        all_words = []

        print(f"开始获取 {words_type} 单词...")
        total_count = (
            material_book.new_count
            if words_type == "NEW"
            else material_book.review_count
        )
        total_pages = math.ceil(total_count / 10)

        tasks = [
            self.get_words_in_page(material_book.id, p, words_type)
            for p in range(1, total_pages + 1)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, dict):
                page_objects = result.get("objects", [])
                all_words.extend(self._parse_words(page_objects))
            else:
                print(f"某页请求出错: {result}")
                continue
        return all_words

    async def close(self):
        """
        关闭客户端连接
        """
        await self.client.aclose()


async def main():
    cookie_manager = CookieManager()
    cookie = cookie_manager.get_cookie("COOKIE")
    api = ShanbayAPI(cookie)

    try:
        book = await api.get_default_material_book()
        if book:
            print(f"当前教材 ID: {book}")

            new_words = await api.get_words_all(book, "NEW")
            print(f"今日新词总数: {len(new_words)}")

            review_words = await api.get_words_all(book, "REVIEW")
            print(f"今日复习词总数: {len(review_words)}")

    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())
