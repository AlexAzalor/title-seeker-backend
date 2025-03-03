from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, Depends, status

import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

genre_router = APIRouter(prefix="/genres", tags=["Genres"])


@genre_router.get("/", status_code=status.HTTP_200_OK, response_model=s.GenreListOut)
def get_genres(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all genres and its subgenres"""

    genres = db.scalars(sa.select(m.Genre)).all()
    if not genres:
        log(log.ERROR, "Genres [%s] not found")
        raise HTTPException(status_code=404, detail="Genres not found")

    genres_out = []

    for genre in genres:
        genres_out.append(
            s.GenreOut(
                key=genre.key,
                name=next((t.name for t in genre.translations if t.language == lang.value)),
                description=next((t.description for t in genre.translations if t.language == lang.value)),
                subgenres=[
                    s.SubgenreOut(
                        key=subgenre.key,
                        name=next((t.name for t in subgenre.translations if t.language == lang.value)),
                        description=next((t.description for t in subgenre.translations if t.language == lang.value)),
                        parent_genre_key=subgenre.genre.key,
                    )
                    for subgenre in genre.subgenres
                ],
            )
        )
    return s.GenreListOut(genres=genres_out)


@genre_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.GenreOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Genre already exists"},
        status.HTTP_201_CREATED: {"description": "Genre successfully created"},
    },
)
def create_genre(
    key: Annotated[str, Form()],
    name_uk: Annotated[str, Form()],
    name_en: Annotated[str, Form()],
    description_uk: Annotated[str | None, Form()] = None,
    description_en: Annotated[str | None, Form()] = None,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new genre"""

    genre = db.scalar(sa.select(m.Genre).where(m.Genre.key == key))

    if genre:
        log(log.ERROR, "Genre [%s] already exists")
        raise HTTPException(status_code=400, detail="Genre already exists")

    try:
        new_genre = m.Genre(
            key=key,
            translations=[
                m.GenreTranslation(
                    language=s.Language.UK.value,
                    name=name_uk,
                    description=description_uk,
                ),
                m.GenreTranslation(
                    language=s.Language.EN.value,
                    name=name_en,
                    description=description_en,
                ),
            ],
        )

        db.add(new_genre)
        db.commit()
        log(log.INFO, "Genre [%s] successfully created", key)
    except Exception as e:
        log(log.ERROR, "Error creating genre [%s]: %s", key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating genre")

    db.refresh(new_genre)

    return s.GenreOut(
        key=new_genre.key,
        name=next((t.name for t in new_genre.translations if t.language == lang.value)),
        description=next((t.description for t in new_genre.translations if t.language == lang.value)),
        subgenres=[
            s.SubgenreOut(
                key=subgenre.key,
                name=next((t.name for t in subgenre.translations if t.language == lang.value)),
                description=next((t.description for t in subgenre.translations if t.language == lang.value)),
                parent_genre_key=subgenre.new_genre.key,
            )
            for subgenre in new_genre.subgenres
        ],
    )
