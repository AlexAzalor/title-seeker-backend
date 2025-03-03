from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, Depends, status

import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

subgenre_router = APIRouter(prefix="/subgenres", tags=["Subgenres"])


@subgenre_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.SubgenreOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Subgenre already exists"},
        status.HTTP_201_CREATED: {"description": "Subgenre successfully created"},
    },
)
def create_subgenre(
    key: Annotated[str, Form()],
    name_uk: Annotated[str, Form()],
    name_en: Annotated[str, Form()],
    parent_genre_key: Annotated[str, Form()],
    description_uk: Annotated[str | None, Form()] = None,
    description_en: Annotated[str | None, Form()] = None,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new subgenre"""

    subgenre = db.scalar(sa.select(m.Subgenre).where(m.Subgenre.key == key))

    if subgenre:
        log(log.ERROR, "Subgenre [%s] already exists")
        raise HTTPException(status_code=400, detail="Subgenre already exists")

    genre_id = db.scalar(sa.select(m.Genre.id).where(m.Genre.key == parent_genre_key))
    if not genre_id:
        log(log.ERROR, "Genre [%s] not found", parent_genre_key)
        raise HTTPException(status_code=404, detail="Genre not found")

    try:
        new_subgenre = m.Subgenre(
            genre_id=genre_id,
            key=key,
            translations=[
                m.SubgenreTranslation(
                    language=s.Language.UK.value,
                    name=name_uk,
                    description=description_uk,
                ),
                m.SubgenreTranslation(
                    language=s.Language.EN.value,
                    name=name_en,
                    description=description_en,
                ),
            ],
        )

        db.add(new_subgenre)
        db.commit()
        log(log.INFO, "Subgenre [%s] successfully created", key)
    except Exception as e:
        log(log.ERROR, "Error creating subgenre [%s]: %s", key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating subgenre")

    db.refresh(new_subgenre)

    return s.SubgenreOut(
        key=new_subgenre.key,
        name=next((t.name for t in new_subgenre.translations if t.language == lang.value)),
        description=next((t.description for t in new_subgenre.translations if t.language == lang.value)),
        parent_genre_key=parent_genre_key,
    )
