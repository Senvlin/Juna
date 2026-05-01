import asyncio
import math
from typing import Literal

import httpx
from decode import Decoder
from schemas import Material_book, VocabNote, WordItem, WordLearningClick


class ShanbayAPI:
    def __init__(self, cookie: str):
        """
        初始化 API 客户端
        :param cookie: 扇贝网站的 Cookie 字符串, 用于身份验证
        """
        self.cookie: str = cookie
        self.base_url = "https://apiv3.shanbay.com"

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            cookies=self._parse_cookies(cookie),
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Windows; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"  # TODO: 以后会写随机User-Agent的
            },
        )

    def _parse_cookies(self, cookie_str: str) -> dict:
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

    async def get_words_in_page(
        self,
        material_book_id: str,
        page,
        words_type: Literal["NEW", "REVIEW"],
    ) -> dict | str:
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
            return decoded_words

        except httpx.HTTPError as e:
            print(f"请求单词列表失败: {e}")
            return ""

    def _parse_words(self, current_page_words) -> list[WordItem]:
        all_words = []
        for raw_word in current_page_words:
            vocab_with_senses = raw_word["vocab_with_senses"]
            sound = vocab_with_senses["sound"]
            word = WordItem(
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
        self,
        material_book: Material_book,
        words_type: Literal["NEW", "REVIEW"],
    ) -> list[WordItem]:
        """
        并发获取所有符合New/Review的单词

        统一用asyncio.gather()处理异常与结果，异常将被打印到控制台
        """
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

    async def get_vocab_notes(self, word: WordItem) -> list[VocabNote | None]:
        url = "/wordsapp/user_vocab_notes/agg"
        resp = await self.client.get(url, params={"vocab_id": word.id, "limit": 15})
        resp.raise_for_status()
        raw_json = resp.json()
        vocab_notes: dict = raw_json.get("vocab_notes")
        if not vocab_notes:
            return []
        return [VocabNote(**note) for note in vocab_notes]

    # TODO:等前端适配的时候再用这个
    async def submit_word(self, learning_click_item: WordLearningClick):
        url = "/lune/mlog"
        resp = await self.client.post(url, json=learning_click_item.model_dump())

        resp.raise_for_status()

    # TODO: 同上
    # async def sync_word(self, new_words: Iterable[WordItem], review_words: Iterable[WordItem]):
    #     """
    #     与服务器同步单词完成情况
    #     """
    #     url = "/wordsapp/user_material_books/bqydkq/learning/items/sync"
    #     a = self.test_(new_words, review_words)
    #     req = await self.client.put(url, json=a)
    #     req.raise_for_status()

    # def test_(self, new_words: Iterable[WordItem], review_words: Iterable[WordItem]):
    #     a_items_known = [
    #         {"failed_count": 0, "item_id": i.id, "schedule": 0} for i in new_words
    #     ]
    #     c_items_known = [
    #         {
    #             "failed_count": 0,
    #             "item_id": i.id,
    #             "schedule": 3, #schedule指错误之后要背诵的次数 3时为通过，每答对一次就+1
    #             "updated_at": i.updated_at,
    #         }
    #         for i in review_words
    #     ]
    #     return {
    #         "a_items": [],
    #         "a_items_known": a_items_known,
    #         "c_items": [],
    #         "c_items_known": c_items_known,
    #         "date": "2026-04-13",
    #         "learning_time": 145,
    #     }
    async def close(self):
        """
        关闭客户端连接
        """
        await self.client.aclose()
