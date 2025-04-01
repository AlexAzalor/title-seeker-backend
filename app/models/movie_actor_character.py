from app.database import db
import sqlalchemy as sa
from app import schema as s
from sqlalchemy import orm


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .movie import Movie
    from .actor import Actor
    from .character import Character


class MovieActorCharacter(db.Model):
    __tablename__ = "movie_actor_character"

    id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)

    movie_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("movies.id"), nullable=False)
    actor_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("actors.id"), nullable=False)
    character_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("characters.id"), nullable=False)

    movie: orm.Mapped["Movie"] = orm.relationship("Movie", back_populates="characters")
    actor: orm.Mapped["Actor"] = orm.relationship("Actor", back_populates="characters")
    character: orm.Mapped["Character"] = orm.relationship("Character", back_populates="characters")

    __table_args__ = (sa.UniqueConstraint("movie_id", "actor_id", "character_id", name="uq_movie_actor_character"),)

    def __repr__(self):
        return f"<ID: [{self.id}], Movie: [{self.movie_id}], Actor: [{self.actor_id}], Char: [{self.character_id}]>"

    def get_name(self, language: s.Language = s.Language.UK) -> str:
        return next((t.name for t in self.translations if t.language == language.value), self.translations[0].name)
