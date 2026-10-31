from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.controllers.audit_log import (
    EVENT_CATEGORIES,
    get_audit_history,
    get_audit_users,
    get_general_audit_history,
    resolve_entity_id,
)
from api.dependency.user import get_admin
import app.models as m
import app.schema as s
from app.database import get_db
from app.logger import log

audit_log_router = APIRouter(prefix="/audit-logs", tags=["Audit logs"])


@audit_log_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=s.AuditLogSummaryListOut,
    responses={status.HTTP_400_BAD_REQUEST: {"description": "Invalid cursor, category or entity type"}},
)
def get_general_history(
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    event_type: list[str] | None = Query(None, description="Include only these event types (repeatable)"),
    category: list[str] | None = Query(None, description=f"Include event categories: {', '.join(EVENT_CATEGORIES)}"),
    exclude_event_type: list[str] | None = Query(None, description="Exclude these event types (repeatable)"),
    include_visits: bool = Query(
        False,
        description="`movie.visited` is hidden by default; `movie.user.info` needs event_type or",
    ),
    user_id: int | None = None,
    entity_type: str | None = None,
    entity_key: str | None = Query(None, description="Requires `entity_type`"),
    date_from: date | None = Query(None, description="UTC day, inclusive"),
    date_to: date | None = Query(None, description="UTC day, inclusive"),
    search: str | None = Query(None, min_length=1, max_length=128, description="Movie title (any language)"),
    sort: Literal["asc", "desc"] = "desc",
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Get the general history of all entities, without change details.

    Items are grouped by UTC day (`groups`); a day can continue on the next page.
    Keep the same filters and `sort` while paginating with `next_cursor`.
    """

    if entity_key and not entity_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="entity_key requires entity_type")
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="date_from is after date_to")
    bad_categories = [c for c in category or [] if c not in EVENT_CATEGORIES]
    if bad_categories:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown category: {bad_categories[0]}")

    try:
        return get_general_audit_history(
            db,
            limit,
            cursor,
            event_type,
            categories=category,
            exclude_event_types=exclude_event_type,
            include_visits=include_visits,
            user_id=user_id,
            entity_type=entity_type,
            entity_key=entity_key,
            date_from=date_from,
            date_to=date_to,
            search=search,
            sort=sort,
            lang=lang,
        )
    except KeyError:
        log(log.ERROR, "Unsupported audit entity type [%s]", entity_type)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported entity type")
    except ValueError:
        log(log.ERROR, "Invalid audit log cursor [%s]", cursor)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor")


@audit_log_router.get("/users", status_code=status.HTTP_200_OK, response_model=s.AuditLogUserListOut)
def get_history_users(
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Users who authored audit events (full name and role). Use for the `user_id` filter."""

    return get_audit_users(db)


@audit_log_router.get(
    "/{entity_type}/{entity_id}",
    status_code=status.HTTP_200_OK,
    response_model=s.AuditLogListOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid cursor or unsupported entity type"},
        status.HTTP_404_NOT_FOUND: {"description": "Entity not found"},
    },
)
def get_entity_history(
    entity_type: str,
    entity_id: str,
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Get entity audit history (newest first).

    `entity_id` is the entity's public key (e.g. movie key).
    Pass `next_cursor` as `cursor` to load the next page.
    """

    try:
        internal_id = resolve_entity_id(db, entity_type, entity_id)
    except KeyError:
        log(log.ERROR, "Unsupported audit entity type [%s]", entity_type)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported entity type")

    if internal_id is None:
        log(log.ERROR, "Audit entity [%s:%s] not found", entity_type, entity_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")

    try:
        return get_audit_history(db, entity_type, internal_id, limit, cursor)
    except ValueError:
        log(log.ERROR, "Invalid audit log cursor [%s]", cursor)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cursor")
