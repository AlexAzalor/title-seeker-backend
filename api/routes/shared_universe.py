from fastapi import APIRouter, Body, HTTPException, Depends, status

from api.dependency.user import get_admin
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
    response_model=s.BaseSharedUniverse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Shared universe already exists"},
        status.HTTP_201_CREATED: {"description": "Shared universe successfully created"},
    },
)
def create_shared_universe(
    # TODO: refactor GenreFormIn name
    form_data: s.GenreFormIn = Body(...),
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new shared universe"""

    shared_universe = db.scalar(sa.select(m.SharedUniverse.key).where(m.SharedUniverse.key == form_data.key))

    if shared_universe:
        log(log.ERROR, "Shared universe [%s] already exists")
        raise HTTPException(status_code=400, detail="Shared universe already exists")

    try:
        new_su = m.SharedUniverse(
            key=form_data.key,
            translations=[
                m.SharedUniverseTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                    description=form_data.description_uk,
                ),
                m.SharedUniverseTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                    description=form_data.description_en,
                ),
            ],
        )

        db.add(new_su)
        db.commit()
        log(log.INFO, "Shared universe [%s] successfully created by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        log(log.ERROR, "Error creating Shared universe [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating Shared universe")

    db.refresh(new_su)

    return s.GenreFormOut(
        key=new_su.key,
        name=new_su.get_name(lang),
        description=new_su.get_description(lang),
    )
