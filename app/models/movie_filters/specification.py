from uuid import uuid4

from app.database import db
from sqlalchemy import orm
import sqlalchemy as sa
import app.schema as s

from app.models.utils import ModelMixin

from .movie_specifications import movie_specifications

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .specification_translation import SpecificationTranslation
    from ..movie import Movie


class Specification(db.Model, ModelMixin):
    __tablename__ = "specifications"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()), nullable=True)

    key: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False, unique=True, index=True)

    translations: orm.Mapped[list["SpecificationTranslation"]] = orm.relationship()

    movies: orm.Mapped[list["Movie"]] = orm.relationship(
        "Movie",
        secondary=movie_specifications,
        back_populates="specifications",
    )

    def __repr__(self):
        return f"<Specification [{self.id}]: {self.key}>"

    def get_name(self, lang: s.Language = s.Language.UK) -> str:
        return next((t.name for t in self.translations if t.language == lang.value), self.translations[0].name)

    def get_description(self, lang: s.Language = s.Language.UK) -> str:
        return next(
            (t.description for t in self.translations if t.language == lang.value), self.translations[0].description
        )
