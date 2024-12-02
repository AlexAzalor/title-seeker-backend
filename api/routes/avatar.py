from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
import os
import app.models as m
from sqlalchemy.orm import Session
from app.database import get_db

avatar_router = APIRouter(prefix="/avatars", tags=["Avatars"])

UPLOAD_DIRECTORY = "./uploads/avatars/"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


@avatar_router.post("/upload-avatar/{actor_id}")
async def upload_avatar(actor_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload avatar for actor"""

    file_name = f"{actor_id}_{file.filename}"
    file_location = f"{UPLOAD_DIRECTORY}{file_name}"

    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    actor = db.query(m.Actor).filter(m.Actor.id == actor_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="Actor not found")

    actor.avatar = file_name
    db.commit()

    return {"info": "Avatar uploaded successfully"}


@avatar_router.get("/avatars/{filename}")
async def get_avatar(filename: str):
    """Check if file exists and return it (for testing purposes)"""
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
