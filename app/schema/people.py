from datetime import datetime
import json
from pydantic import BaseModel, model_validator

from app.schema.general import MainItemMenu
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


class PersonWithAvatar(BaseModel):
    key: str
    full_name: str
    avatar_url: str


# Only one place
class TopPerson(PersonBase):
    avatar_url: str
    movie_count: int


# Only one place
class PeopleList(BaseModel):
    people: list[TopPerson]


class PersonFields(BaseModel):
    key: str
    first_name_uk: str
    last_name_uk: str
    first_name_en: str
    last_name_en: str
    born_in_uk: str
    born_in_en: str


class PersonForm(PersonFields):
    """Form for creating a new person"""

    born: str
    died: str | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class PersonFormWithID(PersonFields):
    id: int
    born: datetime
    died: datetime | None = None


class MoviePersonOut(BaseModel):
    key: str
    full_name: str
    avatar_url: str
    born_location: str
    age: int
    born: datetime
    died: datetime | None = None


class MovieActorOut(MoviePersonOut):
    character_name: str


class ActorOut(PersonBase):
    movie_count: int


class PeopleListOut(BaseModel):
    people: list[MainItemMenu]
