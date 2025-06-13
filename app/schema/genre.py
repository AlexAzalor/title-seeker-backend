from pydantic import BaseModel

from config import config

CFG = config()


class GenreFormFields(BaseModel):
    key: str
    name_uk: str
    name_en: str
    description_uk: str
    description_en: str
    parent_genre_id: int | None = None


class GenreFormFieldsWithUUID(GenreFormFields):
    uuid: str


class GenresJSONFile(BaseModel):
    items: list[GenreFormFields]


class SubgenreOut(BaseModel):
    key: str
    name: str
    description: str
    parent_genre_key: str


class GenreOut(BaseModel):
    key: str
    name: str
    description: str
    subgenres: list[SubgenreOut]


class GenreListOut(BaseModel):
    genres: list[GenreOut]


class GenreIn(BaseModel):
    key: str
    name_uk: str
    name_en: str
    description_uk: str | None = None
    description_en: str | None = None


class GenreItemOut(BaseModel):
    key: str
    name: str
    description: str
    percentage_match: float
    parent_genre_key: str | None = None


class GenresSubgenresOut(BaseModel):
    genres: list[GenreOut]


class GenreItemFieldEditIn(BaseModel):
    key: str
    name: str
    percentage_match: float


class GenreItemFieldEditFormIn(BaseModel):
    genres: list[GenreItemFieldEditIn]
    subgenres: list[GenreItemFieldEditIn]


class GenreFormIn(BaseModel):
    """Form for creating a new genre and subgenre"""

    key: str
    name_uk: str
    name_en: str
    description_uk: str
    description_en: str
    parent_genre_key: str | None = None


class GenreFormOut(BaseModel):
    key: str
    name: str
    description: str
    parent_genre_key: str | None = None
