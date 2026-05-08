from typing import Literal

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.download import router as download_router
from schemas import ApiResponse, LearningSession, WordItem

from backend.src.services.word_service import (
    get_word_notes,
    get_words_data,
    upload_words,
)

app = FastAPI()
app.include_router(download_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite 默认端口
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/word/{word_type}", response_model=ApiResponse[list[WordItem]])
async def get_words(word_type: Literal["new", "review"]):
    words: list[WordItem] = await get_words_data(word_type)
    return ApiResponse(data=words)


@app.post("/api/word/sync")
async def sync_word(item: LearningSession = Body(...)):
    try:
        await upload_words(item)
    except Exception as e:
        print(f"同步单词失败: {e}")
        return ApiResponse(message="failed", data="同步单词失败")
    return ApiResponse(message="success", data="同步单词成功")


@app.get("/api/test", response_model=ApiResponse)
def read_root():
    return ApiResponse(data="Hello from FastAPI")


@app.post("/api/word/note/", response_model=ApiResponse)
async def create_note(item: WordItem = Body(...)):
    data = await get_word_notes(item)
    return ApiResponse(data=data)
