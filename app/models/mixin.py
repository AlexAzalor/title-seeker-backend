from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import as_declarative


@as_declarative()
class Base:
    pass


# https://chatgpt.com/c/6745a7a0-9a7c-8012-b1a5-bcde9865deff
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )
