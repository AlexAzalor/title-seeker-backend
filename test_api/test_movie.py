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
    data = s.MoviePreviewOutList.model_validate(response.json())
    assert data

    # Test get by key
    movie = movies[0]
    assert movie
    response = client.get(f"/api/movies/{movie.key}")
    assert response.status_code == status.HTTP_200_OK

    response = client.get("/api/movies", params={"lang": s.Language.UK.value})
    assert response.status_code == status.HTTP_200_OK

    response = client.get("/api/movies", params={"lang": s.Language.EN.value})
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_movie(client: TestClient, db: Session):
    movie = db.scalar(sa.select(m.Movie))
    assert movie

    response = client.get(f"/api/movies/{movie.key}")
    assert response.status_code == status.HTTP_200_OK
    data = s.MovieOut.model_validate(response.json())
    assert data
    assert data.key == movie.key
    for actor in data.actors:
        assert actor.character_name
    assert data.actors
    assert data.directors
    assert data.genres
    # assert data.subgenres
    assert data.specifications
    assert data.keywords
    assert data.action_times
    assert data.ratings


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_search_movies(client: TestClient, db: Session):
    GENRES = ["crime", "drama"]
    ACTORS = ["morgan-freeman"]
    RESULT_MOVIE = ["the-shawshank-redemption", "the-dark-knight"]

    genres = db.scalars(sa.select(m.Genre).where(m.Genre.key.in_(GENRES))).all()
    assert genres

    actors = db.scalars(sa.select(m.Actor).where(m.Actor.key.in_(ACTORS))).all()
    assert actors

    response = client.get("/api/movies/search/", params={"genre_name": GENRES, "actor_name": ACTORS})
    assert response.status_code == status.HTTP_200_OK
    data = s.MovieSearchResult.model_validate(response.json())
    assert data
    assert [m.key for m in data.movies] == RESULT_MOVIE

    # Test search by all filters
    GENRES = ["adventure", "drama", "fantasy"]
    SUBGENRES = ["quest", "sword-sorcery"]
    ACTORS = ["hugo-weaving", "elijah-wood", "lan-mckellen"]
    DIRECTORS = ["peter-jackson"]
    RESULT_MOVIE = ["the-lord-of-the-rings-the-fellowship-of-the-ring"]

    genres = db.scalars(sa.select(m.Genre).where(m.Genre.key.in_(GENRES))).all()
    assert genres

    subgenres = db.scalars(sa.select(m.Subgenre).where(m.Subgenre.key.in_(SUBGENRES))).all()
    assert subgenres

    actors = db.scalars(sa.select(m.Actor).where(m.Actor.key.in_(ACTORS))).all()
    assert actors

    directors = db.scalars(sa.select(m.Director).where(m.Director.key.in_(DIRECTORS))).all()
    assert directors

    response = client.get(
        "/api/movies/search/",
        params={"genre_name": GENRES, "subgenre_name": SUBGENRES, "actor_name": ACTORS, "director_name": DIRECTORS},
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.MovieSearchResult.model_validate(response.json())
    assert data
    assert [m.key for m in data.movies] == RESULT_MOVIE

    # Test search by minimal filters
    GENRES = ["crime"]
    DIRECTORS = ["frank-darabont"]
    RESULT_MOVIE = ["the-shawshank-redemption", "the-green-mile"]

    genres = db.scalars(sa.select(m.Genre).where(m.Genre.key.in_(GENRES))).all()
    assert genres

    directors = db.scalars(sa.select(m.Director).where(m.Director.key.in_(DIRECTORS))).all()
    assert directors

    response = client.get("/api/movies/search/", params={"genre_name": GENRES, "director_name": DIRECTORS})
    assert response.status_code == status.HTTP_200_OK
    data = s.MovieSearchResult.model_validate(response.json())
    assert data
    assert [m.key for m in data.movies] == RESULT_MOVIE


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_movie_filters(client: TestClient, db: Session):
    response = client.get("/api/movies/filters/")
    assert response.status_code == status.HTTP_200_OK
    data = s.MovieFiltersListOut.model_validate(response.json())
    assert data.genres
    assert data.actors
    assert data.directors
