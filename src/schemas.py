from typing import Literal

from pydantic import BaseModel, HttpUrl, field_validator


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
    tag_ids: str
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


class Vocab_note(BaseModel):
    content: str
    id: str
    remark: str
    tag: dict
    user_id: str
    user_info: dict[Literal["nickname"], str] | None
    vocab_id: str

    @field_validator("content", mode="before")
    @classmethod
    def lines_to_semicolon(self, v):
        if isinstance(v, str):
            return v.replace("\n", ";")
