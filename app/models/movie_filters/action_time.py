from app.database import db
from sqlalchemy import orm
import sqlalchemy as sa
import app.schema as s
from app.models.utils import ModelMixin
from .movie_action_times import movie_action_times


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .action_time_translation import ActionTimeTranslation
    from ..movie import Movie


class ActionTime(db.Model, ModelMixin):
    __tablename__ = "action_times"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False, unique=True, index=True)

    translations: orm.Mapped[list["ActionTimeTranslation"]] = orm.relationship()

    movies: orm.Mapped[list["Movie"]] = orm.relationship(
        "Movie",
        secondary=movie_action_times,
        back_populates="action_times",
    )

    def __repr__(self):
        return f"<ActionTime [{self.id}]: {self.key}>"

    def get_name(self, lang: s.Language = s.Language.UK) -> str:
        return next((t.name for t in self.translations if t.language == lang.value), self.translations[0].name)

    def get_description(self, lang: s.Language = s.Language.UK) -> str:
        return next(
            (t.description for t in self.translations if t.language == lang.value), self.translations[0].description
        )
