import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from api.controllers.create_movie import get_movies_data_from_file, remove_quick_movie
from app import models as m
from app import schema as s
from config import config

CFG = config()

PAGE_SIZE = 30
PAGE = 1


def test_get_movies(client: TestClient, db: Session):
    movies = db.scalars(sa.select(m.Movie)).all()
    assert movies

    # /api/movies/?lang=uk&page=1&size=30&sort_order=desc&sort_by=id
    response = client.get("/api/movies", params={"page": PAGE, "size": PAGE_SIZE})
    assert response.status_code == status.HTTP_200_OK
    data = s.PaginationDataOut.model_validate(response.json())
    assert data
    assert len(data.items) == PAGE_SIZE
    assert data.total
    assert data.page == PAGE
    assert data.size == PAGE_SIZE
    assert data.pages


def test_get_movie(client: TestClient, db: Session):
    movie = db.scalar(sa.select(m.Movie))
    assert movie

    response = client.get(f"/api/movies/{movie.key}")
    assert response.status_code == status.HTTP_200_OK
    data = s.MovieOut.model_validate(response.json())
    assert data
    assert data.key == movie.key


def test_super_search(client: TestClient, db: Session):
    movies = db.scalars(sa.select(m.Movie)).all()
    assert movies

    SEARCH_GENRE = "action(10,100)"

    response = client.get("/api/movies/super-search/", params={"genre": SEARCH_GENRE})
    assert response.status_code == status.HTTP_200_OK
    data = s.PaginationDataOut.model_validate(response.json())
    assert data
    assert len(data.items)

    # Test super search to find a specific movie (The Shawshank Redemption)
    movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == "the-shawshank-redemption"))
    assert movie
    director = db.scalar(sa.select(m.Director).where(m.Director.key == "frank-darabont"))
    assert director
    actor = db.scalar(sa.select(m.Actor).where(m.Actor.key == "morgan-freeman"))
    assert actor

    SEARCH_PARAMS = {
        "genre": "drama(10,100)",
        "specification": "prison(10,100)",
        "actor": "morgan-freeman",
        "director": "frank-darabont",
    }

    response = client.get("/api/movies/super-search/", params=SEARCH_PARAMS)
    assert response.status_code == status.HTTP_200_OK
    data = s.PaginationDataOut.model_validate(response.json())
    assert data
    assert [m for m in data.items if m.key == movie.key]


def test_search(client: TestClient, db: Session):
    movie = db.scalar(sa.select(m.Movie))
    assert movie

    SEARCH_QUERY = movie.get_title()

    response = client.get("/api/movies/search/", params={"query": SEARCH_QUERY})
    assert response.status_code == status.HTTP_200_OK
    data = s.MovieSearchResult.model_validate(response.json())
    assert data
    assert [m for m in data.movies if m.key == movie.key]


def test_get_movie_filters(client: TestClient, db: Session):
    response = client.get("/api/movies/filters/")
    assert response.status_code == status.HTTP_200_OK
    data = s.MovieFiltersListOut.model_validate(response.json())
    assert data.genres
    assert data.actors
    assert data.directors


