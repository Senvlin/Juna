import json
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import Response

from backend.src.services.word_service import get_words_data

router = APIRouter(prefix="/download", tags=["下载管理"])


@router.get("/word/{word_type}")
async def download_word_task(word_type: Literal["new", "review"]):
    words = await get_words_data(word_type)
    words_json = json.dumps(
        {
            "total": len(words),
            "all_words": [word.model_dump(mode="json") for word in words],
        },
        ensure_ascii=False,
    )
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''word_{word_type}.json",
        "Content-Type": "application/json;charset=utf-8",
    }

    return Response(
        content=words_json,
        media_type="application/json;charset=utf-8",
        headers=headers,
    )
