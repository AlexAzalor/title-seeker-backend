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


class AuditLogListOut(BaseModel):
    items: list[AuditLogOut]
    next_cursor: str | None  # None when there are no more records
