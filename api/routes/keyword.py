from fastapi import APIRouter, Body, HTTPException, Depends, status

import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

keyword_router = APIRouter(prefix="/keywords", tags=["Keywords"])


@keyword_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.MovieFilterFormOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Keyword already exists"},
        status.HTTP_201_CREATED: {"description": "Keyword successfully created"},
    },
)
def create_keyword(
    form_data: s.MovieFilterFormIn = Body(...),
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new keyword"""

    keyword = db.scalar(sa.select(m.Keyword).where(m.Keyword.key == form_data.key))

    if keyword:
        log(log.ERROR, "Keyword [%s] already exists")
        raise HTTPException(status_code=400, detail="Keyword already exists")

    try:
        new_keyword = m.Keyword(
            key=form_data.key,
            translations=[
                m.KeywordTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                    description=form_data.description_uk,
                ),
                m.KeywordTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                    description=form_data.description_en,
                ),
            ],
        )

        db.add(new_keyword)
        db.commit()
        log(log.INFO, "Keyword [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating keyword [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating keyword")

    db.refresh(new_keyword)

    return s.MovieFilterFormOut(
        key=new_keyword.key,
        name=next((t.name for t in new_keyword.translations if t.language == lang.value)),
    )
