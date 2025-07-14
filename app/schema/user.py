from datetime import datetime
from enum import Enum
from pydantic import BaseModel

from config import config

CFG = config()


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"
    OWNER = "owner"

    def has_permissions(self):
        return self in {UserRole.OWNER, UserRole.ADMIN}

    def is_owner(self):
        return self == UserRole.OWNER

    @staticmethod
    def get_admin_roles():
        return [UserRole.ADMIN.value, UserRole.OWNER.value]


class UserExportCreate(BaseModel):
    id: int
    first_name: str
    last_name: str
    role: UserRole
    email: str


class UsersJSONFile(BaseModel):
    users: list[UserExportCreate]


class RatingCriteria(BaseModel):
    acting: float
    plot_storyline: float
    script_dialogue: float
    music: float
    enjoyment: float
    production_design: float
    # Additional
    visual_effects: float | None = None
    scare_factor: float | None = None
    humor: float | None = None
    animation_cartoon: float | None = None


class UserRateMovieIn(BaseModel):
    uuid: str
    movie_key: str
    rating: float
    rating_criteria: RatingCriteria


class TimeRateMovieOut(BaseModel):
    created_at: datetime
    rating: float
    movie_title: str


class MovieChartData(BaseModel):
    movie_chart_data: list[TimeRateMovieOut]


class GenreChartDataOut(BaseModel):
    name: str
    count: int


class TopMyMoviesOut(BaseModel):
    key: str
    title: str
    rating: float
    poster: str


class UserInfoReport(BaseModel):
    genre_data: list[GenreChartDataOut]
    top_rated_movies: list[TopMyMoviesOut]
    joined_date: datetime
    movies_rated: int
    last_movie_rate_date: datetime | None
    total_actors_count: int | None = None
    total_directors_count: int | None = None


class UserOut(BaseModel):
    uuid: str
    full_name: str
    email: str
    role: UserRole
    created_at: datetime
    ratings_count: int
    last_movie_rate_date: datetime | None


class UsersListOut(BaseModel):
    users: list[UserOut]
