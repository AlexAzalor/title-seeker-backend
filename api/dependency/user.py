from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session, joinedload
import sqlalchemy as sa

# from api.controllers.oauth2 import verify_access_token, INVALID_CREDENTIALS_EXCEPTION
from app.database import get_db
import app.models as m
import app.schema as s
from app.logger import log

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    user_uuid: str | None = None,
    db: Session = Depends(get_db),
) -> m.User | None:
    """Raises an exception if the current user is not authenticated"""
    # token_data: s.TokenData = verify_access_token(token, INVALID_CREDENTIALS_EXCEPTION)

    if not user_uuid:
        return None

    user = db.scalar(
        sa.select(m.User)
        .where(
            m.User.is_deleted.is_(False),
            m.User.role.in_([s.UserRole.USER.value, s.UserRole.OWNER.value]),
            m.User.uuid == user_uuid,
        )
        .options(joinedload(m.User.ratings))
    )

    if not user:
        log(log.INFO, "User wasn`t authorized")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not authorized",
        )
    if user.is_deleted:
        log(log.INFO, "User was not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not found",
        )
    return user


# def get_user(request: Request, db: Session = Depends(get_db)) -> m.User | None:
#     """Raises an exception if the current user is authenticated"""
#     auth_header = request.headers.get("Authorization")
#     if auth_header:
#         # Assuming the header value is in the format "Bearer <token>"
#         assert auth_header.startswith("Bearer ")
#         token: s.TokenData = verify_access_token(auth_header.split(" ")[1], INVALID_CREDENTIALS_EXCEPTION)
#         user = db.scalar(
#             sa.select(m.User).where(
#                 m.User.id == token.user_id,
#                 m.User.is_deleted.is_(False),
#             )
#         )
#         return user
#     return None
