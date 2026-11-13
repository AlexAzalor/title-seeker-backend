from datetime import datetime
from typing import Literal

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from api import app
from api.controllers.tournament import tournament_query
from api.dependency.user import get_current_user
from app import models as m
from app import schema as s
from app.database import db as database, get_db


@pytest.fixture
def tournament_db():
    engine = sa.create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    database.Model.metadata.create_all(engine)
    with Session(engine) as session:
        genres = [
            m.Genre(
                key=f"genre-{i}", translations=[m.GenreTranslation(language="en", name=f"Genre {i}", description="")]
            )
            for i in range(5)
        ]
        specs = [m.Specification(key=f"spec-{i}") for i in range(5)]
        movies = [
            m.Movie(
                key=f"movie-{i}",
                duration=120,
                budget=0,
                poster="poster.jpg",
                release_date=datetime(2000, 1, 1),
                translations=[m.MovieTranslation(language="en", title=f"Movie {i}", description="", location="")],
            )
            for i in range(40)
        ]
        session.add_all(genres + specs + movies)
        session.flush()
        for i, movie in enumerate(movies):
            genre_count = 3 if i < 16 else 4 if i < 32 else 5
            spec_count = 4 if i < 16 else 3 if i < 32 else 5
            session.execute(
                m.movie_genres.insert(),
                [
                    {"movie_id": movie.id, "genre_id": genre.id, "percentage_match": 60}
                    for genre in genres[:genre_count]
                ],
            )
            session.execute(
                m.movie_specifications.insert(),
                [
                    {"movie_id": movie.id, "specification_id": spec.id, "percentage_match": 60}
                    for spec in specs[:spec_count]
                ],
            )
        session.commit()
        yield session
    engine.dispose()


@pytest.fixture
def tournament_client(tournament_db):
    def override_db():
        yield tournament_db

    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


def post_pool(client: TestClient, **settings):
    return client.post("/api/movies/tournament/?lang=en", json={"size": 16, **settings})


@pytest.mark.parametrize("size", [16, 32])
def test_random_pool_and_card_fields(tournament_client: TestClient, size: Literal[16, 32]):
    response = post_pool(tournament_client, size=size)
    assert response.status_code == 200
    data = s.MovieTournamentOut.model_validate(response.json())
    assert data.total == 40
    assert len(data.movies) == len({movie.key for movie in data.movies}) == size
    assert all(movie.title.startswith("Movie ") and movie.main_genre and movie.rating == 0 for movie in data.movies)
    sql = str(tournament_query(s.MovieTournamentIn(size=size)))
    assert "ORDER BY random()" in sql
    assert "JOIN ratings" not in sql
    assert "WHERE" not in sql


def test_existing_movie_list_preview(tournament_client: TestClient):
    response = tournament_client.get("/api/movies/?lang=en&page=1&size=16")
    assert response.status_code == 200
    data = s.PaginationDataOut.model_validate(response.json())
    assert data.total == 40
    assert len(data.items) == 16
    assert all(movie.title.startswith("Movie ") and movie.main_genre and movie.rating == 0 for movie in data.items)


def test_filtered_query_compiles_for_postgresql():
    settings = s.MovieTournamentIn(
        size=16,
        include_genres=["genre-0", "genre-1"],
        include_specifications=["spec-0"],
        exclude_genres=["genre-2"],
        exclude_specifications=["spec-1"],
        exclude_movies=["movie-0"],
        collection_type=s.TournamentCollectionType.STANDALONE,
    )
    sql = str(tournament_query(settings).compile(dialect=postgresql.dialect()))
    assert "count(*) OVER ()" in sql
    assert "ORDER BY random()" in sql
    assert "percentage_match" in sql


def test_empty_filters_and_unknown_exclusions_do_not_restrict_pool(tournament_client):
    response = post_pool(
        tournament_client,
        genre_threshold=60,
        specification_threshold=60,
        exclude_genres=["missing"],
        exclude_specifications=["missing"],
        exclude_movies=["missing"],
        exclude_shared_universes=["missing"],
    )
    assert response.status_code == 200
    assert response.json()["total"] == 40


