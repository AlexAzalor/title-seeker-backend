import sqlalchemy as sa

# from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from api.routes.people import TOP_PEOPLE_LIMIT
from app import models as m
from app import schema as s
from fastapi import status

# from app import schema as s
from config import config

CFG = config()


def test_actors(client: TestClient, db: Session, auth_user_owner: m.User):
    actors = db.scalars(sa.select(m.Actor)).all()
    assert actors

    form_data = s.PersonForm(
        key="test_actor",
        first_name_uk="Тестовий",
        last_name_uk="Актор",
        first_name_en="Test",
        last_name_en="Actor",
        born="01.01.1990",
        died=None,
        born_in_uk="США",
        born_in_en="US",
    )

    actor_name = "1_Morgan Freeman.png"
    actor_path = f"{CFG.TEST_DATA_PATH}{actor_name}"

    with open(actor_path, "rb") as image:
        response = client.post(
            "/api/people/actors/",
            data={"form_data": form_data.model_dump_json()},
            files={"file": (actor_name, image, "image/png")},
            params={"user_uuid": auth_user_owner.uuid},
        )
    assert response.status_code == status.HTTP_201_CREATED
    data = s.PersonBase.model_validate(response.json())
    assert data
    assert data.key == form_data.key

    # Test create actor with existing key (should fail)
    with open(actor_path, "rb") as image:
        response = client.post(
            "/api/people/actors/",
            data={"form_data": form_data.model_dump_json()},
            files={"file": (actor_name, image, "image/png")},
            params={"user_uuid": auth_user_owner.uuid},
        )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Test get actors with most movies
    response = client.get("/api/people/actors-with-most-movies/")
    assert response.status_code == status.HTTP_200_OK
    top_actors = s.PeopleList.model_validate(response.json())
    assert top_actors
    assert len(top_actors.people) == TOP_PEOPLE_LIMIT


def test_characters(client: TestClient, db: Session, auth_user_owner: m.User):
    characters = db.scalars(sa.select(m.Character)).all()
    assert characters

    form_data = s.CharacterFormIn(
        key="test_character",
        name_en="Test Character",
        name_uk="Тестовий Персонаж",
    )

    response = client.post(
        "/api/people/characters/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = s.CharacterOut.model_validate(response.json())
    assert data
    assert data.key == form_data.key


def test_directors(client: TestClient, db: Session, auth_user_owner: m.User):
    directors = db.scalars(sa.select(m.Director)).all()
    assert directors

    form_data = s.PersonForm(
        key="test_director",
        first_name_uk="Тестовий",
        last_name_uk="Режисер",
        first_name_en="Test",
        last_name_en="Director",
        born="01.01.1990",
        died=None,
        born_in_uk="США",
        born_in_en="US",
    )

    director_name = "1_Frank Darabont.png"
    director_path = f"{CFG.TEST_DATA_PATH}{director_name}"

    with open(director_path, "rb") as image:
        response = client.post(
            "/api/people/directors/",
            data={"form_data": form_data.model_dump_json()},
            files={"file": (director_name, image, "image/png")},
            params={"user_uuid": auth_user_owner.uuid},
        )
    assert response.status_code == status.HTTP_201_CREATED
    data = s.PersonBase.model_validate(response.json())
    assert data
    assert data.key == form_data.key

    # Test create director with existing key (should fail)
    with open(director_path, "rb") as image:
        response = client.post(
            "/api/people/directors/",
            data={"form_data": form_data.model_dump_json()},
            files={"file": (director_name, image, "image/png")},
            params={"user_uuid": auth_user_owner.uuid},
        )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Test get directors with most movies
    response = client.get("/api/people/directors-with-most-movies/")
    assert response.status_code == status.HTTP_200_OK
    top_directors = s.PeopleList.model_validate(response.json())
    assert top_directors
    assert len(top_directors.people) == TOP_PEOPLE_LIMIT


def test_search_actors(client: TestClient, db: Session):
    actor = db.scalar(sa.select(m.Actor))
    assert actor

    response = client.get("/api/people/search-actors/", params={"query": actor.full_name(s.Language.EN)})
    assert response.status_code == status.HTTP_200_OK
    data = s.SearchResults.model_validate(response.json())
    assert data
    assert len(data.results) > 0
    assert data.results[0].key == actor.key


def test_search_directors(client: TestClient, db: Session):
    director = db.scalar(sa.select(m.Director))
    assert director

    response = client.get("/api/people/search-directors/", params={"query": director.full_name(s.Language.EN)})
    assert response.status_code == status.HTTP_200_OK
    data = s.SearchResults.model_validate(response.json())
    assert data
    assert len(data.results) > 0
    assert data.results[0].key == director.key


def test_search_characters(client: TestClient, db: Session):
    character = db.scalar(sa.select(m.Character))
    assert character

    response = client.get("/api/people/search-characters/", params={"query": character.get_name(s.Language.EN)})
    assert response.status_code == status.HTTP_200_OK
    data = s.SearchResults.model_validate(response.json())
    assert data
    assert len(data.results) > 0
    assert data.results[0].key == character.key
