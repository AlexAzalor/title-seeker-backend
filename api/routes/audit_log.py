from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.controllers.audit_log import get_audit_history, resolve_entity_id
from api.dependency.user import get_admin
import app.models as m
import app.schema as s
from app.database import get_db
from app.logger import log

audit_log_router = APIRouter(prefix="/audit-logs", tags=["Audit logs"])


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
