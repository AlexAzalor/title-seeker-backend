import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from api.controllers.create_movie import QUICK_MOVIES_FILE, get_movies_data_from_file
from api.dependency.user import get_admin, get_current_user
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session, selectinload
from app.database import get_db
from config import config

CFG = config()

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.post(
    "/google-auth",
    status_code=status.HTTP_200_OK,
    response_model=s.GoogleAuthOut,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Google account not found"}},
)
def google_auth(
    auth_data: s.GoogleAuthIn,
    db: Session = Depends(get_db),
):
    """Authenticate user with Google account"""

    user = db.scalar(sa.select(m.User).where(m.User.is_deleted.is_(False), m.User.email == auth_data.email))

    if not user:
        user = m.User(first_name=auth_data.given_name, last_name=auth_data.family_name, email=auth_data.email)
        db.add(user)
        db.commit()
        db.refresh(user)

        log(log.DEBUG, "User [%s] created", user.email)

    new_movies_to_add_count = 0

    if user.role == s.UserRole.OWNER.value:
        if os.path.exists(QUICK_MOVIES_FILE):
            quick_movies = get_movies_data_from_file()

            if quick_movies:
                new_movies_to_add_count = len(quick_movies)

    return s.GoogleAuthOut(
        uuid=user.uuid,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        new_movies_to_add_count=new_movies_to_add_count,
    )


