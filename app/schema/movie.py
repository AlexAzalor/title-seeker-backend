from datetime import datetime
from enum import Enum
import json

from fastapi import File, UploadFile
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schema.actor import ActorOut
from app.schema.director import DirectorOut
from app.schema.genre import GenreOut, SubgenreOut
from app.schema.rating import RatingCriterion
from app.schema.shared_universe import SharedUniversePreCreateOut
from app.schema.specifications import SpecificationOut
from app.schema.keyword import KeywordOut
from app.schema.action_time import ActionTimeOut
from config import config

CFG = config()


class RelatedMovie(Enum):
    BASE = "base"
    # A direct continuation of the story. (e.g., The Lord of the Rings: The Two Towers after The Fellowship of the Ring).
    SEQUEL = "sequel"
    # A story set before the original movie. (e.g., Rogue One before Star Wars: A New Hope).
    PREQUEL = "prequel"
    # A movie focusing on a secondary character or element from the original film. (e.g., Logan from X-Men).
    SPIN_OFF = "spin_off"
    # A new version of a movie with updated visuals, cast, and sometimes story changes. (e.g., The Lion King (2019) after The Lion King (1994)).
    REMAKE = "remake"
    # A fresh start for a franchise, often ignoring previous installments. (e.g., The Amazing Spider-Man (2012) rebooting Spider-Man (2002)).
    REBOOT = "reboot"
    # A movie combining characters or elements from different franchises. (e.g., Freddy vs. Jason or Avengers: Endgame).
    CROSSOVER = "crossover"
    # A movie that diverges from an established timeline. (e.g., X-Men: Days of Future Past creates a new timeline).
    ALTERNATIVE_TIMELINE = "alternative_timeline"
    # A Shared Universe refers to a collection of movies that exist within the same fictional world, often featuring overlapping characters, events, and storylines. (e.g., the Marvel Cinematic Universe).
    SHARED_UNIVERSE = "shared_universe"


class MovieExportCreate(BaseModel):
    id: int
    key: str
    title_uk: str
    title_en: str
    description_uk: str
    description_en: str
    release_date: datetime | None = None
    duration: int
    budget: int
    domestic_gross: int | None = None
    worldwide_gross: int | None = None
    poster: str | None = None
    actors_ids: list[int]
    directors_ids: list[int]
    location_uk: str
    location_en: str
    # users_ratings: list[dict[int, float]]
    rating_criterion: RatingCriterion
    # Genres
    genres_list: list[dict[int, float]]
    genres_ids: list[int]
    # Subgenres
    subgenres_list: list[dict[int, float]] | None = None
    subgenres_ids: list[int] | None = None
    # Specifications
    specifications_list: list[dict[int, float]]
    specifications_ids: list[int]
    # Keywords
    keywords_list: list[dict[int, float]]
    keywords_ids: list[int]
    # Action times
    action_times_list: list[dict[int, float]]
    action_times_ids: list[int]

    relation_type: RelatedMovie | None = None
    base_movie_id: int | None = None
    collection_order: int | None = None

    shared_universe_id: int | None = None
    shared_universe_order: int | None = None

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
    description: str
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieSubgenre(BaseModel):
    key: str
    parent_genre: MovieGenre
    name: str
    description: str
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


class MovieSpecification(BaseModel):
    key: str
    name: str
    description: str
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieKeyword(BaseModel):
    key: str
    name: str
    description: str
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieActionTime(BaseModel):
    key: str
    name: str
    description: str
    percentage_match: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class RelatedMovieOut(BaseModel):
    key: str
    title: str
    relation_type: RelatedMovie
    poster: str


class SharedUniverseMovies(BaseModel):
    key: str
    title: str
    poster: str
    order: int | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class SharedUniverseOut(BaseModel):
    key: str
    name: str
    description: str
    movies: list[SharedUniverseMovies]


class MovieOut(BaseModel):
    key: str
    title: str
    description: str
    location: str
    release_date: datetime
    duration: str
    budget: str
    domestic_gross: str
    worldwide_gross: str
    actors: list[MovieActor]
    poster: str
    directors: list[MovieDirector]
    genres: list[MovieGenre] = []
    subgenres: list[MovieSubgenre] = []
    ratings: list[MovieRating]
    average_rating: float
    ratings_count: int
    user_rating: UserRatingCriteria | None = None
    rating_criterion: RatingCriterion
    specifications: list[MovieSpecification]
    keywords: list[MovieKeyword]
    action_times: list[MovieActionTime]

    related_movies: list[RelatedMovieOut] | None = None
    shared_universe: SharedUniverseOut | None = None

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
    release_date: datetime
    duration: str
    main_genre: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class TempMovie(BaseModel):
    key: str
    title_en: str
    rating: float

    model_config = ConfigDict(
        from_attributes=True,
    )


