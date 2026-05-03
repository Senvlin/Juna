import datetime
from typing import Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = Field(default=200, description="业务状态码")
    message: str = Field(default="success", description="提示信息")
    data: Optional[T] = None


class SenseItem(BaseModel):
    definition_cn: str
    pos: str

    @field_validator("definition_cn", "pos", mode="before")
    @classmethod
    def strip_word(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class MaterialBook(BaseModel):
    id: str
    description: str
    icon_url: HttpUrl
    name: str
    tag_ids: list[str]
    total_count: int
    new_count: int
    review_count: int


class WordItem(BaseModel):
    """
    存储单词信息
    一词多义在senses中, 包括词性在内
    """

    id: str
    type_of: Literal["NEW", "REVIEW"]
    audio_uk_url: HttpUrl
    audio_us_url: HttpUrl
    ipa_uk: str
    ipa_us: str
    word: str
    senses: list[SenseItem]
    updated_at: datetime.datetime


class VocabNote(BaseModel):
    content: str
    id: str
    remark: str
    tag: dict
    user_id: str
    user_info: dict[Literal["nickname"], str] | None
    vocab_id: str


class WordTask(BaseModel):
    total: int | None = None
    all_word: list[WordItem]

    @model_validator(mode="after")
    def word_count(self):
        if self.total is None:
            self.total: int = len(self.all_word)
        return self


class NewWordKnowledge(BaseModel):
    failed_count: int
    item_id: str
    schedule: int


class ReviewWordKnowledge(BaseModel):
    failed_count: int
    item_id: str
    schedule: int
    updated_at: datetime.datetime


class LearningSession(BaseModel):
    new_words: list[WordItem] = Field(alias="a_items")
    new_words_known: list[NewWordKnowledge] = Field(alias="a_items_known")
    review_words: list[WordItem] = Field(alias="c_items")
    review_words_known: list[ReviewWordKnowledge] = Field(alias="c_items_known")
    date: datetime.date
    learning_time: int  # 单位是秒


# 以下两个对应的是submit_word(), 也许以后有用, 先保留
class WordInteraction(BaseModel):
    user_id: dict = {}
    word: str
    word_type: int = 1
    clk_too_easy: int
    clk_hint: int
    clk_know: int
    clk_not_known: int


class WordLearningClick(BaseModel):
    action: str = "user_word_learning_click"
    biz: str = "default"
    data: WordInteraction
