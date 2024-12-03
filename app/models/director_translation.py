import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.schema.language import Language

from .utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .director import Director


class DirectorTranslation(db.Model, ModelMixin):
    __tablename__ = "director_translations"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    director_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("directors.id"), nullable=False)
    language: orm.Mapped[str] = orm.mapped_column(sa.String(5), default=Language.UK.value)

    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)
    last_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)
    born_in: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=True)

    director: orm.Mapped["Director"] = orm.relationship(
        "Director",
        back_populates="translations",
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<DirectorTranslation [{self.id}] - {self.full_name}>"
