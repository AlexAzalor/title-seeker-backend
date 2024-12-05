from fastapi import APIRouter, HTTPException, Depends, status
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

genre_router = APIRouter(prefix="/genres", tags=["Genres"])


@genre_router.get("/", status_code=status.HTTP_200_OK, response_model=s.GenreListOut)
async def get_genres(
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
                    )
                    for subgenre in genre.subgenres
                ],
            )
        )
    return s.GenreListOut(genres=genres_out)
