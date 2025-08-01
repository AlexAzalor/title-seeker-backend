from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.models.mixins import CreatableMixin, UpdatableMixin
from app.schema.language import Language
from .movie_actors import movie_actors

from .utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .movie import Movie
    from .actor_translation import ActorTranslation
    from .movie_actor_character import MovieActorCharacter


class Actor(db.Model, ModelMixin, CreatableMixin, UpdatableMixin):
    __tablename__ = "actors"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False, unique=True)

    born: orm.Mapped[datetime] = orm.mapped_column(sa.DateTime, nullable=False)
    died: orm.Mapped[datetime | None] = orm.mapped_column(sa.DateTime, nullable=True)

    avatar: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=True)

    translations: orm.Mapped[list["ActorTranslation"]] = orm.relationship()

    movies: orm.Mapped[list["Movie"]] = orm.relationship(
        "Movie",
        secondary=movie_actors,
        back_populates="actors",
    )

    characters: orm.Mapped[list["MovieActorCharacter"]] = orm.relationship(
        "MovieActorCharacter", back_populates="actor"
    )

    def __repr__(self):
        return f"<Actor [{self.id}]: {self.translations[0].full_name}>"

    def full_name(self, lang: Language = Language.UK) -> str:
        return next((t.full_name for t in self.translations if t.language == lang.value), "")

    def get_born_location(self, lang: Language = Language.UK) -> str:
        return next((t.born_in for t in self.translations if t.language == lang.value), "")

    @property
    def age(self) -> int:
        if self.died:
            return (self.died - self.born).days // 365
        return (datetime.now() - self.born).days // 365
