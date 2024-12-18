from app.database import db
from sqlalchemy import orm
import sqlalchemy as sa

from app.models.utils import ModelMixin

from .movie_keywords import movie_keywords

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .keyword_translation import KeywordTranslation
    from ..movie import Movie


class Keyword(db.Model, ModelMixin):
    __tablename__ = "keywords"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False, unique=True, index=True)

    translations: orm.Mapped[list["KeywordTranslation"]] = orm.relationship()

    movies: orm.Mapped[list["Movie"]] = orm.relationship(
        "Movie",
        secondary=movie_keywords,
        back_populates="keywords",
    )

    def __repr__(self):
        return f"<Keywords [{self.id}]: {self.key}>"
