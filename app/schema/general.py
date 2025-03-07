from enum import Enum
from config import config

CFG = config()


class TitleType(Enum):
    MOVIES = "movies"
    TVSERIES = "tvseries"
    ANIME = "anime"
    GAMES = "games"
