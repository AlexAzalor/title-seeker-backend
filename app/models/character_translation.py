import sqlalchemy as sa
from app.database import db
from sqlalchemy import orm

from app.models.mixins import CreatableMixin, UpdatableMixin


class CharacterTranslation(db.Model, CreatableMixin, UpdatableMixin):
    __tablename__ = "character_translations"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    character_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("characters.id"), nullable=False)

    language: orm.Mapped[str] = orm.mapped_column(sa.String(5), nullable=False)

    name: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)

    def __repr__(self):
        return f"<CharacterTranslation [{self.id}] - {self.name}>"
