from fastapi import APIRouter, Body, HTTPException, Depends, status

from api.dependency.user import get_admin
from api.utils import check_admin_permissions
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db
from config import config

CFG = config()

visual_profile_router = APIRouter(
    prefix="/visual-profile",
    tags=["Visual Profile"],
)


@visual_profile_router.get(
    "/categories/",
    status_code=status.HTTP_200_OK,
    response_model=s.VisualProfileListOut,
    responses={
        status.HTTP_200_OK: {"description": "Categories successfully retrieved"},
        status.HTTP_404_NOT_FOUND: {"description": "No categories found"},
    },
)
def get_categories(
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Get all categories"""
    check_admin_permissions(current_user)

    categories = db.scalars(
        sa.select(m.TitleCategory)
        .join(m.TitleCategory.translations)
        .where(m.TitleCategoryTranslation.language == lang.value)
        .order_by(m.TitleCategoryTranslation.name)
    ).all()

    categories_out = [
        s.TitleCategoryData(
            key=category.key,
            name=category.get_name(lang),
            description=category.get_description(lang),
            criteria=[
                s.CategoryCriterionData(
                    key=criterion.key,
                    name=criterion.get_name(lang),
                    description=criterion.get_description(lang),
                    rating=0,
                )
                for criterion in category.criteria
            ],
        )
        for category in categories
    ]
    return s.VisualProfileListOut(items=categories_out)


@visual_profile_router.post(
    "/category/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.CategoryFormOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Category already exists"},
        status.HTTP_201_CREATED: {"description": "Category successfully created"},
    },
)
def create_category(
    form_data: s.CategoryFormIn = Body(...),
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new category"""

    check_admin_permissions(current_user)

    category = db.scalar(sa.select(m.TitleCategory).where(m.TitleCategory.key == form_data.key))

    if category:
        log(log.ERROR, "Category [%s] already exists")
        raise HTTPException(status_code=400, detail="Category already exists")

    try:
        new_category = m.TitleCategory(
            key=form_data.key,
            translations=[
                m.TitleCategoryTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                    description=form_data.description_uk,
                ),
                m.TitleCategoryTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                    description=form_data.description_en,
                ),
            ],
        )

        db.add(new_category)
        db.commit()
        log(log.INFO, "Category [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating category [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating category")

    db.refresh(new_category)

    return s.CategoryFormOut(
        key=new_category.key,
        name=new_category.get_name(lang),
        description=new_category.get_description(lang),
    )


