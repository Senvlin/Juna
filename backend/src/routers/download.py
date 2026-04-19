import json
from typing import Literal

from fastapi import APIRouter

from services.download_service import DOWNLOAD_DIR
from services.word_service import get_words_data

router = APIRouter(prefix="/routers/download", tags=["下载管理"])


async def download_words_task(word_type: Literal["new", "review"]):
    words = await get_words_data(word_type)
    with open(f"{DOWNLOAD_DIR}\\words_{word_type}.json", "w", encoding="utf-8") as f:
        json.dump(
            [word.model_dump(mode="json") for word in words],
            f,
            ensure_ascii=False,
            indent=4,
        )


@router.get("/word/{word_type}")
async def download_word_task(word_type: Literal["new", "review"]):
    await download_words_task(word_type)
    return {"message": "已下载完成，请查看下载目录"}
