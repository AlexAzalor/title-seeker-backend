import json
import os
from datetime import datetime
from random import randint
from typing import Annotated, Sequence

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
import sqlalchemy as sa
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, File, UploadFile

from sqlalchemy.orm import Session, aliased, joinedload

from api.controllers.create_movie import (
    QUICK_MOVIES_FILE,
    add_image_to_s3_bucket,
    add_poster_to_new_movie,
    add_new_characters,
    add_new_movie_rating,
    add_visual_profile,
    create_new_movie,
    get_movies_data_from_file,
    remove_quick_movie,
    set_percentage_match,
)

from api.controllers.movie_filters import get_filters
from api.dependency.user import get_admin, get_current_user
from api.utils import check_admin_permissions, extract_values, extract_word, get_error_message, normalize_query
import app.models as m
import app.schema as s
from app.database import get_db
from app.logger import log
from config import config

CFG = config()

movie_router = APIRouter(prefix="/movies", tags=["Movies"])

UPLOAD_DIRECTORY = "./uploads/posters/"

# fix
# if not os.path.exists(UPLOAD_DIRECTORY):
#     os.makedirs(UPLOAD_DIRECTORY)


@movie_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=Page[s.MoviePreviewOut],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def get_movies(
    # query: str = Query(default="", max_length=128),
    sort_by: s.SortBy = s.SortBy.RATED_AT,
    sort_order: s.SortOrder = s.SortOrder.DESC,
    current_user: m.User = Depends(get_current_user),
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
    params: Params = Depends(),
):
    """Get movies by query params"""

    is_reverse = sort_order == s.SortOrder.DESC

    print("------TEST------")

    def get_main_genre(movie: m.Movie) -> str:
        biggest_genre = db.scalar(
            sa.select(m.Genre)
            .join(m.movie_genres)
            .where(m.movie_genres.c.movie_id == movie.id)
            .order_by(m.movie_genres.c.percentage_match.desc())
            .limit(1)
        )

        if biggest_genre:
            genre_name = biggest_genre.get_name(lang)
            percentage_match = next(
                (
                    mg.percentage_match
                    for mg in db.query(m.movie_genres).filter_by(movie_id=movie.id, genre_id=biggest_genre.id)
                ),
                0.0,
            )
            return f"{genre_name} ({percentage_match}%)"
        return "No main genre"

    def rating_to_custom_schema(movies: Sequence[m.Rating]) -> Sequence[s.MoviePreviewOut]:
        return [
            s.MoviePreviewOut(
                key=movie.movie.key,
                title=movie.movie.get_title(lang),
                poster=movie.movie.poster,
                # TODO: fix none release date
                release_date=movie.movie.release_date if movie.movie.release_date else datetime.now(),
                duration=movie.movie.formatted_duration(lang.value),
                main_genre=get_main_genre(movie.movie),
                rating=next((t.rating for t in movie.movie.ratings if t.user_id == current_user.id), 0.0)
                if current_user
                else 0.0,
            )
            for movie in movies
        ]

    def movie_to_custom_schema(movies: Sequence[m.Movie]) -> Sequence[s.MoviePreviewOut]:
        return [
            s.MoviePreviewOut(
                key=movie.key,
                title=movie.get_title(lang),
                poster=movie.poster,
                # TODO: fix none release date
                release_date=movie.release_date if movie.release_date else datetime.now(),
                duration=movie.formatted_duration(lang.value),
                main_genre=get_main_genre(movie),
                rating=next((t.rating for t in movie.ratings if t.user_id == current_user.id), 0.0)
                if current_user
                else 0.0,
            )
            for movie in movies
        ]

    if current_user:
        if sort_by == s.SortBy.RATED_AT:
            rated_at = m.Rating.updated_at.desc() if is_reverse else m.Rating.updated_at.asc()
            base_rating_query = sa.select(m.Rating).where(m.Rating.user_id == current_user.id).order_by(rated_at)

        if sort_by == s.SortBy.RATING:
            rating = m.Rating.rating.desc() if is_reverse else m.Rating.rating.asc()
            base_rating_query = sa.select(m.Rating).where(m.Rating.user_id == current_user.id).order_by(rating)

        if sort_by == s.SortBy.RATINGS_COUNT:
            ratings_count = m.Movie.ratings_count.desc() if is_reverse else m.Movie.ratings_count.asc()
            base_rating_query = (
                sa.select(m.Rating)
                .join(m.Movie, m.Rating.movie)
                .where(m.Rating.user_id == current_user.id)
                .order_by(ratings_count)
            )

        if sort_by == s.SortBy.RELEASE_DATE:
            release_date = m.Movie.release_date.desc() if is_reverse else m.Movie.release_date.asc()
            # If you need to reuse the logic for accessing movie.release_date in multiple places, a @hybrid_property is a good choice. However, if this is a one-off query or performance is critical, using an explicit join is better.
            base_rating_query = (
                sa.select(m.Rating)
                .join(m.Movie, m.Rating.movie)
                .where(m.Rating.user_id == current_user.id)
                .order_by(release_date)
            )

        if sort_by == s.SortBy.RANDOM:
            base_rating_query = (
                sa.select(m.Rating).where(m.Rating.user_id == current_user.id).order_by(sa.func.random())
            )

        return paginate(db, base_rating_query, params, transformer=rating_to_custom_schema)

    if sort_by == s.SortBy.RELEASE_DATE:
        release_date = m.Movie.release_date.desc() if is_reverse else m.Movie.release_date.asc()
        base_query = (
            sa.select(m.Movie)
            .where(m.Movie.is_deleted.is_(False))
            .order_by(release_date)
            .options(joinedload(m.Movie.translations))
        )
    elif sort_by == s.SortBy.RANDOM:
        base_query = (
            sa.select(m.Movie)
            .where(m.Movie.is_deleted.is_(False))
            .order_by(sa.func.random())
            .options(joinedload(m.Movie.translations))
        )
    elif sort_by == s.SortBy.RATING:
        average_rating = m.Movie.average_rating.desc() if is_reverse else m.Movie.average_rating.asc()
        base_query = (
            sa.select(m.Movie)
            .where(m.Movie.is_deleted.is_(False))
            .order_by(average_rating)
            .options(joinedload(m.Movie.translations))
        )
    elif sort_by == s.SortBy.RATINGS_COUNT:
        ratings_count = m.Movie.ratings_count.desc() if is_reverse else m.Movie.ratings_count.asc()
        base_query = (
            sa.select(m.Movie)
            .where(m.Movie.is_deleted.is_(False))
            .order_by(ratings_count)
            .options(joinedload(m.Movie.translations))
        )
    else:
        by_id = m.Movie.id.desc() if is_reverse else m.Movie.id.asc()
        base_query = (
            sa.select(m.Movie)
            .where(m.Movie.is_deleted.is_(False))
            .order_by(by_id)
            .options(joinedload(m.Movie.translations))
        )

    return paginate(db, base_query, params, transformer=movie_to_custom_schema)


