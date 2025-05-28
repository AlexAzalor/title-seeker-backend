import sqlalchemy as sa

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m

from app import schema as s
from config import config

CFG = config()


def test_rate_movie(client: TestClient, db: Session):
    movie = db.scalar(sa.select(m.Movie))
    assert movie

    user = db.scalar(sa.select(m.User).where(m.User.role == s.UserRole.USER.value))
    assert user

    rating = db.scalar(sa.select(m.Rating))
    assert rating

    # Test add new rate
    data_in = s.UserRateMovieIn(
        uuid=user.uuid,
        movie_key=movie.key,
        rating=7.69,
        rating_criteria=s.RatingCriteria(
            acting=1.83,
            plot_storyline=1.65,
            script_dialogue=1.48,
            music=1.09,
            enjoyment=0.87,
            production_design=0.77,
        ),
    )

    response = client.post(f"/api/users/rate-movie/{user.uuid}", json=data_in.model_dump())
    assert response.status_code == status.HTTP_201_CREATED
    assert movie.ratings
    ratings_values = [rating.rating for rating in movie.ratings if rating.user_id == user.id]
    assert data_in.rating in ratings_values

    # Test update rate
    data_in = s.UserRateMovieIn(
        uuid=user.uuid,
        movie_key=movie.key,
        rating=9.08,
        rating_criteria=s.RatingCriteria(
            acting=2.42,
            plot_storyline=1.85,
            script_dialogue=1.90,
            music=1.4,
            enjoyment=0.81,
            production_design=0.7,
        ),
    )

    response = client.put(f"/api/users/rate-movie/{user.uuid}", json=data_in.model_dump())
    assert response.status_code == status.HTTP_200_OK
    assert movie.ratings
    ratings_values = [rating.rating for rating in movie.ratings if rating.user_id == user.id]
    assert data_in.rating in ratings_values


def test_get_time_rate_chart_movies(client: TestClient, auth_user_owner: m.User):
    assert auth_user_owner.ratings

    response = client.get("/api/users/time-rate-movies/", params={"user_uuid": auth_user_owner.uuid})
    assert response.status_code == status.HTTP_200_OK
    data = s.MovieChartData.model_validate(response.json())
    assert data
    assert len(data.movie_chart_data) == 30


def test_get_genre_radar_chart_data(client: TestClient, auth_user_owner: m.User):
    assert auth_user_owner.ratings

    response = client.get("/api/users/genre-radar-chart/", params={"user_uuid": auth_user_owner.uuid})
    assert response.status_code == status.HTTP_200_OK
    data = s.GenreChartDataList.model_validate(response.json())
    assert data
    assert data.genre_data
    assert data.top_rated_movies
    assert data.joined_date


def test_get_all_users(client: TestClient, auth_user_owner: m.User):
    assert auth_user_owner.ratings

    response = client.get("/api/users/all/", params={"user_uuid": auth_user_owner.uuid})
    assert response.status_code == status.HTTP_200_OK
    data = s.UsersListOut.model_validate(response.json())
    assert data
    assert data.users


def test_set_language(client: TestClient, auth_simple_user: m.User):
    assert auth_simple_user.preferred_language == s.Language.UK.value

    # Set new language
    lang = s.Language.EN.value
    response = client.put(f"/api/users/language/{auth_simple_user.uuid}", params={"lang": lang})
    assert response.status_code == status.HTTP_200_OK
    assert auth_simple_user.preferred_language == lang


def test_title_visual_profile_movie(client: TestClient, db: Session, auth_user_owner: m.User):
    OLD_RATING_VALUE = 3
    NEW_RATING_VALUE = 5

    movie = db.scalar(sa.select(m.Movie))
    assert movie
    assert movie.visual_profiles
    assert movie.visual_profiles[0].ratings
    assert movie.visual_profiles[0].ratings[0].rating == OLD_RATING_VALUE

    criteria = [
        s.CriterionRatingIn(
            name=criterion.criterion.get_name(),
            key=criterion.criterion.key,
            rating=NEW_RATING_VALUE,
        )
        for criterion in movie.visual_profiles[0].ratings
    ]

    data_in = s.TitleVisualProfileIn(
        category_key=movie.visual_profiles[0].category.key,
        movie_key=movie.key,
        # user_uuid=auth_user_owner.uuid,
        criteria=criteria[::-1],  # Reverse the order to match the expected input
    )

    response = client.put(f"/api/users/title-visual-profile/{auth_user_owner.uuid}", json=data_in.model_dump())
    assert response.status_code == status.HTTP_200_OK
    assert movie.visual_profiles[0].ratings
    assert movie.visual_profiles[0].ratings[0].rating == NEW_RATING_VALUE
    # Check that the order is preserved (max 6)
    assert movie.visual_profiles[0].ratings[0].order == 6
