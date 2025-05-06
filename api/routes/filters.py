from fastapi import APIRouter, Body, HTTPException, Depends, status

from api.dependency.user import get_admin
from api.utils import check_admin_permissions
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

filter_router = APIRouter(
    prefix="/filters",
    tags=["Filters"],
)


@filter_router.post(
    "/specifications/",
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
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new specification"""

    check_admin_permissions(current_user)

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


@filter_router.post(
    "/keywords/",
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
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new keyword"""

    check_admin_permissions(current_user)

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


@filter_router.post(
    "/action-times/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.MovieFilterFormOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Action Time already exists"},
        status.HTTP_201_CREATED: {"description": "Action Time successfully created"},
    },
)
def create_action_time(
    form_data: s.MovieFilterFormIn = Body(...),
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new action time"""

    check_admin_permissions(current_user)

    action_time = db.scalar(sa.select(m.ActionTime).where(m.ActionTime.key == form_data.key))

    if action_time:
        log(log.ERROR, "ActionTime [%s] already exists")
        raise HTTPException(status_code=400, detail="ActionTime already exists")

    try:
        new_action_time = m.ActionTime(
            key=form_data.key,
            translations=[
                m.ActionTimeTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                    description=form_data.description_uk,
                ),
                m.ActionTimeTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                    description=form_data.description_en,
                ),
            ],
        )

        db.add(new_action_time)
        db.commit()
        log(log.INFO, "ActionTime [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating action time [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating action time")

    db.refresh(new_action_time)

    return s.MovieFilterFormOut(
        key=new_action_time.key,
        name=next((t.name for t in new_action_time.translations if t.language == lang.value)),
    )
