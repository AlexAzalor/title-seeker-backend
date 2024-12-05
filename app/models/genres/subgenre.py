import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from app.models.mixins import CreatableMixin, UpdatableMixin
from .movie_subgenres import movie_subgenres

from ..utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .subgenre_translation import SubgenreTranslation
    from .genre import Genre
    from ..movie import Movie


class Subgenre(db.Model, ModelMixin, CreatableMixin, UpdatableMixin):
    __tablename__ = "subgenres"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(36), nullable=False)
    genre_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("genres.id"), nullable=False)

    translations: orm.Mapped[list["SubgenreTranslation"]] = orm.relationship()

    genre: orm.Mapped["Genre"] = orm.relationship(
        "Genre",
        back_populates="subgenres",
    )

    movies: orm.Mapped[list["Movie"]] = orm.relationship(
        "Movie",
        secondary=movie_subgenres,
        back_populates="subgenres",
    )

    def __repr__(self):
        return f"<Subgenre [{self.id}] - {self.translations[0].name}>"
