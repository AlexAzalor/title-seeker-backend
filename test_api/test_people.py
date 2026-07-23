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


def test_get_actors(client: TestClient, db: Session):
    actors = db.scalars(sa.select(m.Actor)).all()
    assert actors

    response = client.get("/api/people/actors")
    assert response.status_code == status.HTTP_200_OK

    data = s.PeopleListOut.model_validate(response.json())
    assert data.people
    assert any(person.key == actors[0].key for person in data.people)


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


def test_get_actor(client: TestClient, db: Session):
    actor = db.scalar(sa.select(m.Actor))
    assert actor

    uk_translation = next((t for t in actor.translations if t.language == s.Language.UK.value), None)
    en_translation = next((t for t in actor.translations if t.language == s.Language.EN.value), None)
    assert uk_translation
    assert en_translation

    response = client.get(f"/api/people/actor/{actor.id}")
    assert response.status_code == status.HTTP_200_OK

    data = s.PersonFormWithID.model_validate(response.json())
    assert data.id == actor.id
    assert data.key == actor.key
    assert data.first_name_uk == uk_translation.first_name
    assert data.first_name_en == en_translation.first_name


def test_edit_actor(client: TestClient, db: Session, auth_user_owner: m.User, auth_simple_user: m.User):
    actor = db.scalar(sa.select(m.Actor))
    assert actor

    uk_translation = next((t for t in actor.translations if t.language == s.Language.UK.value), None)
    en_translation = next((t for t in actor.translations if t.language == s.Language.EN.value), None)
    assert uk_translation
    assert en_translation

    form_data = s.PersonFormWithID(
        id=actor.id,
        key=actor.key,
        first_name_uk=f"{uk_translation.first_name}_updated",
        last_name_uk=uk_translation.last_name,
        first_name_en=f"{en_translation.first_name}_updated",
        last_name_en=en_translation.last_name,
        born=actor.born,
        died=actor.died,
        born_in_uk=uk_translation.born_in,
        born_in_en=en_translation.born_in,
    )

    response = client.put(
        "/api/people/actor/",
        json=form_data.model_dump(mode="json"),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_200_OK

    db.refresh(actor)
    assert actor.key == form_data.key

    updated_uk_translation = next((t for t in actor.translations if t.language == s.Language.UK.value), None)
    updated_en_translation = next((t for t in actor.translations if t.language == s.Language.EN.value), None)
    assert updated_uk_translation
    assert updated_en_translation
    assert updated_uk_translation.first_name == form_data.first_name_uk
    assert updated_en_translation.first_name == form_data.first_name_en

    # Test with simple user - should fail
    response = client.put(
        "/api/people/actor/",
        json=form_data.model_dump(mode="json"),
        params={"user_uuid": auth_simple_user.uuid},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_actor(client: TestClient, db: Session, auth_user_owner: m.User, auth_simple_user: m.User):
    bound_actor = db.scalar(sa.select(m.Actor).join(m.Actor.movies))
    assert bound_actor

    response = client.delete(
        f"/api/people/actor/{bound_actor.key}",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    detail = response.json()["detail"]
    assert "movies" in detail
    assert "characters" in detail
    assert isinstance(detail["movies"], list)
    assert isinstance(detail["characters"], list)

    deletable_actor_key = "delete-test-actor"
    deletable_actor = m.Actor(
        key=deletable_actor_key,
        born=bound_actor.born,
        died=None,
        translations=[
            m.ActorTranslation(
                language=s.Language.UK.value,
                first_name="Delete",
                last_name="ActorUK",
                born_in="UA",
            ),
            m.ActorTranslation(
                language=s.Language.EN.value,
                first_name="Delete",
                last_name="ActorEN",
                born_in="US",
            ),
        ],
    )
    db.add(deletable_actor)
    db.commit()

    response = client.delete(
        f"/api/people/actor/{deletable_actor_key}",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    deleted_actor = db.scalar(sa.select(m.Actor).where(m.Actor.key == deletable_actor_key))
    assert deleted_actor is None

    response = client.delete(
        f"/api/people/actor/{bound_actor.key}",
        params={"user_uuid": auth_simple_user.uuid},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_directors(client: TestClient, db: Session):
    directors = db.scalars(sa.select(m.Director)).all()
    assert directors

    response = client.get("/api/people/directors")
    assert response.status_code == status.HTTP_200_OK

    data = s.PeopleListOut.model_validate(response.json())
    assert data.people
    assert any(person.key == directors[0].key for person in data.people)


def test_get_director(client: TestClient, db: Session):
    director = db.scalar(sa.select(m.Director))
    assert director

    uk_translation = next((t for t in director.translations if t.language == s.Language.UK.value), None)
    en_translation = next((t for t in director.translations if t.language == s.Language.EN.value), None)
    assert uk_translation
    assert en_translation

    response = client.get(f"/api/people/director/{director.id}")
    assert response.status_code == status.HTTP_200_OK

    data = s.PersonFormWithID.model_validate(response.json())
    assert data.id == director.id
    assert data.key == director.key
    assert data.first_name_uk == uk_translation.first_name
    assert data.first_name_en == en_translation.first_name


def test_edit_director(client: TestClient, db: Session, auth_user_owner: m.User, auth_simple_user: m.User):
    director = db.scalar(sa.select(m.Director))
    assert director

    uk_translation = next((t for t in director.translations if t.language == s.Language.UK.value), None)
    en_translation = next((t for t in director.translations if t.language == s.Language.EN.value), None)
    assert uk_translation
    assert en_translation

    form_data = s.PersonFormWithID(
        id=director.id,
        key=director.key,
        first_name_uk=f"{uk_translation.first_name}_updated",
        last_name_uk=uk_translation.last_name,
        first_name_en=f"{en_translation.first_name}_updated",
        last_name_en=en_translation.last_name,
        born=director.born,
        died=director.died,
        born_in_uk=uk_translation.born_in,
        born_in_en=en_translation.born_in,
    )

    response = client.put(
        "/api/people/director/",
        json=form_data.model_dump(mode="json"),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_200_OK

    db.refresh(director)
    updated_uk_translation = next((t for t in director.translations if t.language == s.Language.UK.value), None)
    updated_en_translation = next((t for t in director.translations if t.language == s.Language.EN.value), None)
    assert updated_uk_translation
    assert updated_en_translation
    assert director.key == form_data.key
    assert updated_uk_translation.first_name == form_data.first_name_uk
    assert updated_en_translation.first_name == form_data.first_name_en

    response = client.put(
        "/api/people/director/",
        json=form_data.model_dump(mode="json"),
        params={"user_uuid": auth_simple_user.uuid},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_director(client: TestClient, db: Session, auth_user_owner: m.User, auth_simple_user: m.User):
    bound_director = db.scalar(sa.select(m.Director).join(m.Director.movies))
    assert bound_director

    response = client.delete(
        f"/api/people/director/{bound_director.key}",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    detail = response.json()["detail"]
    assert "movies" in detail
    assert isinstance(detail["movies"], list)

    deletable_director_key = "delete-test-director"
    deletable_director = m.Director(
        key=deletable_director_key,
        born=bound_director.born,
        died=None,
        translations=[
            m.DirectorTranslation(
                language=s.Language.UK.value,
                first_name="Delete",
                last_name="DirectorUK",
                born_in="UA",
            ),
            m.DirectorTranslation(
                language=s.Language.EN.value,
                first_name="Delete",
                last_name="DirectorEN",
                born_in="US",
            ),
        ],
    )
    db.add(deletable_director)
    db.commit()

    response = client.delete(
        f"/api/people/director/{deletable_director_key}",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    deleted_director = db.scalar(sa.select(m.Director).where(m.Director.key == deletable_director_key))
    assert deleted_director is None

    response = client.delete(
        f"/api/people/director/{bound_director.key}",
        params={"user_uuid": auth_simple_user.uuid},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_characters(client: TestClient, db: Session):
    characters = db.scalars(sa.select(m.Character)).all()
    assert characters

    response = client.get("/api/people/characters")
    assert response.status_code == status.HTTP_200_OK

    data = s.PeopleListOut.model_validate(response.json())
    assert data.people
    assert any(person.key == characters[0].key for person in data.people)


def test_get_character(client: TestClient, db: Session):
    character = db.scalar(sa.select(m.Character))
    assert character

    uk_translation = next((t for t in character.translations if t.language == s.Language.UK.value), None)
    en_translation = next((t for t in character.translations if t.language == s.Language.EN.value), None)
    assert uk_translation
    assert en_translation

    response = client.get(f"/api/people/character/{character.id}")
    assert response.status_code == status.HTTP_200_OK

    data = s.CharacterFormFieldsOut.model_validate(response.json())
    assert data.id == character.id
    assert data.key == character.key
    assert data.name_uk == uk_translation.name
    assert data.name_en == en_translation.name


def test_edit_character(client: TestClient, db: Session, auth_user_owner: m.User, auth_simple_user: m.User):
    character = db.scalar(sa.select(m.Character))
    assert character

    uk_translation = next((t for t in character.translations if t.language == s.Language.UK.value), None)
    en_translation = next((t for t in character.translations if t.language == s.Language.EN.value), None)
    assert uk_translation
    assert en_translation

    form_data = s.CharacterFormPutIn(
        id=character.id,
        key=character.key,
        name_en=f"{en_translation.name} Updated",
        name_uk=f"{uk_translation.name} Оновлено",
    )

    response = client.put(
        "/api/people/character/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_200_OK

    db.refresh(character)
    updated_uk_translation = next((t for t in character.translations if t.language == s.Language.UK.value), None)
    updated_en_translation = next((t for t in character.translations if t.language == s.Language.EN.value), None)
    assert updated_uk_translation
    assert updated_en_translation
    assert character.key == form_data.key
    assert updated_uk_translation.name == form_data.name_uk
    assert updated_en_translation.name == form_data.name_en

    response = client.put(
        "/api/people/character/",
        json=form_data.model_dump(),
        params={"user_uuid": auth_simple_user.uuid},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


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


def test_delete_character(client: TestClient, db: Session, auth_user_owner: m.User, auth_simple_user: m.User):
    bound_character = db.scalar(sa.select(m.Character).join(m.Character.characters))
    assert bound_character

    response = client.delete(
        f"/api/people/character/{bound_character.key}",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    detail = response.json()["detail"]
    assert "movies" in detail
    assert "actors" in detail
    assert isinstance(detail["movies"], list)
    assert isinstance(detail["actors"], list)

    deletable_character_key = "delete-test-character"
    deletable_character = m.Character(
        key=deletable_character_key,
        translations=[
            m.CharacterTranslation(language=s.Language.UK.value, name="Delete Character UK"),
            m.CharacterTranslation(language=s.Language.EN.value, name="Delete Character EN"),
        ],
    )
    db.add(deletable_character)
    db.commit()

    response = client.delete(
        f"/api/people/character/{deletable_character_key}",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    deleted_character = db.scalar(sa.select(m.Character).where(m.Character.key == deletable_character_key))
    assert deleted_character is None

    response = client.delete(
        f"/api/people/character/{bound_character.key}",
        params={"user_uuid": auth_simple_user.uuid},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


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
