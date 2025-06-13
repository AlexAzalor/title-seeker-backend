from enum import Enum
import json
from pydantic import BaseModel, model_validator
from config import config

CFG = config()


class SearchType(Enum):
    MOVIES = "movies"
    TVSERIES = "tvseries"
    ANIME = "anime"
    GAMES = "games"
    ACTORS = "actors"
    DIRECTORS = "directors"
    CHARACTERS = "characters"


class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


class SortBy(Enum):
    RATING = "rating"
    RATINGS_COUNT = "ratings_count"
    RATED_AT = "rated_at"
    RELEASE_DATE = "release_date"
    # CREATED_AT = "created_at"
    RANDOM = "random"
    ID = "id"


class PersonForm(BaseModel):
    """Form for creating a new person"""

    key: str
    first_name_uk: str
    last_name_uk: str
    first_name_en: str
    last_name_en: str
    born: str
    born_in_uk: str
    born_in_en: str
    died: str | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class MovieFilterFormIn(BaseModel):
    """Form for creating a new movie attribute for specification, keyword, action time"""

    key: str
    name_uk: str
    name_en: str
    description_uk: str | None = None
    description_en: str | None = None


class MovieFilterFormOut(BaseModel):
    key: str
    name: str


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


class SearchResult(BaseModel):
    key: str
    name: str
    type: SearchType
    image: str | None = None
    extra_info: str | None = None


class SearchResults(BaseModel):
    results: list[SearchResult]
