from fastapi import APIRouter, HTTPException, Depends, status
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db
from config import config

CFG = config()

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.put(
    "/rate-movie/{user_uuid}",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def update_rate_movie(
    user_uuid: str,
    data: s.UserRateMovieIn,
    # lang: s.Language = s.Language.UK,
    # current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user = CFG.CURRENT_USER
    """Update rating for a movie"""

    movie = db.scalars(sa.select(m.Movie).where(m.Movie.key == data.movie_key)).first()
    if not movie:
        log(log.ERROR, "Movie [%s] not found")
        raise HTTPException(status_code=404, detail="Movie not found")

    user = db.scalar(sa.select(m.User).where(m.User.id == current_user))
    if not user:
        log(log.ERROR, "User [%s] not found")
        raise HTTPException(status_code=404, detail="User not found")

    rating_data = data.rating_criteria

    if user.ratings:
        for rating in user.ratings:
            if rating.movie_id == movie.id:
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

    movie_ratings = movie.ratings
    average_rating = round(sum([rating.rating for rating in movie_ratings]) / len(movie_ratings), 2)

    movie.average_rating = average_rating
    movie.ratings_count = len(movie_ratings)

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


@user_router.post(
    "/rate-movie/{user_uuid}",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def rate_movie(
    user_uuid: str,
    data: s.UserRateMovieIn,
    # lang: s.Language = s.Language.UK,
    # current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user = CFG.CURRENT_USER
    """Rate a movie"""

    movie = db.scalars(sa.select(m.Movie).where(m.Movie.key == data.movie_key)).first()
    if not movie:
        log(log.ERROR, "Movie [%s] not found")
        raise HTTPException(status_code=404, detail="Movie not found")

    user = db.scalar(sa.select(m.User).where(m.User.id == current_user))
    if not user:
        log(log.ERROR, "User [%s] not found")
        raise HTTPException(status_code=404, detail="User not found")

    user_rating = db.scalar(
        sa.select(m.Rating).where(m.Rating.movie_id == movie.id).where(m.Rating.user_id == current_user)
    )
    if user_rating:
        log(log.ERROR, "Rating for movie [%s] already exists")
        raise HTTPException(status_code=400, detail="Rating for movie already exists")

    rating_data = data.rating_criteria

    new_rating = m.Rating(
        user_id=current_user,
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

    movie_ratings = movie.ratings
    average_rating = round(sum([rating.rating for rating in movie_ratings]) / len(movie_ratings), 2)

    movie.average_rating = average_rating
    movie.ratings_count = len(movie_ratings)

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
