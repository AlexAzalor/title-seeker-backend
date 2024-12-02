from datetime import datetime

from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class ActorExportCreate(BaseModel):
    first_name_uk: str
    last_name_uk: str
    first_name_en: str
    last_name_en: str
    born: datetime
    died: datetime | None = None
    born_in_uk: str
    born_in_en: str
    character_name_uk: str
    character_name_en: str
    movies: list[int]
    avatar: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ActorsJSONFile(BaseModel):
    actors: list[ActorExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )
