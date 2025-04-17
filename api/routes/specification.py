from fastapi import APIRouter, Body, HTTPException, Depends, status

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
    response_model=s.MovieFilterFormOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Specification already exists"},
        status.HTTP_201_CREATED: {"description": "Specification successfully created"},
    },
)
def create_specification(
    form_data: s.MovieFilterFormIn = Body(...),
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new specification"""

    specification = db.scalar(sa.select(m.Specification).where(m.Specification.key == form_data.key))

    if specification:
        log(log.ERROR, "Specification [%s] already exists")
        raise HTTPException(status_code=400, detail="Specification already exists")

    try:
        new_specification = m.Specification(
            key=form_data.key,
            translations=[
                m.SpecificationTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                    description=form_data.description_uk,
                ),
                m.SpecificationTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                    description=form_data.description_en,
                ),
            ],
        )

        db.add(new_specification)
        db.commit()
        log(log.INFO, "Specification [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating specification [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating specification")

    db.refresh(new_specification)

    return s.MovieFilterFormOut(
        key=new_specification.key,
        name=next((t.name for t in new_specification.translations if t.language == lang.value)),
    )
