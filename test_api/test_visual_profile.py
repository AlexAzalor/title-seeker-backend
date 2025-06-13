import sqlalchemy as sa

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m
from app import schema as s

from config import config

CFG = config()


def test_visual_profile_categories(client: TestClient, db: Session, auth_user_owner: m.User, auth_simple_user: m.User):
    NEW_CATEGORY_KEY = "test_visual_profile_category"
    NEW_CRITERION_KEY = "test_visual_profile_criterion"

    visual_profiles = db.scalars(sa.select(m.VisualProfile)).all()
    assert visual_profiles

    response = client.get(
        "/api/visual-profile/",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.VisualProfileListOut.model_validate(response.json())
    assert data
    assert data.items

    # Create a new category with a new criterion
    form_data = s.VisualProfileFormIn(
        key=NEW_CATEGORY_KEY,
        name_uk="Тестова категорія",
        name_en="Test category",
        description_uk="Тестовий опис категорії",
        description_en="Test category description",
        criteria=[
            s.VisualProfileField(
                key=NEW_CRITERION_KEY,
                name_uk="Тестовий критерій",
                name_en="Test criterion",
                description_uk="Тестовий опис критерію",
                description_en="Test criterion description",
            )
        ],
    )

    response = client.post(
        "/api/visual-profile/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_201_CREATED
    new_category = db.scalar(sa.select(m.VisualProfileCategory).where(m.VisualProfileCategory.key == NEW_CATEGORY_KEY))
    assert new_category
    assert new_category.key == NEW_CATEGORY_KEY
    assert new_category.criteria
    # Check that the new criterion is created with the universal one - impact criterion
    assert [c.key for c in new_category.criteria] == [CFG.UNIQUE_CRITERION_KEY, NEW_CRITERION_KEY]

    # Test post with a simple user - should fail
    response = client.post(
        "/api/visual-profile/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_simple_user.uuid},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Update the category
    new_form_data = s.VisualProfileFieldWithUUID(
        uuid=new_category.uuid,
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
    updated_category = db.scalar(
        sa.select(m.VisualProfileCategory).where(m.VisualProfileCategory.key == new_form_data.key)
    )
    assert updated_category

    # Check old key is not present
    old_category = db.scalar(sa.select(m.VisualProfileCategory).where(m.VisualProfileCategory.key == NEW_CATEGORY_KEY))
    assert not old_category

    # Test update with a simple user - should fail
    response = client.put(
        "/api/visual-profile/category/",
        json=new_form_data.model_dump(),
        params={"user_uuid": auth_simple_user.uuid},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_visual_profile_forms(client: TestClient, db: Session, auth_user_owner: m.User, auth_simple_user: m.User):
    category = db.scalars(sa.select(m.VisualProfileCategory)).all()
    assert category

    impact = db.scalar(
        sa.select(m.VisualProfileCategoryCriterion).where(
            m.VisualProfileCategoryCriterion.key == CFG.UNIQUE_CRITERION_KEY
        )
    )
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

    # Test with a simple user - should fail
    response = client.get(
        "/api/visual-profile/forms/",
        params={"user_uuid": auth_simple_user.uuid},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
