from fastapi import APIRouter, Body, HTTPException, Depends, status

from api.dependency.user import get_admin, get_owner
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session, selectinload
from app.database import get_db
from config import config

CFG = config()

visual_profile_router = APIRouter(
    prefix="/visual-profile",
    tags=["Visual Profile"],
)


@visual_profile_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.VisualProfileListOut,
    responses={
        status.HTTP_200_OK: {"description": "Categories successfully retrieved"},
        status.HTTP_404_NOT_FOUND: {"description": "No categories found"},
    },
)
def get_visual_profiles(
    lang: s.Language = s.Language.UK,
    # current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Get visual profile list"""

    visual_profiles = db.scalars(
        sa.select(m.VisualProfileCategory).options(
            selectinload(m.VisualProfileCategory.translations),
            selectinload(m.VisualProfileCategory.criteria).selectinload(m.VisualProfileCategoryCriterion.translations),
        )
    ).all()
    if not visual_profiles:
        log(log.WARNING, "No visual profiles found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No visual profiles found")

    categories_out = [
        s.VisualProfileData(
            key=vp_category.key,
            name=vp_category.get_name(lang),
            description=vp_category.get_description(lang),
            criteria=[
                s.VisualProfileCriterionData(
                    key=criterion.key,
                    name=criterion.get_name(lang),
                    description=criterion.get_description(lang),
                    rating=0,
                )
                for criterion in vp_category.criteria
            ],
        )
        for vp_category in sorted(visual_profiles, key=lambda x: x.id)
    ]

    return s.VisualProfileListOut(items=categories_out)


@visual_profile_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Category already exists"},
        status.HTTP_201_CREATED: {"description": "Category successfully created"},
    },
)
def create_visual_profile(
    form_data: s.VisualProfileFormIn = Body(...),
    current_user: m.User = Depends(get_owner),
    db: Session = Depends(get_db),
):
    """Create new visual profile in the admin page"""

    category = db.scalar(sa.select(m.VisualProfileCategory).where(m.VisualProfileCategory.key == form_data.key))
    if category:
        log(log.ERROR, "Category [%s] already exists")
        raise HTTPException(status_code=400, detail="Category already exists")

    # Universal criterion for all categories
    impact_criterion = db.scalar(
        sa.select(m.VisualProfileCategoryCriterion).where(
            m.VisualProfileCategoryCriterion.key == CFG.UNIQUE_CRITERION_KEY
        )
    )
    if not impact_criterion:
        log(log.ERROR, "Impact criterion not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impact criterion not found")

    try:
        new_category = m.VisualProfileCategory(
            key=form_data.key,
            translations=[
                m.VPCategoryTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                    description=form_data.description_uk,
                ),
                m.VPCategoryTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                    description=form_data.description_en,
                ),
            ],
        )

        new_category.criteria.append(impact_criterion)
        db.add(new_category)
        db.flush()

        for criterion in form_data.criteria:
            criterion_db = db.scalar(
                sa.select(m.VisualProfileCategoryCriterion).where(m.VisualProfileCategoryCriterion.key == criterion.key)
            )

            if criterion_db:
                log(log.ERROR, "Criterion [%s] already exists", criterion.key)
                raise HTTPException(status_code=400, detail=f"Criterion [{criterion.key}] already exists")

            new_criterion = m.VisualProfileCategoryCriterion(
                key=criterion.key,
                translations=[
                    m.VPCriterionTranslation(
                        language=s.Language.UK.value,
                        name=criterion.name_uk,
                        description=criterion.description_uk,
                    ),
                    m.VPCriterionTranslation(
                        language=s.Language.EN.value,
                        name=criterion.name_en,
                        description=criterion.description_en,
                    ),
                ],
            )
            db.add(new_criterion)
            new_category.criteria.append(new_criterion)

        db.commit()

        log(log.INFO, "Category [%s] successfully created by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        log(log.ERROR, "Error creating category [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating category")


@visual_profile_router.put(
    "/category/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Category already exists"},
        status.HTTP_204_NO_CONTENT: {"description": "Category successfully updated"},
    },
)
def update_category(
    form_data: s.VisualProfileFieldWithUUID = Body(...),
    current_user: m.User = Depends(get_owner),
    db: Session = Depends(get_db),
):
    """Update existing category in the admin page"""

    category = db.scalar(sa.select(m.VisualProfileCategory).where(m.VisualProfileCategory.uuid == form_data.uuid))
    if not category:
        log(log.ERROR, "Category [%s] does not exist", form_data.key)
        raise HTTPException(status_code=400, detail="Category does not exist")

    try:
        if category.key != form_data.key:
            category.key = form_data.key

        existing = {t.language: t for t in category.translations}

        existing[s.Language.EN.value].name = form_data.name_en
        existing[s.Language.EN.value].description = form_data.description_en
        existing[s.Language.UK.value].name = form_data.name_uk
        existing[s.Language.UK.value].description = form_data.description_uk

        db.commit()
        log(log.INFO, "Category [%s] successfully updated by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        log(log.ERROR, "Error updating category [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating category")


@visual_profile_router.put(
    "/criterion/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Criterion already exists"},
        status.HTTP_204_NO_CONTENT: {"description": "Criterion successfully updated"},
    },
)
def update_criterion(
    form_data: s.VisualProfileFieldWithUUID = Body(...),
    current_user: m.User = Depends(get_owner),
    db: Session = Depends(get_db),
):
    """Update existing criterion in the admin page"""

    criterion = db.scalar(
        sa.select(m.VisualProfileCategoryCriterion).where(m.VisualProfileCategoryCriterion.uuid == form_data.uuid)
    )
    if not criterion:
        log(log.ERROR, "Criterion [%s] does not exist", form_data.key)
        raise HTTPException(status_code=400, detail="Criterion does not exist")

    try:
        if criterion.key != form_data.key:
            criterion.key = form_data.key

        existing = {t.language: t for t in criterion.translations}

        existing[s.Language.EN.value].name = form_data.name_en
        existing[s.Language.EN.value].description = form_data.description_en
        existing[s.Language.UK.value].name = form_data.name_uk
        existing[s.Language.UK.value].description = form_data.description_uk

        db.commit()
        log(log.INFO, "Criterion [%s] successfully updated by user [%s]", form_data.key, current_user.email)
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
    """Get all categories with criteria for admin page (with all fields)"""

    categories = db.scalars(
        sa.select(m.VisualProfileCategory).options(
            selectinload(m.VisualProfileCategory.translations),
            selectinload(m.VisualProfileCategory.criteria).selectinload(m.VisualProfileCategoryCriterion.translations),
        )
    ).all()
    if not categories:
        log(log.WARNING, "No categories found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No categories found")

    # Universal criterion for all categories
    # TODO: centralize somewhere?
    impact = db.scalar(
        sa.select(m.VisualProfileCategoryCriterion)
        .options(selectinload(m.VisualProfileCategoryCriterion.translations))
        .where(m.VisualProfileCategoryCriterion.key == CFG.UNIQUE_CRITERION_KEY)
    )
    if not impact:
        log(log.ERROR, "Impact criterion not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impact criterion not found")

    categories_out = [
        s.VisualProfileForm(
            uuid=category.uuid,
            key=category.key,
            name_en=category.get_name(s.Language.EN),
            name_uk=category.get_name(s.Language.UK),
            description_en=category.get_description(s.Language.EN),
            description_uk=category.get_description(s.Language.UK),
            criteria=[
                s.VisualProfileFieldWithUUID(
                    uuid=criterion.uuid,
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
        for category in sorted(categories, key=lambda x: x.id)
    ]

    items = s.VisualProfileFormOut(
        impact=s.VisualProfileFieldWithUUID(
            uuid=impact.uuid,
            key=impact.key,
            name_en=impact.get_name(s.Language.EN),
            name_uk=impact.get_name(s.Language.UK),
            description_en=impact.get_description(s.Language.EN),
            description_uk=impact.get_description(s.Language.UK),
        ),
        categories=categories_out,
    )

    return items
