import os
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, File, Form, HTTPException, Depends, UploadFile, status
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
    key: Annotated[str, Form()],
    first_name_uk: Annotated[str, Form()],
    last_name_uk: Annotated[str, Form()],
    first_name_en: Annotated[str, Form()],
    last_name_en: Annotated[str, Form()],
    born: Annotated[str, Form()],
    born_in_uk: Annotated[str, Form()],
    born_in_en: Annotated[str, Form()],
    died: Annotated[str | None, Form()] = None,
    file: UploadFile = File(None),
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new actor"""

    actor = db.scalar(sa.select(m.Actor).where(m.Actor.key == key))

    if actor:
        log(log.ERROR, "Actor [%s] already exists")
        raise HTTPException(status_code=400, detail="Actor already exists")

    try:
        new_actor = m.Actor(
            key=key,
            born=datetime.strptime(born, "%d.%m.%Y"),
            died=datetime.strptime(died, "%d.%m.%Y") if died else None,
            translations=[
                m.ActorTranslation(
                    language=s.Language.UK.value,
                    first_name=first_name_uk,
                    last_name=last_name_uk,
                    born_in=born_in_uk,
                ),
                m.ActorTranslation(
                    language=s.Language.EN.value,
                    first_name=first_name_en,
                    last_name=last_name_en,
                    born_in=born_in_en,
                ),
            ],
        )

        db.add(new_actor)
        db.commit()
        log(log.INFO, "Actor [%s] successfully created", key)
    except Exception as e:
        log(log.ERROR, "Error creating actor [%s]: %s", key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating actor")

    db.refresh(new_actor)

    file_name = f"{new_actor.id}_{file.filename}"

    if CFG.ENV == "production":
        add_image_to_s3_bucket(file, "actors", file_name)
        new_actor.avatar = file_name
        db.commit()
        log(log.INFO, "Avatar for actor [%s] successfully uploaded to the S3 Bucket", key)
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

            log(log.INFO, "Avatar for actor [%s] successfully uploaded", key)
        except Exception as e:
            log(log.ERROR, "Error uploading avatar for actor [%s]: %s", key, e)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error uploading avatar for actor")

    return s.ActorOut(
        key=new_actor.key,
        name=new_actor.full_name(lang),
    )
