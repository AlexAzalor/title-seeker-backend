from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Body, File, HTTPException, Depends, Query, UploadFile, status
from api.controllers.movie_filters import get_people_filters
from api.controllers.people import add_avatar_to_new_actor, add_avatar_to_new_director
from api.dependency.user import get_admin
from api.utils import normalize_query
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session, selectinload
from app.database import get_db
from config import config

CFG = config()
TOP_PEOPLE_LIMIT = 20

people_router = APIRouter(prefix="/people", tags=["People"])


@people_router.get("/actors", status_code=status.HTTP_200_OK, response_model=s.PeopleListOut)
def get_actors(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get list of actors"""

    actors_out, _, _ = get_people_filters(db, lang)

    return s.PeopleListOut(people=actors_out)


@people_router.get("/actor/{id}", status_code=status.HTTP_200_OK, response_model=s.PersonFormWithID)
def get_actor(
    id: int,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get actor by ID"""

    actor = db.scalar(sa.select(m.Actor).where(m.Actor.id == id))
    if not actor:
        log(log.ERROR, "Actor [%s] not found", id)
        raise HTTPException(status_code=404, detail="Actor not found")

    uk_translation = next((t for t in actor.translations if t.language == s.Language.UK.value), None)
    en_translation = next((t for t in actor.translations if t.language == s.Language.EN.value), None)

    return s.PersonFormWithID(
        id=actor.id,
        key=actor.key,
        first_name_uk=uk_translation.first_name if uk_translation else "",
        last_name_uk=uk_translation.last_name if uk_translation else "",
        born_in_uk=uk_translation.born_in if uk_translation else "",
        first_name_en=en_translation.first_name if en_translation else "",
        last_name_en=en_translation.last_name if en_translation else "",
        born_in_en=en_translation.born_in if en_translation else "",
        born=actor.born,
        died=actor.died,
    )


@people_router.put(
    "/actor/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Error updating actor"},
        status.HTTP_404_NOT_FOUND: {"description": "Actor not found"},
    },
)
def edit_actor(
    form_data: s.PersonFormWithID,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Edit actor data and translations"""

    actor = db.scalar(sa.select(m.Actor).where(m.Actor.id == form_data.id))
    if not actor:
        log(log.ERROR, "Actor [%s] not found", form_data.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actor not found")

    if form_data.key != actor.key:
        actor_with_same_key = db.scalar(sa.select(m.Actor).where(m.Actor.key == form_data.key))
        if actor_with_same_key:
            log(log.ERROR, "Actor key [%s] already exists", form_data.key)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Actor key already exists")

    uk_translation = next((t for t in actor.translations if t.language == s.Language.UK.value), None)
    en_translation = next((t for t in actor.translations if t.language == s.Language.EN.value), None)

    if not uk_translation:
        uk_translation = m.ActorTranslation(actor_id=actor.id, language=s.Language.UK.value)
        db.add(uk_translation)

    if not en_translation:
        en_translation = m.ActorTranslation(actor_id=actor.id, language=s.Language.EN.value)
        db.add(en_translation)

    try:
        actor.key = form_data.key
        actor.born = form_data.born
        actor.died = form_data.died

        uk_translation.first_name = form_data.first_name_uk
        uk_translation.last_name = form_data.last_name_uk
        uk_translation.born_in = form_data.born_in_uk

        en_translation.first_name = form_data.first_name_en
        en_translation.last_name = form_data.last_name_en
        en_translation.born_in = form_data.born_in_en

        db.commit()
        log(log.INFO, "Actor [%s] successfully updated by user [%s]", actor.key, current_user.email)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error updating actor [%s]: %s", form_data.id, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating actor")


@people_router.post(
    "/actors/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.PersonBase,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Actor already exists"},
        status.HTTP_201_CREATED: {"description": "Actor successfully created"},
    },
)
def create_actor(
    form_data: Annotated[s.PersonForm, Body(...)],
    file: UploadFile = File(),
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new actor"""

    actor = db.scalar(sa.select(m.Actor).where(m.Actor.key == form_data.key))

    if actor:
        log(log.ERROR, "Actor [%s] already exists")
        raise HTTPException(status_code=400, detail="Actor already exists")

    try:
        new_actor = m.Actor(
            key=form_data.key,
            born=datetime.strptime(form_data.born, "%d.%m.%Y"),
            died=datetime.strptime(form_data.died, "%d.%m.%Y") if form_data.died else None,
            translations=[
                m.ActorTranslation(
                    language=s.Language.UK.value,
                    first_name=form_data.first_name_uk,
                    last_name=form_data.last_name_uk,
                    born_in=form_data.born_in_uk,
                ),
                m.ActorTranslation(
                    language=s.Language.EN.value,
                    first_name=form_data.first_name_en,
                    last_name=form_data.last_name_en,
                    born_in=form_data.born_in_en,
                ),
            ],
        )

        db.add(new_actor)
        db.commit()
        log(log.INFO, "Actor [%s] successfully created by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error creating actor [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating actor")

    db.refresh(new_actor)

    add_avatar_to_new_actor(
        actor_key=form_data.key,
        file=file,
        new_actor=new_actor,
        db=db,
    )
    return s.PersonBase(
        key=new_actor.key,
        name=new_actor.full_name(lang),
    )


@people_router.get("/actors-with-most-movies", status_code=status.HTTP_200_OK, response_model=s.PeopleList)
def get_actors_with_most_movies(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get actors with the most movies"""

    # Subquery to count the number of movies for each actor
    subquery = (
        sa.select(m.Actor.id, sa.func.count(m.Movie.id).label("movie_count"))
        .join(m.Movie.actors)
        .group_by(m.Actor.id)
        .subquery()
    )

    # Main query to select actors ordered by the movie count
    actors = db.execute(
        sa.select(m.Actor, subquery.c.movie_count)
        .options(selectinload(m.Actor.translations))
        .join(subquery, m.Actor.id == subquery.c.id)
        .order_by(subquery.c.movie_count.desc())
        .limit(TOP_PEOPLE_LIMIT)
    ).all()
    if not actors:
        log(log.ERROR, "Actors [%s] not found")
        raise HTTPException(status_code=404, detail="Actors not found")

    actors_out = []

    for actor, movie_count in actors:
        actors_out.append(
            s.TopPerson(key=actor.key, name=actor.full_name(lang), avatar_url=actor.avatar, movie_count=movie_count)
        )

    return s.PeopleList(people=actors_out)


@people_router.get("/directors", status_code=status.HTTP_200_OK, response_model=s.PeopleListOut)
def get_directors(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get list of directors"""

    _, directors_out, _ = get_people_filters(db, lang)

    return s.PeopleListOut(people=directors_out)


@people_router.get("/director/{id}", status_code=status.HTTP_200_OK, response_model=s.PersonFormWithID)
def get_director(
    id: int,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get director by ID"""

    director = db.scalar(sa.select(m.Director).where(m.Director.id == id))
    if not director:
        log(log.ERROR, "Director [%s] not found", id)
        raise HTTPException(status_code=404, detail="Director not found")

    uk_translation = next((t for t in director.translations if t.language == s.Language.UK.value), None)
    en_translation = next((t for t in director.translations if t.language == s.Language.EN.value), None)

    return s.PersonFormWithID(
        id=director.id,
        key=director.key,
        first_name_uk=uk_translation.first_name if uk_translation else "",
        last_name_uk=uk_translation.last_name if uk_translation else "",
        born_in_uk=uk_translation.born_in if uk_translation else "",
        first_name_en=en_translation.first_name if en_translation else "",
        last_name_en=en_translation.last_name if en_translation else "",
        born_in_en=en_translation.born_in if en_translation else "",
        born=director.born,
        died=director.died,
    )


@people_router.put(
    "/director/",
    status_code=status.HTTP_200_OK,
    # response_model=s.PersonFormWithID,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Error updating director"},
        status.HTTP_404_NOT_FOUND: {"description": "Director not found"},
    },
)
def edit_director(
    form_data: s.PersonFormWithID,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Edit director data and translations"""

    director = db.scalar(sa.select(m.Director).where(m.Director.id == form_data.id))
    if not director:
        log(log.ERROR, "Director [%s] not found", form_data.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Director not found")

    if form_data.key != director.key:
        director_with_same_key = db.scalar(sa.select(m.Director).where(m.Director.key == form_data.key))
        if director_with_same_key:
            log(log.ERROR, "Director key [%s] already exists", form_data.key)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Director key already exists")

    uk_translation = next((t for t in director.translations if t.language == s.Language.UK.value), None)
    en_translation = next((t for t in director.translations if t.language == s.Language.EN.value), None)

    if not uk_translation:
        uk_translation = m.DirectorTranslation(director_id=director.id, language=s.Language.UK.value)
        db.add(uk_translation)

    if not en_translation:
        en_translation = m.DirectorTranslation(director_id=director.id, language=s.Language.EN.value)
        db.add(en_translation)

    try:
        director.key = form_data.key
        director.born = form_data.born
        director.died = form_data.died

        uk_translation.first_name = form_data.first_name_uk
        uk_translation.last_name = form_data.last_name_uk
        uk_translation.born_in = form_data.born_in_uk

        en_translation.first_name = form_data.first_name_en
        en_translation.last_name = form_data.last_name_en
        en_translation.born_in = form_data.born_in_en

        db.commit()
        log(log.INFO, "Director [%s] successfully updated by user [%s]", director.key, current_user.email)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error updating director [%s]: %s", form_data.id, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating director")


@people_router.get("/directors-with-most-movies", status_code=status.HTTP_200_OK, response_model=s.PeopleList)
def get_directors_with_most_movies(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get directors with the most movies"""

    subquery = (
        sa.select(m.Director.id, sa.func.count(m.Movie.id).label("movie_count"))
        .join(m.Movie.directors)
        .group_by(m.Director.id)
        .subquery()
    )

    directors = db.execute(
        sa.select(m.Director, subquery.c.movie_count)
        .options(selectinload(m.Director.translations))
        .join(subquery, m.Director.id == subquery.c.id)
        .order_by(subquery.c.movie_count.desc())
        .limit(TOP_PEOPLE_LIMIT)
    ).all()
    if not directors:
        log(log.ERROR, "Directors [%s] not found")
        raise HTTPException(status_code=404, detail="Directors not found")

    directors_out = []

    for director, movie_count in directors:
        directors_out.append(
            s.TopPerson(
                key=director.key, name=director.full_name(lang), avatar_url=director.avatar, movie_count=movie_count
            )
        )

    return s.PeopleList(people=directors_out)


@people_router.get("/characters", status_code=status.HTTP_200_OK, response_model=s.PeopleListOut)
def get_characters(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get list of characters"""

    _, _, characters_out = get_people_filters(db, lang)

    return s.PeopleListOut(people=characters_out)


@people_router.get("/character/{id}", status_code=status.HTTP_200_OK, response_model=s.CharacterFormFieldsOut)
def get_character(
    id: int,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get character by ID"""

    character = db.scalar(sa.select(m.Character).where(m.Character.id == id))
    if not character:
        log(log.ERROR, "Character [%s] not found", id)
        raise HTTPException(status_code=404, detail="Character not found")

    uk_translation = next((t for t in character.translations if t.language == s.Language.UK.value), None)
    en_translation = next((t for t in character.translations if t.language == s.Language.EN.value), None)

    return s.CharacterFormFieldsOut(
        id=character.id,
        key=character.key,
        name_en=en_translation.name if en_translation else "",
        name_uk=uk_translation.name if uk_translation else "",
    )


@people_router.put(
    "/character/",
    status_code=status.HTTP_200_OK,
    # response_model=s.PersonFormWithID,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Error updating character"},
        status.HTTP_404_NOT_FOUND: {"description": "Character not found"},
    },
)
def edit_character(
    form_data: s.CharacterFormPutIn,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Edit character data and translations"""

    character = db.scalar(sa.select(m.Character).where(m.Character.id == form_data.id))
    if not character:
        log(log.ERROR, "Character [%s] not found", form_data.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    if form_data.key != character.key:
        char_with_same_key = db.scalar(sa.select(m.Character).where(m.Character.key == form_data.key))
        if char_with_same_key:
            log(log.ERROR, "Character key [%s] already exists", form_data.key)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Character key already exists")

    uk_translation = next((t for t in character.translations if t.language == s.Language.UK.value), None)
    en_translation = next((t for t in character.translations if t.language == s.Language.EN.value), None)

    if not uk_translation:
        uk_translation = m.CharacterTranslation(character_id=character.id, language=s.Language.UK.value)
        db.add(uk_translation)

    if not en_translation:
        en_translation = m.CharacterTranslation(character_id=character.id, language=s.Language.EN.value)
        db.add(en_translation)

    try:
        character.key = form_data.key
        en_translation.name = form_data.name_en
        uk_translation.name = form_data.name_uk

        db.commit()
        log(log.INFO, "Character [%s] successfully updated by user [%s]", character.key, current_user.email)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error updating character [%s]: %s", form_data.id, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating character")


@people_router.post(
    "/characters/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.CharacterOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Character already exists"},
        status.HTTP_201_CREATED: {"description": "Character successfully created"},
    },
)
def create_character(
    form_data: s.CharacterFormIn = Body(...),
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new character"""

    character = db.scalar(sa.select(m.Character).where(m.Character.key == form_data.key))

    if character:
        log(log.ERROR, "Character [%s] already exists")
        raise HTTPException(status_code=400, detail="Character already exists")

    try:
        new_character = m.Character(
            key=form_data.key,
            translations=[
                m.CharacterTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                ),
                m.CharacterTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                ),
            ],
        )

        db.add(new_character)
        db.commit()
        log(log.INFO, "Character [%s] successfully created by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error creating Character [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating character")

    db.refresh(new_character)

    return s.CharacterOut(
        key=new_character.key,
        name=new_character.get_name(lang),
    )


@people_router.post(
    "/directors/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.PersonBase,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Director already exists"},
        status.HTTP_201_CREATED: {"description": "Director successfully created"},
    },
)
def create_director(
    form_data: Annotated[s.PersonForm, Body(...)],
    file: UploadFile = File(),
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Create new director"""

    director = db.scalar(sa.select(m.Director).where(m.Director.key == form_data.key))

    if director:
        log(log.ERROR, "Director [%s] already exists")
        raise HTTPException(status_code=400, detail="Director already exists")

    try:
        new_director = m.Director(
            key=form_data.key,
            born=datetime.strptime(form_data.born, "%d.%m.%Y"),
            died=datetime.strptime(form_data.died, "%d.%m.%Y") if form_data.died else None,
            translations=[
                m.DirectorTranslation(
                    language=s.Language.UK.value,
                    first_name=form_data.first_name_uk,
                    last_name=form_data.last_name_uk,
                    born_in=form_data.born_in_uk,
                ),
                m.DirectorTranslation(
                    language=s.Language.EN.value,
                    first_name=form_data.first_name_en,
                    last_name=form_data.last_name_en,
                    born_in=form_data.born_in_en,
                ),
            ],
        )

        db.add(new_director)
        db.commit()
        log(log.INFO, "Director [%s] successfully created by user [%s]", form_data.key, current_user.email)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error creating director [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating director")

    db.refresh(new_director)

    add_avatar_to_new_director(
        director_key=form_data.key,
        file=file,
        new_director=new_director,
        db=db,
    )

    return s.PersonBase(
        key=new_director.key,
        name=new_director.full_name(lang),
    )


@people_router.get(
    "/search-actors/",
    status_code=status.HTTP_200_OK,
    response_model=s.SearchResults,
    responses={status.HTTP_400_BAD_REQUEST: {"description": "Query is empty"}},
)
def search_actors(
    query: str = Query(default="", max_length=128),
    db: Session = Depends(get_db),
):
    """Search actor by name"""

    if not query:
        log(log.ERROR, "Query is empty")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query is empty")

    normalized_query = normalize_query(query)

    name_search_pattern = (
        sa.func.lower(m.ActorTranslation.first_name) + " " + sa.func.lower(m.ActorTranslation.last_name)
    )

    actors = (
        db.scalars(
            sa.select(m.Actor)
            .where(
                m.Actor.translations.any(
                    sa.func.regexp_replace(name_search_pattern, r"[^a-zA-Zа-яА-Я0-9 ]", "", "g").ilike(
                        f"%{normalized_query}%"
                    )
                )
            )
            .limit(5)
        )
        .unique()
        .all()
    )

    return s.SearchResults(
        results=[
            s.SearchResult(
                key=actor.key,
                name=actor.full_name(s.Language.EN) + f" ({actor.full_name(s.Language.UK)})",
                image=actor.avatar,
                extra_info=f"Movies: {len(actor.movies)}",
                type=s.SearchType.ACTORS,
            )
            for actor in actors
        ]
    )


@people_router.get(
    "/search-directors/",
    status_code=status.HTTP_200_OK,
    response_model=s.SearchResults,
    responses={status.HTTP_400_BAD_REQUEST: {"description": "Query is empty"}},
)
def search_directors(
    query: str = Query(default="", max_length=128),
    db: Session = Depends(get_db),
):
    """Search directors by name"""

    if not query:
        log(log.ERROR, "Query is empty")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query is empty")

    normalized_query = normalize_query(query)

    name_search_pattern = (
        sa.func.lower(m.DirectorTranslation.first_name) + " " + sa.func.lower(m.DirectorTranslation.last_name)
    )

    directors = (
        db.scalars(
            sa.select(m.Director)
            .where(
                m.Director.translations.any(
                    sa.func.regexp_replace(name_search_pattern, r"[^a-zA-Zа-яА-Я0-9 ]", "", "g").ilike(
                        f"%{normalized_query}%"
                    )
                )
            )
            .limit(5)
        )
        .unique()
        .all()
    )

    return s.SearchResults(
        results=[
            s.SearchResult(
                key=director.key,
                name=director.full_name(s.Language.EN) + f" ({director.full_name(s.Language.UK)})",
                image=director.avatar,
                extra_info=f"Movies: {len(director.movies)}",
                type=s.SearchType.DIRECTORS,
            )
            for director in directors
        ]
    )


@people_router.get(
    "/search-characters/",
    status_code=status.HTTP_200_OK,
    response_model=s.SearchResults,
    responses={status.HTTP_400_BAD_REQUEST: {"description": "Query is empty"}},
)
def search_characters(
    query: str = Query(default="", max_length=128),
    db: Session = Depends(get_db),
):
    """Search characters by name"""

    if not query:
        log(log.ERROR, "Query is empty")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query is empty")

    normalized_query = normalize_query(query)

    name_search_pattern = sa.func.lower(m.CharacterTranslation.name)

    characters = (
        db.scalars(
            sa.select(m.Character)
            .where(
                m.Character.translations.any(
                    sa.func.regexp_replace(name_search_pattern, r"[^a-zA-Zа-яА-Я0-9 ]", "", "g").ilike(
                        f"%{normalized_query}%"
                    )
                )
            )
            .limit(5)
        )
        .unique()
        .all()
    )

    return s.SearchResults(
        results=[
            s.SearchResult(
                key=char.key,
                name=char.get_name(s.Language.EN) + f" ({char.get_name(s.Language.UK)})",
                type=s.SearchType.CHARACTERS,
            )
            for char in characters
        ]
    )


@people_router.delete(
    "/actor/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Actor successfully deleted"},
        status.HTTP_400_BAD_REQUEST: {
            "description": "Actor is associated with other entities",
        },
        status.HTTP_404_NOT_FOUND: {"description": "Actor not found"},
    },
)
def delete_actor(
    key: str,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Delete actor if it has no relations with movies/characters"""

    actor = db.scalar(
        sa.select(m.Actor)
        .options(
            selectinload(m.Actor.movies).selectinload(m.Movie.translations),
            selectinload(m.Actor.characters)
            .selectinload(m.MovieActorCharacter.character)
            .selectinload(m.Character.translations),
        )
        .where(m.Actor.key == key)
    )

    if not actor:
        log(log.ERROR, "Actor [%s] not found", key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actor not found")

    if actor.movies or actor.characters:
        movies = [s.MovieMenuItem(key=movie.key, name=movie.get_title(s.Language.EN)) for movie in actor.movies]
        characters = [
            s.MovieMenuItem(key=rel.character.key, name=rel.character.get_name(s.Language.EN))
            for rel in actor.characters
            if rel.character
        ]

        # Keep only unique entries by key for cleaner frontend rendering.
        movies_unique = list({item.key: item for item in movies}.values())
        characters_unique = list({item.key: item for item in characters}.values())

        log(log.ERROR, "Actor [%s] is associated with other entities and cannot be deleted", actor.key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "movies": [item.model_dump() for item in movies_unique],
                "characters": [item.model_dump() for item in characters_unique],
            },
        )

    try:
        db.execute(sa.delete(m.ActorTranslation).where(m.ActorTranslation.actor_id == actor.id))
        db.delete(actor)
        db.commit()
        log(log.INFO, "Actor [%s] successfully deleted by user [%s]", actor.key, current_user.email)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error deleting actor [%s]: %s", actor.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error deleting actor")


@people_router.delete(
    "/director/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Director successfully deleted"},
        status.HTTP_400_BAD_REQUEST: {
            "description": "Director is associated with other entities",
        },
        status.HTTP_404_NOT_FOUND: {"description": "Director not found"},
    },
)
def delete_director(
    key: str,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Delete director if it has no relations with movies"""

    director = db.scalar(
        sa.select(m.Director)
        .options(
            selectinload(m.Director.movies).selectinload(m.Movie.translations),
        )
        .where(m.Director.key == key)
    )

    if not director:
        log(log.ERROR, "Director [%s] not found", key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Director not found")

    if director.movies:
        movies = [s.MovieMenuItem(key=movie.key, name=movie.get_title(s.Language.EN)) for movie in director.movies]
        # Keep only unique entries by key for cleaner frontend rendering.
        movies_unique = list({item.key: item for item in movies}.values())

        log(log.ERROR, "Director [%s] is associated with other entities and cannot be deleted", director.key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "movies": [item.model_dump() for item in movies_unique],
            },
        )

    try:
        db.execute(sa.delete(m.DirectorTranslation).where(m.DirectorTranslation.director_id == director.id))
        db.delete(director)
        db.commit()
        log(log.INFO, "Director [%s] successfully deleted by user [%s]", director.key, current_user.email)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error deleting director [%s]: %s", director.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error deleting director")


@people_router.delete(
    "/character/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Character successfully deleted"},
        status.HTTP_400_BAD_REQUEST: {
            "description": "Character is associated with other entities",
        },
        status.HTTP_404_NOT_FOUND: {"description": "Character not found"},
    },
)
def delete_character(
    key: str,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Delete character if it has no relations with movies or actors"""

    character = db.scalar(
        sa.select(m.Character)
        .options(
            selectinload(m.Character.characters)
            .selectinload(m.MovieActorCharacter.movie)
            .selectinload(m.Movie.translations),
            selectinload(m.Character.characters)
            .selectinload(m.MovieActorCharacter.actor)
            .selectinload(m.Actor.translations),
        )
        .where(m.Character.key == key)
    )

    if not character:
        log(log.ERROR, "Character [%s] not found", key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")

    if character.characters:
        movies = [
            s.MovieMenuItem(key=rel.movie.key, name=rel.movie.get_title(s.Language.EN))
            for rel in character.characters
            if rel.movie
        ]
        actors = [
            s.MovieMenuItem(key=rel.actor.key, name=rel.actor.full_name(s.Language.EN))
            for rel in character.characters
            if rel.actor
        ]

        # Keep only unique entries by key for cleaner frontend rendering.
        movies_unique = list({item.key: item for item in movies}.values())
        actors_unique = list({item.key: item for item in actors}.values())

        log(log.ERROR, "Character [%s] is associated with other entities and cannot be deleted", character.key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "movies": [item.model_dump() for item in movies_unique],
                "actors": [item.model_dump() for item in actors_unique],
            },
        )

    try:
        db.execute(sa.delete(m.CharacterTranslation).where(m.CharacterTranslation.character_id == character.id))
        db.delete(character)
        db.commit()
        log(log.INFO, "Character [%s] successfully deleted by user [%s]", character.key, current_user.email)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error deleting character [%s]: %s", character.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error deleting character")
