from fastapi import Depends, HTTPException, status

from sqlalchemy.orm import Session
import sqlalchemy as sa

from app.database import get_db
import app.models as m
import app.schema as s
from app.logger import log


def get_current_user(
    user_uuid: str | None = None,
    db: Session = Depends(get_db),
) -> m.User | None:
    """Raises an exception if the current user is not authenticated"""

    if not user_uuid:
        return None

    user = db.scalar(
        sa.select(m.User).where(
            m.User.is_deleted.is_(False),
            m.User.uuid == user_uuid,
        )
    )

    if not user:
        log(log.INFO, "User wasn`t authorized")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not authorized",
        )
    if user.is_deleted:
        log(log.INFO, "User [%s] was deleted", user_uuid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was deleted",
        )
    return user


def get_admin(
    user_uuid: str,
    db: Session = Depends(get_db),
) -> m.User:
    """Raises an exception if the current user is not admin or owner"""

    user = db.scalar(
        sa.select(m.User).where(
            m.User.is_deleted.is_(False),
            m.User.uuid == user_uuid,
        )
    )

    if not user:
        log(log.INFO, "User [%s] not found", user_uuid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not s.UserRole(user.role).has_permissions():
        log(log.INFO, "User [%s] is not admin or owner", user_uuid)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return user


def get_owner(
    user_uuid: str,
    db: Session = Depends(get_db),
) -> m.User:
    """Only owner is allowed to work with Add Movie, Quickly add Movie, Visual Profile (post, put).
    Raises an exception if the current user is not owner"""

    user = db.scalar(
        sa.select(m.User).where(
            m.User.is_deleted.is_(False),
            m.User.uuid == user_uuid,
        )
    )

    if not user:
        log(log.INFO, "User [%s] not found", user_uuid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not s.UserRole(user.role).is_owner():
        log(log.INFO, "User [%s] is not owner", user_uuid)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return user
