from app.database import db
from sqlalchemy import orm
import sqlalchemy as sa

from app.models.utils import ModelMixin

from .movie_specifications import movie_specifications

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .specification_translation import SpecificationTranslation
    from ..movie import Movie


class Specification(db.Model, ModelMixin):
    __tablename__ = "specifications"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False, unique=True, index=True)

    translations: orm.Mapped[list["SpecificationTranslation"]] = orm.relationship()

    movies: orm.Mapped[list["Movie"]] = orm.relationship(
        "Movie",
        secondary=movie_specifications,
        back_populates="specifications",
    )

    def __repr__(self):
        return f"<Specification [{self.id}]: {self.key}>"
