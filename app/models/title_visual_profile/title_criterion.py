from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import orm
from app import schema as s

from app.database import db
from .category_criteria import category_criteria

from ..utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .title_criterion_translation import VPCriterionTranslation
    from .title_category import VisualProfileCategory


class VisualProfileCategoryCriterion(db.Model, ModelMixin):
    __tablename__ = "visual_profile_category_criteria"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))
    key: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False, unique=True, index=True)

    translations: orm.Mapped[list["VPCriterionTranslation"]] = orm.relationship()

    categories: orm.Mapped[list["VisualProfileCategory"]] = orm.relationship(
        secondary=category_criteria, back_populates="criteria"
    )

    def __repr__(self):
        return f"<VPCategoryCriterion [{self.id}]>"

    def get_name(self, lang: s.Language = s.Language.UK) -> str:
        return next((t.name for t in self.translations if t.language == lang.value), self.translations[0].name)

    def get_description(self, lang: s.Language = s.Language.UK) -> str:
        return next(
            (t.description for t in self.translations if t.language == lang.value), self.translations[0].description
        )
