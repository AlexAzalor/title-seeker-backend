from fastapi import APIRouter, Body, HTTPException, Depends, status

from api.dependency.user import get_admin
from api.utils import get_all_items
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

genre_router = APIRouter(prefix="/genres", tags=["Genres"])


@genre_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.FilterList,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Error retrieving genres"},
        status.HTTP_200_OK: {"description": "Genres successfully retrieved"},
    },
)
def get_genres(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all genres"""

    genre_selection_query = (
        sa.select(m.Genre)
        .join(m.Genre.translations)
        .where(m.GenreTranslation.language == lang.value)
        .order_by(m.GenreTranslation.name)
    )

    items = get_all_items(db, genre_selection_query, lang)
    return s.FilterList(items=items)


@genre_router.get(
    "/subgenres/",
    status_code=status.HTTP_200_OK,
    response_model=s.FilterList,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Error retrieving subgenres"},
        status.HTTP_200_OK: {"description": "Subgenres successfully retrieved"},
    },
)
def get_subgenres(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all subgenres"""

    subgenre_selection_query = (
        sa.select(m.Subgenre)
        .join(m.Subgenre.translations)
        .where(m.SubgenreTranslation.language == lang.value)
        .order_by(m.SubgenreTranslation.name)
    )

    items = get_all_items(db, subgenre_selection_query, lang)
    return s.FilterList(items=items)


@genre_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.GenreFormOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Genre already exists"},
        status.HTTP_201_CREATED: {"description": "Genre successfully created"},
    },
)
def create_genre(
    form_data: s.GenreFormIn = Body(...),
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new genre"""

    genre = db.scalar(sa.select(m.Genre).where(m.Genre.key == form_data.key))

    if genre:
        log(log.ERROR, "Genre [%s] already exists")
        raise HTTPException(status_code=400, detail="Genre already exists")

    try:
        new_genre = m.Genre(
            key=form_data.key,
            translations=[
                m.GenreTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                    description=form_data.description_uk,
                ),
                m.GenreTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                    description=form_data.description_en,
                ),
            ],
        )

        db.add(new_genre)
        db.commit()
        log(log.INFO, "Genre [%s] successfully created by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        log(log.ERROR, "Error creating genre [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating genre")

    db.refresh(new_genre)

    return s.GenreFormOut(
        key=new_genre.key,
        name=new_genre.get_name(lang),
        description=new_genre.get_description(lang),
    )


@genre_router.post(
    "/subgenres/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.GenreFormOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Subgenre already exists"},
        status.HTTP_201_CREATED: {"description": "Subgenre successfully created"},
    },
)
def create_subgenre(
    form_data: s.GenreFormIn = Body(...),
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new subgenre"""

    subgenre = db.scalar(sa.select(m.Subgenre).where(m.Subgenre.key == form_data.key))

    if subgenre:
        log(log.ERROR, "Subgenre [%s] already exists")
        raise HTTPException(status_code=400, detail="Subgenre already exists")

    genre_id = db.scalar(sa.select(m.Genre.id).where(m.Genre.key == form_data.parent_genre_key))
    if not genre_id:
        log(log.ERROR, "Genre [%s] not found", form_data.parent_genre_key)
        raise HTTPException(status_code=404, detail="Genre not found")

    try:
        new_subgenre = m.Subgenre(
            genre_id=genre_id,
            key=form_data.key,
            translations=[
                m.SubgenreTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                    description=form_data.description_uk,
                ),
                m.SubgenreTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                    description=form_data.description_en,
                ),
            ],
        )

        db.add(new_subgenre)
        db.commit()
        log(log.INFO, "Subgenre [%s] successfully created by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        log(log.ERROR, "Error creating subgenre [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating subgenre")

    db.refresh(new_subgenre)

    return s.GenreFormOut(
        key=new_subgenre.key,
        name=new_subgenre.get_name(lang),
        description=new_subgenre.get_description(lang),
        parent_genre_key=form_data.parent_genre_key,
    )


@genre_router.put(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Genre does not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Error updating genre"},
        status.HTTP_204_NO_CONTENT: {"description": "Genre successfully updated"},
    },
)
def update_genre_item(
    type: s.FilterEnum,
    form_data: s.GenreFormFieldsWithUUID = Body(...),
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Update genre item in the admin page"""

    genre_item = None

    if type == s.FilterEnum.GENRE:
        genre_item = db.scalar(sa.select(m.Genre).where(m.Genre.uuid == form_data.uuid))
        if not genre_item:
            log(log.ERROR, "Genre [%s] does not exist", form_data.key)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Genre does not exist")

    if type == s.FilterEnum.SUBGENRE:
        genre_item = db.scalar(sa.select(m.Subgenre).where(m.Subgenre.uuid == form_data.uuid))
        if not genre_item:
            log(log.ERROR, "Subgenre [%s] does not exist", form_data.key)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subgenre does not exist")

    if not genre_item:
        log(log.ERROR, "Genre item [%s] does not exist", form_data.key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genre item does not exist")

    try:
        if genre_item.key != form_data.key:
            genre_item.key = form_data.key

        existing = {t.language: t for t in genre_item.translations}

        existing[s.Language.EN.value].name = form_data.name_en
        existing[s.Language.EN.value].description = form_data.description_en
        existing[s.Language.UK.value].name = form_data.name_uk
        existing[s.Language.UK.value].description = form_data.description_uk

        db.commit()
        log(log.INFO, "Genre item [%s] successfully updated by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        log(log.ERROR, "Error updating genre item [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating genre item")


@genre_router.get(
    "/form-fields/",
    status_code=status.HTTP_200_OK,
    response_model=s.GenreFormFieldsWithUUID,
    responses={
        status.HTTP_200_OK: {"description": "Genre form fields successfully retrieved"},
        status.HTTP_404_NOT_FOUND: {"description": "No items found"},
    },
)
def get_genre_form_fields(
    item_key: str,
    type: s.FilterEnum | None = None,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Get genre form field for admin page (with all fields)"""

    item_out = None
    item = None

    if type == s.FilterEnum.GENRE:
        item = db.scalar(sa.select(m.Genre).where(m.Genre.key == item_key))
    if type == s.FilterEnum.SUBGENRE:
        item = db.scalar(sa.select(m.Subgenre).where(m.Subgenre.key == item_key))

    if not item:
        log(log.WARNING, "No item found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No item found")

    item_out = s.GenreFormFieldsWithUUID(
        uuid=item.uuid,
        key=item.key,
        name_en=item.get_name(s.Language.EN),
        name_uk=item.get_name(s.Language.UK),
        description_en=item.get_description(s.Language.EN),
        description_uk=item.get_description(s.Language.UK),
    )

    if not item_out:
        log(log.WARNING, "No item found for key: %s", item_key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No item found")
    return item_out
