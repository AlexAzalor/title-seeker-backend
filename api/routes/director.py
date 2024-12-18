from fastapi import APIRouter, HTTPException, Depends, status
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

director_router = APIRouter(prefix="/directorrs", tags=["Directors"])


@director_router.get("/", status_code=status.HTTP_200_OK, response_model=s.DirectorListOut)
def get_directors(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all directors"""

    directors = db.scalars(sa.select(m.Director)).all()
    if not directors:
        log(log.ERROR, "Director [%s] not found")
        raise HTTPException(status_code=404, detail="Director not found")

    directors_out = []

    for director in directors:
        directors_out.append(
            s.DirectorOut(
                key=director.key,
                full_name=director.full_name(lang),
            )
        )
    return s.DirectorListOut(directors=directors_out)
