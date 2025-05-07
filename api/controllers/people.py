import os

from fastapi import HTTPException, UploadFile, status
from api.controllers.create_movie import add_image_to_s3_bucket
from api.routes.file import UPLOAD_DIRECTORY
import app.models as m

from app.logger import log
from sqlalchemy.orm import Session
from config import config

CFG = config()


def add_avatar_to_new_actor(actor_key: str, file: UploadFile, new_actor: m.Actor, db: Session) -> None:
    file_name = f"{new_actor.id}_{file.filename}"

    if CFG.ENV == "production":
        try:
            add_image_to_s3_bucket(file, "actors", file_name)
            new_actor.avatar = file_name
            db.commit()
            log(log.INFO, "Avatar for actor [%s] successfully uploaded to the S3 Bucket", actor_key)
        except Exception as e:
            log(log.ERROR, "Error uploading avatar for actor [%s] to S3: %s", actor_key, e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Error uploading avatar for actor to S3"
            )
    else:
        app_env = os.getenv("APP_ENV")

        try:
            actor_dir = UPLOAD_DIRECTORY + "actors/"
            file_location = actor_dir + file_name

            if app_env == "testing":
                file_name = file.filename if file.filename else ""
                file_location = f"{CFG.TEST_DATA_PATH}{file_name}"

            if not os.path.exists(actor_dir):
                os.makedirs(actor_dir)

            with open(file_location, "wb+") as file_object:
                file_object.write(file.file.read())

            new_actor.avatar = file_name
            db.commit()

            log(log.INFO, "Avatar for actor [%s] successfully uploaded", actor_key)
        except Exception as e:
            log(log.ERROR, "Error uploading avatar for actor [%s]: %s", actor_key, e)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error uploading avatar for actor")


def add_avatar_to_new_director(director_key: str, file: UploadFile, new_director: m.Director, db: Session) -> None:
    file_name = f"{new_director.id}_{file.filename}"

    if CFG.ENV == "production":
        try:
            add_image_to_s3_bucket(file, "directors", file_name)
            new_director.avatar = file_name
            db.commit()
            log(log.INFO, "Avatar for director [%s] successfully uploaded to the S3 Bucket", director_key)
        except Exception as e:
            log(log.ERROR, "Error uploading avatar for director [%s] to S3: %s", director_key, e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Error uploading avatar for director to S3"
            )
    else:
        app_env = os.getenv("APP_ENV")

        try:
            director_dir = UPLOAD_DIRECTORY + "directors/"
            file_location = director_dir + file_name

            if app_env == "testing":
                file_name = file.filename if file.filename else ""
                file_location = f"{CFG.TEST_DATA_PATH}{file_name}"

            if not os.path.exists(director_dir):
                os.makedirs(director_dir)

            with open(file_location, "wb+") as file_object:
                file_object.write(file.file.read())

            new_director.avatar = file_name
            db.commit()

            log(log.INFO, "Avatar for director [%s] successfully uploaded", director_key)
        except Exception as e:
            log(log.ERROR, "Error uploading avatar for director [%s]: %s", director_key, e)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error uploading avatar for director")