class MoviePreviewOutList(BaseModel):
    movies: list[MoviePreviewOut]
    # Temporary new movies
    temporary_movies: list[TempMovie]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieSearchOut(BaseModel):
    key: str
    title_en: str
    title_uk: str
    poster: str | None = None
    release_date: datetime
    duration: str
    main_genre: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class ActorShort(BaseModel):
    key: str
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieSuperSearchResult(BaseModel):
    movies: list[MoviePreviewOut]

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
    subgenres: list[SubgenreOut]
    actors: list[ActorOut]
    directors: list[DirectorOut]
    specifications: list[SpecificationOut]
    keywords: list[KeywordOut]
    action_times: list[ActionTimeOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieFilterField(BaseModel):
    key: str
    percentage_match: float
    subgenre_parent_key: str = Field(None, alias="subgenre_parent_key")
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class MoviePersonFilterField(BaseModel):
    key: str
    character_key: str
    character_name_uk: str
    character_name_en: str


class MovieIn(BaseModel):
    id: int
    key: str
    title_uk: str
    title_en: str
    description_uk: str
    description_en: str
    release_date: str
    duration: int
    budget: int
    domestic_gross: int
    worldwide_gross: int
    poster: str
    location_uk: str
    location_en: str
    actors_keys: list[MoviePersonFilterField]
    directors_keys: list[str]
    genres: list[MovieFilterField]
    subgenres: list[MovieFilterField]
    specifications: list[MovieFilterField]
    keywords: list[MovieFilterField]
    action_times: list[MovieFilterField]
    rating_criterion_type: RatingCriterion
    rating_criteria: UserRatingCriteria
    rating: float
    file: UploadFile = File(None)

    model_config = ConfigDict(
        from_attributes=True,
    )


class QuickMovieFormData(BaseModel):
    key: str
    title_en: str
    rating_criterion_type: RatingCriterion
    rating_criteria: UserRatingCriteria
    rating: float


class QuickMovieJSON(BaseModel):
    movies: list[QuickMovieFormData]


class MoviePreCreateData(BaseModel):
    actors: list[ActorOut]
    directors: list[DirectorOut]
    genres: list[GenreOut]
    specifications: list[SpecificationOut]
    keywords: list[KeywordOut]
    action_times: list[ActionTimeOut]
    temporary_movie: QuickMovieFormData | None = None
    shared_universes: list[SharedUniversePreCreateOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieFormData(BaseModel):
    key: str
    title_uk: str
    title_en: str
    description_uk: str
    description_en: str
    release_date: str
    duration: int
    budget: int
    actors_keys: list[MoviePersonFilterField]
    directors_keys: list[str]
    genres: list[MovieFilterField]
    subgenres: list[MovieFilterField]
    specifications: list[MovieFilterField]
    keywords: list[MovieFilterField]
    action_times: list[MovieFilterField]
    rating_criterion_type: RatingCriterion
    rating_criteria: UserRatingCriteria
    rating: float
    domestic_gross: int | None = None
    worldwide_gross: int | None = None
    poster: str | None = None
    location_uk: str | None = None
    location_en: str | None = None

    collection_order: int | None = None
    relation_type: RelatedMovie | None = None
    base_movie_key: str | None = None

    shared_universe_key: str | None = None
    shared_universe_order: int | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class ActorSimple(BaseModel):
    key: str
    full_name: str
    avatar_url: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class DirectorSimple(BaseModel):
    key: str
    full_name: str
    avatar_url: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieCarousel(BaseModel):
    key: str
    title: str
    poster: str
    release_date: datetime
    duration: str
    location: str
    description: str

    genres: list[MovieGenre]
    actors: list[ActorSimple]
    directors: list[DirectorSimple]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieCarouselList(BaseModel):
    movies: list[MovieCarousel]

    model_config = ConfigDict(
        from_attributes=True,
    )
