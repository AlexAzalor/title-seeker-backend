from uuid import uuid4
import sqlalchemy as sa
from sqlalchemy import orm
import app.schema as s

from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db

from app.models.mixins import CreatableMixin, UpdatableMixin
from config import config
from app.logger import log

from .utils import ModelMixin
from typing import TYPE_CHECKING, Self

CFG = config()

if TYPE_CHECKING:
    from .rating import Rating
    from .title_visual_profile.title_visual_profile import TitleVisualProfile


class User(db.Model, ModelMixin, CreatableMixin, UpdatableMixin):
    __tablename__ = "users"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    email: orm.Mapped[str] = orm.mapped_column(sa.String(128), unique=True)  # get from google
    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), default="")  # get from google
    last_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), default="")  # get from google

    role: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=s.UserRole.USER.value)

    ratings: orm.Mapped[list["Rating"]] = orm.relationship("Rating", back_populates="user")

    visual_profiles: orm.Mapped[list["TitleVisualProfile"]] = orm.relationship(
        "TitleVisualProfile", back_populates="user"
    )

    password_hash: orm.Mapped[str | None] = orm.mapped_column(sa.String(256))  # only for admin

    preferred_language: orm.Mapped[str] = orm.mapped_column(
        sa.String(10), default=s.Language.UK.value, server_default=s.Language.UK.value
    )

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @classmethod
    def authenticate(
        cls,
        username: str,
        password: str,
        session: orm.Session,
    ) -> Self | None:
        assert username and password, "username and password must be provided"

        # test role user
        query = cls.select().where(
            sa.and_(
                cls.is_deleted.is_(False),
                sa.func.lower(cls.first_name) == sa.func.lower(username),
                cls.role == s.UserRole.OWNER.value,
            )
        )
        user = session.scalar(query)
        if not user:
            log(log.WARNING, "user:[%s] not found", username)
        elif check_password_hash(user.password_hash, password):
            return user
        return None

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<{self.id}: {self.full_name}>"