@movie_router.get(
    "/{movie_key}",
    status_code=status.HTTP_200_OK,
    response_model=s.MovieOut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Movie not found"},
    },
)
def get_movie(
    movie_key: str,
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get movie by key"""

    movie: m.Movie | None = db.scalar(
        sa.select(m.Movie)
        .where(m.Movie.key == movie_key)
        .options(
            # add rest?
            # Do I need to use joinedload() for all relationships? I get name from db function
            joinedload(m.Movie.translations),
            joinedload(m.Movie.actors),
            joinedload(m.Movie.directors),
            joinedload(m.Movie.genres),
            joinedload(m.Movie.subgenres),
            joinedload(m.Movie.specifications),
            joinedload(m.Movie.keywords),
            joinedload(m.Movie.action_times),
            joinedload(m.Movie.ratings),
            joinedload(m.Movie.shared_universe),
        )
    )

    if not movie:
        log(log.ERROR, "Movie [%s] not found", movie_key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    # separate route?
    user_rating = None
    if current_user:
        user_rating = db.scalar(
            sa.select(m.Rating).where(m.Rating.movie_id == movie.id).where(m.Rating.user_id == current_user.id)
        )

    owner = db.scalar(sa.select(m.User).where(m.User.role == s.UserRole.OWNER.value))
    if not owner:
        log(log.ERROR, "Owner not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")

    owner_rating = db.scalar(
        sa.select(m.Rating).where(m.Rating.movie_id == movie.id).where(m.Rating.user_id == owner.id)
    )
    if not owner_rating:
        log(log.ERROR, "Owner rating for movie [%s] not found", movie_key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner rating not found")

    visual_profile = None
    if current_user:
        visual_profile = movie.get_users_rating(current_user.id)

    return s.MovieOut(
        created_at=movie.created_at,
        key=movie.key,
        title=movie.get_title(lang),
        description=movie.get_description(lang),
        location=movie.get_location(lang),
        poster=movie.poster,
        budget=movie.formatted_budget,
        duration=movie.formatted_duration(lang.value),
        domestic_gross=movie.formatted_domestic_gross,
        worldwide_gross=movie.formatted_worldwide_gross,
        release_date=movie.release_date if movie.release_date else datetime.now(),
        # Visual Profile
        visual_profile=s.TitleVisualProfileOut(
            key=visual_profile.category.key,
            name=visual_profile.category.get_name(lang),
            description=visual_profile.category.get_description(lang),
            criteria=[
                s.Criterion(
                    key=title_rating.criterion.key,
                    name=title_rating.criterion.get_name(lang),
                    description=title_rating.criterion.get_description(lang),
                    rating=title_rating.rating,
                )
                for title_rating in sorted(visual_profile.ratings, key=lambda x: x.order)
            ],
        )
        if visual_profile
        else None,
        # Rating
        # All movies ratings
        ratings=[
            s.MovieRating(
                uuid=rating.uuid,
                rating=rating.rating,
                comment=rating.comment,
            )
            for rating in movie.ratings
        ],
        ratings_count=movie.ratings_count,
        # Rating Type
        rating_criterion=s.RatingCriterion(movie.rating_criterion),
        # Owner rating
        # owner_rating=owner_rating.rating,
        owner_rating=owner_rating.rating,
        # Main AVERAGE rating
        # The .get() method only returns the default value if the key does not exist in the dictionary. If the key exists but its value is None, .get() will return None instead of the default value.
        overall_average_rating=movie.average_rating,
        overall_average_rating_criteria=s.UserRatingCriteria(
            acting=movie.average_by_criteria.get("acting") or 0.01,
            # acting=movie.average_by_criteria.get("acting", 0.01),
            plot_storyline=movie.average_by_criteria.get("plot_storyline") or 0.01,
            script_dialogue=movie.average_by_criteria.get("script_dialogue") or 0.01,
            music=movie.average_by_criteria.get("music") or 0.01,
            enjoyment=movie.average_by_criteria.get("enjoyment") or 0.01,
            production_design=movie.average_by_criteria.get("production_design") or 0.01,
            visual_effects=movie.average_by_criteria.get("visual_effects"),
            scare_factor=movie.average_by_criteria.get("scare_factor"),
            humor=movie.average_by_criteria.get("humor"),
            animation_cartoon=movie.average_by_criteria.get("animation_cartoon"),
        ),
        # User rating
        user_rating=user_rating.rating if user_rating and current_user.id != owner.id else None,
        user_rating_criteria=s.UserRatingCriteria(
            acting=user_rating.acting,
            plot_storyline=user_rating.plot_storyline,
            script_dialogue=user_rating.script_dialogue,
            music=user_rating.music,
            enjoyment=user_rating.enjoyment,
            production_design=user_rating.production_design,
            visual_effects=user_rating.visual_effects
            if movie.rating_criterion == s.RatingCriterion.VISUAL_EFFECTS.value
            else None,
            scare_factor=user_rating.scare_factor
            if movie.rating_criterion == s.RatingCriterion.SCARE_FACTOR.value
            else None,
            humor=user_rating.humor if movie.rating_criterion == s.RatingCriterion.HUMOR.value else None,
            animation_cartoon=user_rating.animation_cartoon
            if movie.rating_criterion == s.RatingCriterion.ANIMATION_CARTOON.value
            else None,
        )
        if user_rating
        else None,
        actors=[
            s.MovieActor(
                key=char.actor.key,
                full_name=char.actor.full_name(lang),
                character_name=char.character.get_name(lang),
                avatar_url=char.actor.avatar,
            )
            for char in sorted(movie.characters, key=lambda x: x.order)
        ],
        directors=[
            s.MovieDirector(
                key=director.key,
                full_name=director.full_name(lang),
                avatar_url=director.avatar,
            )
            for director in movie.directors
        ],
        genres=[
            s.MovieFilterItem(
                key=genre.key,
                name=genre.get_name(lang),
                description=genre.get_description(lang),
                percentage_match=next(
                    (
                        mg.percentage_match
                        for mg in db.query(m.movie_genres).filter_by(movie_id=movie.id, genre_id=genre.id)
                    ),
                    0.0,
                ),
            )
            for genre in movie.genres
        ],
        subgenres=[
            s.MovieFilterItem(
                key=subgenre.key,
                parent_genre=s.MovieFilterItem(
                    key=subgenre.genre.key,
                    name=subgenre.genre.get_name(lang),
                    description=subgenre.genre.get_description(lang),
                    percentage_match=next(
                        (
                            mg.percentage_match
                            for mg in db.query(m.movie_genres).filter_by(movie_id=movie.id, genre_id=subgenre.genre.id)
                        ),
                        0.0,
                    ),
                ),
                name=subgenre.get_name(lang),
                description=subgenre.get_description(lang),
                percentage_match=next(
                    (
                        mg.percentage_match
                        for mg in db.query(m.movie_subgenres).filter_by(movie_id=movie.id, subgenre_id=subgenre.id)
                    ),
                    0.0,
                ),
            )
            for subgenre in movie.subgenres
        ],
        specifications=[
            s.MovieFilterItem(
                key=specification.key,
                name=specification.get_name(lang),
                description=specification.get_description(lang),
                percentage_match=next(
                    (
                        mg.percentage_match
                        for mg in db.query(m.movie_specifications).filter_by(
                            movie_id=movie.id, specification_id=specification.id
                        )
                    ),
                    0.0,
                ),
            )
            for specification in movie.specifications
        ],
        keywords=[
            s.MovieFilterItem(
                key=keyword.key,
                name=keyword.get_name(lang),
                description=keyword.get_description(lang),
                percentage_match=next(
                    (
                        mg.percentage_match
                        for mg in db.query(m.movie_keywords).filter_by(movie_id=movie.id, keyword_id=keyword.id)
                    ),
                    0.0,
                ),
            )
            for keyword in movie.keywords
        ],
        action_times=[
            s.MovieFilterItem(
                key=action_time.key,
                name=action_time.get_name(lang),
                description=action_time.get_description(lang),
                percentage_match=next(
                    (
                        mg.percentage_match
                        for mg in db.query(m.movie_action_times).filter_by(
                            movie_id=movie.id, action_time_id=action_time.id
                        )
                    ),
                    0.0,
                ),
            )
            for action_time in movie.action_times
        ],
        related_movies=[
            s.RelatedMovieOut(
                key=related_movie.key,
                poster=related_movie.poster,
                title=related_movie.get_title(lang),
                relation_type=s.RelatedMovie(related_movie.relation_type),
            )
            for related_movie in movie.related_movies_collection
        ]
        if movie.relation_type
        else None,
        shared_universe_order=movie.shared_universe_order,
        shared_universe=s.SharedUniverseOut(
            key=movie.shared_universe.key,
            name=movie.shared_universe.get_name(lang),
            description=movie.shared_universe.get_description(lang),
            movies=[
                s.SharedUniverseMovies(
                    key=shared_movie.key,
                    title=shared_movie.get_title(lang),
                    poster=shared_movie.poster,
                    order=shared_movie.shared_universe_order,
                )
                for shared_movie in movie.shared_universe.get_sorted_movies()
            ],
        )
        if movie.shared_universe
        else None,
    )


@movie_router.get(
    "/super-search/",
    status_code=status.HTTP_200_OK,
    response_model=Page[s.MoviePreviewOut],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def super_search_movies(
    # query: str = Query(default="", max_length=128),
    genre: Annotated[list[str], Query()] = [],
    subgenre: Annotated[list[str], Query()] = [],
    specification: Annotated[list[str], Query()] = [],
    keyword: Annotated[list[str], Query()] = [],
    action_time: Annotated[list[str], Query()] = [],
    actor: Annotated[list[str], Query()] = [],
    director: Annotated[list[str], Query()] = [],
    universe: Annotated[list[str], Query()] = [],
    exact_match: Annotated[bool, Query()] = False,
    sort_by: s.SortBy = s.SortBy.RATED_AT,
    sort_order: s.SortOrder = s.SortOrder.DESC,
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    params: Params = Depends(),
):
    """Get movies by query params"""

    def get_main_genre(movie: m.Movie) -> str:
        biggest_genre = db.scalar(
            sa.select(m.Genre)
            .join(m.movie_genres)
            .where(m.movie_genres.c.movie_id == movie.id)
            .order_by(m.movie_genres.c.percentage_match.desc())
            .limit(1)
        )

        if biggest_genre:
            genre_name = biggest_genre.get_name(lang)
            percentage_match = next(
                (
                    mg.percentage_match
                    for mg in db.query(m.movie_genres).filter_by(movie_id=movie.id, genre_id=biggest_genre.id)
                ),
                0.0,
            )
            return f"{genre_name} ({percentage_match}%)"
        return "No main genre"

    def movie_to_custom_schema(movies: Sequence[m.Movie]) -> Sequence[s.MoviePreviewOut]:
        return [
            s.MoviePreviewOut(
                key=movie.key,
                title=movie.get_title(lang),
                poster=movie.poster,
                # TODO: fix none release date
                release_date=movie.release_date if movie.release_date else datetime.now(),
                duration=movie.formatted_duration(lang.value),
                main_genre=get_main_genre(movie),
                rating=next((t.rating for t in movie.ratings if t.user_id == current_user.id), 0.0)
                if current_user
                else 0.0,
            )
            for movie in movies
        ]

    query = sa.select(m.Movie).options(joinedload(m.Movie.translations))

    # condition = lambda x: x > 5
    # filtered = list(filter(condition, [1,2,3,4,5,6,7,8,9,10]))

    genres_keys = extract_word(genre)
    genres_values: list[list[int]] = extract_values(genre)

    if genres_keys:
        db_g_keys = db.scalars(sa.select(m.Genre.key).where(m.Genre.key.in_(genres_keys))).all()
        if len(db_g_keys) != len(genres_keys):
            log(log.ERROR, "Genres [%s] not found", genres_keys)
            raise HTTPException(status_code=404, detail="Genres not found")

    subgenres_keys: list[str] = extract_word(subgenre)
    subgenres_values: list[list[int]] = extract_values(subgenre)

    if subgenres_keys:
        db_sg_keys = db.scalars(sa.select(m.Subgenre.key).where(m.Subgenre.key.in_(subgenres_keys))).all()
        if len(db_sg_keys) != len(subgenres_keys):
            log(log.ERROR, "Subgenres [%s] not found", subgenres_keys)
            raise HTTPException(status_code=404, detail="Subgenres not found")

    specifications_keys: list[str] = extract_word(specification)
    specifications_values = extract_values(specification)

    if specifications_keys:
        db_s_keys = db.scalars(sa.select(m.Specification.key).where(m.Specification.key.in_(specifications_keys))).all()
        if len(db_s_keys) != len(specifications_keys):
            log(log.ERROR, "Specifications [%s] not found", specifications_keys)
            raise HTTPException(status_code=404, detail="Specifications not found")

    keywords_keys: list[str] = extract_word(keyword)
    keywords_values = extract_values(keyword)

    if keywords_keys:
        db_k_keys = db.scalars(sa.select(m.Keyword.key).where(m.Keyword.key.in_(keywords_keys))).all()
        if len(db_k_keys) != len(keywords_keys):
            log(log.ERROR, "Keyword(s) [%s] not found", keywords_keys)
            raise HTTPException(status_code=404, detail="Keywords not found")

    action_times_keys: list[str] = extract_word(action_time)
    action_times_values = extract_values(action_time)

    if action_times_keys:
        db_at_keys = db.scalars(sa.select(m.ActionTime.key).where(m.ActionTime.key.in_(action_times_keys))).all()
        if len(db_at_keys) != len(action_times_keys):
            log(log.ERROR, "Action times [%s] not found", action_times_keys)
            raise HTTPException(status_code=404, detail="Action times not found")

    if universe:
        db_su_keys = db.scalars(sa.select(m.SharedUniverse.key).where(m.SharedUniverse.key.in_(universe))).all()
        if not db_su_keys:
            log(log.ERROR, "Shared Universe(s) [%s] not found", universe)
            raise HTTPException(status_code=404, detail="Shared Universe(s) not found")

    # What Happens to the Query at Each Filter Step?
    # It is augmented, not replaced.
    # Each call to query.where() appends additional conditions, effectively adding AND logic to the query.
    # Both genre and subgenre conditions are combined, meaning that the final query will only return movies that satisfy both filters (if both are provided).

    logical_op = sa.and_ if exact_match else sa.or_

    if genres_keys:
        query = query.where(logical_op(*[m.Movie.genres.any(m.Genre.key == genre_key) for genre_key in genres_keys]))

        if genres_values:
            conditions = [
                m.Movie.genres.any(
                    sa.and_(
                        m.Genre.key == genre_key,
                        m.movie_genres.c.percentage_match >= value_range[0],
                        m.movie_genres.c.percentage_match <= value_range[1],
                    )
                )
                for genre_key, value_range in zip(genres_keys, genres_values)
                if value_range
            ]

            query = query.where(logical_op(*conditions))

    # Filter only by subgenre
    if subgenres_keys:
        query = query.where(
            logical_op(*[m.Movie.subgenres.any(m.Subgenre.key == subgenre_key) for subgenre_key in subgenres_keys])
        )

        if subgenres_values:
            conditions = [
                m.Movie.subgenres.any(
                    sa.and_(
                        m.Subgenre.key == subgenre_key,
                        m.movie_subgenres.c.percentage_match >= value_range[0],
                        m.movie_subgenres.c.percentage_match <= value_range[1],
                    )
                )
                for subgenre_key, value_range in zip(subgenres_keys, subgenres_values)
                if value_range
            ]

            query = query.where(logical_op(*conditions))

    if specifications_keys:
        query = query.where(
            logical_op(
                *[
                    m.Movie.specifications.any(m.Specification.key == specification_key)
                    for specification_key in specifications_keys
                ]
            )
        )

        if specifications_values:
            conditions = [
                m.Movie.specifications.any(
                    sa.and_(
                        m.Specification.key == specification_key,
                        m.movie_specifications.c.percentage_match >= value_range[0],
                        m.movie_specifications.c.percentage_match <= value_range[1],
                    )
                )
                for specification_key, value_range in zip(specifications_keys, specifications_values)
                if value_range
            ]

            query = query.where(logical_op(*conditions))

    if keywords_keys:
        query = query.where(
            logical_op(*[m.Movie.keywords.any(m.Keyword.key == keyword_key) for keyword_key in keywords_keys])
        )

        if keywords_keys:
            conditions = [
                m.Movie.keywords.any(
                    sa.and_(
                        m.Keyword.key == keyword_key,
                        m.movie_keywords.c.percentage_match >= value_range[0],
                        m.movie_keywords.c.percentage_match <= value_range[1],
                    )
                )
                for keyword_key, value_range in zip(keywords_keys, keywords_values)
                if value_range
            ]

            query = query.where(logical_op(*conditions))

    if action_times_keys:
        query = query.where(
            logical_op(
                *[
                    m.Movie.action_times.any(m.ActionTime.key == action_time_key)
                    for action_time_key in action_times_keys
                ]
            )
        )

        if action_times_values:
            conditions = [
                m.Movie.action_times.any(
                    sa.and_(
                        m.ActionTime.key == action_time_key,
                        m.movie_action_times.c.percentage_match >= value_range[0],
                        m.movie_action_times.c.percentage_match <= value_range[1],
                    )
                )
                for action_time_key, value_range in zip(action_times_keys, action_times_values)
                if value_range
            ]

            query = query.where(logical_op(*conditions))

    if actor:
        query = query.where(logical_op(*[m.Movie.actors.any(m.Actor.key == actor_key) for actor_key in actor]))

    if director:
        query = query.where(m.Movie.directors.any(m.Director.key.in_(director)))

    if universe:
        query = query.where(
            logical_op(*[m.Movie.shared_universe.has(m.SharedUniverse.key == su_key) for su_key in universe])
        )

    is_reverse = sort_order == s.SortOrder.DESC
    if sort_by == s.SortBy.RELEASE_DATE:
        release_date = m.Movie.release_date.desc() if is_reverse else m.Movie.release_date.asc()
        query = query.order_by(release_date)
    elif sort_by == s.SortBy.RANDOM:
        query = query.order_by(sa.func.random())
    elif sort_by == s.SortBy.RATING:
        average_rating = m.Movie.average_rating.desc() if is_reverse else m.Movie.average_rating.asc()
        query = query.order_by(average_rating)
    elif sort_by == s.SortBy.RATINGS_COUNT:
        ratings_count = m.Movie.ratings_count.desc() if is_reverse else m.Movie.ratings_count.asc()
        query = query.order_by(ratings_count)
    else:
        by_id = m.Movie.id.desc() if is_reverse else m.Movie.id.asc()
        query = query.order_by(by_id)

    return paginate(db, query, params, transformer=movie_to_custom_schema)


@movie_router.get(
    "/search/",
    status_code=status.HTTP_200_OK,
    response_model=s.MovieSearchResult,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def search(
    query: str = Query(default="", max_length=128),
    title_type: s.TitleType = s.TitleType.MOVIES,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Search titles by query"""

    if title_type != s.TitleType.MOVIES:
        log(log.ERROR, "Title type [%s] not supported", title_type)
        raise HTTPException(status_code=404, detail="Title type not supported")

    normalized_query = normalize_query(query)

    movies_db = (
        db.scalars(
            sa.select(m.Movie)
            .where(m.Movie.is_deleted.is_(False))
            .where(
                m.Movie.translations.any(
                    sa.func.regexp_replace(
                        sa.func.lower(m.MovieTranslation.title), r"[^a-zA-Zа-яА-Я0-9 ]", "", "g"
                    ).ilike(f"%{normalized_query}%")
                )
            )
            .limit(5)
            .options(joinedload(m.Movie.translations))
        )
        .unique()
        .all()
    )
    movies_out = []
    if movies_db:
        for movie in movies_db:
            biggest_genre = db.scalar(
                sa.select(m.Genre)
                .join(m.movie_genres)
                .where(m.movie_genres.c.movie_id == movie.id)
                .order_by(m.movie_genres.c.percentage_match.desc())
                .limit(1)
            )

            main_genre = "No genre"
            if biggest_genre:
                genre_name = biggest_genre.get_name(lang)
                percentage_match = next(
                    (
                        mg.percentage_match
                        for mg in db.query(m.movie_genres).filter_by(movie_id=movie.id, genre_id=biggest_genre.id)
                    ),
                    0.0,
                )
                main_genre = f"{genre_name} ({percentage_match}%)"
            movies_out.append(
                s.MovieSearchOut(
                    key=movie.key,
                    title_en=movie.get_title(s.Language.EN),
                    title_uk=movie.get_title(s.Language.UK),
                    poster=movie.poster,
                    release_date=movie.release_date if movie.release_date else datetime.now(),
                    duration=movie.formatted_duration(lang.value),
                    main_genre=main_genre,
                )
            )

    return s.MovieSearchResult(
        movies=movies_out,
    )


@movie_router.get("/filters/", status_code=status.HTTP_200_OK, response_model=s.MovieFiltersListOut)
def get_movie_filters(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all movie filters"""

    genres_out, specifications_out, keywords_out, action_times_out, actors_out, directors_out = get_filters(db, lang)

    # TODO: Fix this
    subgenres = db.scalars(
        sa.select(m.Subgenre)
        .join(m.Subgenre.translations)
        .where(m.SubgenreTranslation.language == lang.value)
        .order_by(m.SubgenreTranslation.name)
    ).all()
    if not subgenres:
        log(log.ERROR, "Subgenre [%s] not found")
        raise HTTPException(status_code=404, detail="Subgenre not found")

    subgenres_out = [
        s.SubgenreOut(
            key=subgenre.key,
            name=subgenre.get_name(lang),
            description=subgenre.get_description(lang),
            parent_genre_key=subgenre.genre.key,
        )
        for subgenre in subgenres
    ]

    return s.MovieFiltersListOut(
        genres=genres_out,
        subgenres=subgenres_out,
        actors=actors_out,
        directors=directors_out,
        specifications=specifications_out,
        keywords=keywords_out,
        action_times=action_times_out,
    )


@movie_router.get(
    "/pre-create/",
    response_model=s.MoviePreCreateData,
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Data not found"}},
)
def get_pre_create_data(
    quick_movie_key: str | None = None,
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get pre-create data for a new movie"""

    if current_user.role != s.UserRole.OWNER.value:
        log(log.ERROR, "Only owner allowed to add movie")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner allowed to add movie")

    genres_out, specifications_out, keywords_out, action_times_out, actors_out, directors_out = get_filters(db, lang)

    # Order by natural order of RelatedMovie
    base_movies = db.scalars(
        sa.select(m.Movie)
        .join(m.Movie.translations)
        .where(m.MovieTranslation.language == lang.value)
        .where(m.Movie.is_deleted.is_(False))
        .order_by(
            # Ignore "The" at the beginning of the title (not remove)
            sa.func.regexp_replace(m.MovieTranslation.title, r"^(The\s)", "", "i"),
            m.Movie.relation_type,
        )
    ).all()
    if not base_movies:
        log(log.ERROR, "Base movies not found")
        raise HTTPException(status_code=404, detail="Base movies not found")

    # TODO: add full_name as hybrid_property?
    shared_universes = db.scalars(
        sa.select(m.SharedUniverse)
        .join(m.SharedUniverse.translations)
        .where(m.SharedUniverseTranslation.language == lang.value)
        .order_by(m.SharedUniverseTranslation.name)
    ).all()
    if not shared_universes:
        log(log.ERROR, "Shared universes [%s] not found")
        raise HTTPException(status_code=404, detail="Shared universes not found")

    characters = db.scalars(
        sa.select(m.Character)
        .join(m.Character.translations)
        .where(m.CharacterTranslation.language == lang.value)
        .order_by(m.CharacterTranslation.name)
    ).all()
    if not characters:
        log(log.ERROR, "Characters [%s] not found")
        raise HTTPException(status_code=404, detail="Characters not found")

    base_movies_out = [
        s.MovieOutShort(
            key=base_movie.key,
            name=base_movie.get_title(lang),
        )
        for base_movie in base_movies
    ]

    categories = db.scalars(
        sa.select(m.TitleCategory)
        .join(m.TitleCategory.translations)
        .where(m.TitleCategoryTranslation.language == lang.value)
        .order_by(m.TitleCategoryTranslation.name)
    ).all()
    if not categories:
        log(log.ERROR, "Title categories not found")
        raise HTTPException(status_code=404, detail="Title categories not found")

    categories_out = [
        s.TitleCategoryData(
            key=category.key,
            name=category.get_name(lang),
            description=category.get_description(lang),
            criteria=[
                s.CategoryCriterionData(
                    key=criterion.key,
                    name=criterion.get_name(lang),
                    description=criterion.get_description(lang),
                    rating=0,
                )
                for criterion in category.criteria
            ],
        )
        for category in categories
    ]

    quick_movie = None

    if quick_movie_key:
        if os.path.exists(QUICK_MOVIES_FILE):
            movies = get_movies_data_from_file()

            if movies:
                for movie in movies:
                    if movie.key == quick_movie_key:
                        quick_movie = s.QuickMovieFormData(
                            key=movie.key,
                            title_en=movie.title_en,
                            rating=movie.rating,
                            rating_criterion_type=movie.rating_criterion_type,
                            rating_criteria=movie.rating_criteria,
                        )

    shared_universes_out = [
        s.SharedUniversePreCreateOut(
            key=universe.key,
            name=universe.get_name(lang),
            description=universe.get_description(lang),
        )
        for universe in shared_universes
    ]

    characters_out = [
        s.CharacterOut(
            key=character.key,
            name=character.get_name(lang),
        )
        for character in characters
    ]

    return s.MoviePreCreateData(
        title_categories=categories_out,
        base_movies=base_movies_out,
        actors=actors_out,
        directors=directors_out,
        specifications=specifications_out,
        genres=genres_out,
        keywords=keywords_out,
        action_times=action_times_out,
        quick_movie=quick_movie,
        shared_universes=shared_universes_out,
        characters=characters_out,
    )


@movie_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Movie already exists"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Error with type VALIDATION"},
    },
)
def create_movie(
    form_data: Annotated[s.MovieFormData, Body(...)],
    file: UploadFile = File(None),
    lang: s.Language = s.Language.UK,
    is_quick_movie: bool = Query(default=False),
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new movie"""

    if current_user.role != s.UserRole.OWNER.value:
        log(log.ERROR, "Only owner allowed to add movie")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner allowed to add movie")

    if db.scalar(sa.select(m.Movie).where(m.Movie.key == form_data.key)):
        message = get_error_message(lang, "Фільм вже існує", "Movie already exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)

    try:
        new_movie = create_new_movie(db, form_data)
        db.add(new_movie)
        # Flush need to get new_movie ID but not commit new data to DB, for rollback (in case of error)
        db.flush()

        if CFG.ENV == "production":
            file_name = f"{new_movie.id}_{file.filename}"
            new_movie.poster = file_name
            add_image_to_s3_bucket(file, "posters", file_name)
        else:
            add_poster_to_new_movie(new_movie, file, UPLOAD_DIRECTORY)

        set_percentage_match(new_movie.id, db, form_data)

        add_new_characters(new_movie.id, db, form_data.actors_keys)

        add_new_movie_rating(new_movie, db, current_user.id, form_data)

        add_visual_profile(
            form_data.category_key,
            form_data.category_criteria,
            new_movie.id,
            current_user.id,
            db,
        )

        if is_quick_movie:
            remove_quick_movie(form_data.key)

        db.commit()
        log(log.INFO, "Movie [%s] successfully created", form_data.key)
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error creating movie [%s]: %s", form_data.key, e)
        error_message = get_error_message(lang, "Помилка створення фільму", "Error creating movie")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{error_message} - {e}")


@movie_router.post(
    "/quick-add/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Movie already exists"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Error with type VALIDATION"},
    },
)
def quick_add_movie(
    form_data: s.QuickMovieFormData,
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """For quick and temporary adding of new movies in a JSON file.
    Then these data will be used to fully add the movie to the database."""

    if current_user.role != s.UserRole.OWNER.value:
        log(log.ERROR, "Only owner allowed to add movie")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner allowed to add movie")

    if db.scalar(sa.select(m.Movie).where(m.Movie.key == form_data.key)):
        message = get_error_message(lang, "Фільм вже існує", "Movie already exists")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)

    try:
        movies = get_movies_data_from_file()

        movies_to_file = [form_data]

        if movies:
            keys = [movie.key for movie in movies]

            if form_data.key in keys:
                message = get_error_message(lang, "Фільм вже існує", "Movie already exists")
                log(log.ERROR, "Movie [%s] already exists", form_data.key)
                raise Exception(message)

            # Add new movie to existing movies
            movies_to_file += movies

        with open(QUICK_MOVIES_FILE, "w") as file:
            json.dump(s.QuickMovieJSON(movies=movies_to_file).model_dump(mode="json"), file, indent=4)

        log(log.INFO, "Movie [%s] successfully created", form_data.key)

    except Exception as e:
        log(log.ERROR, "Error adding movie to JSON [%s]: %s", form_data.key, e)
        error_message = get_error_message(lang, "Помилка додавання фільму до JSON", "Error adding movie to JSON")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{error_message} - {e}")


@movie_router.get(
    "/random/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.MovieCarouselList,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Movie already exists"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Error with type VALIDATION"},
    },
)
def get_random_list(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get 10 random movies"""

    # Get the total number of movies
    total_movies = db.scalar(sa.select(sa.func.count()).select_from(m.Movie))

    if not total_movies:
        log(log.ERROR, "Movies not found")
        raise HTTPException(status_code=404, detail="Movies not found")

    # Generate a random offset
    random_offset = randint(0, max(0, total_movies - 10))

    # Select 10 random movies using the random offset
    movies_db = (
        db.scalars(
            sa.select(m.Movie)
            .offset(random_offset)
            .limit(10)
            .options(
                joinedload(m.Movie.translations),
                joinedload(m.Movie.genres),
                joinedload(m.Movie.actors),
                joinedload(m.Movie.directors),
            )
        )
        .unique()
        .all()
    )

    movies_out = []
    for movie in movies_db:
        movies_out.append(
            s.MovieCarousel(
                key=movie.key,
                title=next((t.title for t in movie.translations if t.language == lang.value)),
                poster=movie.poster,
                release_date=movie.release_date if movie.release_date else datetime.now(),
                duration=movie.formatted_duration(lang.value),
                # main_genre=main_genre,
                location=next((t.location for t in movie.translations if t.language == lang.value)),
                description=next((t.description for t in movie.translations if t.language == lang.value)),
                genres=[
                    s.MovieGenre(
                        key=genre.key,
                        name=next((t.name for t in genre.translations if t.language == lang.value)),
                        description=next((t.description for t in genre.translations if t.language == lang.value)),
                        percentage_match=next(
                            (
                                mg.percentage_match
                                for mg in db.query(m.movie_genres).filter_by(movie_id=movie.id, genre_id=genre.id)
                            ),
                            0.0,
                        ),
                    )
                    for genre in movie.genres
                ],
                actors=[
                    s.ActorSimple(
                        key=actor.key,
                        full_name=actor.full_name(lang),
                        avatar_url=actor.avatar,
                    )
                    for actor in movie.actors
                ],
                directors=[
                    s.DirectorSimple(
                        key=director.key,
                        full_name=director.full_name(lang),
                        avatar_url=director.avatar if director.avatar else "",
                    )
                    for director in movie.directors
                ],
            ),
        )

    return s.MovieCarouselList(
        movies=movies_out,
    )


@movie_router.get(
    "/similar/",
    status_code=status.HTTP_200_OK,
    response_model=s.SimilarMovieOutList,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def get_similar_movies(
    movie_key: str,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get similar movies by movie key"""

    # TODO: Update and improve db query when adding more movies (100-200)

    movie: m.Movie | None = db.scalar(
        sa.select(m.Movie)
        .where(m.Movie.key == movie_key)
        .options(
            joinedload(m.Movie.translations),
            joinedload(m.Movie.genres),
            joinedload(m.Movie.subgenres),
        )
    )

    if not movie:
        log(log.ERROR, "Movie [%s] not found", movie_key)
        raise HTTPException(status_code=404, detail="Movie not found")

    genres_list = [
        s.MovieFilterItem(
            key=genre.key,
            name=next((t.name for t in genre.translations if t.language == lang.value)),
            description=next((t.description for t in genre.translations if t.language == lang.value)),
            percentage_match=next(
                (
                    mg.percentage_match
                    for mg in db.query(m.movie_genres).filter_by(movie_id=movie.id, genre_id=genre.id)
                ),
                0.0,
            ),
        )
        for genre in movie.genres
    ]

    subgenres_list = [
        s.MovieFilterItem(
            key=subgenre.key,
            parent_genre=s.MovieFilterItem(
                key=subgenre.genre.key,
                name=next((t.name for t in subgenre.genre.translations if t.language == lang.value)),
                description=next((t.description for t in subgenre.genre.translations if t.language == lang.value)),
                percentage_match=next(
                    (
                        mg.percentage_match
                        for mg in db.query(m.movie_genres).filter_by(movie_id=movie.id, genre_id=subgenre.genre.id)
                    ),
                    0.0,
                ),
            ),
            name=next((t.name for t in subgenre.translations if t.language == lang.value)),
            description=next((t.description for t in subgenre.translations if t.language == lang.value)),
            percentage_match=next(
                (
                    mg.percentage_match
                    for mg in db.query(m.movie_subgenres).filter_by(movie_id=movie.id, subgenre_id=subgenre.id)
                ),
                0.0,
            ),
        )
        for subgenre in movie.subgenres
    ]

    specifications_list = [
        s.MovieFilterItem(
            key=specification.key,
            name=next((t.name for t in specification.translations if t.language == lang.value)),
            description=next((t.description for t in specification.translations if t.language == lang.value)),
            percentage_match=next(
                (
                    mg.percentage_match
                    for mg in db.query(m.movie_specifications).filter_by(
                        movie_id=movie.id, specification_id=specification.id
                    )
                ),
                0.0,
            ),
        )
        for specification in movie.specifications
    ]

    keywords_list = [
        s.MovieFilterItem(
            key=keyword.key,
            name=next((t.name for t in keyword.translations if t.language == lang.value)),
            description=next((t.description for t in keyword.translations if t.language == lang.value)),
            percentage_match=next(
                (
                    mg.percentage_match
                    for mg in db.query(m.movie_keywords).filter_by(movie_id=movie.id, keyword_id=keyword.id)
                ),
                0.0,
            ),
        )
        for keyword in movie.keywords
    ]

    # action_times_list = [
    #         s.MovieActionTime(
    #             key=action_time.key,
    #             name=next((t.name for t in action_time.translations if t.language == lang.value)),
    #             description=next((t.description for t in action_time.translations if t.language == lang.value)),
    #             percentage_match=next(
    #                 (
    #                     mg.percentage_match
    #                     for mg in db.query(m.movie_action_times).filter_by(
    #                         movie_id=movie.id, action_time_id=action_time.id
    #                     )
    #                 ),
    #                 0.0,
    #             ),
    #         )
    #         for action_time in movie.action_times
    #     ]

    biggest_genres = db.scalars(
        sa.select(m.Genre)
        .join(m.movie_genres)
        .where(m.movie_genres.c.movie_id == movie.id)
        .order_by(m.movie_genres.c.percentage_match.desc())
    ).all()
    # biggest_subgenres = db.scalars(
    #         sa.select(m.Subgenre)
    #         .join(m.movie_subgenres)
    #         .where(m.movie_subgenres.c.movie_id == movie.id)
    #         .order_by(m.movie_subgenres.c.percentage_match.desc())
    #     ).all()

    max_genre_percentage_match = 0

    for item in biggest_genres:
        percentage_match = next(
            (mg.percentage_match for mg in db.query(m.movie_genres).filter_by(movie_id=movie.id, genre_id=item.id)),
            0.0,
        )
        if percentage_match == 100:
            max_genre_percentage_match += 1

    min_range = 10
    max_range = 10

    if len(biggest_genres) > 1:
        max_range = 20
        min_range = 20

    if max_genre_percentage_match == 1:
        max_range = 0
        min_range = 15

    if max_genre_percentage_match == 2:
        max_range = 0
        min_range = 20

    if max_genre_percentage_match >= 3:
        max_range = 0
        min_range = 25

    mg = aliased(m.movie_genres)
    ms = aliased(m.movie_subgenres)
    mspec = aliased(m.movie_specifications)
    mkw = aliased(m.movie_keywords)
    # mact = aliased(m.movie_action_times)
    g = aliased(m.Genre)
    sg = aliased(m.Subgenre)
    spec = aliased(m.Specification)
    kw = aliased(m.Keyword)
    # act = aliased(m.ActionTime)

    genre_conditions = []
    subgenre_conditions = []
    spec_conditions = []
    keyword_conditions = []
    # action_time_conditions = []

    # Dynamically add genre conditions
    for genre in genres_list:
        genre_conditions.append(
            sa.exists().where(
                sa.and_(
                    mg.c.movie_id == m.Movie.id,
                    mg.c.genre_id == g.id,
                    g.key == genre.key,
                    # movie >= 50 (current movie)
                    mg.c.percentage_match >= genre.percentage_match - min_range,
                    # movie <= 100 (current movie)
                    mg.c.percentage_match <= genre.percentage_match + max_range,
                )
            )
        )

    # Dynamically add subgenre conditions
    for subgenre in subgenres_list:
        subgenre_conditions.append(
            sa.exists().where(
                sa.and_(
                    ms.c.movie_id == m.Movie.id,
                    ms.c.subgenre_id == sg.id,
                    sg.key == subgenre.key,
                    ms.c.percentage_match >= subgenre.percentage_match - 10,
                    ms.c.percentage_match <= subgenre.percentage_match + 10,
                )
            )
        )

    # Ensure at least one genre and one subgenre match
    stmt = sa.select(m.Movie).where(
        m.Movie.id != movie.id,  # Exclude the current movie
        m.Movie.key.not_in([m.key for m in movie.related_movies_collection]),  # Exclude specific movies
        sa.and_(
            sa.or_(*genre_conditions)
            if genre_conditions
            else sa.literal(True),  # If genres are provided, at least one must match
            sa.or_(*subgenre_conditions)
            if subgenre_conditions
            else sa.literal(True),  # If subgenres are provided, at least one must match
        ),
    )

    similar_movies = db.execute(stmt).scalars().all()

    if len(similar_movies) == 0:
        for spec_item in specifications_list:
            spec_conditions.append(
                sa.exists().where(
                    sa.and_(
                        mspec.c.movie_id == m.Movie.id,
                        mspec.c.specification_id == spec.id,
                        spec.key == spec_item.key,
                        mspec.c.percentage_match >= spec_item.percentage_match - 10,
                        mspec.c.percentage_match <= spec_item.percentage_match + 10,
                    )
                )
            )

        for k in keywords_list:
            keyword_conditions.append(
                sa.exists().where(
                    sa.and_(
                        mkw.c.movie_id == m.Movie.id,
                        mkw.c.keyword_id == kw.id,
                        kw.key == k.key,
                        mkw.c.percentage_match >= k.percentage_match - 10,
                        mkw.c.percentage_match <= k.percentage_match + 10,
                    )
                )
            )

        # for a in action_times_list:
        #     action_time_conditions.append(
        #         sa.exists().where(
        #             sa.and_(
        #                 mact.c.movie_id == m.Movie.id,
        #                 mact.c.action_time_id == act.id,
        #                 act.key == a.key,
        #                 mact.c.percentage_match >= a.percentage_match - 10,
        #                 mact.c.percentage_match <= a.percentage_match + 10,
        #             )
        #         )
        #     )

        stmt = sa.select(m.Movie).where(
            m.Movie.id != movie.id,
            m.Movie.key.not_in([m.key for m in movie.related_movies_collection]),
            sa.and_(
                sa.or_(*genre_conditions) if genre_conditions else sa.literal(True),
                # sa.or_(*subgenre_conditions)
                # if subgenre_conditions
                # else sa.literal(True),
                # sa.or_(*spec_conditions)
                # if spec_conditions
                # else sa.literal(True),
                # sa.or_(*keyword_conditions)
                # if keyword_conditions
                # else sa.literal(True),
            ),
            sa.or_(
                sa.or_(*spec_conditions) if spec_conditions else sa.literal(True),
                sa.or_(*keyword_conditions) if keyword_conditions else sa.literal(True),
                # sa.or_(*action_time_conditions)
                # if action_time_conditions
                # else sa.literal(True),
            ),
        )

        similar_movies = db.execute(stmt).scalars().all()

    # if len(similar_movies) > 10:
    #     stmt = (
    #     sa.select(m.Movie)
    #     .where(
    #         m.Movie.id != movie.id,
    #         m.Movie.key.not_in([m.key for m in movie.related_movies_collection]),
    #         sa.and_(
    #             sa.and_(*genre_conditions)
    #             if genre_conditions
    #             else sa.literal(True),
    #             sa.or_(*subgenre_conditions)
    #             if subgenre_conditions
    #             else sa.literal(True),
    #         ),
    #     )
    # )
    #     similar_movies = db.execute(stmt).scalars().all()

    return s.SimilarMovieOutList(
        similar_movies=[
            s.SimilarMovieOut(
                key=movie.key,
                title=movie.get_title(lang),
                poster=movie.poster,
            )
            for movie in similar_movies
        ],
    )


@movie_router.get(
    "/movies-to-add/",
    status_code=status.HTTP_200_OK,
    response_model=s.QuickMovieList,
)
def movies_to_add(
    admin_user: m.User = Depends(get_admin),
):
    """List of new movies to add"""

    quick_movies_out = []

    if os.path.exists(QUICK_MOVIES_FILE):
        quick_movies = get_movies_data_from_file()

        if quick_movies:
            for quick_movie in quick_movies:
                quick_movies_out.append(
                    s.QuickMovie(
                        key=quick_movie.key,
                        title_en=quick_movie.title_en,
                        rating=quick_movie.rating,
                    )
                )

    return s.QuickMovieList(quick_movies=quick_movies_out)


@movie_router.put(
    "/specifications/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Specification already exists"},
        status.HTTP_201_CREATED: {"description": "Specification successfully created"},
    },
)
def edit_specifications(
    form_data: s.FilterFormIn,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Edit movie specifications"""

    check_admin_permissions(current_user)

    items_keys = [item.key for item in form_data.items]
    specifications = db.scalars(sa.select(m.Specification).where(m.Specification.key.in_(items_keys))).all()

    if not specifications:
        log(log.ERROR, "Specification [%s] not found")
        raise HTTPException(status_code=404, detail="Specification not found")

    try:
        movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == form_data.movie_key))

        if not movie:
            log(log.ERROR, "Movie [%s] not found", form_data.movie_key)
            raise HTTPException(status_code=404, detail="Movie not found")

        movie.specifications.clear()
        movie.specifications.extend(specifications)
        db.commit()

        for item in form_data.items:
            specification = db.scalar(sa.select(m.Specification).where(m.Specification.key == item.key))
            if not specification:
                log(log.ERROR, "Specification [%s] not found", item.key)
                raise HTTPException(status_code=404, detail="Specification not found")
            movie_specification = (
                m.movie_specifications.update()
                .values({"percentage_match": item.percentage_match})
                .where(
                    m.movie_specifications.c.movie_id == movie.id,
                    m.movie_specifications.c.specification_id == specification.id,
                )
            )
            db.execute(movie_specification)
        db.commit()

        log(log.INFO, "Specification [%s] successfully updated", form_data.movie_key)
    except Exception as e:
        log(log.ERROR, "Error updating specification [%s]: %s", form_data.movie_key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating specification")


@movie_router.put(
    "/keywords/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Keywords already exists"},
        status.HTTP_201_CREATED: {"description": "Keywords successfully created"},
    },
)
def edit_Keywords(
    form_data: s.FilterFormIn,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Edit movie keywords"""

    check_admin_permissions(current_user)
    items_keys = [item.key for item in form_data.items]
    keywords = db.scalars(sa.select(m.Keyword).where(m.Keyword.key.in_(items_keys))).all()

    if not keywords:
        log(log.ERROR, "Keywords [%s] not found")
        raise HTTPException(status_code=404, detail="Keywords not found")

    try:
        movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == form_data.movie_key))

        if not movie:
            log(log.ERROR, "Movie [%s] not found", form_data.movie_key)
            raise HTTPException(status_code=404, detail="Movie not found")

        movie.keywords.clear()
        movie.keywords.extend(keywords)
        db.commit()

        for item in form_data.items:
            keyword = db.scalar(sa.select(m.Keyword).where(m.Keyword.key == item.key))
            if not keyword:
                log(log.ERROR, "Keyword [%s] not found", item.key)
                raise HTTPException(status_code=404, detail="Keyword not found")
            movie_keyword = (
                m.movie_keywords.update()
                .values({"percentage_match": item.percentage_match})
                .where(
                    m.movie_keywords.c.movie_id == movie.id,
                    m.movie_keywords.c.keyword_id == keyword.id,
                )
            )
            db.execute(movie_keyword)
        db.commit()

        log(log.INFO, "Keywords [%s] successfully updated", form_data.movie_key)
    except Exception as e:
        log(log.ERROR, "Error updating keyword [%s]: %s", form_data.movie_key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating keyword")


@movie_router.put(
    "/action-times/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Action Times already exists"},
        status.HTTP_201_CREATED: {"description": "Action Times successfully created"},
    },
)
def edit_action_times(
    form_data: s.FilterFormIn,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Edit movie action times"""

    check_admin_permissions(current_user)
    items_keys = [item.key for item in form_data.items]
    action_times = db.scalars(sa.select(m.ActionTime).where(m.ActionTime.key.in_(items_keys))).all()

    if not action_times:
        log(log.ERROR, "Action Times [%s] not found")
        raise HTTPException(status_code=404, detail="Action Times not found")

    try:
        movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == form_data.movie_key))

        if not movie:
            log(log.ERROR, "Movie [%s] not found", form_data.movie_key)
            raise HTTPException(status_code=404, detail="Movie not found")

        movie.action_times.clear()
        movie.action_times.extend(action_times)
        db.commit()

        for item in form_data.items:
            action_time = db.scalar(sa.select(m.ActionTime).where(m.ActionTime.key == item.key))
            if not action_time:
                log(log.ERROR, "Action Time [%s] not found", item.key)
                raise HTTPException(status_code=404, detail="Action Time not found")
            movie_action_time = (
                m.movie_action_times.update()
                .values({"percentage_match": item.percentage_match})
                .where(
                    m.movie_action_times.c.movie_id == movie.id,
                    m.movie_action_times.c.action_time_id == action_time.id,
                )
            )
            db.execute(movie_action_time)
        db.commit()

        log(log.INFO, "Action Times [%s] successfully updated", form_data.movie_key)
    except Exception as e:
        log(log.ERROR, "Error updating action time [%s]: %s", form_data.movie_key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating action time")
