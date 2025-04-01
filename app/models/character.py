from app.database import db
import sqlalchemy as sa
from app import schema as s
from sqlalchemy import orm
from app.models.mixins import CreatableMixin, UpdatableMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .character_translation import CharacterTranslation
    from .movie_actor_character import MovieActorCharacter


class Character(db.Model, CreatableMixin, UpdatableMixin):
    __tablename__ = "characters"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False, unique=True)

    translations: orm.Mapped[list["CharacterTranslation"]] = orm.relationship()

    characters: orm.Mapped[list["MovieActorCharacter"]] = orm.relationship(
        "MovieActorCharacter", back_populates="character"
    )

    def __repr__(self):
        return f"<Character [{self.id}]: {self.key}>"

    def get_name(self, language: s.Language) -> str:
        return next((t.name for t in self.translations if t.language == language.value), self.translations[0].name)
