import pytest

import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m
from app import schema as s
from config import config

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_movies(client: TestClient, db: Session):
    movies = db.scalars(sa.select(m.Movie)).all()
    assert movies

    response = client.get("/api/movies")
    assert response.status_code == status.HTTP_200_OK
    data = s.MovieOutList.model_validate(response.json())
    assert data

    # Test get by uuid
    movie = movies[0]
    assert movie
    response = client.get(f"/api/movies/{movie.uuid}")
    assert response.status_code == status.HTTP_200_OK

    response = client.get("/api/movies", params={"lang": s.Language.UK.value})
    assert response.status_code == status.HTTP_200_OK

    response = client.get("/api/movies", params={"lang": s.Language.EN.value})
    assert response.status_code == status.HTTP_200_OK
