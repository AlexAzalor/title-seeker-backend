from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schema.actor import ActorOut
from app.schema.director import DirectorOut
from app.schema.genre import GenreOut
from app.schema.rating import RatingCriterion
from app.schema.specifications import SpecificationOut
from app.schema.keyword import KeywordOut
from app.schema.action_time import ActionTimeOut
from config import config

CFG = config()


class MovieExportCreate(BaseModel):
    key: str
    title_uk: str
    title_en: str
    description_uk: str
    description_en: str
    release_date: datetime
    duration: int
    budget: int
    domestic_gross: int | None = None
    worldwide_gross: int | None = None
    poster: str | None = None
    actors_ids: list[int]
    directors_ids: list[int]
    location_uk: str
    location_en: str
    users_ratings: list[dict[int, float]]
    rating_criterion: RatingCriterion
    # Genres
    genres_ids: list[int]
    genre_percentage_match_list: list[dict[int, float]]
    # Subgenres
    subgenres_ids: list[int] | None = None
    subgenre_percentage_match_list: list[dict[int, float]] | None = None
    # Specifications
    specifications_ids: list[int]
    specifications_list: list[dict[int, float]]
    # Keywords
    keywords_ids: list[int]
    keywords_list: list[dict[int, float]]
    # Action times
    action_times_ids: list[int]
    action_times_list: list[dict[int, float]]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MoviesJSONFile(BaseModel):
    movies: list[MovieExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieActor(BaseModel):
    key: str
    first_name: str
    last_name: str
    character_name: str
    avatar_url: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieDirector(BaseModel):
    key: str
    first_name: str
    last_name: str
    avatar_url: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieGenre(BaseModel):
    key: str
    name: str
    description: str | None = None
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieSubgenre(BaseModel):
    key: str
    parent_genre: MovieGenre
    name: str
    description: str | None = None
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieGenres(BaseModel):
    genres: list[MovieGenre]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieRating(BaseModel):
    uuid: str
    rating: float
    comment: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserRatingCriteria(BaseModel):
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


class MovieSpecification(BaseModel):
    key: str
    name: str
    description: str | None = None
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieKeyword(BaseModel):
    key: str
    name: str
    description: str | None = None
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieActionTime(BaseModel):
    key: str
    name: str
    description: str | None = None
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieOut(BaseModel):
    key: str
    title: str
    description: str
    release_date: datetime | None = None
    duration: str
    budget: str
    domestic_gross: str | None = None
    worldwide_gross: str | None = None
    actors: list[MovieActor] = []
    poster: str | None = None
    directors: list[MovieDirector] = []
    genres: list[MovieGenre] = []
    subgenres: list[MovieSubgenre] = []
    ratings: list[MovieRating]
    average_rating: float
    ratings_count: int
    user_rating: UserRatingCriteria | None = None
    rating_criterion: RatingCriterion
    specifications: list[MovieSpecification] = []
    keywords: list[MovieKeyword] = []
    action_times: list[MovieActionTime] = []

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieOutList(BaseModel):
    movies: list[MovieOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MoviePreviewOut(BaseModel):
    key: str
    title: str
    poster: str | None = None
    release_date: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MoviePreviewOutList(BaseModel):
    movies: list[MoviePreviewOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieSearchOut(BaseModel):
    key: str
    title: str
    poster: str | None = None
    release_date: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ActorShort(BaseModel):
    key: str
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieSearchResult(BaseModel):
    movies: list[MovieSearchOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieByActorsList(BaseModel):
    movies: list[MovieSearchOut]
    actor: list[ActorShort] | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieFiltersListOut(BaseModel):
    genres: list[GenreOut]
    actors: list[ActorOut]
    directors: list[DirectorOut]
    specifications: list[SpecificationOut]
    keywords: list[KeywordOut]
    action_times: list[ActionTimeOut]

    model_config = ConfigDict(
        from_attributes=True,
    )
