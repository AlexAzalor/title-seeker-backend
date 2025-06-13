from datetime import datetime
import enum
from pydantic import BaseModel

from config import config

CFG = config()


class RatingCriterion(str, enum.Enum):
    BASIC = "basic"
    VISUAL_EFFECTS = "visual_effects"
    SCARE_FACTOR = "scare_factor"
    HUMOR = "humor"
    ANIMATION_CARTOON = "animation_cartoon"


class BaseRatingCriteria(BaseModel):
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


class RatingExportCreate(BaseRatingCriteria):
    id: int
    movie_id: int
    user_id: int
    rating: float
    comment: str | None = None
    created_at: datetime
    updated_at: datetime


class RatingsJSONFile(BaseModel):
    ratings: list[RatingExportCreate]


class MovieRating(BaseModel):
    uuid: str
    rating: float
    comment: str
