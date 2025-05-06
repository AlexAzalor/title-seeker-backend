from fastapi import APIRouter, Body, HTTPException, Depends, status

from api.dependency.user import get_admin
from api.utils import check_admin_permissions
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

genre_router = APIRouter(prefix="/genres", tags=["Genres"])


@genre_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.GenreFormOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Genre already exists"},
        status.HTTP_201_CREATED: {"description": "Genre successfully created"},
    },
)
def create_genre(
    form_data: s.GenreFormIn = Body(...),
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new genre"""

    check_admin_permissions(current_user)

    genre = db.scalar(sa.select(m.Genre).where(m.Genre.key == form_data.key))

    if genre:
        log(log.ERROR, "Genre [%s] already exists")
        raise HTTPException(status_code=400, detail="Genre already exists")

    try:
        new_genre = m.Genre(
            key=form_data.key,
            translations=[
                m.GenreTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                    description=form_data.description_uk,
                ),
                m.GenreTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                    description=form_data.description_en,
                ),
            ],
        )

        db.add(new_genre)
        db.commit()
        log(log.INFO, "Genre [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating genre [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating genre")

    db.refresh(new_genre)

    return s.GenreFormOut(
        key=new_genre.key,
        name=new_genre.get_name(lang),
        description=new_genre.get_description(lang),
    )


@genre_router.post(
    "/subgenres/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.GenreFormOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Subgenre already exists"},
        status.HTTP_201_CREATED: {"description": "Subgenre successfully created"},
    },
)
def create_subgenre(
    form_data: s.GenreFormIn = Body(...),
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new subgenre"""

    check_admin_permissions(current_user)

    subgenre = db.scalar(sa.select(m.Subgenre).where(m.Subgenre.key == form_data.key))

    if subgenre:
        log(log.ERROR, "Subgenre [%s] already exists")
        raise HTTPException(status_code=400, detail="Subgenre already exists")

    genre_id = db.scalar(sa.select(m.Genre.id).where(m.Genre.key == form_data.parent_genre_key))
    if not genre_id:
        log(log.ERROR, "Genre [%s] not found", form_data.parent_genre_key)
        raise HTTPException(status_code=404, detail="Genre not found")

    try:
        new_subgenre = m.Subgenre(
            genre_id=genre_id,
            key=form_data.key,
            translations=[
                m.SubgenreTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                    description=form_data.description_uk,
                ),
                m.SubgenreTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                    description=form_data.description_en,
                ),
            ],
        )

        db.add(new_subgenre)
        db.commit()
        log(log.INFO, "Subgenre [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating subgenre [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating subgenre")

    db.refresh(new_subgenre)

    return s.GenreFormOut(
        key=new_subgenre.key,
        name=new_subgenre.get_name(lang),
        description=new_subgenre.get_description(lang),
        parent_genre_key=form_data.parent_genre_key,
    )
