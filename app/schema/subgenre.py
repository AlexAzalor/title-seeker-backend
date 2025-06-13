from pydantic import BaseModel

from config import config

CFG = config()


class SubgenreExportCreate(BaseModel):
    id: int
    key: str
    name_uk: str
    name_en: str
    description_uk: str | None = None
    description_en: str | None = None
    parent_genre_id: int | None = None


class SubgenresJSONFile(BaseModel):
    subgenres: list[SubgenreExportCreate]
