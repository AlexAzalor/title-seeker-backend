from datetime import datetime

from fastapi import UploadFile
from pydantic import BaseModel

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


class ActorsJSONFile(BaseModel):
    actors: list[ActorExportCreate]


class ActorOut(BaseModel):
    key: str
    name: str


class ActorListOut(BaseModel):
    actors: list[ActorOut]


# This use for the direcors too
# Not used in router, how to validate?
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


class Actor(BaseModel):
    key: str
    name: str
    avatar_url: str
    movie_count: int


class ActorsList(BaseModel):
    actors: list[Actor]
