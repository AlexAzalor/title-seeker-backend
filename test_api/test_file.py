import pytest

import sqlalchemy as sa

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m

from config import config

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_poster(client: TestClient, db: Session):
    movie: m.Movie | None = db.scalar(sa.select(m.Movie).where(m.Movie.id == 1))
    assert movie

    UPLOAD_DIRECTORY = "./uploads/posters/"
    test_file = "1_The Shawshank Redemption.png"
    poster_name = "The Shawshank Redemption.png"

    files = {"file": (poster_name, open(UPLOAD_DIRECTORY + test_file, "rb"))}
    response = client.post(f"/api/file/upload-poster/{movie.id}", files=files)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"info": "Poster uploaded successfully"}
    assert movie.poster == test_file

    response = client.get(f"/api/file/posters/{test_file}")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_actors(client: TestClient, db: Session):
    actor: m.Actor | None = db.scalar(sa.select(m.Actor).where(m.Actor.id == 1))
    assert actor

    UPLOAD_DIRECTORY = "./uploads/actors/"
    test_file = "1_Morgan Freeman.png"
    avatar_name = "Morgan Freeman.png"

    files = {"file": (avatar_name, open(UPLOAD_DIRECTORY + test_file, "rb"))}
    response = client.post(f"/api/file/upload-actor-avatar/{actor.id}", files=files)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"info": "Avatar uploaded successfully"}
    assert actor.avatar == test_file

    response = client.get(f"/api/file/actors/{test_file}")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_director_avatar(client: TestClient, db: Session):
    director: m.Director | None = db.scalar(sa.select(m.Director).where(m.Director.id == 1))
    assert director

    UPLOAD_DIRECTORY = "./uploads/directors/"
    test_file = "1_Frank Darabont.png"
    avatar_name = "Frank Darabont.png"

    files = {"file": (avatar_name, open(UPLOAD_DIRECTORY + test_file, "rb"))}
    response = client.post(f"/api/file/upload-director-avatar/{director.id}", files=files)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"info": "Avatar uploaded successfully"}
    assert director.avatar == test_file

    response = client.get(f"/api/file/directors/{test_file}")
    assert response.status_code == status.HTTP_200_OK
