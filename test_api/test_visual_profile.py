import sqlalchemy as sa

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m
from app import schema as s

from config import config

CFG = config()


def test_get_visual_profiles(client: TestClient, db: Session, auth_user_owner: m.User):
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


def test_create_category(client: TestClient, db: Session, auth_user_owner: m.User):
    NEW_CATEGORY_KEY = "test_visual_profile_category"

    category = db.scalar(sa.select(m.TitleCategory).where(m.TitleCategory.key == NEW_CATEGORY_KEY))
    assert not category

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
    data = s.CategoryFormOut.model_validate(response.json())
    assert data
    assert data.key == NEW_CATEGORY_KEY
