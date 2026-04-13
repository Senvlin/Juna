from dataclasses import dataclass

from yarl import URL


@dataclass
class Material_book:
    id: str
    description: str
    icon_url: URL
    name: str
    tag_ids: str
    total_count: int
    new_count: int
    review_count: int

    def __post_init__(self):
        self.icon_url = URL(self.icon_url)
        self.total_count = int(self.total_count)
        self.new_count = int(self.new_count)
        self.review_count = int(self.review_count)


@dataclass
class Word:
    """
    存储单词信息
    一词多义在senses中, 包括词性在内
    """

    id: str
    type_of: str
    audio_uk_url: URL
    audio_us_url: URL
    ipa_uk: str
    ipa_us: str
    word: str
    senses: list[dict[str, str]]
    updated_at: str

    def __post_init__(self):
        self.audio_uk_url = URL(self.audio_uk_url)
        self.audio_us_url = URL(self.audio_us_url)
        cleaned_senses = []
        for sense in self.senses:
            cleaned_sense = {
                k: v.strip()
                for k, v in sense.items()
                if k == "definition_cn" or k == "pos"
            }
            cleaned_senses.append(cleaned_sense)
        self.senses = cleaned_senses
