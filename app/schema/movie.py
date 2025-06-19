from datetime import datetime
from enum import Enum
import json

from pydantic import BaseModel, Field, model_validator

from app.schema.filters import FilterItemField, FilterItemOut, MovieFilterItem
from app.schema.general import MainItemMenu
from app.schema.genre import GenreOut, MovieGenre, SubgenreOut
from app.schema.pagination import BasePagination
from app.schema.people import MovieActorOut, MoviePersonOut, PersonWithAvatar
from app.schema.rating import MovieRating, RatingCriterion, BaseRatingCriteria
from app.schema.shared_universe import BaseSharedUniverse

from app.schema.visual_profile import VisualProfileCategoryOut, VisualProfileCriterionData, VisualProfileData
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


class BaseMovieForm(BaseModel):
    """Fields with primitive types and enum"""

    key: str
    title_uk: str
    title_en: str
    description_uk: str
    description_en: str
    duration: int
    budget: int
    domestic_gross: int
    worldwide_gross: int
    location_uk: str
    location_en: str
    relation_type: RelatedMovie | None = None
    collection_order: int | None = None
    shared_universe_order: int | None = None


class MovieExportCreate(BaseMovieForm):
    poster: str
    release_date: datetime
    rating_criterion: RatingCriterion
    # People
    actors_ids: list[int]
    directors_ids: list[int]
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

    base_movie_id: int | None = None
    shared_universe_id: int | None = None


class MoviesJSONFile(BaseModel):
    movies: list[MovieExportCreate]


class BaseMovie(BaseModel):
    key: str
    title: str


class MovieMenuItem(BaseModel):
    """For ItemsSelector menu on the frontend"""

    key: str
    name: str


class RelatedMovieOut(BaseMovie):
    relation_type: RelatedMovie
    poster: str


class SharedUniverseMovies(BaseMovie):
    poster: str
    order: int | None = None


class SharedUniverseOut(BaseSharedUniverse):
    movies: list[SharedUniverseMovies]


class SimilarMovieOut(BaseMovie):
    poster: str


class SimilarMovieOutList(BaseModel):
    similar_movies: list[SimilarMovieOut]


class MovieOut(BaseMovie):
    title_en: str | None = None

    # Info
    description: str
    location: str
    release_date: datetime
    duration: str
    budget: str
    domestic_gross: str
    worldwide_gross: str

    # Filters
    actors: list[MovieActorOut]
    poster: str
    directors: list[MoviePersonOut]
    genres: list[MovieFilterItem]
    subgenres: list[MovieFilterItem] = []
    specifications: list[MovieFilterItem]
    keywords: list[MovieFilterItem]
    action_times: list[MovieFilterItem]

    # Visual profile
    visual_profile: VisualProfileData

    # Ratings
    # All movies ratings
    ratings: list[MovieRating]
    ratings_count: int

    # Type
    rating_criterion: RatingCriterion

    # Owner rating
    owner_rating: float

    # User rating
    user_rating: float | None = None
    user_rating_criteria: BaseRatingCriteria | None = None

    # Main AVERAGE rating
    overall_average_rating: float
    overall_average_rating_criteria: BaseRatingCriteria

    # Relations
    related_movies: list[RelatedMovieOut] | None = None
    shared_universe: SharedUniverseOut | None = None
    shared_universe_order: int | None = None

    created_at: datetime


class MoviePreviewOut(BaseMovie):
    poster: str
    release_date: datetime
    duration: str
    main_genre: str
    rating: float


class PaginationDataOut(BasePagination):
    size: int
    items: list[MoviePreviewOut]


class QuickMovie(BaseModel):
    key: str
    title_en: str
    rating: float


class QuickMovieList(BaseModel):
    quick_movies: list[QuickMovie]


class MovieFiltersListOut(BaseModel):
    genres: list[GenreOut]
    subgenres: list[SubgenreOut]
    actors: list[MainItemMenu]
    directors: list[MainItemMenu]
    specifications: list[FilterItemOut]
    keywords: list[FilterItemOut]
    action_times: list[FilterItemOut]
    visual_profile_categories: list[VisualProfileCategoryOut]
    shared_universes: list[BaseSharedUniverse]


class MovieFilterField(FilterItemField):
    subgenre_parent_key: str = Field(None, alias="subgenre_parent_key")


class ActorCharacterKey(BaseModel):
    key: str
    character_key: str


class QuickMovieFormData(BaseModel):
    key: str
    title_en: str
    rating_criterion_type: RatingCriterion
    rating_criteria: BaseRatingCriteria
    rating: float


class QuickMovieJSON(BaseModel):
    movies: list[QuickMovieFormData]


class MoviePreCreateData(BaseModel):
    visual_profile_categories: list[VisualProfileData]
    actors: list[MainItemMenu]
    directors: list[MainItemMenu]
    genres: list[GenreOut]
    specifications: list[FilterItemOut]
    keywords: list[FilterItemOut]
    action_times: list[FilterItemOut]
    quick_movie: QuickMovieFormData | None = None
    shared_universes: list[BaseSharedUniverse]
    base_movies: list[MovieMenuItem]
    characters: list[MainItemMenu]


class MovieFormData(BaseMovieForm):
    release_date: str
    # Rating
    rating: float
    rating_criterion_type: RatingCriterion
    rating_criteria: BaseRatingCriteria
    # People
    actors_keys: list[ActorCharacterKey]
    directors_keys: list[str]
    # Genres
    genres: list[MovieFilterField]
    subgenres: list[MovieFilterField]
    # Filters
    specifications: list[MovieFilterField]
    keywords: list[MovieFilterField]
    action_times: list[MovieFilterField]
    # Related
    base_movie_key: str | None = None
    shared_universe_key: str | None = None
    # Visual profile
    category_key: str
    category_criteria: list[VisualProfileCriterionData]

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class MovieCarousel(BaseMovie):
    poster: str
    release_date: datetime
    duration: str
    location: str
    description: str

    genres: list[MovieGenre]
    actors: list[PersonWithAvatar]
    directors: list[PersonWithAvatar]


class MovieCarouselList(BaseModel):
    movies: list[MovieCarousel]
