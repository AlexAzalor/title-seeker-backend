from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy import orm


@as_declarative()
class Base:
    pass


# https://chatgpt.com/c/6745a7a0-9a7c-8012-b1a5-bcde9865deff
class CreatableMixin:
    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


class UpdatableMixin:
    updated_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    # updated_by: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)
