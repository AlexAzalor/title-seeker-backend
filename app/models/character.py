from app.database import db
import sqlalchemy as sa
from sqlalchemy import orm
from app.models.mixins import CreatableMixin, UpdatableMixin
from .movie_characters import movie_characters
from .actor_characters import actor_characters

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .character_translation import CharacterTranslation
    from .movie import Movie
    from .actor import Actor


class Character(db.Model, CreatableMixin, UpdatableMixin):
    __tablename__ = "characters"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False, unique=True)

    translations: orm.Mapped[list["CharacterTranslation"]] = orm.relationship()

    movies: orm.Mapped[list["Movie"]] = orm.relationship(
        "Movie",
        secondary=movie_characters,
        back_populates="characters",
    )

    actors: orm.Mapped[list["Actor"]] = orm.relationship(
        "Actor", secondary=actor_characters, back_populates="characters"
    )

    def __repr__(self):
        return f"<Character [{self.id}]: {self.key}>"
