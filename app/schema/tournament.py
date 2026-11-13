from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.schema.movie import MoviePreviewOut


TournamentKey = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class TournamentCollectionType(str, Enum):
    STANDALONE = "standalone"
    BASE = "base"


class MovieTournamentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    size: Literal[16, 32]
    include_genres: list[TournamentKey] = Field(default_factory=list)
    exclude_genres: list[TournamentKey] = Field(default_factory=list)
    genre_threshold: float = Field(
        default=100,
        ge=60,
        le=100,
        allow_inf_nan=False,
        description="Minimum stored match percentage for each included genre.",
    )
    include_specifications: list[TournamentKey] = Field(default_factory=list)
    exclude_specifications: list[TournamentKey] = Field(default_factory=list)
    specification_threshold: float = Field(
        default=100,
        ge=60,
        le=100,
        allow_inf_nan=False,
        description="Minimum stored match percentage for each included specification.",
    )
    collection_type: TournamentCollectionType | None = None
    exclude_movies: list[TournamentKey] = Field(default_factory=list)
    exclude_shared_universes: list[TournamentKey] = Field(default_factory=list)

    @field_validator(
        "include_genres",
        "exclude_genres",
        "include_specifications",
        "exclude_specifications",
        "exclude_movies",
        "exclude_shared_universes",
    )
    @classmethod
    def unique_keys(cls, keys: list[str]) -> list[str]:
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate keys are not allowed")
        return keys


class MovieTournamentOut(BaseModel):
    movies: list[MoviePreviewOut]
    total: int
