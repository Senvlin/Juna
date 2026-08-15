from typing import Literal

from backend.src.schemas import LearningSession, MaterialBook, WordItem
from backend.src.services.download_service import CookieManager
from backend.src.shanbei_api import ShanbayAPI

cookie_manager = CookieManager()

_api: ShanbayAPI | None = None


def get_api() -> ShanbayAPI:
    global _api
    current: str = cookie_manager.get_cookie("COOKIE")
    if _api is None:
        _api = ShanbayAPI(current)
    elif _api.cookie != current:
        _api.set_cookie(current)
    return _api


# 旧逻辑：启动时立即读取 Cookie；现在改为 get_api() 懒加载，便于登录后热更新
# api = ShanbayAPI(cookie)  # 已移除


async def get_words_data(word_type: Literal["new", "review"]) -> list[WordItem]:
    api = get_api()
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
    api = get_api()
    book: MaterialBook | None = await api.get_default_material_book()
    if book:
        await api.sync_word(
            learning_session=learning_session,
            material_book=book,
        )
    else:
        raise ValueError("未找到书籍")


async def get_word_notes(word: WordItem):
    api = get_api()
    return await api.get_vocab_notes(word)
