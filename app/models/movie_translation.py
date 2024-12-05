import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.schema.language import Language

from .utils import ModelMixin


class MovieTranslation(db.Model, ModelMixin):
    __tablename__ = "movie_translations"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    movie_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("movies.id"), nullable=False)
    language: orm.Mapped[str] = orm.mapped_column(sa.String(5), default=Language.UK.value)

    title: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(sa.Text, nullable=False)

    def __repr__(self):
        return f"<MovieTranslation [{self.id}] - {self.title}>"
