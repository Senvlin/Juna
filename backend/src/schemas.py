from typing import Literal

from pydantic import BaseModel, HttpUrl, field_validator, model_validator


class SenseItem(BaseModel):
    definition_cn: str
    pos: str

    @field_validator("definition_cn", "pos", mode="before")
    @classmethod
    def strip_word(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class Material_book(BaseModel):
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
    updated_at: str


class VocabNote(BaseModel):
    content: str
    id: str
    remark: str
    tag: dict
    user_id: str
    user_info: dict[Literal["nickname"], str] | None
    vocab_id: str

    @field_validator("content", mode="before")
    @classmethod
    def lines_to_semicolon(cls, v):
        if isinstance(v, str):
            return v.replace("\n", ";")


class WordTask(BaseModel):
    total: int | None = None
    all_word: list[WordItem]

    @model_validator(mode="after")
    def word_count(self):
        if self.total is None:
            self.total = len(self.all_word)
        return self


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
