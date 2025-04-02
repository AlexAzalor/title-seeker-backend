import sqlalchemy as sa
from sqlalchemy import orm
import app.schema as s
from app.database import db
from .movie_genres import movie_genres

from app.models.mixins import CreatableMixin, UpdatableMixin

from ..utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .genre_translation import GenreTranslation
    from .subgenre import Subgenre
    from ..movie import Movie


class Genre(db.Model, ModelMixin, CreatableMixin, UpdatableMixin):
    __tablename__ = "genres"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(36), nullable=False, unique=True)

    translations: orm.Mapped[list["GenreTranslation"]] = orm.relationship()

    movies: orm.Mapped[list["Movie"]] = orm.relationship(
        "Movie",
        secondary=movie_genres,
        back_populates="genres",
    )

    subgenres: orm.Mapped[list["Subgenre"]] = orm.relationship(
        "Subgenre",
        back_populates="genre",
    )

    def __repr__(self):
        return f"<Genre [{self.id}] - {self.translations[0].name}>"

    def get_name(self, lang: s.Language = s.Language.UK) -> str:
        return next((t.name for t in self.translations if t.language == lang.value), self.translations[0].name)

    def get_description(self, lang: s.Language = s.Language.UK) -> str:
        return next(
            (t.description for t in self.translations if t.language == lang.value), self.translations[0].description
        )
