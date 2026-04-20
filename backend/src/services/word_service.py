from typing import Literal

from schemas import WordItem
from shanbei_api import ShanbayAPI

from backend.src.services.download_service import CookieManager

cookie_manager = CookieManager()
cookie = cookie_manager.get_cookie("COOKIE")
api = ShanbayAPI(cookie)


async def get_words_data(word_type: Literal["new", "review"]) -> list[WordItem]:
    book = await api.get_default_material_book()
    if book:
        if word_type == "new":
            new_words = await api.get_words_all(book, "NEW")
            return new_words
        elif word_type == "review":
            review_words = await api.get_words_all(book, "REVIEW")
            return review_words
    else:
        raise ValueError("未找到书籍")