@pytest.mark.parametrize(
    ("genre_keys", "spec_keys", "genre_threshold", "spec_threshold", "expected"),
    [
        (["genre-0"], [], 60, 60, set(range(16)) | set(range(32, 40))),
        (["genre-0"], [], 60.1, 60, set(range(32, 40))),
        (["genre-0"], [], 100, 60, set(range(32, 40))),
        ([], ["spec-0"], 60, 80, set(range(16, 32))),
        (["genre-0", "genre-1"], [], 60, 60, set(range(40))),
        (["genre-0"], ["spec-0"], 60, 80, set(range(40))),
    ],
)
def test_tournament_matches_super_search_percentages(
    tournament_client, tournament_db, genre_keys, spec_keys, genre_threshold, spec_threshold, expected
):
    movies = tournament_db.scalars(sa.select(m.Movie).order_by(m.Movie.id)).all()
    genre_ids = dict(tournament_db.execute(sa.select(m.Genre.key, m.Genre.id)).all())
    spec_id = tournament_db.scalar(sa.select(m.Specification.id).where(m.Specification.key == "spec-0"))
    for i, movie in enumerate(movies):
        for key, percentage in (
            ("genre-0", 60 if i < 16 else 59 if i < 32 else 100),
            ("genre-1", 100 if 16 <= i < 32 else 10),
        ):
            tournament_db.execute(
                m.movie_genres.update()
                .where(m.movie_genres.c.movie_id == movie.id, m.movie_genres.c.genre_id == genre_ids[key])
                .values(percentage_match=percentage)
            )
        tournament_db.execute(
            m.movie_specifications.update()
            .where(m.movie_specifications.c.movie_id == movie.id, m.movie_specifications.c.specification_id == spec_id)
            .values(percentage_match=80 if 16 <= i < 32 else 10)
        )
    tournament_db.commit()
    settings = s.MovieTournamentIn(
        size=16,
        include_genres=genre_keys,
        genre_threshold=genre_threshold,
        include_specifications=spec_keys,
        specification_threshold=spec_threshold,
    )
    rows = tournament_db.execute(tournament_query(settings)).all()
    response = post_pool(tournament_client, **settings.model_dump(exclude={"size"}))
    expected_keys = {f"movie-{i}" for i in expected}
    assert {row[0].key for row in rows} <= expected_keys
    if len(expected) < 16:
        assert response.status_code == 400
        assert response.json()["detail"]["available_movies"] == len(expected)
    else:
        assert response.status_code == 200
        assert response.json()["total"] == len(expected)
        assert {movie["key"] for movie in response.json()["movies"]} <= expected_keys
    if float(genre_threshold).is_integer() and float(spec_threshold).is_integer():
        params = [("lang", "en"), ("size", "100")]
        params += [("genre", f"{key}({int(genre_threshold)},100)") for key in genre_keys]
        params += [("specification", f"{key}({int(spec_threshold)},100)") for key in spec_keys]
        search = tournament_client.get("/api/movies/super-search/", params=params)
        assert search.status_code == 200
        assert {item["key"] for item in search.json()["items"]} == expected_keys


def test_default_threshold_and_exclusions(tournament_client, tournament_db):
    movie_ids = list(tournament_db.scalars(sa.select(m.Movie.id).order_by(m.Movie.id)))
    genre_id = tournament_db.scalar(sa.select(m.Genre.id).where(m.Genre.key == "genre-0"))
    tournament_db.execute(
        m.movie_genres.update()
        .where(m.movie_genres.c.movie_id.in_(movie_ids[:16]), m.movie_genres.c.genre_id == genre_id)
        .values(percentage_match=100)
    )
    tournament_db.execute(
        m.movie_genres.update()
        .where(m.movie_genres.c.movie_id == movie_ids[16], m.movie_genres.c.genre_id == genre_id)
        .values(percentage_match=101)
    )
    tournament_db.commit()
    response = post_pool(tournament_client, include_genres=["missing", "genre-0"])
    assert response.status_code == 200
    assert response.json()["total"] == 16
    assert {movie["key"] for movie in response.json()["movies"]} == {f"movie-{i}" for i in range(16)}
    response = post_pool(
        tournament_client,
        include_genres=["genre-0"],
        exclude_specifications=["spec-0"],
    )
    assert response.status_code == 400
    assert response.json()["detail"]["available_movies"] == 0


def test_super_search_exact_match_behavior_is_preserved(tournament_client):
    params = [("lang", "en"), ("size", "100"), ("exact_match", "true"), ("inner_exact_match", "true")]
    params += [("genre", f"genre-{i}(60,100)") for i in range(3)]
    params += [("specification", f"spec-{i}(60,100)") for i in range(4)]
    response = tournament_client.get("/api/movies/super-search/", params=params)
    assert response.status_code == 200
    assert {movie["key"] for movie in response.json()["items"]} == {f"movie-{i}" for i in range(16)}


def test_combined_filters_and_exclusions(tournament_client):
    response = post_pool(
        tournament_client,
        include_genres=["genre-0", "genre-1", "genre-2", "genre-3", "genre-4"],
        genre_threshold=80,
        include_specifications=["spec-0", "spec-1", "spec-2", "spec-3", "spec-4"],
        specification_threshold=60,
        exclude_genres=["genre-4"],
        exclude_specifications=["spec-3"],
        exclude_movies=["movie-16"],
    )
    assert response.status_code == 400
    assert response.json()["detail"]["available_movies"] == 15
    response = post_pool(tournament_client, exclude_movies=["movie-0"], exclude_genres=["genre-4"])
    assert response.status_code == 200
    assert response.json()["total"] == 31
    assert all(movie["key"] != "movie-0" for movie in response.json()["movies"])


