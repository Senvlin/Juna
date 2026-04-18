from typing import Literal

from fastapi import FastAPI

from download import router as download_router
from schemas import WordTask
from src.services.word_service import get_words_data

app = FastAPI()
app.include_router(download_router)


@app.get("/word/{word_type}", response_model=WordTask)
async def get_words(word_type: Literal["new", "review"]):
    words = await get_words_data(word_type)
    return WordTask(all_word=words)
