from typing import Literal

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.download import router as download_router
from schemas import ApiResponse, WordItem

from backend.src.services.word_service import get_words_data, get_word_notes

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


@app.post("/api/word/submit")
async def create_word(item): ...


@app.get("/api/test", response_model=ApiResponse)
def read_root():
    return ApiResponse(data="Hello from FastAPI")


@app.post("/api/word/note/", response_model=ApiResponse)
async def create_note(item: WordItem = Body(...)):
    data = await get_word_notes(item)
    return ApiResponse(data=data)
