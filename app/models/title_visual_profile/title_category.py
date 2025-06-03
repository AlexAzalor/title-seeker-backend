from uuid import uuid4
from app.database import db
from sqlalchemy import orm
import sqlalchemy as sa
import app.schema as s
from app.models.utils import ModelMixin


from typing import TYPE_CHECKING
from .category_criteria import category_criteria

if TYPE_CHECKING:
    from .title_category_translation import VPCategoryTranslation
    from .title_criterion import VisualProfileCategoryCriterion


class VisualProfileCategory(db.Model, ModelMixin):
    __tablename__ = "visual_profile_categories"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))
    key: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False, unique=True, index=True)

    translations: orm.Mapped[list["VPCategoryTranslation"]] = orm.relationship()

    criteria: orm.Mapped[list["VisualProfileCategoryCriterion"]] = orm.relationship(
        secondary=category_criteria, back_populates="categories"
    )

    def __repr__(self):
        return f"<VisualProfileCategory [{self.id}]: {self.key}>"

    def get_name(self, lang: s.Language = s.Language.UK) -> str:
        return next((t.name for t in self.translations if t.language == lang.value), self.translations[0].name)

    def get_description(self, lang: s.Language = s.Language.UK) -> str:
        return next(
            (t.description for t in self.translations if t.language == lang.value), self.translations[0].description
        )
