import os
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Body, File, HTTPException, Depends, UploadFile, status
from api.controllers.create_movie import add_image_to_s3_bucket
from api.routes.avatar import UPLOAD_DIRECTORY
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db
from config import config

CFG = config()

actor_router = APIRouter(prefix="/actors", tags=["Actors"])


@actor_router.get("/", status_code=status.HTTP_200_OK, response_model=s.ActorListOut)
def get_actors(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all actors"""

    actors = db.scalars(sa.select(m.Actor)).all()
    if not actors:
        log(log.ERROR, "Actors [%s] not found")
        raise HTTPException(status_code=404, detail="Actors not found")

    actors_out = []

    for actor in actors:
        actors_out.append(
            s.ActorOut(
                key=actor.key,
                name=actor.full_name(lang),
            )
        )
    return s.ActorListOut(actors=actors_out)


@actor_router.post(
    "/",
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
        log(log.INFO, "Actor [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating actor [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating actor")

    db.refresh(new_actor)

    file_name = f"{new_actor.id}_{file.filename}"

    if CFG.ENV == "production":
        add_image_to_s3_bucket(file, "actors", file_name)
        new_actor.avatar = file_name
        db.commit()
        log(log.INFO, "Avatar for actor [%s] successfully uploaded to the S3 Bucket", form_data.key)
    else:
        try:
            directory_path = UPLOAD_DIRECTORY + "actors/"

            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            file_location = f"{directory_path}{file_name}"

            with open(file_location, "wb+") as file_object:
                file_object.write(file.file.read())

            new_actor.avatar = file_name
            db.commit()

            log(log.INFO, "Avatar for actor [%s] successfully uploaded", form_data.key)
        except Exception as e:
            log(log.ERROR, "Error uploading avatar for actor [%s]: %s", form_data.key, e)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error uploading avatar for actor")

    return s.ActorOut(
        key=new_actor.key,
        name=new_actor.full_name(lang),
    )


@actor_router.get("/top-movies-count", status_code=status.HTTP_200_OK, response_model=s.ActorsList)
def get_top_movies_count_actors(
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
        .limit(20)
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
