from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from .movie_actors import movie_actors
from .movie_directors import movie_directors
from .genres.movie_genres import movie_genres
from .genres.movie_subgenres import movie_subgenres

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
    budget: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)
    # Box office
    domestic_gross: orm.Mapped[int | None] = orm.mapped_column(sa.Integer, nullable=True)
    worldwide_gross: orm.Mapped[int | None] = orm.mapped_column(sa.Integer, nullable=True)
    poster: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=True)

    actors: orm.Mapped[list["Actor"]] = orm.relationship(
        "Actor",
        secondary=movie_actors,
        back_populates="movies",
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

    ratings: orm.Mapped[list["Rating"]] = orm.relationship("Rating", back_populates="movie")
    average_rating: orm.Mapped[float] = orm.mapped_column(sa.Float, default=0.00)
    ratings_count: orm.Mapped[int] = orm.mapped_column(sa.Integer, default=0)
    rating_criterion: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=s.RatingCriterion.BASIC.value)

    # rating - relationship? or just a column? There will be very advanced rating system.
    # related_movies - relationship
    # similar_movies - relationship or property?

    # Not for MVP
    # reviews - relationship
    # screenshots - relationship
    # pegi_rating - enum?

    # created_at: orm.Mapped[datetime] = orm.mapped_column(
    #     sa.DateTime,
    #     default=datetime.now(UTC),
    # )

    # updated_at: orm.Mapped[sa.DateTime] = orm.mapped_column(
    #     sa.DateTime,
    #     default=sa.func.now(),
    #     onupdate=sa.func.now(),
    # )

    is_deleted: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, default=False)

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

    def __repr__(self):
        return f"<Movie [{self.id}]: {self.translations[0].title}>"
