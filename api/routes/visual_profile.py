from fastapi import APIRouter, Body, HTTPException, Depends, status

from api.dependency.user import get_admin
from api.utils import check_admin_permissions
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

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
