from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.dialects.postgresql import JSONB

from app.database import db

# JSONB on PostgreSQL, plain JSON elsewhere (SQLite in tests)
JSONType = sa.JSON().with_variant(JSONB(), "postgresql")


class AuditLog(db.Model):
    """Immutable record of a change made to an entity (movie, series, anime, game, ...)."""

    __tablename__ = "audit_logs"

    id: orm.Mapped[int] = orm.mapped_column(sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True)

    entity_type: orm.Mapped[str] = orm.mapped_column(sa.String(64), nullable=False)  # "movie", "series", ...
    entity_id: orm.Mapped[int] = orm.mapped_column(sa.BigInteger, nullable=False)
    event_type: orm.Mapped[str] = orm.mapped_column(sa.String(128), nullable=False)  # "movie.description.updated"

    user_id: orm.Mapped[int | None] = orm.mapped_column(sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    changes: orm.Mapped[dict] = orm.mapped_column(JSONType, nullable=False)

    created_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=sa.func.now(),
    )

    __table_args__ = (
        # Serves the entity history query: filter by entity, ordered by (created_at DESC, id DESC)
        sa.Index(
            "ix_audit_logs_entity_history",
            "entity_type",
            "entity_id",
            sa.text("created_at DESC"),
            sa.text("id DESC"),
        ),
    )

    def __repr__(self):
        return f"<AuditLog [{self.id}] {self.event_type} {self.entity_type}:{self.entity_id}>"
