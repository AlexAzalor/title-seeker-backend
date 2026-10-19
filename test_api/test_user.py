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

    created = db.scalar(
        sa.select(m.AuditLog)
        .where(m.AuditLog.entity_id == movie.id, m.AuditLog.event_type == "movie.rating.created")
        .order_by(m.AuditLog.id.desc())
    )
    assert created
    assert created.user_id == user.id
    assert created.changes["user_rating"]["rating"] == {"old": None, "new": 7.69}
    assert created.changes["user_rating"]["acting"] == {"old": None, "new": 1.83}
    assert "visual_effects" not in created.changes["user_rating"]
    overall = created.changes["overall_rating"]
    assert overall["ratings_count"]["new"] == overall["ratings_count"]["old"] + 1
    assert overall["rating"]["new"] == movie.average_rating

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

    audit = db.scalar(
        sa.select(m.AuditLog)
        .where(m.AuditLog.entity_id == movie.id, m.AuditLog.event_type == "movie.rating.updated")
        .order_by(m.AuditLog.id.desc())
    )
    assert audit
    assert audit.user_id == user.id
    assert audit.changes["user_rating"]["rating"] == {"old": 7.69, "new": 9.08}
    assert audit.changes["user_rating"]["acting"] == {"old": 1.83, "new": 2.42}
    assert "visual_effects" not in audit.changes["user_rating"]
    overall = audit.changes["overall_rating"]
    assert overall["rating"]["new"] == movie.average_rating
    assert "ratings_count" not in overall  # an edit doesn't change the votes count


def test_get_time_rate_chart_movies(client: TestClient, auth_user_owner: m.User):
    assert auth_user_owner.ratings

    response = client.get("/api/users/time-rate-movies/", params={"user_uuid": auth_user_owner.uuid})
    assert response.status_code == status.HTTP_200_OK
    data = s.MovieChartData.model_validate(response.json())
    assert data
    assert len(data.movie_chart_data) == 30


def test_get_info_report_data(client: TestClient, auth_user_owner: m.User):
    assert auth_user_owner.ratings

    response = client.get("/api/users/info-report/", params={"user_uuid": auth_user_owner.uuid})
    assert response.status_code == status.HTTP_200_OK
    data = s.UserInfoReport.model_validate(response.json())
    assert data
    assert data.genre_data
    assert data.top_rated_movies
    assert data.joined_date
    assert data.total_actors_count is not None
    assert data.total_directors_count is not None


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
    expected_languages = {s.Language.EN.value, s.Language.UK.value}

    movie = db.scalar(sa.select(m.Movie))
    assert movie
    assert movie.visual_profiles
    assert movie.visual_profiles[0].ratings
    assert movie.visual_profiles[0].ratings[0].rating == OLD_RATING_VALUE

    criteria = [
        s.VisualProfileCriterionData(
            name=criterion.criterion.get_name(),
            key=criterion.criterion.key,
            rating=NEW_RATING_VALUE,
            description=criterion.criterion.get_description(),
        )
        for criterion in movie.visual_profiles[0].ratings
    ]

    data_in = s.VisualProfileIn(
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

    def last_audit():
        db.expire_all()
        return db.scalar(
            sa.select(m.AuditLog)
            .where(m.AuditLog.entity_id == movie.id, m.AuditLog.event_type == "movie.visual_profile.updated")
            .order_by(m.AuditLog.id.desc())
        )

    audit = last_audit()
    assert audit
    assert audit.user_id == auth_user_owner.id
    # same category: only the criteria list is logged, with full details per entry
    assert "category" not in audit.changes
    new_criteria = audit.changes["criteria"]["new"]
    assert len(new_criteria) == 6
    assert {"key", "name", "rating", "order"} == set(new_criteria[0])
    assert all(c["rating"] == NEW_RATING_VALUE for c in new_criteria)
    criterion_by_key = {criterion.key: criterion for criterion in movie.visual_profiles[0].category.criteria}
    for criterion_snapshot in new_criteria:
        assert set(criterion_snapshot["name"]) == expected_languages
        assert criterion_snapshot["name"] == {
            translation.language: translation.name
            for translation in criterion_by_key[criterion_snapshot["key"]].translations
        }

    # Test update category with new criteria
    new_category = db.scalar(
        sa.select(m.VisualProfileCategory).where(m.VisualProfileCategory.key != movie.visual_profiles[0].category.key)
    )
    assert new_category

    data_in = s.VisualProfileIn(
        category_key=new_category.key,
        movie_key=movie.key,
        criteria=[
            s.VisualProfileCriterionData(
                name=criterion.get_name(),
                key=criterion.key,
                rating=NEW_RATING_VALUE,
                description=criterion.get_description(),
            )
            for criterion in new_category.criteria
        ],
    )

    response = client.put(f"/api/users/title-visual-profile/{auth_user_owner.uuid}", json=data_in.model_dump())
    assert response.status_code == status.HTTP_200_OK
    assert movie.visual_profiles[0].category.key == new_category.key

    audit = last_audit()
    assert audit
    assert audit.changes["category"]["new"]["key"] == new_category.key
    assert set(audit.changes["category"]["new"]["name"]) == expected_languages
    assert set(audit.changes["category"]["old"]["name"]) == expected_languages
    assert audit.changes["category"]["new"]["name"] == {
        translation.language: translation.name for translation in new_category.translations
    }
    assert audit.changes["category"]["old"]["key"] != new_category.key
    new_criteria = audit.changes["criteria"]["new"]
    assert {c["key"] for c in new_criteria} == {c.key for c in new_category.criteria}
    criterion_by_key = {criterion.key: criterion for criterion in new_category.criteria}
    for criterion_snapshot in new_criteria:
        assert set(criterion_snapshot["name"]) == expected_languages
        assert criterion_snapshot["name"] == {
            translation.language: translation.name
            for translation in criterion_by_key[criterion_snapshot["key"]].translations
        }