def test_collection_types_and_shared_universe(tournament_client, tournament_db):
    movies = tournament_db.scalars(sa.select(m.Movie).order_by(m.Movie.id)).all()
    universe = m.SharedUniverse(key="universe")
    tournament_db.add(universe)
    tournament_db.flush()
    movies[0].relation_type = "base"
    movies[0].collection_order = 2
    movies[1].relation_type = "prequel"
    movies[1].collection_order = 1
    movies[1].collection_base_movie_id = movies[0].id
    movies[2].shared_universe_id = universe.id
    tournament_db.commit()
    response = post_pool(tournament_client, collection_type="standalone")
    assert response.status_code == 200
    assert response.json()["total"] == 37
    assert not {movie["key"] for movie in response.json()["movies"]} & {"movie-0", "movie-1", "movie-2"}
    response = post_pool(tournament_client, collection_type="base")
    assert response.status_code == 400
    assert response.json()["detail"]["available_movies"] == 1
    rows = tournament_db.execute(
        tournament_query(s.MovieTournamentIn(size=16, collection_type=s.TournamentCollectionType.BASE))
    ).all()
    assert [row[0].key for row in rows] == ["movie-0"]
    assert post_pool(tournament_client).json()["total"] == 40


def test_excluding_collection_base_also_excludes_members(tournament_client, tournament_db):
    base = tournament_db.scalar(sa.select(m.Movie).where(m.Movie.key == "movie-0"))
    member_one = tournament_db.scalar(sa.select(m.Movie).where(m.Movie.key == "movie-1"))
    member_two = tournament_db.scalar(sa.select(m.Movie).where(m.Movie.key == "movie-2"))
    assert base and member_one and member_two
    base.relation_type = s.RelatedMovie.BASE.value
    member_one.relation_type = s.RelatedMovie.SEQUEL.value
    member_one.collection_base_movie_id = base.id
    member_two.relation_type = s.RelatedMovie.SEQUEL.value
    member_two.collection_base_movie_id = base.id
    tournament_db.commit()

    response = post_pool(tournament_client, exclude_movies=[base.key])

    assert response.status_code == 200
    assert response.json()["total"] == 37
    assert not {movie["key"] for movie in response.json()["movies"]} & {
        base.key,
        member_one.key,
        member_two.key,
    }


def test_exclude_shared_universe(tournament_client, tournament_db):
    universe = m.SharedUniverse(key="star-wars")
    tournament_db.add(universe)
    tournament_db.flush()
    universe_movie_keys = {"movie-0", "movie-1", "movie-2"}
    for key in universe_movie_keys:
        movie = tournament_db.scalar(sa.select(m.Movie).where(m.Movie.key == key))
        assert movie is not None
        movie.shared_universe_id = universe.id
    tournament_db.commit()

    response = post_pool(tournament_client, exclude_shared_universes=["star-wars"])

    assert response.status_code == 200
    assert response.json()["total"] == 37
    assert not {movie["key"] for movie in response.json()["movies"]} & universe_movie_keys


def test_insufficient_zero_and_unknown_keys(tournament_client):
    response = post_pool(tournament_client, include_genres=["missing"])
    assert response.status_code == 400
    assert response.json()["detail"]["available_movies"] == 0
    response = post_pool(tournament_client, exclude_movies=[f"movie-{i}" for i in range(25)])
    assert response.status_code == 400
    assert response.json()["detail"]["available_movies"] == 15
    assert "movies" not in response.json()


@pytest.mark.parametrize(
    "settings",
    [
        {"size": 8},
        {"size": 16, "genre_threshold": 59},
        {"size": 16, "specification_threshold": 101},
        {"size": 16, "collection_type": "sequel"},
        {"size": 16, "include_genres": ["genre-0", "genre-0"]},
        {"size": 16, "exclude_movies": [" "]},
        {"size": 16, "exclude_shared_universes": ["star-wars", "star-wars"]},
        {"size": 16, "unknown": True},
    ],
)
def test_invalid_settings(tournament_client, settings):
    assert tournament_client.post("/api/movies/tournament/", json=settings).status_code == 422


def test_authenticated_pool_does_not_require_ratings(tournament_client, tournament_db):
    movie = tournament_db.scalar(sa.select(m.Movie).where(m.Movie.key == "movie-0"))
    assert movie is not None
    tournament_db.add(
        m.Rating(
            movie_id=movie.id,
            user_id=123,
            rating=8.5,
            acting=1,
            plot_storyline=1,
            script_dialogue=1,
            music=1,
            enjoyment=1,
            production_design=1,
        )
    )
    tournament_db.commit()
    app.dependency_overrides[get_current_user] = lambda: m.User(id=123)
    response = post_pool(tournament_client, exclude_movies=[f"movie-{i}" for i in range(16, 40)])
    assert response.status_code == 200
    assert response.json()["total"] == 16
    ratings = {movie["key"]: movie["rating"] for movie in response.json()["movies"]}
    assert ratings["movie-0"] == 8.5
    assert ratings["movie-1"] == 0
    response = tournament_client.get("/api/movies/?lang=en&page=1&size=16")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["rating"] == 8.5
