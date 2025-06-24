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


class GenreShort(BaseModel):
    key: str
    name: str


class GenreBase(GenreShort):
    description: str


class SubgenreOut(GenreBase):
    parent_genre_key: str


class GenreOut(GenreBase):
    subgenres: list[SubgenreOut]


class GenresSubgenresOut(BaseModel):
    genres: list[GenreOut]


class GenreItemFieldEditIn(GenreShort):
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


class GenreFormOut(GenreBase):
    parent_genre_key: str | None = None


class MovieGenre(GenreBase):
    percentage_match: float


class MovieGenres(BaseModel):
    genres: list[MovieGenre]
