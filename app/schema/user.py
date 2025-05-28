from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"
    OWNER = "owner"


class UserExportCreate(BaseModel):
    id: int
    first_name: str
    last_name: str
    role: UserRole
    email: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class UsersJSONFile(BaseModel):
    users: list[UserExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


# TODO: Enum?
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

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserRateMovieIn(BaseModel):
    uuid: str
    movie_key: str
    rating: float
    rating_criteria: RatingCriteria

    model_config = ConfigDict(
        from_attributes=True,
    )


class TimeRateMovieOut(BaseModel):
    created_at: datetime
    rating: float
    movie_title: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieChartData(BaseModel):
    movie_chart_data: list[TimeRateMovieOut]


class GenreChartDataOut(BaseModel):
    name: str
    count: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class TopMyMoviesOut(BaseModel):
    key: str
    title: str
    rating: float
    poster: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class GenreChartDataList(BaseModel):
    genre_data: list[GenreChartDataOut]
    top_rated_movies: list[TopMyMoviesOut]
    joined_date: datetime
    movies_rated: int
    last_movie_rate_date: datetime | None
    total_actors_count: int | None = None


class UserOut(BaseModel):
    uuid: str
    full_name: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class UsersListOut(BaseModel):
    users: list[UserOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class CriterionRatingIn(BaseModel):
    key: str
    rating: int
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class TitleVisualProfileIn(BaseModel):
    movie_key: str
    category_key: str
    criteria: list[CriterionRatingIn]

    model_config = ConfigDict(
        from_attributes=True,
    )


class CategoryCriterionData(BaseModel):
    key: str
    name: str
    description: str
    rating: int

    model_config = ConfigDict(
        from_attributes=True,
    )


class TitleCategoryData(BaseModel):
    key: str
    name: str
    description: str
    criteria: list[CategoryCriterionData]

    model_config = ConfigDict(
        from_attributes=True,
    )
