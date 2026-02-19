from typing import TYPE_CHECKING
import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.models.mixins import CreatableMixin, UpdatableMixin

if TYPE_CHECKING:
    from app.models.knowledge_base.question_answer.orm import KnowledgeBaseQuestionAnswer


class KnowledgeBaseTechnology(db.Model, CreatableMixin, UpdatableMixin):
    """1"""

    __tablename__ = "knowledge_base_technologies"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    key: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False, unique=True)
    category_id: orm.Mapped[int] = orm.mapped_column(
        sa.Integer, sa.ForeignKey("knowledge_base_categories.id"), nullable=False
    )

    name: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(sa.Text, nullable=False)

    questions_answers: orm.Mapped[list["KnowledgeBaseQuestionAnswer"]] = orm.relationship()

    def __repr__(self):
        return f"<KnowledgeBaseTechnology [{self.id}]: {self.name}>"
