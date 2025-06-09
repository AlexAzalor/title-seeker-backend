from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from ..utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .visual_profile_category import VisualProfileCategory
    from ..movie import Movie
    from ..user import User
    from .visual_profile_rating import VisualProfileRating


class VisualProfile(db.Model, ModelMixin):
    """Represents a visual profile for a movie, associated with a user and category."""

    __tablename__ = "visual_profiles"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    movie_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("movies.id"), nullable=False)
    user_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("users.id"), nullable=False)
    category_id: orm.Mapped[int] = orm.mapped_column(
        sa.Integer, sa.ForeignKey("visual_profile_categories.id"), nullable=False
    )

    user: orm.Mapped["User"] = orm.relationship("User", back_populates="visual_profiles")
    movie: orm.Mapped["Movie"] = orm.relationship("Movie", back_populates="visual_profiles")
    category: orm.Mapped["VisualProfileCategory"] = orm.relationship("VisualProfileCategory")

    ratings: orm.Mapped[list["VisualProfileRating"]] = orm.relationship(
        "VisualProfileRating", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<VisualProfile [{self.id}]>"
