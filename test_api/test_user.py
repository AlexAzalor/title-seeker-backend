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
def test_rate_movie(client: TestClient, db: Session):
    movie = db.scalar(sa.select(m.Movie))
    assert movie

    user = db.scalar(sa.select(m.User))
    assert user

    rating = db.scalar(sa.select(m.Rating))
    assert rating

    # Test rate movie
    data_in = s.UserRateMovieIn(
        uuid=user.uuid,
        movie_key=movie.key,
        rating=7.34,
        acting=5,
        plot_storyline=4,
        music=3,
        re_watchability=2,
        emotional_impact=1,
        dialogue=2,
        production_design=3,
        duration=4,
    )

    response = client.post(f"/api/users/rate-movie/{user.uuid}", json=data_in.model_dump())
    assert response.status_code == status.HTTP_200_OK
    assert movie.ratings
    ratings_values = [rating.rating for rating in movie.ratings if rating.user_id == user.id]
    assert data_in.rating in ratings_values

    data_in = s.UserRateMovieIn(
        uuid=user.uuid,
        movie_key=movie.key,
        rating=9.5,
        acting=5,
        plot_storyline=4,
        music=3,
        re_watchability=2,
        emotional_impact=1,
        dialogue=2,
        production_design=3,
        duration=4,
    )

    # Test update rate movie
    response = client.put(f"/api/users/rate-movie/{user.uuid}", json=data_in.model_dump())
    assert response.status_code == status.HTTP_200_OK
    assert movie.ratings
    ratings_values = [rating.rating for rating in movie.ratings if rating.user_id == user.id]
    assert data_in.rating in ratings_values
