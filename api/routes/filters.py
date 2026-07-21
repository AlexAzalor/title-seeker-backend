from fastapi import APIRouter, Body, HTTPException, Depends, status

from api.dependency.user import get_admin
from api.utils import get_all_items
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session, selectinload
from app.database import get_db

filter_router = APIRouter(
    prefix="/filters",
    tags=["Filters"],
)


@filter_router.get(
    "/specifications/",
    status_code=status.HTTP_200_OK,
    response_model=s.FilterList,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Specification already exists"},
        status.HTTP_201_CREATED: {"description": "Specification successfully created"},
    },
)
def get_specifications(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all specifications"""

    specification_select = (
        sa.select(m.Specification)
        .options(selectinload(m.Specification.translations))
        .join(m.Specification.translations)
        .where(m.SpecificationTranslation.language == lang.value)
        .order_by(m.Specification.movie_count.desc())
    )

    items = get_all_items(db, specification_select, lang)
    return s.FilterList(items=items)


@filter_router.get(
    "/keywords/",
    status_code=status.HTTP_200_OK,
    response_model=s.FilterList,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Keywords already exists"},
        status.HTTP_201_CREATED: {"description": "Keywords successfully created"},
    },
)
def get_keywords(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all keywords"""

    keyword_select = (
        sa.select(m.Keyword)
        .options(selectinload(m.Keyword.translations))
        .join(m.Keyword.translations)
        .where(m.KeywordTranslation.language == lang.value)
        .order_by(m.Keyword.movie_count.desc())
    )

    items = get_all_items(db, keyword_select, lang)
    return s.FilterList(items=items)


@filter_router.get(
    "/action-times/",
    status_code=status.HTTP_200_OK,
    response_model=s.FilterList,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Keywords already exists"},
        status.HTTP_201_CREATED: {"description": "Keywords successfully created"},
    },
)
def get_action_times(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all action times"""

    action_time_select = (
        sa.select(m.ActionTime)
        .options(selectinload(m.ActionTime.translations))
        .join(m.ActionTime.translations)
        .where(m.ActionTimeTranslation.language == lang.value)
        .order_by(m.ActionTime.order.desc())
    )

    items = get_all_items(db, action_time_select, lang)
    return s.FilterList(items=items)


@filter_router.post(
    "/specifications/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.FilterItemOut,
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
        log(log.INFO, "Specification [%s] successfully created by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        log(log.ERROR, "Error creating specification [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating specification")

    db.refresh(new_specification)

    return s.FilterItemOut(
        key=new_specification.key,
        name=new_specification.get_name(lang),
        description=new_specification.get_description(lang),
        percentage_match=0.0,
        movie_count=0,
    )


@filter_router.post(
    "/keywords/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.FilterItemOut,
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
        log(log.INFO, "Keyword [%s] successfully created by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        log(log.ERROR, "Error creating keyword [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating keyword")

    db.refresh(new_keyword)

    return s.FilterItemOut(
        key=new_keyword.key,
        name=new_keyword.get_name(lang),
        description=new_keyword.get_description(lang),
        percentage_match=0.0,
        movie_count=0,
    )


@filter_router.post(
    "/action-times/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.FilterItemOut,
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
        log(log.INFO, "ActionTime [%s] successfully created by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        log(log.ERROR, "Error creating action time [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating action time")

    db.refresh(new_action_time)

    return s.FilterItemOut(
        key=new_action_time.key,
        name=new_action_time.get_name(lang),
        description=new_action_time.get_description(lang),
        percentage_match=0.0,
        movie_count=0,
    )


@filter_router.put(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Specification does not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Error updating specification"},
        status.HTTP_204_NO_CONTENT: {"description": "Specification successfully updated"},
    },
)
def update_filter_item(
    type: s.FilterEnum,
    form_data: s.FilterFieldsWithUUID = Body(...),
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Update filter item in the admin page"""

    filter_item = None

    if type == s.FilterEnum.SPECIFICATION:
        filter_item = db.scalar(sa.select(m.Specification).where(m.Specification.uuid == form_data.uuid))
        if not filter_item:
            log(log.ERROR, "Specification [%s] does not exist", form_data.key)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Specification does not exist")

    if type == s.FilterEnum.KEYWORD:
        filter_item = db.scalar(sa.select(m.Keyword).where(m.Keyword.uuid == form_data.uuid))
        if not filter_item:
            log(log.ERROR, "Keyword [%s] does not exist", form_data.key)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Keyword does not exist")

    if type == s.FilterEnum.ACTION_TIME:
        filter_item = db.scalar(sa.select(m.ActionTime).where(m.ActionTime.uuid == form_data.uuid))
        if not filter_item:
            log(log.ERROR, "ActionTime [%s] does not exist", form_data.key)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ActionTime does not exist")

    if not filter_item:
        log(log.ERROR, "Filter item [%s] does not exist", form_data.key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filter item does not exist")

    try:
        if filter_item.key != form_data.key:
            filter_item.key = form_data.key

        if form_data.order is not None:
            filter_item.order = form_data.order

        existing = {t.language: t for t in filter_item.translations}

        existing[s.Language.EN.value].name = form_data.name_en
        existing[s.Language.EN.value].description = form_data.description_en
        existing[s.Language.UK.value].name = form_data.name_uk
        existing[s.Language.UK.value].description = form_data.description_uk

        db.commit()
        log(log.INFO, "Filter item [%s] successfully updated by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        log(log.ERROR, "Error updating filter item [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating filter item")


@filter_router.get(
    "/form-fields/",
    status_code=status.HTTP_200_OK,
    response_model=s.FilterFieldsWithUUID,
    responses={
        status.HTTP_200_OK: {"description": "Filter forms successfully retrieved"},
        status.HTTP_404_NOT_FOUND: {"description": "No items found"},
    },
)
def get_filter_form_fields(
    item_key: str,
    type: s.FilterEnum | None = None,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Get filter form field for admin page (with all fields)"""

    item_out = None
    item = None

    if type == s.FilterEnum.SPECIFICATION:
        item = db.scalar(
            sa.select(m.Specification)
            .options(selectinload(m.Specification.translations))
            .where(m.Specification.key == item_key)
        )
    if type == s.FilterEnum.KEYWORD:
        item = db.scalar(
            sa.select(m.Keyword).options(selectinload(m.Keyword.translations)).where(m.Keyword.key == item_key)
        )
    if type == s.FilterEnum.ACTION_TIME:
        item = db.scalar(
            sa.select(m.ActionTime).options(selectinload(m.ActionTime.translations)).where(m.ActionTime.key == item_key)
        )

    if not item:
        log(log.WARNING, "No item found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No item found")

    item_out = s.FilterFieldsWithUUID(
        uuid=item.uuid,
        key=item.key,
        name_en=item.get_name(s.Language.EN),
        name_uk=item.get_name(s.Language.UK),
        description_en=item.get_description(s.Language.EN),
        description_uk=item.get_description(s.Language.UK),
        order=getattr(item, "order", None),
    )

    if not item_out:
        log(log.WARNING, "No item found for key: %s", item_key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No item found")
    return item_out


@filter_router.delete(
    "/specification/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Specification successfully deleted"},
        status.HTTP_400_BAD_REQUEST: {
            "description": "Keyword is associated with multiple movies",
            "model": list[s.MovieMenuItem],
        },
        status.HTTP_404_NOT_FOUND: {"description": "Specification not found"},
    },
)
def delete_specification(
    key: str,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Delete specification from a movie"""

    specification = db.scalar(
        sa.select(m.Specification)
        .options(selectinload(m.Specification.movies).selectinload(m.Movie.translations))
        .where(m.Specification.key == key)
    )

    if not specification:
        log(log.ERROR, "Specification [%s] not found", key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specification not found")

    if specification.movie_count > 1:
        movie_list = [
            s.MovieMenuItem(key=movie.key, name=movie.get_title(s.Language.EN)) for movie in specification.movies
        ]
        log(log.ERROR, "Specification [%s] is associated with multiple movies and cannot be deleted", specification.key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[item.model_dump() for item in movie_list],
        )

    try:
        db.delete(specification)
        db.commit()

        log(log.INFO, "Specification [%s] successfully deleted", specification.key)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error deleting specification [%s]: %s", specification.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error deleting specification")


@filter_router.delete(
    "/keyword/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Keywords successfully deleted"},
        status.HTTP_400_BAD_REQUEST: {
            "description": "Keyword is associated with multiple movies",
            "model": list[s.MovieMenuItem],
        },
        status.HTTP_404_NOT_FOUND: {"description": "Keywords not found"},
    },
)
def delete_keyword(
    key: str,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Delete keyword from a movie"""

    keyword = db.scalar(
        sa.select(m.Keyword)
        .options(selectinload(m.Keyword.movies).selectinload(m.Movie.translations))
        .where(m.Keyword.key == key)
    )

    if not keyword:
        log(log.ERROR, "Keyword [%s] not found", key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keyword not found")

    if keyword.movie_count > 1:
        movie_list = [s.MovieMenuItem(key=movie.key, name=movie.get_title(s.Language.EN)) for movie in keyword.movies]
        log(log.ERROR, "Keyword [%s] is associated with multiple movies and cannot be deleted", keyword.key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[item.model_dump() for item in movie_list],
        )

    try:
        db.delete(keyword)
        db.commit()

        log(log.INFO, "Keyword [%s] successfully deleted", keyword.key)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error deleting keyword [%s]: %s", keyword.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error deleting keyword")


@filter_router.delete(
    "/action-time/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Action time successfully deleted"},
        status.HTTP_400_BAD_REQUEST: {
            "description": "Keyword is associated with multiple movies",
            "model": list[s.MovieMenuItem],
        },
        status.HTTP_404_NOT_FOUND: {"description": "Action time not found"},
    },
)
def delete_action_time(
    key: str,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Delete action time from a movie"""

    action_time = db.scalar(
        sa.select(m.ActionTime)
        .options(selectinload(m.ActionTime.movies).selectinload(m.Movie.translations))
        .where(m.ActionTime.key == key)
    )

    if not action_time:
        log(log.ERROR, "ActionTime [%s] not found", key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ActionTime not found")

    if action_time.movie_count > 1:
        movie_list = [
            s.MovieMenuItem(key=movie.key, name=movie.get_title(s.Language.EN)) for movie in action_time.movies
        ]
        log(log.ERROR, "ActionTime [%s] is associated with multiple movies and cannot be deleted", action_time.key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[item.model_dump() for item in movie_list],
        )

    try:
        db.delete(action_time)
        db.commit()

        log(log.INFO, "ActionTime [%s] successfully deleted", action_time.key)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error deleting action time [%s]: %s", action_time.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error deleting action time")
