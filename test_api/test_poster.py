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

    UPLOAD_DIRECTORY = "./uploads/movie-posters/"
    test_file = "1_The Shawshank Redemption.png"
    poster_name = "The Shawshank Redemption.png"

    files = {"file": (poster_name, open(UPLOAD_DIRECTORY + test_file, "rb"))}
    response = client.post(f"/api/movies/upload-poster/{movie.id}", files=files)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"info": "Poster uploaded successfully"}
    assert movie.poster == test_file

    response = client.get(f"/api/movies/poster/{test_file}")
    assert response.status_code == status.HTTP_200_OK