@visual_profile_router.put(
    "/category/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Category already exists"},
        status.HTTP_204_NO_CONTENT: {"description": "Category successfully updated"},
    },
)
def update_category(
    form_data: s.EditCategoryFormIn = Body(...),
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Update existing category"""

    check_admin_permissions(current_user)

    category = db.scalar(sa.select(m.TitleCategory).where(m.TitleCategory.key == form_data.old_key))
    if not category:
        log(log.ERROR, "Category [%s] does not exist", form_data.key)
        raise HTTPException(status_code=400, detail="Category does not exist")

    try:
        if form_data.key != form_data.old_key:
            category.key = form_data.key

        existing = {t.language: t for t in category.translations}

        existing[s.Language.EN.value].name = form_data.name_en
        existing[s.Language.EN.value].description = form_data.description_en
        existing[s.Language.UK.value].name = form_data.name_uk
        existing[s.Language.UK.value].description = form_data.description_uk

        db.commit()
        log(log.INFO, "Category [%s] successfully updated", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error updating category [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating category")


@visual_profile_router.get(
    "/criteria/",
    status_code=status.HTTP_200_OK,
    response_model=s.CriterionFormList,
    responses={
        status.HTTP_200_OK: {"description": "Criteria successfully retrieved"},
        status.HTTP_404_NOT_FOUND: {"description": "No Criteria found"},
    },
)
def get_criteria(
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Get all criteria"""

    check_admin_permissions(current_user)

    criteria = db.scalars(sa.select(m.TitleCriterion)).all()

    if not criteria:
        log(log.WARNING, "No criteria found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Criteria found")

    criteria_out = [
        s.CategoryFormIn(
            key=category.key,
            name_en=category.get_name(s.Language.EN),
            name_uk=category.get_name(s.Language.UK),
            description_en=category.get_description(s.Language.EN),
            description_uk=category.get_description(s.Language.UK),
        )
        for category in criteria
    ]

    return s.CriterionFormList(criteria=criteria_out)


@visual_profile_router.post(
    "/criterion/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.CategoryFormOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Criterion already exists"},
        status.HTTP_201_CREATED: {"description": "Criterion successfully created"},
    },
)
def create_criterion(
    form_data: s.CategoryFormIn = Body(...),
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new criterion"""

    check_admin_permissions(current_user)

    criterion = db.scalar(sa.select(m.TitleCriterion).where(m.TitleCriterion.key == form_data.key))

    if criterion:
        log(log.ERROR, "Criterion [%s] already exists")
        raise HTTPException(status_code=400, detail="Criterion already exists")

    try:
        new_criterion = m.TitleCriterion(
            key=form_data.key,
            translations=[
                m.TitleCriterionTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                    description=form_data.description_uk,
                ),
                m.TitleCriterionTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                    description=form_data.description_en,
                ),
            ],
        )

        db.add(new_criterion)
        db.commit()
        log(log.INFO, "Criterion [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating criterion [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating criterion")

    db.refresh(new_criterion)

    return s.CategoryFormOut(
        key=new_criterion.key,
        name=new_criterion.get_name(lang),
        description=new_criterion.get_description(lang),
    )


@visual_profile_router.put(
    "/criterion/",
    status_code=status.HTTP_204_NO_CONTENT,
    # response_model=s.CategoryFormOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Criterion already exists"},
        status.HTTP_204_NO_CONTENT: {"description": "Criterion successfully updated"},
    },
)
def update_criterion(
    form_data: s.EditCategoryFormIn = Body(...),
    # lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Update existing criterion"""

    check_admin_permissions(current_user)

    criterion = db.scalar(sa.select(m.TitleCriterion).where(m.TitleCriterion.key == form_data.old_key))
    if not criterion:
        log(log.ERROR, "Criterion [%s] does not exist", form_data.key)
        raise HTTPException(status_code=400, detail="Criterion does not exist")

    try:
        if form_data.key != form_data.old_key:
            criterion.key = form_data.key

        existing = {t.language: t for t in criterion.translations}

        existing[s.Language.EN.value].name = form_data.name_en
        existing[s.Language.EN.value].description = form_data.description_en
        existing[s.Language.UK.value].name = form_data.name_uk
        existing[s.Language.UK.value].description = form_data.description_uk

        db.commit()
        log(log.INFO, "Criterion [%s] successfully updated", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error updating criterion [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating criterion")


@visual_profile_router.get(
    "/forms/",
    status_code=status.HTTP_200_OK,
    response_model=s.VisualProfileFormOut,
    responses={
        status.HTTP_200_OK: {"description": "Categories successfully retrieved"},
        status.HTTP_404_NOT_FOUND: {"description": "No items found"},
    },
)
def get_visual_profile_forms(
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Get all categories with criteria for visual profile forms"""

    check_admin_permissions(current_user)

    categories = db.scalars(sa.select(m.TitleCategory)).all()
    if not categories:
        log(log.WARNING, "No categories found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No categories found")

    impact = db.scalar(sa.select(m.TitleCriterion).where(m.TitleCriterion.key == CFG.UNIQUE_CRITERION_KEY))
    if not impact:
        log(log.ERROR, "Impact criterion not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impact criterion not found")

    categories_out = [
        s.VisualProfileForm(
            key=category.key,
            name_en=category.get_name(s.Language.EN),
            name_uk=category.get_name(s.Language.UK),
            description_en=category.get_description(s.Language.EN),
            description_uk=category.get_description(s.Language.UK),
            criteria=[
                s.CategoryFormIn(
                    key=criterion.key,
                    name_en=criterion.get_name(s.Language.EN),
                    name_uk=criterion.get_name(s.Language.UK),
                    description_en=criterion.get_description(s.Language.EN),
                    description_uk=criterion.get_description(s.Language.UK),
                )
                for criterion in sorted(category.criteria, key=lambda x: x.id)
                if criterion.key != CFG.UNIQUE_CRITERION_KEY
            ],
        )
        for category in categories
    ]
    return s.VisualProfileFormOut(
        impact=s.CategoryFormIn(
            key=impact.key,
            name_en=impact.get_name(s.Language.EN),
            name_uk=impact.get_name(s.Language.UK),
            description_en=impact.get_description(s.Language.EN),
            description_uk=impact.get_description(s.Language.UK),
        ),
        categories=categories_out,
    )
