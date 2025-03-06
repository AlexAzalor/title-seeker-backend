from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, Depends, status

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
    response_model=s.KeywordOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Keyword already exists"},
        status.HTTP_201_CREATED: {"description": "Keyword successfully created"},
    },
)
def create_keyword(
    key: Annotated[str, Form()],
    name_uk: Annotated[str, Form()],
    name_en: Annotated[str, Form()],
    description_uk: Annotated[str | None, Form()] = None,
    description_en: Annotated[str | None, Form()] = None,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new keyword"""

    keyword = db.scalar(sa.select(m.Keyword).where(m.Keyword.key == key))

    if keyword:
        log(log.ERROR, "Keyword [%s] already exists")
        raise HTTPException(status_code=400, detail="Keyword already exists")

    try:
        new_keyword = m.Keyword(
            key=key,
            translations=[
                m.KeywordTranslation(
                    language=s.Language.UK.value,
                    name=name_uk,
                    description=description_uk,
                ),
                m.KeywordTranslation(
                    language=s.Language.EN.value,
                    name=name_en,
                    description=description_en,
                ),
            ],
        )

        db.add(new_keyword)
        db.commit()
        log(log.INFO, "Keyword [%s] successfully created", key)
    except Exception as e:
        log(log.ERROR, "Error creating keyword [%s]: %s", key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating keyword")

    db.refresh(new_keyword)

    return s.KeywordOut(
        key=new_keyword.key,
        name=next((t.name for t in new_keyword.translations if t.language == lang.value)),
        description=next((t.description for t in new_keyword.translations if t.language == lang.value)),
    )
