import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from ..utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .title_criterion import TitleCriterion


class TitleCriterionRating(db.Model, ModelMixin):
    __tablename__ = "title_criterion_ratings"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    title_visual_profile_id: orm.Mapped[int] = orm.mapped_column(
        sa.Integer, sa.ForeignKey("title_visual_profiles.id"), nullable=False
    )
    criterion_id: orm.Mapped[int] = orm.mapped_column(sa.Integer, sa.ForeignKey("title_criteria.id"), nullable=False)

    rating: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)
    order: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False, default=1)

    criterion: orm.Mapped["TitleCriterion"] = orm.relationship("TitleCriterion")

    def __repr__(self):
        return f"<TitleCriterionRating [{self.id}]>"
