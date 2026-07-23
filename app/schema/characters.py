from typing import Annotated

import json
from pydantic import BaseModel, model_validator
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


class CharacterFormFieldsOut(BaseModel):
    id: int
    key: str
    name_uk: str
    name_en: str


class CharacterFormPutIn(BaseModel):
    """Form for updating a new character"""

    id: int
    key: str
    name_en: str
    name_uk: str

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value
