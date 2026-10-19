import sqlalchemy as sa

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m
from app import schema as s

from config import config

CFG = config()


def assert_filter_audit(db: Session, movie: m.Movie, event_type: str, field: str, new_key: str, pm: float):
    db.expire_all()
    audit = db.scalar(
        sa.select(m.AuditLog)
        .where(m.AuditLog.entity_id == movie.id, m.AuditLog.event_type == event_type)
        .order_by(m.AuditLog.id.desc())
    )
    assert audit
    entry = next(e for e in audit.changes[field]["new"] if e["key"] == new_key)
    assert entry["percentage_match"] == pm
    assert {"en", "uk"} <= set(entry["name"])


def test_get_specifications(client: TestClient, db: Session, auth_user_owner: m.User):
    specifications = db.scalars(sa.select(m.Specification)).all()
    assert specifications

    response = client.get(
        "/api/filters/specifications/",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.FilterList.model_validate(response.json())
    assert data
    assert data.items


def test_get_keywords(client: TestClient, db: Session, auth_user_owner: m.User):
    keywords = db.scalars(sa.select(m.Keyword)).all()
    assert keywords

    response = client.get(
        "/api/filters/keywords/",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.FilterList.model_validate(response.json())
    assert data
    assert data.items


def test_get_action_times(client: TestClient, db: Session, auth_user_owner: m.User):
    action_times = db.scalars(sa.select(m.ActionTime)).all()
    assert action_times

    response = client.get(
        "/api/filters/action-times/",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.FilterList.model_validate(response.json())
    assert data
    assert data.items


def test_create_specification(client: TestClient, db: Session, auth_user_owner: m.User, auth_simple_user: m.User):
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
    data = s.FilterItemOut.model_validate(response.json())
    assert data
    assert data.key == NEW_SPEC_KEY

    # # Test update specifications (on movie page)
    movie = db.scalar(sa.select(m.Movie))
    assert movie
    assert not [s for spec in movie.specifications if spec.key == NEW_SPEC_KEY]

    add_form_data = s.FilterFormIn(
        movie_key=movie.key,
        items=[
            s.FilterItemField(
                key=NEW_SPEC_KEY,
                name="Test specification",
                percentage_match=70.0,
            ),
            s.FilterItemField(
                key="philosophical",
                name="Philosophical",
                percentage_match=40.0,
            ),
        ],
    )

    response = client.put(
        "/api/movies/specifications/",
        json=add_form_data.model_dump(),
        params={
            "user_uuid": auth_user_owner.uuid,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert [s for spec in movie.specifications if spec.key == NEW_SPEC_KEY]
    assert_filter_audit(db, movie, "movie.specifications.updated", "specifications", NEW_SPEC_KEY, 70.0)

    # Test edit specification by simple user
    response = client.put(
        "/api/movies/specifications/",
        json=add_form_data.model_dump(),
        params={
            "user_uuid": auth_simple_user.uuid,
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test update specification with existing key
    specification = db.scalar(sa.select(m.Specification).where(m.Specification.key == NEW_SPEC_KEY))
    assert specification

    update_form_data = s.FilterFieldsWithUUID(
        uuid=specification.uuid,
        key="new-test-specification-2",
        name_uk="Тестовий специфікація 2",
        name_en="Test specification 2",
        description_uk="Тестовий опис специфікації 2",
        description_en="Test specification description 2",
    )
    response = client.put(
        "/api/filters/",
        json=update_form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid, "type": s.FilterEnum.SPECIFICATION.value},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert specification.key == update_form_data.key

    # Test get filters fields for form
    response = client.get(
        "/api/filters/form-fields/",
        params={
            "user_uuid": auth_user_owner.uuid,
            "item_key": specification.key,
            "type": s.FilterEnum.SPECIFICATION.value,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    form_data_out = s.FilterFieldsWithUUID.model_validate(response.json())
    assert form_data_out
    assert form_data_out.key == specification.key


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
    data = s.FilterItemOut.model_validate(response.json())
    assert data
    assert data.key == NEW_KEYWORD_KEY

    # Test update keyword for movie
    movie = db.scalar(sa.select(m.Movie))
    assert movie
    assert not [s for keyword in movie.keywords if keyword.key == NEW_KEYWORD_KEY]

    add_form_data = s.FilterFormIn(
        movie_key=movie.key,
        items=[
            s.FilterItemField(
                key=NEW_KEYWORD_KEY,
                name="Test keyword",
                percentage_match=70.0,
            ),
            s.FilterItemField(
                key="cool-antagonist",
                name="Cool Antagonist",
                percentage_match=40.0,
            ),
        ],
    )

    response = client.put(
        "/api/movies/keywords/",
        json=add_form_data.model_dump(),
        params={
            "user_uuid": auth_user_owner.uuid,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert [s for keyword in movie.keywords if keyword.key == NEW_KEYWORD_KEY]
    assert_filter_audit(db, movie, "movie.keywords.updated", "keywords", NEW_KEYWORD_KEY, 70.0)


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
    data = s.FilterItemOut.model_validate(response.json())
    assert data
    assert data.key == NEW_AT_KEY

    # Test update action_time for movie
    movie = db.scalar(sa.select(m.Movie))
    assert movie
    assert not [s for at in movie.action_times if at.key == NEW_AT_KEY]

    add_form_data = s.FilterFormIn(
        movie_key=movie.key,
        items=[
            s.FilterItemField(
                key=NEW_AT_KEY,
                name="Test action_time",
                percentage_match=70.0,
            ),
            s.FilterItemField(
                key="21st-century",
                name="21st Century",
                percentage_match=40.0,
            ),
        ],
    )

    response = client.put(
        "/api/movies/action-times/",
        json=add_form_data.model_dump(),
        params={
            "user_uuid": auth_user_owner.uuid,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert [s for at in movie.action_times if at.key == NEW_AT_KEY]
    assert_filter_audit(db, movie, "movie.action_times.updated", "action_times", NEW_AT_KEY, 70.0)
