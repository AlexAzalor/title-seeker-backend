import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from api.controllers.create_movie import QUICK_MOVIES_FILE, get_movies_data_from_file
from api.dependency.user import get_current_user
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db
from app.schema.user import UserRole
from config import config

CFG = config()

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post(
    "/google",
    status_code=status.HTTP_200_OK,
    response_model=s.GoogleAuthOut,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Google account not found"}},
)
def google_auth(
    auth_data: s.GoogleAuthIn,
    db: Session = Depends(get_db),
):
    """Authenticate user with Google account.
    This function checks if the user already exists in the database.
    If the user does not exist, it creates a new user with the provided Google account information.
    **Real Google authentication process on the frontend (Next.js) side.**
    """

    user = db.scalar(sa.select(m.User).where(m.User.is_deleted.is_(False), m.User.email == auth_data.email))

    if not user:
        first_name = auth_data.given_name if auth_data.given_name else ""
        last_name = auth_data.family_name if auth_data.family_name else ""

        user = m.User(first_name=first_name, last_name=last_name, email=auth_data.email)
        db.add(user)
        db.commit()
        db.refresh(user)

        log(log.DEBUG, "User [%s] created", user.email)

    new_movies_to_add_count = 0

    if user.role == s.UserRole.OWNER.value:
        if os.path.exists(QUICK_MOVIES_FILE):
            quick_movies = get_movies_data_from_file()

            if quick_movies:
                new_movies_to_add_count = len(quick_movies)

    return s.GoogleAuthOut(
        uuid=user.uuid,
        full_name=user.full_name,
        email=user.email,
        role=UserRole(user.role),
        new_movies_to_add_count=new_movies_to_add_count,
        my_language=s.Language(user.preferred_language),
    )


@auth_router.delete(
    "/google",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Google account not found"}},
)
def delete_google_profile(
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete user profile"""

    if current_user.role == s.UserRole.OWNER.value:
        log(log.ERROR, "Owner profile cannot be deleted")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner profile cannot be deleted")

    current_user.is_deleted = True
    current_user.email = current_user.email + "-delete at-" + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # The synchronize_session=False argument ensures that the session does not attempt to synchronize
    # the in-memory state with the database after the bulk delete.
    db.query(m.Rating).filter(m.Rating.user_id == current_user.id).delete(synchronize_session=False)

    db.commit()
    log(log.DEBUG, "User [%s] deleted", current_user.email)