@user_router.delete(
    "/delete-google-profile",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Google account not found"}},
)
def delete_google_profile(
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete user profile"""

    if current_user.role == s.UserRole.OWNER.value:
        log(log.ERROR, "Owner profile cannot be deleted")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner profile cannot be deleted")

    current_user.is_deleted = True
    current_user.email = current_user.email + "-delete at-" + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # The synchronize_session=False argument ensures that the session does not attempt to synchronize the in-memory state with the database after the bulk delete.
    db.query(m.Rating).filter(m.Rating.user_id == current_user.id).delete(synchronize_session=False)

    db.commit()
    log(log.DEBUG, "User [%s] deleted", current_user.email)


@user_router.put(
    "/rate-movie/{user_uuid}",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def update_rate_movie(
    data: s.UserRateMovieIn,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update movie rating"""

    if not current_user.ratings:
        log(log.ERROR, "User [%s] has no ratings to update", current_user.email)
        raise HTTPException(status_code=404, detail="User has no ratings to update")

    rating = next((r for r in current_user.ratings if r.movie.key == data.movie_key), None)
    if not rating:
        log(log.ERROR, "Rating for movie [%s] not found", data.movie_key)
        raise HTTPException(status_code=404, detail="Rating not found")

    rating_data = data.rating_criteria

    rating.rating = data.rating
    rating.acting = rating_data.acting
    rating.plot_storyline = rating_data.plot_storyline
    rating.script_dialogue = rating_data.script_dialogue
    rating.music = rating_data.music
    rating.enjoyment = rating_data.enjoyment
    rating.production_design = rating_data.production_design
    rating.visual_effects = rating_data.visual_effects if rating_data.visual_effects else None
    rating.scare_factor = rating_data.scare_factor if rating_data.scare_factor else None
    rating.humor = rating_data.humor if rating_data.humor else None
    rating.animation_cartoon = rating_data.animation_cartoon if rating_data.animation_cartoon else None

    db.commit()
    # movie_ratings = movie.ratings
    # average_rating = round(sum([rating.rating for rating in movie_ratings]) / len(movie_ratings), 2)

    # movie.average_rating = average_rating
    # movie.ratings_count = len(movie_ratings)

    db.commit()

    log(log.DEBUG, "Rating for movie [%s] updated", data.movie_key)

    # backgroud task?
    # https://fastapi.tiangolo.com/tutorial/background-tasks/
    # ratings = db.scalars(sa.select(m.Rating)).all()
    # if not ratings:
    #     log(log.ERROR, "Ratings are empty!")

    # ratings_to_file = []
    # for rating in ratings:
    #     ratings_to_file.append(
    #         s.RatingExportCreate(
    #             id=rating.id,
    #             movie_id=rating.movie_id,
    #             user_id=rating.user_id,
    #             rating=rating.rating,
    #             acting=rating.acting,
    #             plot_storyline=rating.plot_storyline,
    #             music=rating.music,

    #             dialogue=rating.dialogue,
    #             production_design=rating.production_design,

    #             visual_effects=rating.visual_effects,
    #             scare_factor=rating.scare_factor,
    #             comment=rating.comment,
    #         )
    #     )

    # with open("data/ratings.json", "w") as file:
    #     json.dump(s.RatingsJSONFile(ratings=ratings_to_file).model_dump(mode="json"), file, indent=4)
    #     print("Ratings data saved to [data/ratings.json] file")


@user_router.post(
    "/rate-movie/{user_uuid}",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def rate_movie(
    data: s.UserRateMovieIn,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rate a movie"""

    movie = db.scalars(sa.select(m.Movie).where(m.Movie.key == data.movie_key)).first()
    if not movie:
        log(log.ERROR, "Movie [%s] not found")
        raise HTTPException(status_code=404, detail="Movie not found")

    user_rating = db.scalar(
        sa.select(m.Rating).where(m.Rating.movie_id == movie.id).where(m.Rating.user_id == current_user.id)
    )
    if user_rating:
        log(log.ERROR, "Rating for movie [%s] already exists", movie.key)
        raise HTTPException(status_code=400, detail="Rating for movie already exists")

    rating_data = data.rating_criteria

    new_rating = m.Rating(
        user_id=current_user.id,
        movie_id=movie.id,
        rating=data.rating,
        acting=rating_data.acting,
        plot_storyline=rating_data.plot_storyline,
        script_dialogue=rating_data.script_dialogue,
        music=rating_data.music,
        enjoyment=rating_data.enjoyment,
        production_design=rating_data.production_design,
        visual_effects=rating_data.visual_effects if rating_data.visual_effects else None,
        scare_factor=rating_data.scare_factor if rating_data.scare_factor else None,
        humor=rating_data.humor if rating_data.humor else None,
        animation_cartoon=rating_data.animation_cartoon if rating_data.animation_cartoon else None,
    )

    db.add(new_rating)
    db.flush()
    log(log.DEBUG, "Rating for movie [%s] created", movie.key)

    # movie_ratings = movie.ratings
    # average_rating = round(sum([rating.rating for rating in movie_ratings]) / len(movie_ratings), 2)

    # movie.average_rating = average_rating
    # movie.ratings_count = len(movie_ratings)

    db.commit()

    log(log.DEBUG, "Rating for movie [%s] updated", movie.key)

    # backgroud task?
    # https://fastapi.tiangolo.com/tutorial/background-tasks/
    # ratings = db.scalars(sa.select(m.Rating)).all()
    # if not ratings:
    #     log(log.ERROR, "Ratings are empty!")

    # ratings_to_file = []
    # for rating in ratings:
    #     ratings_to_file.append(
    #         s.RatingExportCreate(
    #             id=rating.id,
    #             movie_id=rating.movie_id,
    #             user_id=rating.user_id,
    #             rating=rating.rating,
    #             acting=rating.acting,
    #             plot_storyline=rating.plot_storyline,
    #             music=rating.music,

    #             dialogue=rating.dialogue,
    #             production_design=rating.production_design,

    #             visual_effects=rating.visual_effects,
    #             scare_factor=rating.scare_factor,
    #             comment=rating.comment,
    #         )
    #     )

    # with open("data/ratings.json", "w") as file:
    #     json.dump(s.RatingsJSONFile(ratings=ratings_to_file).model_dump(mode="json"), file, indent=4)
    #     print("Ratings data saved to [data/ratings.json] file")


@user_router.get(
    "/time-rate-movies",
    status_code=status.HTTP_200_OK,
    response_model=s.MovieChartData,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def time_rate_movie(
    current_user: m.User = Depends(get_current_user),
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get data for time rate movies chart"""

    movies = db.scalars(sa.select(m.Movie).where(m.Movie.is_deleted.is_(False))).all()
    if not movies:
        log(log.ERROR, "Movies not found")
        raise HTTPException(status_code=404, detail="Movies not found")

    data = []

    for rating in current_user.ratings:
        created_at = rating.created_at if rating.created_at > rating.updated_at else rating.updated_at
        data.append(
            s.TimeRateMovieOut(
                # TODO: Implement Timezone
                created_at=created_at + +timedelta(hours=3),
                rating=rating.rating,
                movie_title=rating.movie.get_title(lang),
            )
        )

    return s.MovieChartData(movie_chart_data=sorted(data, key=lambda x: x.created_at)[-30:])


@user_router.get(
    "/genre-radar-chart",
    status_code=status.HTTP_200_OK,
    response_model=s.GenreChartDataList,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def genre_radar_chart(
    current_user: m.User = Depends(get_current_user),
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get top users genres for radar chart"""

    ratings = sorted(current_user.ratings, key=lambda x: x.rating, reverse=True)[:3]

    top_rated_movies = [
        s.TopMyMoviesOut(
            key=rating.movie.key, title=rating.movie.get_title(lang), rating=rating.rating, poster=rating.movie.poster
        )
        for rating in ratings
    ]

    genres_keys = ["action", "adventure", "comedy", "drama", "fantasy", "sci-fi", "horror", "romance"]

    # separate route?
    stmt = (
        sa.select(m.Genre)
        .options(selectinload(m.Genre.movies), selectinload(m.Genre.translations))
        .join(m.Genre.movies)
        .join(m.Movie.ratings)
        .where(m.Rating.user_id == current_user.id)
        .where(m.Genre.key.in_(genres_keys))
        .group_by(m.Genre.id)  # Grouping by ID since we're returning Genre objects
    )

    result = db.scalars(stmt).all()

    genre_counts = []

    for genre in result:
        count = sum(1 for movie in genre.movies if any(r.user_id == current_user.id for r in movie.ratings))
        genre_counts.append(
            s.GenreChartDataOut(
                name=genre.get_name(lang),
                count=count,
            )
        )

    last_rating_date = None

    if current_user.ratings:
        create_date = current_user.ratings[-1].created_at
        update_date = current_user.ratings[-1].updated_at
        # Compare the two dates and assign the later one to last_rating_date
        last_rating_date = create_date if create_date > update_date else update_date

    actors_count = None

    if current_user.role == s.UserRole.OWNER.value:
        actors_count = db.scalars(sa.select(sa.func.count()).select_from(m.Actor)).first()

    return s.GenreChartDataList(
        genre_data=genre_counts,
        top_rated_movies=top_rated_movies,
        joined_date=current_user.created_at,
        movies_rated=len(current_user.ratings),
        last_movie_rate_date=last_rating_date,
        total_actors_count=actors_count,
    )


@user_router.get(
    "/all/",
    status_code=status.HTTP_200_OK,
    response_model=s.UsersListOut,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def get_all_users(
    admin: m.User = Depends(get_admin),
    # lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all users"""

    users = db.scalars(sa.select(m.User).where(m.User.is_deleted.is_(False))).all()

    if not users:
        log(log.ERROR, "Users not found")
        raise HTTPException(status_code=404, detail="Users not found")

    users_out = [
        s.UserOut(
            uuid=user.uuid,
            full_name=user.full_name,
            email=user.email,
            role=s.UserRole(user.role),
            created_at=user.created_at,
        )
        for user in users
        if user.role != s.UserRole.OWNER.value
    ]

    return s.UsersListOut(users=users_out)
