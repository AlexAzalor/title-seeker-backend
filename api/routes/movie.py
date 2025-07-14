import json
from datetime import datetime
from random import randint
from typing import Annotated, Sequence

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
import sqlalchemy as sa
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, File, UploadFile

from sqlalchemy.orm import Session, aliased, selectinload

from api.controllers.create_movie import (
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

from api.controllers.movie import build_movie_query, get_main_genres_for_movies, get_movie_data
from api.controllers.movie_filters import get_filters, get_genre_filters, get_people_filters
from api.controllers.super_search import (
    get_filter_query_conditions,
    get_genre_query_conditions,
    get_people_query_conditions,
    get_shared_universe_query_conditions,
    get_visual_profile_query_conditions,
)
from api.dependency.user import get_admin, get_current_user, get_owner
from api.utils import get_error_message, get_quick_movie_file_path, normalize_query
import app.models as m
import app.schema as s
from app.database import get_db
from app.logger import log
from config import config

CFG = config()

movie_router = APIRouter(prefix="/movies", tags=["Movies"])

UPLOAD_DIRECTORY = "./uploads/posters/"


@movie_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=Page[s.MoviePreviewOut],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def get_movies(
    sort_by: s.SortBy = s.SortBy.RATED_AT,
    sort_order: s.SortOrder = s.SortOrder.DESC,
    current_user: m.User | None = Depends(get_current_user),
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
    params: Params = Depends(),
):
    """Get movies by query params"""

    is_reverse = sort_order == s.SortOrder.DESC

    base_query = build_movie_query(sort_by, is_reverse, current_user)

    def transform_movies_to_preview(movies: Sequence[m.Movie]) -> Sequence[s.MoviePreviewOut]:
        movie_ids = [movie.id for movie in movies]
        main_genre_map = get_main_genres_for_movies(db, movie_ids, lang)

        return [
            s.MoviePreviewOut(
                key=movie.key,
                title=movie.get_title(lang),
                poster=movie.poster,
                # TODO: fix none release date
                release_date=movie.release_date if movie.release_date else datetime.now(),
                duration=movie.formatted_duration(lang.value),
                main_genre=main_genre_map.get(movie.id, "No main genre"),
                rating=next((t.rating for t in movie.ratings if t.user_id == current_user.id), 0.0)
                if current_user
                else 0.0,
            )
            for movie in movies
        ]

    return paginate(db, base_query, params, transformer=transform_movies_to_preview)


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
    current_user: m.User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all movie details by key"""

    movie = db.scalar(
        sa.select(m.Movie)
        .where(m.Movie.key == movie_key)
        # "selectinload" for deep queries speeds up execution. All other, simple ones, on the contrary, can slow down (like movie.translations).
        .options(
            # Visual profile
            selectinload(m.Movie.visual_profiles)
            .selectinload(m.VisualProfile.ratings)
            .selectinload(m.VisualProfileRating.criterion)
            .selectinload(m.VisualProfileCategoryCriterion.translations),
            # Actor
            selectinload(m.Movie.characters)
            .selectinload(m.MovieActorCharacter.actor)
            .selectinload(m.Actor.translations),
            # Character
            selectinload(m.Movie.characters)
            .selectinload(m.MovieActorCharacter.character)
            .selectinload(m.Character.translations),
        )
    )

    if not movie:
        log(log.ERROR, "Movie [%s] not found", movie_key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    return get_movie_data(
        movie,
        db,
        lang,
        current_user,
    )


@movie_router.get(
    "/super-search/",
    status_code=status.HTTP_200_OK,
    response_model=Page[s.MoviePreviewOut],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def super_search_movies(
    genre: Annotated[list[str], Query()] = [],
    subgenre: Annotated[list[str], Query()] = [],
    specification: Annotated[list[str], Query()] = [],
    keyword: Annotated[list[str], Query()] = [],
    action_time: Annotated[list[str], Query()] = [],
    actor: Annotated[list[str], Query()] = [],
    director: Annotated[list[str], Query()] = [],
    character: Annotated[list[str], Query()] = [],
    shared_universe: Annotated[list[str], Query()] = [],
    visual_profile: Annotated[list[str], Query()] = [],
    exact_match: Annotated[bool, Query()] = False,
    inner_exact_match: Annotated[bool, Query()] = False,
    sort_by: s.SortBy = s.SortBy.RATED_AT,
    sort_order: s.SortOrder = s.SortOrder.DESC,
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    params: Params = Depends(),
):
    """Get movies by query params"""

    query = sa.select(m.Movie).options(selectinload(m.Movie.translations), selectinload(m.Movie.ratings))

    logical_op = sa.and_ if exact_match else sa.or_
    inner_logical_op = sa.and_ if inner_exact_match else sa.or_

    # What Happens to the Query at Each Filter Step?
    # Build conditions for each filter type
    filter_conditions = []

    # GENRES, SUBGENRES
    genre_conditions, subgenre_conditions = get_genre_query_conditions(genre, subgenre, db)
    if genre_conditions:
        filter_conditions.append(inner_logical_op(*genre_conditions))
    if subgenre_conditions:
        filter_conditions.append(inner_logical_op(*subgenre_conditions))

    # SPECIFICATIONS, KEYWORDS, ACTION TIMES
    spec_conditions, keyword_conditions, at_conditions = get_filter_query_conditions(
        specification, keyword, action_time, db
    )
    if spec_conditions:
        filter_conditions.append(inner_logical_op(*spec_conditions))
    if keyword_conditions:
        filter_conditions.append(inner_logical_op(*keyword_conditions))
    if at_conditions:
        filter_conditions.append(inner_logical_op(*at_conditions))

    # ACTORS, DIRECTORS, CHARACTERS
    actor_conditions, director_conditions, char_conditions = get_people_query_conditions(actor, director, character, db)
    if actor_conditions:
        filter_conditions.append(inner_logical_op(*actor_conditions))
    if director_conditions:
        filter_conditions.append(inner_logical_op(*director_conditions))
    if char_conditions:
        filter_conditions.append(inner_logical_op(*char_conditions))

    # SHARED UNIVERSE
    if shared_universe:
        su_conditions = get_shared_universe_query_conditions(shared_universe, db)
        if su_conditions:
            filter_conditions.append(inner_logical_op(*su_conditions))

    # VISUAL PROFILE
    if visual_profile:
        vp_conditions = get_visual_profile_query_conditions(visual_profile, db)
        if vp_conditions:
            filter_conditions.append(inner_logical_op(*vp_conditions))

    # Combine conditions
    if filter_conditions:
        query = query.where(logical_op(*filter_conditions))

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

    def movie_to_custom_schema(movies: Sequence[m.Movie]) -> Sequence[s.MoviePreviewOut]:
        return [
            s.MoviePreviewOut(
                key=movie.key,
                title=movie.get_title(lang),
                poster=movie.poster,
                # TODO: fix none release date
                release_date=movie.release_date if movie.release_date else datetime.now(),
                duration=movie.formatted_duration(lang.value),
                main_genre="",
                rating=next((t.rating for t in movie.ratings if t.user_id == current_user.id), 0.0)
                if current_user
                else 0.0,
            )
            for movie in movies
        ]

    return paginate(db, query, params, transformer=movie_to_custom_schema)


@movie_router.get(
    "/search/",
    status_code=status.HTTP_200_OK,
    response_model=s.SearchResults,
    responses={status.HTTP_403_FORBIDDEN: {"description": "Title type not supported"}},
)
def search(
    query: str = Query(default="", max_length=128),
    title_type: s.SearchType = s.SearchType.MOVIES,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Search titles by query"""

    if title_type != s.SearchType.MOVIES:
        log(log.ERROR, "Title type [%s] not supported", title_type)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Title type not supported")

    normalized_query = normalize_query(query)

    movies_db = (
        db.scalars(
            sa.select(m.Movie)
            .options(selectinload(m.Movie.translations))
            .where(
                m.Movie.translations.any(
                    sa.func.regexp_replace(
                        sa.func.lower(m.MovieTranslation.title), r"[^a-zA-Zа-яА-Я0-9 ]", "", "g"
                    ).ilike(f"%{normalized_query}%")
                )
            )
            .limit(5)
        )
        .unique()
        .all()
    )

    main_genre_map = get_main_genres_for_movies(db, [movie.id for movie in movies_db], lang)

    movies_out = []

    if movies_db:
        for movie in movies_db:
            release_date = movie.release_date.year if movie.release_date else "No release date"
            duration = movie.formatted_duration(lang.value)
            main_genre = main_genre_map.get(movie.id, "No main genre")

            movies_out.append(
                s.SearchResult(
                    key=movie.key,
                    name=movie.get_title(s.Language.EN) + f" ({movie.get_title(s.Language.UK)})",
                    image=movie.poster,
                    extra_info=f"{duration} | {release_date} | {main_genre}",
                    type=s.SearchType.MOVIES,
                )
            )

    return s.SearchResults(
        results=movies_out,
    )


@movie_router.get("/filters/", status_code=status.HTTP_200_OK, response_model=s.MovieFiltersListOut)
def get_movie_filters(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all movie filters"""

    specifications_out, keywords_out, action_times_out, su_out = get_filters(db, lang)
    actors_out, directors_out, characters_out = get_people_filters(db, lang)
    genres_out = get_genre_filters(db, lang)

    # selectinload - used to reduce the number of database requests, especially for loops and working with languages (.get_name(lang)).

    subgenres = db.scalars(
        sa.select(m.Subgenre)
        .options(selectinload(m.Subgenre.translations))  # avoids N+1 queries
        .join(m.Subgenre.translations)
        .where(m.SubgenreTranslation.language == lang.value)
        .order_by(m.SubgenreTranslation.name)  # this only works if joined
    ).all()
    if not subgenres:
        log(log.ERROR, "Subgenre [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subgenre not found")

    visual_profile_categories = db.scalars(
        sa.select(m.VisualProfileCategory).options(selectinload(m.VisualProfileCategory.translations))
    ).all()
    if not visual_profile_categories:
        log(log.ERROR, "Visual profile categories [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visual profile categories not found")

    subgenres_out = [
        s.SubgenreOut(
            key=subgenre.key,
            name=subgenre.get_name(lang),
            description=subgenre.get_description(lang),
            parent_genre_key=subgenre.genre.key,
        )
        for subgenre in subgenres
    ]

    vp_categories_out = [
        s.VisualProfileCategoryOut(
            key=category.key,
            name=category.get_name(lang),
            description=category.get_description(lang),
        )
        for category in visual_profile_categories
    ]

    return s.MovieFiltersListOut(
        genres=genres_out,
        subgenres=subgenres_out,
        specifications=specifications_out,
        keywords=keywords_out,
        action_times=action_times_out,
        actors=actors_out,
        directors=directors_out,
        characters=characters_out,
        visual_profile_categories=vp_categories_out,
        shared_universes=su_out,
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
    current_user: m.User = Depends(get_owner),
    db: Session = Depends(get_db),
):
    """Get pre-create data for a new movie"""

    specifications_out, keywords_out, action_times_out, su_out = get_filters(db, lang)
    actors_out, directors_out, characters_out = get_people_filters(db, lang)
    genres_out = get_genre_filters(db, lang)

    base_movies = db.scalars(
        sa.select(m.Movie)
        .options(selectinload(m.Movie.translations))
        .join(m.Movie.translations)
        .where(m.MovieTranslation.language == lang.value)
        .order_by(
            # Ignore "The" at the beginning of the title (not remove)
            sa.func.regexp_replace(m.MovieTranslation.title, r"^(The\s)", "", "i"),
            m.Movie.relation_type,
        )
    ).all()
    if not base_movies:
        log(log.ERROR, "Base movies not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Base movies not found")

    categories = db.scalars(
        sa.select(m.VisualProfileCategory)
        .options(
            selectinload(m.VisualProfileCategory.translations),
            selectinload(m.VisualProfileCategory.criteria).selectinload(m.VisualProfileCategoryCriterion.translations),
        )
        .join(m.VisualProfileCategory.translations)
        .where(m.VPCategoryTranslation.language == lang.value)
        .order_by(m.VPCategoryTranslation.name)
    ).all()
    if not categories:
        log(log.ERROR, "Title categories not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Title categories not found")

    base_movies_out = [
        s.MovieMenuItem(
            key=base_movie.key,
            name=base_movie.get_title(lang),
        )
        for base_movie in base_movies
    ]

    categories_out = [
        s.VisualProfileData(
            key=category.key,
            name=category.get_name(lang),
            description=category.get_description(lang),
            criteria=[
                s.VisualProfileCriterionData(
                    key=criterion.key,
                    name=criterion.get_name(lang),
                    description=criterion.get_description(lang),
                    rating=0,
                )
                for criterion in category.criteria
            ],
        )
        for category in sorted(categories, key=lambda x: x.id)
    ]

    quick_movie = None

    if quick_movie_key:
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

    return s.MoviePreCreateData(
        visual_profile_categories=categories_out,
        base_movies=base_movies_out,
        actors=actors_out,
        directors=directors_out,
        specifications=specifications_out,
        genres=genres_out,
        keywords=keywords_out,
        action_times=action_times_out,
        quick_movie=quick_movie,
        shared_universes=su_out,
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
    current_user: m.User = Depends(get_owner),
    db: Session = Depends(get_db),
):
    """Create a new movie"""

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
    current_user: m.User = Depends(get_owner),
    db: Session = Depends(get_db),
):
    """For quick and temporary adding of new movies in a JSON file.
    Then these data will be used to fully add the movie to the database."""

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

        file_path = get_quick_movie_file_path()

        with open(file_path, "w") as file:
            json.dump(s.QuickMovieJSON(movies=movies_to_file).model_dump(mode="json"), file, indent=4)

        log(log.INFO, "Movie [%s] successfully added by [%s]", form_data.key, current_user.email)

    except Exception as e:
        log(log.ERROR, "Error adding movie to JSON [%s]: %s", form_data.key, e)
        error_message = get_error_message(lang, "Помилка додавання фільму до JSON", "Error adding movie to JSON")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{error_message} - {e}")


@movie_router.get(
    "/random/",
    status_code=status.HTTP_200_OK,
    response_model=s.MovieCarouselList,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Movies not found"},
    },
)
def get_random_list(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get 10 random movies (for carousel)"""

    # Get the total number of movies
    total_movies = db.scalar(sa.select(sa.func.count()).select_from(m.Movie))

    if not total_movies:
        log(log.ERROR, "Movies not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movies not found")

    count = 10

    # Generate a random offset
    random_offset = randint(0, max(0, total_movies - count))

    # Select 10 random movies using the random offset
    movies_db = (
        db.scalars(
            sa.select(m.Movie)
            .options(
                selectinload(m.Movie.translations),
                selectinload(m.Movie.genres).selectinload(m.Genre.translations),
                selectinload(m.Movie.actors).selectinload(m.Actor.translations),
                selectinload(m.Movie.directors).selectinload(m.Director.translations),
            )
            .offset(random_offset)
            .limit(count)
        )
        .unique()
        .all()
    )

    return s.MovieCarouselList(
        movies=[
            s.MovieCarousel(
                key=movie.key,
                title=movie.get_title(lang),
                description=movie.get_description(lang),
                poster=movie.poster,
                release_date=movie.release_date if movie.release_date else datetime.now(),
                duration=movie.formatted_duration(lang.value),
                location=movie.get_location(lang),
                genres=[
                    s.GenreShort(
                        key=genre.key,
                        name=genre.get_name(lang),
                    )
                    for genre in movie.genres
                ],
                actors=[
                    s.PersonWithAvatar(
                        key=actor.key,
                        full_name=actor.full_name(lang),
                        avatar_url=actor.avatar,
                    )
                    for actor in movie.actors
                ],
                directors=[
                    s.PersonWithAvatar(
                        key=director.key,
                        full_name=director.full_name(lang),
                        avatar_url=director.avatar if director.avatar else "",
                    )
                    for director in movie.directors
                ],
            )
            for movie in movies_db
        ]
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
    """Get similar movies for current one"""

    # TODO: IMPLEMENT/IMPROVE ALGORITHM When there will be enough movies on prod (200+)
    # Also the radar chart should be more round in shape, this means there is a rich variety of movies

    movie = db.scalar(
        sa.select(m.Movie)
        .options(
            selectinload(m.Movie.translations),
            selectinload(m.Movie.genres).selectinload(m.Genre.translations),
            selectinload(m.Movie.subgenres).selectinload(m.Subgenre.translations),
            selectinload(m.Movie.specifications).selectinload(m.Specification.translations),
            selectinload(m.Movie.keywords).selectinload(m.Keyword.translations),
        )
        .where(m.Movie.key == movie_key)
    )

    if not movie:
        log(log.ERROR, "Movie [%s] not found", movie_key)
        raise HTTPException(status_code=404, detail="Movie not found")

    genres_list = [
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
    ]

    subgenres_list = [
        s.MovieFilterItem(
            key=subgenre.key,
            subgenre_parent_key=subgenre.genre.key,
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
    ]

    specifications_list = [
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
    ]

    keywords_list = [
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

    movies_limit = 10

    # Ensure at least one genre and one subgenre match
    stmt = (
        sa.select(m.Movie)
        .where(
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
        .limit(movies_limit)
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

        stmt = (
            sa.select(m.Movie)
            .where(
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
            .limit(movies_limit)
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
def get_movies_to_add_list(
    admin_user: m.User = Depends(get_admin),
):
    """List of new movies to add"""

    quick_movies_out = []

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


@movie_router.get(
    "/genres-subgenres/",
    status_code=status.HTTP_200_OK,
    response_model=s.GenresSubgenresOut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Genres not found"},
        status.HTTP_200_OK: {"description": "Genres and subgenres successfully retrieved"},
    },
)
def get_genres_subgenres(
    lang: s.Language = s.Language.UK,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Get all genres and related subgenres for the movie page (for edit)"""

    genres = db.scalars(
        sa.select(m.Genre).options(
            selectinload(m.Genre.translations), selectinload(m.Genre.subgenres).selectinload(m.Subgenre.translations)
        )
    ).all()

    if not genres:
        log(log.ERROR, "Genres [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genres not found")

    return s.GenresSubgenresOut(
        genres=[
            s.GenreOut(
                key=genre.key,
                name=genre.get_name(lang),
                description=genre.get_description(lang),
                subgenres=sorted(
                    [
                        s.SubgenreOut(
                            key=subgenre.key,
                            name=subgenre.get_name(lang),
                            description=subgenre.get_description(lang),
                            parent_genre_key=subgenre.genre.key,
                        )
                        for subgenre in genre.subgenres
                    ],
                    key=lambda x: x.name,
                ),
            )
            for genre in genres
        ],
    )


@movie_router.put(
    "/genres-subgenres/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Error updating genres"},
        status.HTTP_204_NO_CONTENT: {"description": "Genres successfully updated"},
    },
)
def edit_genres_subgenres(
    movie_key: str,
    form_data: s.GenreItemFieldEditFormIn,
    current_user: m.User = Depends(get_admin),
    db: Session = Depends(get_db),
):
    """Edit genres of a movie"""

    movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == movie_key))

    if not movie:
        log(log.ERROR, "Movie [%s] not found", movie_key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    items_keys = [item.key for item in form_data.genres]
    genres = db.scalars(sa.select(m.Genre).where(m.Genre.key.in_(items_keys))).all()

    if not genres:
        log(log.ERROR, "Genres [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genres not found")

    items_keys = [item.key for item in form_data.subgenres]
    # Subenres can be empty, so we don't raise an error if not found
    subgenres = db.scalars(sa.select(m.Subgenre).where(m.Subgenre.key.in_(items_keys))).all()

    try:
        # Clear existing old genres and subgenres
        movie.genres.clear()
        movie.subgenres.clear()
        # Extend with new genres and subgenres
        movie.genres.extend(genres)
        movie.subgenres.extend(subgenres)
        db.commit()

        for item in form_data.genres:
            genre = db.scalar(sa.select(m.Genre).where(m.Genre.key == item.key))
            if not genre:
                log(log.ERROR, "Genre [%s] not found", item.key)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found")
            movie_genre = (
                m.movie_genres.update()
                .values({"percentage_match": item.percentage_match})
                .where(
                    m.movie_genres.c.movie_id == movie.id,
                    m.movie_genres.c.genre_id == genre.id,
                )
            )
            db.execute(movie_genre)

        if subgenres:
            for item in form_data.subgenres:
                subgenre = db.scalar(sa.select(m.Subgenre).where(m.Subgenre.key == item.key))
                if not subgenre:
                    log(log.ERROR, "Subgenre [%s] not found", item.key)
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subgenre not found")
                movie_subgenre = (
                    m.movie_subgenres.update()
                    .values({"percentage_match": item.percentage_match})
                    .where(
                        m.movie_subgenres.c.movie_id == movie.id,
                        m.movie_subgenres.c.subgenre_id == subgenre.id,
                    )
                )
                db.execute(movie_subgenre)
        db.commit()

        log(log.INFO, "Genre [%s] successfully updated", movie_key)
    except Exception as e:
        log(log.ERROR, "Error updating genre [%s]: %s", movie_key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating genre")


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

    movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == form_data.movie_key))

    if not movie:
        log(log.ERROR, "Movie [%s] not found", form_data.movie_key)
        raise HTTPException(status_code=404, detail="Movie not found")

    items_keys = [item.key for item in form_data.items]
    specifications = db.scalars(sa.select(m.Specification).where(m.Specification.key.in_(items_keys))).all()

    if not specifications:
        log(log.ERROR, "Specification [%s] not found")
        raise HTTPException(status_code=404, detail="Specification not found")

    try:
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

    movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == form_data.movie_key))

    if not movie:
        log(log.ERROR, "Movie [%s] not found", form_data.movie_key)
        raise HTTPException(status_code=404, detail="Movie not found")

    items_keys = [item.key for item in form_data.items]
    keywords = db.scalars(sa.select(m.Keyword).where(m.Keyword.key.in_(items_keys))).all()

    if not keywords:
        log(log.ERROR, "Keywords [%s] not found")
        raise HTTPException(status_code=404, detail="Keywords not found")

    try:
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

    movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == form_data.movie_key))

    if not movie:
        log(log.ERROR, "Movie [%s] not found", form_data.movie_key)
        raise HTTPException(status_code=404, detail="Movie not found")

    items_keys = [item.key for item in form_data.items]
    action_times = db.scalars(sa.select(m.ActionTime).where(m.ActionTime.key.in_(items_keys))).all()

    if not action_times:
        log(log.ERROR, "Action Times [%s] not found")
        raise HTTPException(status_code=404, detail="Action Times not found")

    try:
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
