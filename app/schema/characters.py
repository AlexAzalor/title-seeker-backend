from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class CharacterExportCreate(BaseModel):
    key: str
    name_uk: str
    name_en: str
    actors_ids: list[int]
    movies_ids: list[int]

    model_config = ConfigDict(
        from_attributes=True,
    )


class CharactersJSONFile(BaseModel):
    characters: list[CharacterExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )
