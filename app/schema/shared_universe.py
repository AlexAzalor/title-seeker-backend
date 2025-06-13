from pydantic import BaseModel

from config import config

CFG = config()


class SharedUniverseExportCreate(BaseModel):
    id: int
    key: str
    name_uk: str
    name_en: str
    description_uk: str | None = None
    description_en: str | None = None


class SharedUniversesJSONFile(BaseModel):
    shared_universes: list[SharedUniverseExportCreate]


class SharedUniversePreCreateOut(BaseModel):
    key: str
    name: str
    description: str
