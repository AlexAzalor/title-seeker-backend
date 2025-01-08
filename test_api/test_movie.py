import os
import pytest

import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from api.controllers.create_movie import get_movies_data_from_file, remove_temp_movie
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
    ACTORS = ["hugo-weaving", "elijah-wood", "ian-mckellen"]
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


def test_create_movie(client: TestClient, db: Session):
    actor = db.scalar(sa.select(m.Actor))
    assert actor
    director = db.scalar(sa.select(m.Director))
    assert director

    genre = db.scalar(sa.select(m.Genre).where(m.Genre.subgenres.any()))
    assert genre
    assert genre.subgenres

    specification = db.scalar(sa.select(m.Specification))
    assert specification
    keyword = db.scalar(sa.select(m.Keyword))
    assert keyword
    action_time = db.scalar(sa.select(m.ActionTime))
    assert action_time

    form_data = s.MovieFormData(
        key="test-create-key",
        title_uk="Test create UK",
        title_en="Test create EN",
        description_uk="Text UK",
        description_en="Text EN",
        release_date="2025-01-03T09:56:44.611Z",
        duration=100,
        budget=1000000,
        domestic_gross=3000000,
        worldwide_gross=5000000,
        poster="id_title.png",
        location_uk="Location UK",
        location_en="Location EN",
        actors_keys=[
            s.MoviePersonFilterField(
                key=actor.key,
                character_key="Char key",
                character_name_uk="Char uk name",
                character_name_en="Char en name",
            )
        ],
        directors_keys=[director.key],
        genres=[
            s.MovieFilterField(
                key=genre.key,
                percentage_match=100,
            )
        ],
        subgenres=[
            s.MovieFilterField(
                key=genre.subgenres[0].key,
                percentage_match=80,
                subgenre_parent_key=genre.key,
            )
        ],
        specifications=[s.MovieFilterField(key=specification.key, percentage_match=70)],
        keywords=[s.MovieFilterField(key=keyword.key, percentage_match=50)],
        action_times=[s.MovieFilterField(key=action_time.key, percentage_match=100)],
        rating_criterion_type=s.RatingCriterion.BASIC,
        rating=5,
        rating_criteria=s.UserRatingCriteria(
            acting=5,
            plot_storyline=5,
            music=5,
            re_watchability=5,
            emotional_impact=5,
            dialogue=5,
            production_design=5,
            duration=5,
            visual_effects=5,
            scare_factor=5,
        ),
    )

    with open("./uploads/movie-posters/1_The Shawshank Redemption.png", "rb") as image:
        response = client.post(
            "/api/movies",
            data={"form_data": form_data.model_dump_json()},
            files={"file": ("1_The Shawshank Redemption.png", image, "image/png")},
            params={"lang": s.Language.EN.value, "import_to_google_sheet": False},
        )

    assert response.status_code == status.HTTP_201_CREATED

    # Test create with existing key
    response = client.post(
        "/api/movies",
        data={"form_data": form_data.model_dump_json()},
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == form_data.key))
    assert movie
    os.remove(f"./uploads/movie-posters/{movie.id}_1_The Shawshank Redemption.png")


def test_quick_movies(client: TestClient):
    form_data = s.QuickMovieFormData(
        key="test-quick-add-key",
        title_en="Test quick EN",
        rating=5,
        rating_criterion_type=s.RatingCriterion.BASIC,
        rating_criteria=s.UserRatingCriteria(
            acting=5,
            plot_storyline=5,
            music=5,
            re_watchability=5,
            emotional_impact=5,
            dialogue=5,
            production_design=5,
            duration=5,
            visual_effects=5,
            scare_factor=5,
        ),
    )

    initial_movie_data = get_movies_data_from_file()

    response = client.post("/api/movies/quick-add/", json=form_data.model_dump())
    assert response.status_code == status.HTTP_201_CREATED

    updated_movie_data = get_movies_data_from_file()
    assert len(initial_movie_data) + 1 == len(updated_movie_data)

    # Test quick add with existing (in file) key
    response = client.post("/api/movies/quick-add/", json=form_data.model_dump())
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    remove_temp_movie(form_data.key)

    current_movies = get_movies_data_from_file()
    assert len(initial_movie_data) == len(current_movies)
