import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
import app.schema as s

from app.models.mixins import CreatableMixin, UpdatableMixin

from .utils import ModelMixin
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .movie import Movie
    from .shared_universe_i18n import SharedUniverseTranslation


class SharedUniverse(db.Model, ModelMixin, CreatableMixin, UpdatableMixin):
    __tablename__ = "shared_universes"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False, unique=True)

    translations: orm.Mapped[list["SharedUniverseTranslation"]] = orm.relationship()
    movies: orm.Mapped[List["Movie"]] = orm.relationship("Movie", back_populates="shared_universe")

    def __repr__(self):
        return f"<SU: {self.translations[0].name} [{self.id}]>"

    def get_name(self, language: s.Language = s.Language.UK) -> str:
        return next((t.name for t in self.translations if t.language == language.value), self.translations[0].name)

    def get_description(self, language: s.Language = s.Language.UK) -> str:
        return next(
            (t.description for t in self.translations if t.language == language.value), self.translations[0].description
        )
