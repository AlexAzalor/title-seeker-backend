from enum import Enum
from typing import Annotated
from pydantic import BaseModel
from config import config
from pydantic.json_schema import WithJsonSchema

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


class SearchResult(BaseModel):
    key: str
    name: str
    type: SearchType
    image: str | None = None
    extra_info: str | None = None


class SearchResults(BaseModel):
    results: list[SearchResult]


class MainItemMenu(BaseModel):
    """For ItemsSelector menu on the frontend"""

    key: str
    name: str
    # To search for items regardless of the user's chosen language
    another_lang_name: str
    movie_count: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
