import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.schema.language import Language

from ..utils import ModelMixin


class SubgenreTranslation(db.Model, ModelMixin):
    __tablename__ = "subgenre_translations"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    subgenre_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("subgenres.id"), nullable=False)
    language: orm.Mapped[str] = orm.mapped_column(sa.String(5), default=Language.UK.value)

    name: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(sa.Text(), nullable=False)

    def __repr__(self):
        return f"<SubgenreTranslation [{self.id}]>"
