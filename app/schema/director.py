from datetime import datetime

from fastapi import UploadFile
from pydantic import BaseModel

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


class DirectorsJSONFile(BaseModel):
    directors: list[DirectorExportCreate]


class DirectorOut(BaseModel):
    key: str
    name: str


class DirectorListOut(BaseModel):
    directors: list[DirectorOut]


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
