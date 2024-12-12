from fastapi import APIRouter, HTTPException, Depends, status
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

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
    current_user = 1
    """Update rating for a movie"""

    movie = db.scalars(sa.select(m.Movie).where(m.Movie.key == data.movie_key)).first()
    if not movie:
        log(log.ERROR, "Movie [%s] not found")
        raise HTTPException(status_code=404, detail="Movie not found")

    user = db.scalar(sa.select(m.User).where(m.User.id == current_user))
    if not user:
        log(log.ERROR, "User [%s] not found")
        raise HTTPException(status_code=404, detail="User not found")

    if user.ratings:
        for rating in user.ratings:
            if rating.movie_id == movie.id:
                rating.rating = data.rating
                rating.acting = data.acting
                rating.plot_storyline = data.plot_storyline
                rating.music = data.music
                rating.re_watchability = data.re_watchability
                rating.emotional_impact = data.emotional_impact
                rating.dialogue = data.dialogue
                rating.production_design = data.production_design
                rating.duration = data.duration
                rating.visual_effects = data.visual_effects if data.visual_effects else None
                rating.scare_factor = data.scare_factor if data.scare_factor else None

    db.commit()

    movie_ratings = movie.ratings
    average_rating = round(sum([rating.rating for rating in movie_ratings]) / len(movie_ratings), 2)

    movie.average_rating = average_rating
    movie.ratings_count = len(movie_ratings)

    db.commit()

    log(log.DEBUG, "Rating for movie [%s] updated", movie.key)


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
    current_user = 1
    """Rate a movie"""

    movie = db.scalars(sa.select(m.Movie).where(m.Movie.key == data.movie_key)).first()
    if not movie:
        log(log.ERROR, "Movie [%s] not found")
        raise HTTPException(status_code=404, detail="Movie not found")

    user = db.scalar(sa.select(m.User).where(m.User.id == current_user))
    if not user:
        log(log.ERROR, "User [%s] not found")
        raise HTTPException(status_code=404, detail="User not found")

    new_rating = m.Rating(
        user_id=current_user,
        movie_id=movie.id,
        rating=data.rating,
        acting=data.acting,
        plot_storyline=data.plot_storyline,
        music=data.music,
        re_watchability=data.re_watchability,
        emotional_impact=data.emotional_impact,
        dialogue=data.dialogue,
        production_design=data.production_design,
        duration=data.duration,
        visual_effects=data.visual_effects if data.visual_effects else None,
        scare_factor=data.scare_factor if data.scare_factor else None,
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
