import datetime as dt
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    id: int
    event_type: str
    user_id: int | None
    user_name: str | None
    changes: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogSummaryOut(BaseModel):
    """General history entry: the fact that something changed, without the change details."""

    id: int
    event_type: str
    entity_type: str
    entity_key: str | None  # None if the entity was deleted
    entity_title: str | None  # localized; None if the entity was deleted or has no title
    entity_poster: str | None
    user_id: int | None
    user_name: str | None
    created_at: datetime


class AuditLogDayGroupOut(BaseModel):
    date: dt.date  # UTC day
    items: list[AuditLogSummaryOut]


class AuditLogSummaryListOut(BaseModel):
    groups: list[AuditLogDayGroupOut]
    next_cursor: str | None  # None when there are no more records


class AuditLogListOut(BaseModel):
    items: list[AuditLogOut]
    next_cursor: str | None  # None when there are no more records


class AuditLogUserOut(BaseModel):
    id: int
    full_name: str
    role: str


class AuditLogUserListOut(BaseModel):
    users: list[AuditLogUserOut]
