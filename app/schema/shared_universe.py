from pydantic import BaseModel

from config import config

CFG = config()


class SharedUniverseExportCreate(BaseModel):
    key: str
    name_uk: str
    name_en: str
    description_uk: str
    description_en: str


class SharedUniversesJSONFile(BaseModel):
    shared_universes: list[SharedUniverseExportCreate]


class BaseSharedUniverse(BaseModel):
    key: str
    name: str
    description: str
