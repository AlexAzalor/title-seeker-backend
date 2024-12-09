from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.models.mixins import CreatableMixin, UpdatableMixin
from app.schema.language import Language
from .movie_directors import movie_directors

from .utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .movie import Movie
    from .director_translation import DirectorTranslation


class Director(db.Model, ModelMixin, CreatableMixin, UpdatableMixin):
    __tablename__ = "directors"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False, unique=True)

    born: orm.Mapped[datetime] = orm.mapped_column(sa.DateTime, nullable=False)
    died: orm.Mapped[datetime | None] = orm.mapped_column(sa.DateTime, nullable=True)

    avatar: orm.Mapped[str | None] = orm.mapped_column(sa.String(255), nullable=True)

    translations: orm.Mapped[list["DirectorTranslation"]] = orm.relationship(
        "DirectorTranslation",
        back_populates="director",
    )

    movies: orm.Mapped[list["Movie"]] = orm.relationship(
        "Movie",
        secondary=movie_directors,
        back_populates="directors",
    )

    def full_name(self, lang: Language = Language.UK) -> str:
        return next((t.full_name for t in self.translations if t.language == lang.value))

    def __repr__(self):
        return f"<Director [{self.id}]: {self.translations[0].full_name}>"
