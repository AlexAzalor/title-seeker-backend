import pytest

import sqlalchemy as sa

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m
from app import schema as s

from config import config

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_create_specification(client: TestClient, db: Session, auth_user_owner: m.User):
    NEW_SPEC_KEY = "test_specification"

    specification = db.scalar(sa.select(m.Specification).where(m.Specification.key == NEW_SPEC_KEY))
    assert not specification

    form_data = s.MovieFilterFormIn(
        key=NEW_SPEC_KEY,
        name_uk="Тестовий специфікація",
        name_en="Test specification",
        description_uk="Тестовий опис специфікації",
        description_en="Test specification description",
    )

    response = client.post(
        "/api/filters/specifications/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = s.MovieFilterFormOut.model_validate(response.json())
    assert data
    assert data.key == NEW_SPEC_KEY


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_create_keyword(client: TestClient, db: Session, auth_user_owner: m.User):
    NEW_KEYWORD_KEY = "test_keyword"

    keyword = db.scalar(sa.select(m.Keyword).where(m.Keyword.key == NEW_KEYWORD_KEY))
    assert not keyword

    form_data = s.MovieFilterFormIn(
        key=NEW_KEYWORD_KEY,
        name_uk="Тестове ключове слово",
        name_en="Test keyword",
        description_uk="Тестовий опис ключового слова",
        description_en="Test keyword description",
    )

    response = client.post(
        "/api/filters/keywords/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = s.MovieFilterFormOut.model_validate(response.json())
    assert data
    assert data.key == NEW_KEYWORD_KEY


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_create_action_time(client: TestClient, db: Session, auth_user_owner: m.User):
    NEW_AT_KEY = "test_action_time"

    action_time = db.scalar(sa.select(m.ActionTime).where(m.ActionTime.key == NEW_AT_KEY))
    assert not action_time

    form_data = s.MovieFilterFormIn(
        key=NEW_AT_KEY,
        name_uk="Тест час події",
        name_en="Test action_time",
        description_uk="Тестовий опис часу події",
        description_en="Test action_time description",
    )

    response = client.post(
        "/api/filters/action-times/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = s.MovieFilterFormOut.model_validate(response.json())
    assert data
    assert data.key == NEW_AT_KEY
