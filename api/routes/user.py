from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from api.dependency.user import get_admin, get_current_user
from api.utils import process_movie_rating
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
    "/rate-movie/{user_uuid}",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def rate_movie(
    data: s.UserRateMovieIn,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add new movie rating"""

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

    process_movie_rating(movie)

    db.commit()

    log(log.DEBUG, "Rating for movie [%s] updated", movie.key)


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

    movie = db.scalars(sa.select(m.Movie).where(m.Movie.key == data.movie_key)).first()
    if not movie:
        log(log.ERROR, "Movie [%s] not found", data.movie_key)
        raise HTTPException(status_code=404, detail="Movie not found")

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

    process_movie_rating(movie)

    db.commit()

    log(log.DEBUG, "Rating for movie [%s] updated", data.movie_key)


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
            ratings_count=len(user.ratings),
            last_movie_rate_date=max(
                (rating.created_at for rating in user.ratings), default=None, key=lambda x: x or 0
            ),
        )
        for user in users
        if user.role != s.UserRole.OWNER.value
    ]

    return s.UsersListOut(users=users_out)


@user_router.put(
    "/language/{user_uuid}",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"description": "User not found"}},
)
def set_language(
    lang: s.Language,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set user language"""

    if not current_user:
        log(log.ERROR, "User [%s] not found", current_user.email)
        raise HTTPException(status_code=404, detail="User not found")

    current_user.preferred_language = lang.value
    db.commit()


@user_router.put(
    "/title-visual-profile/{user_uuid}",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def update_title_visual_profile(
    data: s.VisualProfileIn,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user's title visual profile"""

    movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == data.movie_key))
    if not movie:
        log(log.ERROR, "Movie [%s] not found", data.movie_key)
        raise HTTPException(status_code=404, detail="Movie not found")

    user_vp = next((vp for vp in movie.visual_profiles if vp.user_id == current_user.id), None)
    if not user_vp:
        log(log.ERROR, "User [%s] has no visual profile for movie [%s]", current_user.email, data.movie_key)
        raise HTTPException(status_code=404, detail="User has no visual profile for this movie")

    # Change category and its criteria
    if user_vp.category.key != data.category_key:
        category = db.scalar(sa.select(m.VisualProfileCategory).where(m.VisualProfileCategory.key == data.category_key))
        if not category:
            log(log.ERROR, "Category [%s] not found", data.category_key)
            raise HTTPException(status_code=404, detail="Category not found")

        user_vp.category_id = category.id
        user_vp.ratings.clear()

        for idx, criterion in enumerate(data.criteria):
            criterion_db = db.scalar(
                sa.select(m.VisualProfileCategoryCriterion).where(m.VisualProfileCategoryCriterion.key == criterion.key)
            )

            if not criterion_db:
                log(log.ERROR, "Criterion [%s] not found", criterion.key)
                raise HTTPException(status_code=404, detail="Criterion not found")

            new_rating = m.VisualProfileRating(
                title_visual_profile_id=user_vp.id,
                criterion_id=criterion_db.id,
                rating=criterion.rating,
                order=idx + 1,
            )
            db.add(new_rating)
        db.commit()
        log(log.DEBUG, "Title visual profile for movie [%s] updated with new category", data.movie_key)

    # Update existing criteria ratings
    else:
        # enumerate for order
        for idx, criterion in enumerate(data.criteria):
            criterion_db = db.scalar(
                sa.select(m.VisualProfileCategoryCriterion).where(m.VisualProfileCategoryCriterion.key == criterion.key)
            )

            if not criterion_db:
                log(log.ERROR, "Criterion [%s] not found", criterion.key)
                raise HTTPException(status_code=404, detail="Criterion not found")

            criterion_rating = db.scalar(
                sa.select(m.VisualProfileRating).where(
                    m.VisualProfileRating.title_visual_profile_id == user_vp.id,
                    m.VisualProfileRating.criterion_id == criterion_db.id,
                )
            )

            if not criterion_rating:
                log(log.ERROR, "Criterion rating for movie [%s] not found", data.movie_key)
                raise HTTPException(status_code=404, detail="Criterion rating not found")

            criterion_rating.rating = criterion.rating
            criterion_rating.order = idx + 1
            db.commit()

    log(log.DEBUG, "Title visual profile for movie [%s] updated", data.movie_key)
