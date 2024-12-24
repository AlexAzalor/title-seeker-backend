from datetime import datetime

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class ActorExportCreate(BaseModel):
    id: int
    key: str
    first_name_uk: str
    last_name_uk: str
    first_name_en: str
    last_name_en: str
    born: datetime
    died: datetime | None = None
    born_in_uk: str
    born_in_en: str
    avatar: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ActorsJSONFile(BaseModel):
    actors: list[ActorExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class ActorOut(BaseModel):
    key: str
    full_name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ActorListOut(BaseModel):
    actors: list[ActorOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


# This use for the direcors too
class ActorIn(BaseModel):
    key: str
    first_name_uk: str
    last_name_uk: str
    first_name_en: str
    last_name_en: str
    born: str
    died: str | None = None
    born_in_uk: str
    born_in_en: str
    avatar: UploadFile

    model_config = ConfigDict(
        from_attributes=True,
    )
