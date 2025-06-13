from datetime import datetime

from pydantic import BaseModel

from config import config

CFG = config()


class PersonExportCreate(BaseModel):
    """Schema for exporting person data from google sheet."""

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


class PersonJSONFile(BaseModel):
    people: list[PersonExportCreate]


class PersonBase(BaseModel):
    key: str
    name: str


# Only one place
class Actor(PersonBase):
    avatar_url: str
    movie_count: int

# Only one place
class ActorsList(BaseModel):
    actors: list[Actor]
