import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from app.schema.language import Language

from .utils import ModelMixin


class ActorTranslation(db.Model, ModelMixin):
    __tablename__ = "actor_translations"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    actor_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("actors.id"), nullable=False)
    language: orm.Mapped[str] = orm.mapped_column(sa.String(5), default=Language.UK.value)

    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)
    last_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)
    born_in: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=True)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<ActorTranslation [{self.id}] - {self.full_name}>"
