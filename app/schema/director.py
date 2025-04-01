from datetime import datetime

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class DirectorExportCreate(BaseModel):
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


class DirectorsJSONFile(BaseModel):
    directors: list[DirectorExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class DirectorOut(BaseModel):
    key: str
    name: str
    name_uk: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class DirectorListOut(BaseModel):
    directors: list[DirectorOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


# not use on front
class DirectorIn(BaseModel):
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
