import enum
from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class RatingCriterion(enum.Enum):
    BASIC = "basic"
    VISUAL_EFFECTS = "visual_effects"
    SCARE_FACTOR = "scare_factor"
    FULL = "full"


class RatingExportCreate(BaseModel):
    id: int
    movie_id: int
    user_id: int
    rating: float
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
    comment: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class RatingsJSONFile(BaseModel):
    ratings: list[RatingExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )
