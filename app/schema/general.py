from enum import Enum
from config import config

CFG = config()


class TitleType(Enum):
    MOVIES = "movies"
    TVSERIES = "tvseries"
    ANIME = "anime"
    GAMES = "games"


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
