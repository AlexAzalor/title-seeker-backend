from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, Depends, status

import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

shared_universe_router = APIRouter(prefix="/shared-universes", tags=["Shared universes"])


@shared_universe_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.SharedUniversePreCreateOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Shared universe already exists"},
        status.HTTP_201_CREATED: {"description": "Shared universe successfully created"},
    },
)
def create_shared_universe(
    key: Annotated[str, Form()],
    name_uk: Annotated[str, Form()],
    name_en: Annotated[str, Form()],
    description_uk: Annotated[str | None, Form()] = None,
    description_en: Annotated[str | None, Form()] = None,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new shared universe"""

    shared_universe = db.scalar(sa.select(m.SharedUniverse.key).where(m.SharedUniverse.key == key))

    if shared_universe:
        log(log.ERROR, "Shared universe [%s] already exists")
        raise HTTPException(status_code=400, detail="Shared universe already exists")

    try:
        new_su = m.SharedUniverse(
            key=key,
            translations=[
                m.SharedUniverseTranslation(
                    language=s.Language.UK.value,
                    name=name_uk,
                    description=description_uk,
                ),
                m.SharedUniverseTranslation(
                    language=s.Language.EN.value,
                    name=name_en,
                    description=description_en,
                ),
            ],
        )

        db.add(new_su)
        db.commit()
        log(log.INFO, "Shared universe [%s] successfully created", key)
    except Exception as e:
        log(log.ERROR, "Error creating Shared universe [%s]: %s", key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating Shared universe")

    db.refresh(new_su)

    return s.SharedUniversePreCreateOut(
        key=new_su.key,
        name=next((t.name for t in new_su.translations if t.language == lang.value)),
        description=next((t.description for t in new_su.translations if t.language == lang.value)),
    )
