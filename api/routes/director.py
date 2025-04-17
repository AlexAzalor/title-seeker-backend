from datetime import datetime
import os
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

director_router = APIRouter(prefix="/directorrs", tags=["Directors"])


@director_router.get("/", status_code=status.HTTP_200_OK, response_model=s.DirectorListOut)
def get_directors(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all directors"""

    directors = db.scalars(sa.select(m.Director)).all()
    if not directors:
        log(log.ERROR, "Director [%s] not found")
        raise HTTPException(status_code=404, detail="Director not found")

    directors_out = []

    for director in directors:
        directors_out.append(
            s.DirectorOut(
                key=director.key,
                name=director.full_name(lang),
            )
        )
    return s.DirectorListOut(directors=directors_out)


@director_router.post(
    "/",
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
        log(log.INFO, "Director [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating director [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating director")

    db.refresh(new_director)

    file_name = f"{new_director.id}_{file.filename}"

    if CFG.ENV == "production":
        add_image_to_s3_bucket(file, "directors", file_name)
        new_director.avatar = file_name
        db.commit()
    else:
        try:
            directory_path = UPLOAD_DIRECTORY + "directors/"

            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            file_location = f"{directory_path}{file_name}"

            with open(file_location, "wb+") as file_object:
                file_object.write(file.file.read())

            new_director.avatar = file_name
            db.commit()

            log(log.INFO, "Avatar for director [%s] successfully uploaded", form_data.key)
        except Exception as e:
            log(log.ERROR, "Error uploading avatar for director [%s]: %s", form_data.key, e)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error uploading avatar for director")

    return s.DirectorOut(
        key=new_director.key,
        name=new_director.full_name(lang),
    )
