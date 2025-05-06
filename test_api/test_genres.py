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
def test_create_genre(client: TestClient, db: Session, auth_user_owner: m.User):
    genres = db.scalars(sa.select(m.Genre)).all()
    assert genres

    NEW_GENRE_KEY = "test_genre"

    genre = db.scalar(sa.select(m.Genre).where(m.Genre.key == NEW_GENRE_KEY))
    assert not genre

    form_data = s.GenreFormIn(
        key=NEW_GENRE_KEY,
        name_uk="Тестовий жанр",
        name_en="Test genre",
        description_uk="Тестовий опис жанру",
        description_en="Test genre description",
    )

    response = client.post(
        "/api/genres/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = s.GenreFormOut.model_validate(response.json())
    assert data
    assert data.key == NEW_GENRE_KEY


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_create_subgenre(client: TestClient, db: Session, auth_user_owner: m.User):
    subgenres = db.scalars(sa.select(m.Genre)).all()
    assert subgenres

    NEW_SUBGENRE_KEY = "test_subgenre"
    GENRE_KEY = "action"

    genre = db.scalar(sa.select(m.Genre).where(m.Genre.key == GENRE_KEY))
    assert genre

    form_data = s.GenreFormIn(
        key=NEW_SUBGENRE_KEY,
        name_uk="Тестовий сабжанр",
        name_en="Test subgenre",
        description_uk="Тестовий опис сабжанру",
        description_en="Test subgenre description",
        parent_genre_key=GENRE_KEY,
    )

    response = client.post(
        "/api/genres/subgenres/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = s.GenreFormOut.model_validate(response.json())
    assert data
    assert data.key == NEW_SUBGENRE_KEY
