from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Body, File, HTTPException, Depends, UploadFile, status
from api.controllers.people import add_avatar_to_new_actor, add_avatar_to_new_director
from api.dependency.user import get_admin
from api.utils import check_admin_permissions
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db
from config import config

CFG = config()
TOP_ACTORS_LIMIT = 20

people_router = APIRouter(prefix="/people", tags=["People"])


@people_router.post(
    "/actors/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ActorOut,
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

    check_admin_permissions(current_user)

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
        # TODO: need rolback if error
        db.commit()
        log(log.INFO, "Actor [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating actor [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating actor")

    db.refresh(new_actor)

    add_avatar_to_new_actor(
        actor_key=form_data.key,
        file=file,
        new_actor=new_actor,
        db=db,
    )
    return s.ActorOut(
        key=new_actor.key,
        name=new_actor.full_name(lang),
    )


@people_router.get("/actors-with-most-movies", status_code=status.HTTP_200_OK, response_model=s.ActorsList)
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
        .join(subquery, m.Actor.id == subquery.c.id)
        .order_by(subquery.c.movie_count.desc())
        .limit(TOP_ACTORS_LIMIT)
    ).all()
    if not actors:
        log(log.ERROR, "Actors [%s] not found")
        raise HTTPException(status_code=404, detail="Actors not found")

    actors_out = []

    for actor, movie_count in actors:
        actors_out.append(
            s.Actor(key=actor.key, name=actor.full_name(lang), avatar_url=actor.avatar, movie_count=movie_count)
        )
    return s.ActorsList(actors=actors_out)


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

    check_admin_permissions(current_user)

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
        log(log.INFO, "Character [%s] successfully created", form_data.key)
    except Exception as e:
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
    response_model=s.DirectorOut,
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

    check_admin_permissions(current_user)

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
        log(log.INFO, "Director [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating director [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating director")

    db.refresh(new_director)

    add_avatar_to_new_director(
        director_key=form_data.key,
        file=file,
        new_director=new_director,
        db=db,
    )

    return s.DirectorOut(
        key=new_director.key,
        name=new_director.full_name(lang),
    )
