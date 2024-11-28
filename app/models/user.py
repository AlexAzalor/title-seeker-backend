from uuid import uuid4
from datetime import datetime, UTC
from typing import TYPE_CHECKING, Self

import sqlalchemy as sa
from sqlalchemy import orm

from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db
from app.logger import log

from app import schema as s
from config import config

# from .rate import Rate
# from .user_locations import user_locations
# from .user_services import user_services
# from .favorite_jobs import favorite_jobs
# from .favorite_experts import favorite_experts
from .utils import ModelMixin

CFG = config()

# if TYPE_CHECKING:
#     from .location import Location
#     from .service import Service
#     from .auth_account import AuthAccount
#     from .job import Job
#     from .device import Device
#     from .file import File
#     from .education import Education


class User(db.Model, ModelMixin):
    __tablename__ = "users"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    uuid: orm.Mapped[str] = orm.mapped_column(sa.String(36), default=lambda: str(uuid4()))

    # fullname: orm.Mapped[str] = orm.mapped_column(sa.String(128), default="")  # fill in registration form
    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), default="")
    last_name: orm.Mapped[str] = orm.mapped_column(sa.String(64), default="")
    description: orm.Mapped[str] = orm.mapped_column(sa.String(512), default="", server_default="")

    password_hash: orm.Mapped[str | None] = orm.mapped_column(sa.String(256))  # fill in registration form

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=datetime.now(UTC),
    )

    updated_at: orm.Mapped[datetime] = orm.mapped_column(default=sa.func.now(), onupdate=sa.func.now())

    is_deleted: orm.Mapped[bool] = orm.mapped_column(default=False)

    average_rate: orm.Mapped[float] = orm.mapped_column(sa.Float, default=0)

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
        query = cls.select().where(
            sa.and_(cls.is_deleted.is_(False), sa.func.lower(cls.first_name) == sa.func.lower(username))
        )
        user = session.scalar(query)
        if not user:
            log(log.WARNING, "user:[%s] not found", username)
        elif check_password_hash(user.password_hash, password):
            return user
        return None

    def __repr__(self):
        return f"<{self.id}: {self.fullname}>"
