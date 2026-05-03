from typing import Literal

from schemas import WordItem
from shanbei_api import ShanbayAPI

from backend.src.schemas import LearningSession, MaterialBook
from backend.src.services.download_service import CookieManager

cookie_manager = CookieManager()
cookie: str = cookie_manager.get_cookie("COOKIE")
api = ShanbayAPI(cookie)


async def get_words_data(word_type: Literal["new", "review"]) -> list[WordItem]:
    book: MaterialBook | None = await api.get_default_material_book()
    if book:
        if word_type == "new":
            new_words: list[WordItem] = await api.get_words_all(book, "NEW")
            return new_words
        elif word_type == "review":
            review_words: list[WordItem] = await api.get_words_all(book, "REVIEW")
            return review_words
    else:
        raise ValueError("未找到书籍")


async def upload_words(learning_session: LearningSession):
    book: MaterialBook | None = await api.get_default_material_book()
    if book:
        await api.sync_word(
            learning_session=learning_session,
            material_book=book,
        )
    else:
        raise ValueError("未找到书籍")


async def get_word_notes(word: WordItem):
    return await api.get_vocab_notes(word)
