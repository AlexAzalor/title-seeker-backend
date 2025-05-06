from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status
from fastapi.responses import FileResponse
import os
import app.models as m
from sqlalchemy.orm import Session
from app.database import get_db

file_router = APIRouter(prefix="/file", tags=["Files"])

UPLOAD_DIRECTORY = "./uploads/"

############################################
# This routes are for local development only
############################################


# need async?
@file_router.post("/upload-poster/{movie_id}", status_code=status.HTTP_200_OK)
async def upload_poster(movie_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload poster for movie"""

    movie = db.query(m.Movie).filter(m.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    file_name = f"{movie_id}_{file.filename}"
    file_location = f"{UPLOAD_DIRECTORY}{file_name}"

    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    movie.poster = file_name
    db.commit()

    return {"info": "Poster uploaded successfully"}


@file_router.get("/posters/{filename}", status_code=status.HTTP_200_OK)
async def get_poster(filename: str):
    """Check if file exists and return it (for testing purposes)"""

    file_path = os.path.join(UPLOAD_DIRECTORY + "/posters", filename)

    if not os.path.exists(file_path):
        return FileResponse(os.path.join(UPLOAD_DIRECTORY, "poster-placeholder.jpg"))
        # raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


@file_router.post("/upload-actor-avatar/{actor_id}", status_code=status.HTTP_200_OK)
async def upload_avatar(actor_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload avatar for actor"""

    actor = db.query(m.Actor).filter(m.Actor.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")

    directory_path = UPLOAD_DIRECTORY + "actors/"

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    file_name = f"{actor_id}_{file.filename}"
    file_location = f"{directory_path}{file_name}"

    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    actor.avatar = file_name
    db.commit()

    return {"info": "Avatar uploaded successfully"}


@file_router.post("/upload-director-avatar/{director_id}", status_code=status.HTTP_200_OK)
async def upload_director_avatar(director_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload avatar for director"""

    director = db.query(m.Director).filter(m.Director.id == director_id).first()
    if not director:
        raise HTTPException(status_code=404, detail="Director not found")

    directory_path = UPLOAD_DIRECTORY + "directors/"

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    file_name = f"{director_id}_{file.filename}"
    file_location = f"{directory_path}{file_name}"

    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    director.avatar = file_name
    db.commit()

    return {"info": "Avatar uploaded successfully"}


@file_router.get("/actors/{filename}", status_code=status.HTTP_200_OK)
async def get_actor_avatar(filename: str):
    """Check if file exists and return it (for testing purposes)"""

    file_path = os.path.join(UPLOAD_DIRECTORY + "actors/", filename)

    if not os.path.exists(file_path):
        return FileResponse(os.path.join(UPLOAD_DIRECTORY + "actors/", "avatar-placeholder.jpg"))
        # raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


@file_router.get("/directors/{filename}", status_code=status.HTTP_200_OK)
async def get_director_avatar(filename: str):
    """Check if file exists and return it (for testing purposes)"""

    file_path = os.path.join(UPLOAD_DIRECTORY + "directors/", filename)

    if not os.path.exists(file_path):
        return FileResponse(os.path.join(UPLOAD_DIRECTORY + "directors/", "avatar-placeholder.jpg"))
        # raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)
