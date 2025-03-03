from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, Depends, status

import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

specification_router = APIRouter(prefix="/specifications", tags=["Specifications"])


@specification_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.SpecificationOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Specification already exists"},
        status.HTTP_201_CREATED: {"description": "Specification successfully created"},
    },
)
def create_specification(
    key: Annotated[str, Form()],
    name_uk: Annotated[str, Form()],
    name_en: Annotated[str, Form()],
    description_uk: Annotated[str | None, Form()] = None,
    description_en: Annotated[str | None, Form()] = None,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new specification"""

    specification = db.scalar(sa.select(m.Specification).where(m.Specification.key == key))

    if specification:
        log(log.ERROR, "Specification [%s] already exists")
        raise HTTPException(status_code=400, detail="Specification already exists")

    try:
        new_specification = m.Specification(
            key=key,
            translations=[
                m.SpecificationTranslation(
                    language=s.Language.UK.value,
                    name=name_uk,
                    description=description_uk,
                ),
                m.SpecificationTranslation(
                    language=s.Language.EN.value,
                    name=name_en,
                    description=description_en,
                ),
            ],
        )

        db.add(new_specification)
        db.commit()
        log(log.INFO, "Specification [%s] successfully created", key)
    except Exception as e:
        log(log.ERROR, "Error creating specification [%s]: %s", key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating specification")

    db.refresh(new_specification)

    return s.SpecificationOut(
        key=new_specification.key,
        name=next((t.name for t in new_specification.translations if t.language == lang.value)),
        description=next((t.description for t in new_specification.translations if t.language == lang.value)),
    )
