from enum import Enum
from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"


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
