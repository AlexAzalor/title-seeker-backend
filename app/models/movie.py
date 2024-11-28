from datetime import datetime
from uuid import uuid4


import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.models.mixins import CreatableMixin, UpdatableMixin
import app.schema as s

from .utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .movie_translation import MovieTranslation


# Questions/Ideas:
# 1. add future releases? will watch list be implemented?
# 2. Add Notes - only for me. Not visible to others. There will be some notes about the movie, where to watch, etc.
# 3. Tags - for filtering movies. May be useful in the future. But with limit, not 1000 tags per movie.


class Movie(db.Model, ModelMixin, CreatableMixin, UpdatableMixin):
    __tablename__ = "movies"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    # title, description
    translations: orm.Mapped[list["MovieTranslation"]] = orm.relationship(
        "MovieTranslation",
        back_populates="movie",
    )
    release_date: orm.Mapped[datetime | None] = orm.mapped_column(sa.DateTime)  # None?
    duration: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)  # in minutes
    # my_rating: orm.Mapped[float | None] = orm.mapped_column(sa.Float, nullable=True)
    budget: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)
    # Box office
    domestic_gross: orm.Mapped[int | None] = orm.mapped_column(sa.Integer, nullable=True)
    worldwide_gross: orm.Mapped[int | None] = orm.mapped_column(sa.Integer, nullable=True)
    # rating - relationship? or just a column? There will be very advanced rating system.
    # genre - relationship
    # director - relationship
    # actors - relationship
    # location - relationship
    # poster_url - column or relationship?

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
        return f"<Movie [{self.id}]>"
