import sqlalchemy as sa

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m
from app import schema as s

from config import config

CFG = config()


def test_get_visual_profiles(client: TestClient, db: Session, auth_user_owner: m.User):
    NEW_CATEGORY_KEY = "test_visual_profile_category"

    visual_profiles = db.scalars(sa.select(m.TitleVisualProfile)).all()
    assert visual_profiles

    response = client.get(
        "/api/visual-profile/categories/",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.VisualProfileListOut.model_validate(response.json())
    assert data
    assert data.items

    # Create a new category
    form_data = s.CategoryFormIn(
        key=NEW_CATEGORY_KEY,
        name_uk="Тестова категорія",
        name_en="Test category",
        description_uk="Тестовий опис категорії",
        description_en="Test category description",
    )

    response = client.post(
        "/api/visual-profile/category/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_201_CREATED
    new_data = s.CategoryFormOut.model_validate(response.json())
    assert new_data
    assert new_data.key == NEW_CATEGORY_KEY

    # Update the category
    new_form_data = s.EditCategoryFormIn(
        old_key=NEW_CATEGORY_KEY,
        key=NEW_CATEGORY_KEY + "2",
        name_uk="Тестовий категорія 2",
        name_en="Test category 2",
        description_uk="Тестовий опис категорії 2",
        description_en="Test category description 2",
    )

    response = client.put(
        "/api/visual-profile/category/",
        json=new_form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    updated_category = db.scalar(sa.select(m.TitleCategory).where(m.TitleCategory.key == new_form_data.key))
    assert updated_category

    # Check old key is not present
    old_category = db.scalar(sa.select(m.TitleCategory).where(m.TitleCategory.key == NEW_CATEGORY_KEY))
    assert not old_category


def test_get_criteria(client: TestClient, db: Session, auth_user_owner: m.User):
    NEW_CRITERION_KEY = "test_visual_profile_criterion"

    criteria = db.scalars(sa.select(m.TitleCriterion)).all()
    assert criteria

    response = client.get(
        "/api/visual-profile/criteria/",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.CriterionFormList.model_validate(response.json())
    assert data
    assert data.criteria

    # Test creating a new criterion
    form_data = s.CategoryFormIn(
        key=NEW_CRITERION_KEY,
        name_uk="Тестовий критерій",
        name_en="Test criterion",
        description_uk="Тестовий опис критерію",
        description_en="Test criterion description",
    )

    response = client.post(
        "/api/visual-profile/criterion/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_data = s.CategoryFormOut.model_validate(response.json())
    assert created_data
    assert created_data.key == NEW_CRITERION_KEY

    # Update the criterion
    new_form_data = s.EditCategoryFormIn(
        old_key=NEW_CRITERION_KEY,
        key=NEW_CRITERION_KEY + "2",
        name_uk="Тестовий критерій 2",
        name_en="Test criterion 2",
        description_uk="Тестовий опис критерію 2",
        description_en="Test criterion description 2",
    )

    response = client.put(
        "/api/visual-profile/criterion/",
        json=new_form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    updated_criterion = db.scalar(sa.select(m.TitleCriterion).where(m.TitleCriterion.key == new_form_data.key))
    assert updated_criterion

    # Check old key is not present
    old_criterion = db.scalar(sa.select(m.TitleCriterion).where(m.TitleCriterion.key == NEW_CRITERION_KEY))
    assert not old_criterion


def test_get_visual_profile_forms(client: TestClient, db: Session, auth_user_owner: m.User):
    category = db.scalars(sa.select(m.TitleCategory)).all()
    assert category

    impact = db.scalar(sa.select(m.TitleCriterion).where(m.TitleCriterion.key == CFG.UNIQUE_CRITERION_KEY))
    assert impact

    response = client.get(
        "/api/visual-profile/forms/",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.VisualProfileFormOut.model_validate(response.json())
    assert data
    assert data.impact
    assert data.impact.key == CFG.UNIQUE_CRITERION_KEY
    assert data.categories
