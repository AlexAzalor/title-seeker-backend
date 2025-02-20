import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.schema.language import Language

from ..utils import ModelMixin


class GenreTranslation(db.Model, ModelMixin):
    __tablename__ = "genre_translations"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    genre_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("genres.id"), nullable=False)
    language: orm.Mapped[str] = orm.mapped_column(sa.String(5), default=Language.UK.value)

    name: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(sa.Text(), nullable=False)

    def __repr__(self):
        return f"<GenreTranslation [{self.id}]>"