def test_pre_create_movie_data(client: TestClient, auth_user_owner: m.User):
    """Should return all data needed for movie creation"""

    response = client.get(
        "/api/movies/pre-create/",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.MoviePreCreateData.model_validate(response.json())
    assert data
    assert data.actors
    assert data.directors
    assert data.genres
    assert data.specifications
    assert data.keywords
    assert data.action_times
    assert data.shared_universes
    assert data.base_movies
    assert data.characters


def test_create_movie(client: TestClient, db: Session, auth_user_owner: m.User):
    actor = db.scalar(sa.select(m.Actor))
    assert actor
    director = db.scalar(sa.select(m.Director))
    assert director

    character = db.scalar(sa.select(m.Character))
    assert character

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
            s.ActorCharacterKey(
                key=actor.key,
                character_key=character.key,
                # character_name_uk="Char uk name",
                # character_name_en="Char en name",
            )
        ],
        directors_keys=[director.key],
        genres=[
            s.MovieFilterField(
                name="Test name",
                key=genre.key,
                percentage_match=100,
                subgenre_parent_key="",
            )
        ],
        subgenres=[
            s.MovieFilterField(
                name="Test name",
                key=genre.subgenres[0].key,
                percentage_match=80,
                subgenre_parent_key=genre.key,
            )
        ],
        specifications=[
            s.MovieFilterField(key=specification.key, percentage_match=70, name="Test name", subgenre_parent_key="")
        ],
        keywords=[s.MovieFilterField(key=keyword.key, percentage_match=50, name="Test name", subgenre_parent_key="")],
        action_times=[
            s.MovieFilterField(key=action_time.key, percentage_match=100, name="Test name", subgenre_parent_key="")
        ],
        rating_criterion_type=s.RatingCriterion.BASIC,
        rating=5,
        rating_criteria=s.UserRatingCriteria(
            acting=5,
            plot_storyline=5,
            script_dialogue=5,
            music=5,
            enjoyment=5,
            production_design=5,
            visual_effects=5,
            scare_factor=5,
            humor=5,
            animation_cartoon=5,
        ),
    )

    poster_name = "1_The Shawshank Redemption.png"
    poster_path = f"{CFG.TEST_DATA_PATH}{poster_name}"

    with open(poster_path, "rb") as image:
        response = client.post(
            "/api/movies",
            data={"form_data": form_data.model_dump_json()},
            files={"file": (poster_name, image, "image/png")},
            params={"lang": s.Language.EN.value, "user_uuid": auth_user_owner.uuid},
        )

    assert response.status_code == status.HTTP_201_CREATED

    # Test create with existing key - should fail
    with open(poster_path, "rb") as image:
        response = client.post(
            "/api/movies",
            data={"form_data": form_data.model_dump_json()},
            files={"file": (poster_name, image, "image/png")},
            params={"lang": s.Language.EN.value, "user_uuid": auth_user_owner.uuid},
        )
    assert response.status_code == status.HTTP_409_CONFLICT

    movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == form_data.key))
    assert movie


def test_quick_movies(client: TestClient, auth_user_owner: m.User):
    form_data = s.QuickMovieFormData(
        key="test-quick-add-key",
        title_en="Test quick EN",
        rating=5,
        rating_criterion_type=s.RatingCriterion.BASIC,
        rating_criteria=s.UserRatingCriteria(
            acting=5,
            plot_storyline=5,
            script_dialogue=5,
            music=5,
            enjoyment=5,
            production_design=5,
            visual_effects=5,
            scare_factor=5,
            humor=5,
            animation_cartoon=5,
        ),
    )

    initial_movie_data = get_movies_data_from_file()

    response = client.post(
        "/api/movies/quick-add/", json=form_data.model_dump(), params={"user_uuid": auth_user_owner.uuid}
    )
    assert response.status_code == status.HTTP_201_CREATED

    updated_movie_data = get_movies_data_from_file()
    assert len(initial_movie_data) + 1 == len(updated_movie_data)

    # Test quick add with existing (in file) key
    response = client.post(
        "/api/movies/quick-add/", json=form_data.model_dump(), params={"user_uuid": auth_user_owner.uuid}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    remove_quick_movie(form_data.key)

    current_movies = get_movies_data_from_file()
    assert len(initial_movie_data) == len(current_movies)


def test_get_random_movies(client: TestClient):
    """Test 10 random movies"""
    response = client.get("/api/movies/random/")
    assert response.status_code == status.HTTP_201_CREATED
    data = s.MovieCarouselList.model_validate(response.json())
    assert data
    assert len(data.movies) == 10


def test_get_similar_movies(client: TestClient, db: Session):
    movie = db.scalar(sa.select(m.Movie))
    assert movie

    response = client.get("/api/movies/similar/", params={"movie_key": movie.key})
    assert response.status_code == status.HTTP_200_OK
    data = s.SimilarMovieOutList.model_validate(response.json())
    assert data
    assert data.similar_movies
