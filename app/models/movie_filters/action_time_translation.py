import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.schema.language import Language

from ..utils import ModelMixin


class ActionTimeTranslation(db.Model, ModelMixin):
    __tablename__ = "action_time_translations"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    action_time_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("action_times.id"), nullable=False)

    language: orm.Mapped[str] = orm.mapped_column(sa.String(5), default=Language.UK.value)

    name: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)
    description: orm.Mapped[str | None] = orm.mapped_column(sa.Text(), nullable=True)

    def __repr__(self):
        return f"<ActionTimeTranslation [{self.id}]>"
