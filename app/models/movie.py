from datetime import datetime
from functools import cached_property

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from .movie_actors import movie_actors
from .movie_directors import movie_directors
from .genres.movie_genres import movie_genres
from .genres.movie_subgenres import movie_subgenres
from .movie_filters.movie_specifications import movie_specifications
from .movie_filters.movie_keywords import movie_keywords
from .movie_filters.movie_action_times import movie_action_times

from app.models.mixins import CreatableMixin, UpdatableMixin
import app.schema as s

from .utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .movie_translation import MovieTranslation
    from .actor import Actor
    from .director import Director
    from .genres.genre import Genre
    from .genres.subgenre import Subgenre
    from .rating import Rating
    from .character import Character
    from .movie_filters.specification import Specification
    from .movie_filters.keyword import Keyword
    from .movie_filters.action_time import ActionTime
    from .shared_universe import SharedUniverse
    from .movie_actor_character import MovieActorCharacter


# Questions/Ideas:
# 1. add future releases? will watch list be implemented?
# 2. Add Notes - only for me. Not visible to others. There will be some notes about the movie, where to watch, etc.
# 3. Tags - for filtering movies. May be useful in the future. But with limit, not 1000 tags per movie.


class Movie(db.Model, ModelMixin, CreatableMixin, UpdatableMixin):
    __tablename__ = "movies"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False, unique=True)

    # title, description
    translations: orm.Mapped[list["MovieTranslation"]] = orm.relationship()

    release_date: orm.Mapped[datetime | None] = orm.mapped_column(sa.DateTime)  # None?
    duration: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)  # in minutes
    # my_rating: orm.Mapped[float | None] = orm.mapped_column(sa.Float, nullable=True)
    budget: orm.Mapped[int] = orm.mapped_column(sa.BigInteger, nullable=False)
    # Box office
    domestic_gross: orm.Mapped[int | None] = orm.mapped_column(sa.BigInteger, nullable=True)
    worldwide_gross: orm.Mapped[int | None] = orm.mapped_column(sa.BigInteger, nullable=True)
    poster: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=True)

    actors: orm.Mapped[list["Actor"]] = orm.relationship(
        "Actor",
        secondary=movie_actors,
        back_populates="movies",
    )

    characters: orm.Mapped[list["MovieActorCharacter"]] = orm.relationship(
        "MovieActorCharacter", back_populates="movie"
    )

    directors: orm.Mapped[list["Director"]] = orm.relationship(
        "Director",
        secondary=movie_directors,
        back_populates="movies",
    )

    genres: orm.Mapped[list["Genre"]] = orm.relationship(
        "Genre",
        secondary=movie_genres,
        back_populates="movies",
    )
    subgenres: orm.Mapped[list["Subgenre"]] = orm.relationship(
        "Subgenre",
        secondary=movie_subgenres,
        back_populates="movies",
    )

    specifications: orm.Mapped[list["Specification"]] = orm.relationship(
        "Specification",
        secondary=movie_specifications,
        back_populates="movies",
    )

    keywords: orm.Mapped[list["Keyword"]] = orm.relationship(
        "Keyword",
        secondary=movie_keywords,
        back_populates="movies",
    )

    action_times: orm.Mapped[list["ActionTime"]] = orm.relationship(
        "ActionTime",
        secondary=movie_action_times,
        back_populates="movies",
    )

    ratings: orm.Mapped[list["Rating"]] = orm.relationship("Rating", back_populates="movie")
    average_rating: orm.Mapped[float] = orm.mapped_column(sa.Float, default=0.00)
    ratings_count: orm.Mapped[int] = orm.mapped_column(sa.Integer, default=0)
    rating_criterion: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=s.RatingCriterion.BASIC.value)
    average_by_criteria: orm.Mapped[dict[str, float | None]] = orm.mapped_column(sa.JSON, nullable=True)

    collection_order: orm.Mapped[int | None] = orm.mapped_column(sa.Integer, nullable=True)  # Order in collection

    relation_type: orm.Mapped[str | None] = orm.mapped_column(sa.String(36), nullable=True)

    # Collection ID (self-referential)
    collection_base_movie_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("movies.id"), nullable=True)
    # Relationship to get all movies in the same collection
    collection_base_movie: orm.Mapped["Movie"] = orm.relationship(
        "Movie",
        remote_side=[id],
        # Except the base movie
        backref="collection_members",
    )

    # Universe: A larger group of movies
    shared_universe_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("shared_universes.id"), nullable=True)
    shared_universe: orm.Mapped["SharedUniverse"] = orm.relationship("SharedUniverse", back_populates="movies")
    shared_universe_order: orm.Mapped[int | None] = orm.mapped_column(sa.Integer, nullable=True)

    # similar_movies - relationship or property? Dynamic or static? For static run script to fill it.

    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

    def __repr__(self):
        return f"<Movie [{self.id}]: {self.translations[0].title}>"

    @property
    def formatted_budget(self):
        return "${:,.0f}".format(self.budget)

    @property
    def formatted_domestic_gross(self):
        return "${:,.0f}".format(self.domestic_gross) if self.domestic_gross else None

    @property
    def formatted_worldwide_gross(self):
        return "${:,.0f}".format(self.worldwide_gross) if self.worldwide_gross else None

    def formatted_duration(self, lang=s.Language.UK.value):
        hours = self.duration // 60
        minutes = self.duration % 60
        if lang == "en":
            return f"{hours}h {minutes}m"
        elif lang == s.Language.UK.value:
            return f"{hours}г {minutes}хв"
        else:
            raise ValueError("Unsupported language")

    @cached_property
    def related_movies_collection(self) -> list["Movie"]:
        """Return all movies in the collection, ordered by collection_order."""
        base_movie = self.collection_base_movie or self  # Get the base movie
        return sorted(
            [base_movie] + base_movie.collection_members,
            key=lambda movie: (movie.collection_order if movie.collection_order is not None else float("inf")),
        )

    # float("inf") - positive infinity
    # Used here to ensure movies without a collection_order appear at the end of the sorted list.

    def get_title(self, language: s.Language = s.Language.UK) -> str:
        return next((t.title for t in self.translations if t.language == language.value), self.translations[0].title)

    def get_description(self, language: s.Language = s.Language.UK) -> str:
        return next(
            (t.description for t in self.translations if t.language == language.value), self.translations[0].description
        )

    def get_location(self, language: s.Language = s.Language.UK) -> str:
        return next(
            (t.location for t in self.translations if t.language == language.value), self.translations[0].location
        )

    def get_character(self, actor_id: int, lang: s.Language) -> str:
        """Get the character name for the actor in the specified language."""

        character: Character | None = next((c.character for c in self.characters if c.actor_id == actor_id), None)

        if not character:
            raise ValueError(f"Character not found for actor_id: {actor_id}")

        return character.get_name(lang)
