import sqlalchemy as sa
from sqlalchemy import orm
from app import schema as s

from app.database import db
from .category_criteria import category_criteria

from ..utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .title_criterion_translation import TitleCriterionTranslation
    from .title_category import TitleCategory


class TitleCriterion(db.Model, ModelMixin):
    __tablename__ = "title_criteria"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False, unique=True, index=True)

    translations: orm.Mapped[list["TitleCriterionTranslation"]] = orm.relationship()

    categories: orm.Mapped[list["TitleCategory"]] = orm.relationship(
        secondary=category_criteria, back_populates="criteria"
    )

    def __repr__(self):
        return f"<TitleCriterion [{self.id}]>"

    def get_name(self, lang: s.Language = s.Language.UK) -> str:
        return next((t.name for t in self.translations if t.language == lang.value), self.translations[0].name)

    def get_description(self, lang: s.Language = s.Language.UK) -> str:
        return next(
            (t.description for t in self.translations if t.language == lang.value), self.translations[0].description
        )
