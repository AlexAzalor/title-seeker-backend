import sqlalchemy as sa

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m
from app import schema as s

from config import config

CFG = config()


def test_create_shared_universe(client: TestClient, db: Session, auth_user_owner: m.User):
    shared_universes = db.scalars(sa.select(m.SharedUniverse)).all()
    assert shared_universes

    NEW_SU_KEY = "test_shared_universe"

    shared_universe = db.scalar(sa.select(m.SharedUniverse).where(m.SharedUniverse.key == NEW_SU_KEY))
    assert not shared_universe

    form_data = s.GenreFormIn(
        key=NEW_SU_KEY,
        name_uk="Тестовий спільний всесвіт",
        name_en="Test shared universe",
        description_uk="Тестовий опис спільного всесвіту",
        description_en="Test shared universe description",
    )

    response = client.post(
        "/api/shared-universes/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = s.BaseSharedUniverse.model_validate(response.json())
    assert data
    assert data.key == NEW_SU_KEY
