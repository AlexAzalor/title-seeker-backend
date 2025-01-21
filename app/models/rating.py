from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from app.models.mixins import CreatableMixin, UpdatableMixin

from .utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .movie import Movie
    from .user import User


class Rating(db.Model, ModelMixin, CreatableMixin, UpdatableMixin):
    __tablename__ = "ratings"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    movie_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("movies.id"), nullable=False)
    user_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)

    rating: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=False)
    comment: orm.Mapped[str] = orm.mapped_column(sa.String(512), default="")

    movie: orm.Mapped["Movie"] = orm.relationship("Movie", back_populates="ratings")
    user: orm.Mapped["User"] = orm.relationship("User", back_populates="ratings")

    # Criteria
    acting: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=False)
    plot_storyline: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=False)
    script_dialogue: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=False)
    music: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=False)
    enjoyment: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=False)
    production_design: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=False)
    # re_watchability: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=False)
    # emotional_impact: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=False)
    # duration: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=False)

    # Additional
    visual_effects: orm.Mapped[float | None] = orm.mapped_column(sa.Float, nullable=True)
    scare_factor: orm.Mapped[float | None] = orm.mapped_column(sa.Float, nullable=True)
    humor: orm.Mapped[float | None] = orm.mapped_column(sa.Float, nullable=True)
    animation_cartoon: orm.Mapped[float | None] = orm.mapped_column(sa.Float, nullable=True)

    def __repr__(self):
        return f"<Rating [{self.id}] - {self.user.full_name}>"
