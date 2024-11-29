import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db

from .utils import ModelMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .actor import Actor


class ActorTranslation(db.Model, ModelMixin):
    __tablename__ = "actor_translations"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    actor_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("actors.id"), nullable=False)

    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)
    last_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)
    born_in: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=True)
    character_name: orm.Mapped[str] = orm.mapped_column(sa.String(255), nullable=True)

    actor: orm.Mapped["Actor"] = orm.relationship(
        "Actor",
        back_populates="translations",
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<ActorTranslation [{self.id}] - {self.full_name}>"
