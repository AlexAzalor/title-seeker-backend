import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.models.mixins import CreatableMixin, UpdatableMixin


class KnowledgeBaseQuestionAnswer(db.Model, CreatableMixin, UpdatableMixin):
    """1"""

    __tablename__ = "knowledge_base_question_answers"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    technology_id: orm.Mapped[int] = orm.mapped_column(
        sa.Integer, sa.ForeignKey("knowledge_base_technologies.id"), nullable=False
    )

    score: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False, default=0)

    question: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=False)
    short_answer: orm.Mapped[str] = orm.mapped_column(sa.String(512), nullable=False)

    # Content from Editor (WYSIWYG) with rich text, images, links, etc.
    answer: orm.Mapped[str] = orm.mapped_column(sa.Text, nullable=False)

    def __repr__(self):
        return f"<KnowledgeBaseQuestionAnswer [{self.id}]: {self.question}>"
