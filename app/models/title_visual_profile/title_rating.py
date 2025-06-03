from uuid import uuid4
import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from ..utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .title_criterion import VisualProfileCategoryCriterion


class VisualProfileRating(db.Model, ModelMixin):
    __tablename__ = "visual_profile_ratings"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    title_visual_profile_id: orm.Mapped[int] = orm.mapped_column(
        sa.Integer, sa.ForeignKey("visual_profiles.id"), nullable=False
    )
    criterion_id: orm.Mapped[int] = orm.mapped_column(
        sa.Integer, sa.ForeignKey("visual_profile_category_criteria.id"), nullable=False
    )

    rating: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)
    order: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False, default=1)

    criterion: orm.Mapped["VisualProfileCategoryCriterion"] = orm.relationship("VisualProfileCategoryCriterion")

    def __repr__(self):
        return f"<VisualProfileRating [{self.id}]>"
