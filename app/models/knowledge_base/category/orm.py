from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.models.mixins import CreatableMixin, UpdatableMixin

if TYPE_CHECKING:
    from app.models.knowledge_base.technology.orm import KnowledgeBaseTechnology


class KnowledgeBaseCategory(db.Model, CreatableMixin, UpdatableMixin):
    """Represents a category in the knowledge base, which can have multiple associated technologies."""

    __tablename__ = "knowledge_base_categories"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False, unique=True)

    name: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(sa.Text, nullable=False)

    technologies: orm.Mapped[list["KnowledgeBaseTechnology"]] = orm.relationship()

    def __repr__(self):
        return f"<KnowledgeBaseCategory [{self.id}]: {self.name}>"
