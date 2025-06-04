import sqlalchemy as sa

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m
from app import schema as s

from config import config

CFG = config()


def test_get_genres(client: TestClient, db: Session, auth_user_owner: m.User):
    genres = db.scalars(sa.select(m.Genre)).all()
    assert genres

    response = client.get(
        "/api/genres/",
        params={
            "user_uuid": auth_user_owner.uuid,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.FilterList.model_validate(response.json())
    assert data
    assert data.items


def test_get_subgenres(client: TestClient, db: Session, auth_user_owner: m.User):
    subgenres = db.scalars(sa.select(m.Subgenre)).all()
    assert subgenres

    response = client.get(
        "/api/genres/subgenres/",
        params={
            "user_uuid": auth_user_owner.uuid,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.FilterList.model_validate(response.json())
    assert data
    assert data.items


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

    # Test update genre item
    genre = db.scalar(sa.select(m.Genre).where(m.Genre.key == NEW_GENRE_KEY))
    assert genre

    update_form_data = s.GenreFormFieldsWithUUID(
        uuid=genre.uuid,
        key=NEW_GENRE_KEY + "-2",
        name_uk="Тестовий жанр 2",
        name_en="Test genre 2",
        description_uk="Тестовий опис жанру 2",
        description_en="Test genre description 2",
    )
    response = client.put(
        "/api/genres/",
        json=update_form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid, "type": s.FilterEnum.GENRE.value},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert genre.key == update_form_data.key

    # Test get genre fields for form
    response = client.get(
        "/api/genres/form-fields/",
        params={
            "user_uuid": auth_user_owner.uuid,
            "item_key": genre.key,
            "type": s.FilterEnum.GENRE.value,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    form_data_out = s.GenreFormFieldsWithUUID.model_validate(response.json())
    assert form_data_out
    assert form_data_out.key == genre.key


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
