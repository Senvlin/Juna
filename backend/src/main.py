from typing import Literal

from fastapi import FastAPI
from routers.download import router as download_router
from schemas import WordItem

from backend.src.services.word_service import get_words_data

app = FastAPI()
app.include_router(download_router)


@app.get("/word/{word_type}")
async def get_words(word_type: Literal["new", "review"]) -> list[WordItem]:
    words = await get_words_data(word_type)
    return words
