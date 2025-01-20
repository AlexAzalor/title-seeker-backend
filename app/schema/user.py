from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class UserExportCreate(BaseModel):
    id: int
    first_name: str
    last_name: str
    description: str | None = None

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
    music: float
    re_watchability: float
    emotional_impact: float
    dialogue: float
    production_design: float
    duration: float

    visual_effects: float | None = None
    scare_factor: float | None = None

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
