from typing import Annotated

from pydantic import BaseModel
from pydantic.json_schema import WithJsonSchema
from config import config

CFG = config()


class CharacterExportCreate(BaseModel):
    id: int
    key: str
    name_uk: str
    name_en: str
    actors_ids: list[int]
    movies_ids: list[int]


class CharactersJSONFile(BaseModel):
    characters: list[CharacterExportCreate]


class CharacterFormIn(BaseModel):
    """Form for creating a new character"""

    key: str
    name_uk: str
    name_en: str


class CharacterOut(BaseModel):
    key: str
    name: str
    movie_count: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
