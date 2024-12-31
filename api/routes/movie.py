import os
from typing import Annotated
import json
from pydantic import BaseModel, model_validator
import sqlalchemy as sa
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, File, UploadFile
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session, joinedload

import app.models as m
import app.schema as s
from app.database import get_db
from app.logger import log
from config import config

CFG = config()

movie_router = APIRouter(prefix="/movies", tags=["Movies"])

UPLOAD_DIRECTORY = "./uploads/movie-posters/"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


@movie_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.MoviePreviewOutList,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def get_movies(
    # query: str = Query(default="", max_length=128),
    # lang: Language = Language.UK,
    # selected_locations: Annotated[Union[List[str], None], Query()] = None,
    # order_by: s.JobsOrderBy = s.JobsOrderBy.CREATED_AT,
    # order_type: s.OrderType = s.OrderType.ASC,
    # current_user: m.User = Depends(get_current_user),
    # genre_uuid: str | None = None,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get movies by query params"""

    db_movies = (
        db.scalars(
            sa.select(m.Movie).where(m.Movie.is_deleted.is_(False)).options(joinedload(m.Movie.translations))
            # .order_by(m.Movie.release_date.desc())
        )
        .unique()
        .all()
    )

    movies_out = []
    for movie in db_movies:
        movies_out.append(
            s.MoviePreviewOut(
                key=movie.key,
                title=next((t.title for t in movie.translations if t.language == lang.value)),
                poster=movie.poster,
                release_date=movie.release_date,
            )
        )

    return s.MoviePreviewOutList(movies=movies_out)


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
    db: Session = Depends(get_db),
):
    current_user = 1
    movie: m.Movie | None = db.scalar(
        sa.select(m.Movie)
        .where(m.Movie.key == movie_key)
        .options(
            joinedload(m.Movie.translations),
            joinedload(m.Movie.actors),
            joinedload(m.Movie.directors),
            joinedload(m.Movie.genres),
            joinedload(m.Movie.subgenres),
            joinedload(m.Movie.ratings),
            joinedload(m.Movie.characters),
        )
    )
    if not movie:
        log(log.ERROR, "Movie [%s] not found", movie_key)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    user_rating = None
    if current_user:
        user_rating = db.scalar(
            sa.select(m.Rating).where(m.Rating.movie_id == movie.id).where(m.Rating.user_id == current_user)
        )

    return s.MovieOut(
        key=movie.key,
        title=next((t.title for t in movie.translations if t.language == lang.value)),
        description=next((t.description for t in movie.translations if t.language == lang.value)),
        poster=movie.poster,
        budget=movie.formatted_budget,
        duration=movie.formatted_duration(lang.value),
        domestic_gross=movie.formatted_domestic_gross,
        worldwide_gross=movie.formatted_worldwide_gross,
        release_date=movie.release_date,
        actors=[
            s.MovieActor(
                key=actor.key,
                first_name=next((t.first_name for t in actor.translations if t.language == lang.value)),
                last_name=next((t.last_name for t in actor.translations if t.language == lang.value)),
                # character_name=next((t.character_name for t in actor.translations if t.language == lang.value)),
                character_name=next(
                    (
                        t.name
                        for t in next(
                            (с for с in movie.characters if actor.id in [a.id for a in с.actors])
                        ).translations
                        if t.language == lang.value
                    )
                ),
                avatar_url=actor.avatar,
            )
            for actor in movie.actors
        ],
        directors=[
            s.MovieDirector(
                key=director.key,
                first_name=next((t.first_name for t in director.translations if t.language == lang.value)),
                last_name=next((t.last_name for t in director.translations if t.language == lang.value)),
                avatar_url=director.avatar,
            )
            for director in movie.directors
        ],
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
        subgenres=[
            s.MovieSubgenre(
                key=subgenre.key,
                parent_genre=s.MovieGenre(
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
        ],
        ratings=[
            s.MovieRating(
                uuid=rating.uuid,
                rating=rating.rating,
                comment=rating.comment,
            )
            for rating in movie.ratings
        ],
        average_rating=movie.average_rating,
        ratings_count=movie.ratings_count,
        user_rating=s.UserRatingCriteria(
            acting=user_rating.acting,
            plot_storyline=user_rating.plot_storyline,
            music=user_rating.music,
            re_watchability=user_rating.re_watchability,
            emotional_impact=user_rating.emotional_impact,
            dialogue=user_rating.dialogue,
            production_design=user_rating.production_design,
            duration=user_rating.duration,
            visual_effects=user_rating.visual_effects
            if movie.rating_criterion in [s.RatingCriterion.VISUAL_EFFECTS.value, s.RatingCriterion.FULL.value]
            else None,
            scare_factor=user_rating.scare_factor
            if movie.rating_criterion in [s.RatingCriterion.SCARE_FACTOR.value, s.RatingCriterion.FULL.value]
            else None,
        )
        if user_rating
        else None,
        rating_criterion=s.RatingCriterion(movie.rating_criterion),
        specifications=[
            s.MovieSpecification(
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
        ],
        keywords=[
            s.MovieKeyword(
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
        ],
        action_times=[
            s.MovieActionTime(
                key=action_time.key,
                name=next((t.name for t in action_time.translations if t.language == lang.value)),
                description=next((t.description for t in action_time.translations if t.language == lang.value)),
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
    )


# need async?
@movie_router.post("/upload-poster/{movie_id}", status_code=status.HTTP_200_OK)
async def upload_poster(movie_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload poster for movie"""

    movie = db.query(m.Movie).filter(m.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    file_name = f"{movie_id}_{file.filename}"
    file_location = f"{UPLOAD_DIRECTORY}{file_name}"

    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    movie.poster = file_name
    db.commit()

    return {"info": "Poster uploaded successfully"}


@movie_router.get("/poster/{filename}", status_code=status.HTTP_200_OK)
async def get_poster(filename: str):
    """Check if file exists and return it (for testing purposes)"""

    file_path = os.path.join(UPLOAD_DIRECTORY, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


@movie_router.get(
    "/search/",
    status_code=status.HTTP_200_OK,
    response_model=s.MovieSearchResult,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def search_movies(
    # query: str = Query(default="", max_length=128),
    # lang: Language = Language.UK,
    # selected_locations: Annotated[Union[List[str], None], Query()] = None,
    # order_by: s.JobsOrderBy = s.JobsOrderBy.CREATED_AT,
    # order_type: s.OrderType = s.OrderType.ASC,
    # current_user: m.User = Depends(get_current_user),
    # genre_uuid: str,
    genre_name: Annotated[list[str], Query()] = [],
    subgenre_name: Annotated[list[str], Query()] = [],
    actor_name: Annotated[list[str], Query()] = [],
    director_name: Annotated[list[str], Query()] = [],
    specification_name: Annotated[list[str], Query()] = [],
    keyword_name: Annotated[list[str], Query()] = [],
    action_time_name: Annotated[list[str], Query()] = [],
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get movies by query params"""

    query = sa.select(m.Movie).options(joinedload(m.Movie.translations))

    # What Happens to the Query at Each Filter Step?
    # It is augmented, not replaced.
    # Each call to query.where() appends additional conditions, effectively adding AND logic to the query.
    # Both genre and subgenre conditions are combined, meaning that the final query will only return movies that satisfy both filters (if both are provided).

    if actor_name:
        query = query.where(sa.and_(*[m.Movie.actors.any(m.Actor.key == actor_key) for actor_key in actor_name]))

    if director_name:
        query = query.where(m.Movie.directors.any(m.Director.key.in_(director_name)))
        # query = query.where(
        #     sa.and_(*[m.Movie.directors.any(m.Director.key == director_key) for director_key in director_name])
        # )

    if genre_name:
        query = query.where(sa.and_(*[m.Movie.genres.any(m.Genre.key == genre_key) for genre_key in genre_name]))

    # Filter only by subgenre
    if subgenre_name:
        query = query.where(
            sa.and_(*[m.Movie.subgenres.any(m.Subgenre.key == subgenre_key) for subgenre_key in subgenre_name])
        )

    if specification_name:
        query = query.where(
            sa.and_(
                *[
                    m.Movie.specifications.any(m.Specification.key == specification_key)
                    for specification_key in specification_name
                ]
            )
        )

    if keyword_name:
        query = query.where(
            sa.and_(*[m.Movie.keywords.any(m.Keyword.key == keyword_key) for keyword_key in keyword_name])
        )

    if action_time_name:
        query = query.where(
            sa.and_(
                *[m.Movie.action_times.any(m.ActionTime.key == action_time_key) for action_time_key in action_time_name]
            )
        )

    movies_db = db.scalars(query).unique().all()

    movies_out = []
    for movie in movies_db:
        movies_out.append(
            s.MovieSearchOut(
                key=movie.key,
                title=next((t.title for t in movie.translations if t.language == lang.value)),
                poster=movie.poster,
                release_date=movie.release_date,
            )
        )

    return s.MovieSearchResult(
        movies=movies_out,
    )


@movie_router.get(
    "/by-actor/",
    status_code=status.HTTP_200_OK,
    response_model=s.MovieByActorsList,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Movies not found"}},
)
def get_movies_by_actor(
    actor_name: Annotated[list[str], Query()] = [],
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get actors by query params"""

    actors = (
        db.scalars(sa.select(m.Actor).where(m.Actor.key.in_(actor_name)).options(joinedload(m.Actor.movies)))
        .unique()
        .all()
    )

    if not actors:
        log(log.ERROR, "Actor not found")
        return s.MovieByActorsList(movies=[], actor=None)

    movies = []
    for actor in actors:
        movies += actor.movies

    movies = list({movie.id: movie for movie in movies}.values())

    movies_out = []
    for movie in movies:
        movies_out.append(
            s.MovieSearchOut(
                key=movie.key,
                title=next((t.title for t in movie.translations if t.language == lang.value)),
                poster=movie.poster,
                release_date=movie.release_date,
            )
        )

    return s.MovieByActorsList(
        movies=movies_out,
        actor=[
            s.ActorShort(
                key=actor.key,
                name=actor.full_name(lang),
            )
            for actor in actors
        ],
    )


@movie_router.get("/filters/", status_code=status.HTTP_200_OK, response_model=s.MovieFiltersListOut)
def get_movie_filters(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all movie filters"""

    actors = db.scalars(sa.select(m.Actor)).all()
    if not actors:
        log(log.ERROR, "Actors [%s] not found")
        raise HTTPException(status_code=404, detail="Actors not found")

    directors = db.scalars(sa.select(m.Director)).all()
    if not directors:
        log(log.ERROR, "Director [%s] not found")
        raise HTTPException(status_code=404, detail="Director not found")

    genres = db.scalars(sa.select(m.Genre)).all()
    if not genres:
        log(log.ERROR, "Genres [%s] not found")
        raise HTTPException(status_code=404, detail="Genres not found")

    specifications = db.scalars(sa.select(m.Specification)).all()
    if not specifications:
        log(log.ERROR, "Specifications [%s] not found")
        raise HTTPException(status_code=404, detail="Specifications not found")

    keywords = db.scalars(sa.select(m.Keyword)).all()
    if not keywords:
        log(log.ERROR, "Keywords [%s] not found")
        raise HTTPException(status_code=404, detail="Keywords not found")

    action_times = db.scalars(sa.select(m.ActionTime)).all()
    if not action_times:
        log(log.ERROR, "Action times [%s] not found")
        raise HTTPException(status_code=404, detail="Action times not found")

    actors_out = []

    for actor in actors:
        actors_out.append(
            s.ActorOut(
                key=actor.key,
                full_name=actor.full_name(lang),
            )
        )

    directors_out = []

    for director in directors:
        directors_out.append(
            s.DirectorOut(
                key=director.key,
                full_name=director.full_name(lang),
            )
        )

    genres_out = []

    for genre in genres:
        genres_out.append(
            s.GenreOut(
                key=genre.key,
                name=next((t.name for t in genre.translations if t.language == lang.value)),
                description=next((t.description for t in genre.translations if t.language == lang.value)),
                subgenres=[
                    s.SubgenreOut(
                        key=subgenre.key,
                        name=next((t.name for t in subgenre.translations if t.language == lang.value)),
                        description=next((t.description for t in subgenre.translations if t.language == lang.value)),
                        parent_genre_key=subgenre.genre.key,
                    )
                    for subgenre in genre.subgenres
                ],
            )
        )

    specifications_out = []

    for specification in specifications:
        specifications_out.append(
            s.SpecificationOut(
                key=specification.key,
                name=next((t.name for t in specification.translations if t.language == lang.value)),
                description=next((t.description for t in specification.translations if t.language == lang.value)),
            )
        )

    keywords_out = []
    for keyword in keywords:
        keywords_out.append(
            s.KeywordOut(
                key=keyword.key,
                name=next((t.name for t in keyword.translations if t.language == lang.value)),
                description=next((t.description for t in keyword.translations if t.language == lang.value)),
            )
        )

    action_times_out = []
    for action_time in action_times:
        action_times_out.append(
            s.ActionTimeOut(
                key=action_time.key,
                name=next((t.name for t in action_time.translations if t.language == lang.value)),
                description=next((t.description for t in action_time.translations if t.language == lang.value)),
            )
        )

    return s.MovieFiltersListOut(
        genres=genres_out,
        actors=actors_out,
        directors=directors_out,
        specifications=specifications_out,
        keywords=keywords_out,
        action_times=action_times_out,
    )


# form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
class FormData(BaseModel):
    key: str
    title_uk: str
    title_en: str
    description_uk: str
    description_en: str
    release_date: str
    duration: int
    budget: int
    actors_keys: list[s.MoviePersonFilterField]
    directors_keys: list[str]
    genres: list[s.MovieFilterField]
    subgenres: list[s.MovieFilterField]
    specifications: list[s.MovieFilterField]
    keywords: list[s.MovieFilterField]
    action_times: list[s.MovieFilterField]
    rating_criterion_type: s.RatingCriterion
    rating_criteria: s.UserRatingCriteria
    rating: float
    domestic_gross: int | None = None
    worldwide_gross: int | None = None
    poster: str | None = None
    location_uk: str | None = None
    location_en: str | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


@movie_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Movie already exists"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Error with type VALIDATION"},
    },
)
def create_movie(
    form_data: Annotated[FormData, Body(...)],
    file: UploadFile = File(None),
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create a new movie"""

    current_user = 1

    if db.scalar(sa.select(m.Movie).where(m.Movie.key == form_data.key)):
        # message = "Фільм вже існує" if lang == s.Language.UK else "Movie already exists"
        raise HTTPException(status_code=400, detail="Movie already exists")

    # Create movie
    try:
        new_movie = m.Movie(
            key=form_data.key,
            release_date=form_data.release_date,
            budget=form_data.budget,
            duration=form_data.duration,
            domestic_gross=form_data.domestic_gross,
            worldwide_gross=form_data.worldwide_gross,
            rating_criterion=form_data.rating_criterion_type.value,
            poster=form_data.poster,
            translations=[
                m.MovieTranslation(
                    language=s.Language.UK.value,
                    title=form_data.title_uk,
                    description=form_data.description_uk,
                    location=form_data.location_uk,
                ),
                m.MovieTranslation(
                    language=s.Language.EN.value,
                    title=form_data.title_en,
                    description=form_data.description_en,
                    location=form_data.location_en,
                ),
            ],
            actors=[
                db.scalar(sa.select(m.Actor).where(m.Actor.key == actor_key))
                for actor_key in [actor_key.key for actor_key in form_data.actors_keys]
            ],
            directors=[
                db.scalar(sa.select(m.Director).where(m.Director.key == director_key))
                for director_key in form_data.directors_keys
            ],
            genres=[
                db.scalar(sa.select(m.Genre).where(m.Genre.key == genre_key.key)) for genre_key in form_data.genres
            ],
            subgenres=[
                db.scalar(sa.select(m.Subgenre).where(m.Subgenre.key == subgenre_key.key))
                for subgenre_key in form_data.subgenres
            ],
            specifications=[
                db.scalar(sa.select(m.Specification).where(m.Specification.key == specification_key.key))
                for specification_key in form_data.specifications
            ],
            keywords=[
                db.scalar(sa.select(m.Keyword).where(m.Keyword.key == keyword_key.key))
                for keyword_key in form_data.keywords
            ],
            action_times=[
                db.scalar(sa.select(m.ActionTime).where(m.ActionTime.key == action_time_key.key))
                for action_time_key in form_data.action_times
            ],
        )
        db.add(new_movie)
        db.commit()
        log(log.INFO, "Movie [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating movie [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=400, detail="Error creating movie")

    db.refresh(new_movie)

    # Upload poster
    try:
        file_name = f"{new_movie.id}_{file.filename}"
        file_location = f"{UPLOAD_DIRECTORY}{file_name}"

        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())

        new_movie.poster = file_name
        db.commit()
    except Exception as e:
        log(log.ERROR, "Error uploading poster for movie [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error uploading poster for movie")

    # Genres percentage match
    try:
        for percentage_match_dict in form_data.genres:
            genre_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            genre = db.scalar(sa.select(m.Genre).where(m.Genre.key == genre_key))

            if not genre:
                log(log.ERROR, "Genre [%s] not found", genre_key)
                raise Exception(f"Genre [{genre_key}] not found")

            movie_genre = (
                m.movie_genres.update()
                .values({"percentage_match": percentage_match})
                .where(m.movie_genres.c.movie_id == new_movie.id, m.movie_genres.c.genre_id == genre.id)
            )
            db.execute(movie_genre)

        # Subgenres percentage match
        for percentage_match_dict in form_data.subgenres:
            subgenre_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            subgenre = db.scalar(sa.select(m.Subgenre).where(m.Subgenre.key == subgenre_key))

            if not subgenre:
                log(log.ERROR, "Subgenre [%s] not found", subgenre_key)
                raise Exception(f"Subgenre [{subgenre_key}] not found")

            movie_subgenre = (
                m.movie_subgenres.update()
                .values({"percentage_match": percentage_match})
                .where(m.movie_subgenres.c.movie_id == new_movie.id, m.movie_subgenres.c.subgenre_id == subgenre.id)
            )
            db.execute(movie_subgenre)

        # Specifications percentage match
        for percentage_match_dict in form_data.specifications:
            specification_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            specification = db.scalar(sa.select(m.Specification).where(m.Specification.key == specification_key))

            if not specification:
                log(log.ERROR, "Specification [%s] not found", specification_key)
                raise Exception(f"Specification [{specification_key}] not found")

            movie_specification = (
                m.movie_specifications.update()
                .values({"percentage_match": percentage_match})
                .where(
                    m.movie_specifications.c.movie_id == new_movie.id,
                    m.movie_specifications.c.specification_id == specification.id,
                )
            )
            db.execute(movie_specification)

        # Keywords percentage match
        for percentage_match_dict in form_data.keywords:
            keyword_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            keyword = db.scalar(sa.select(m.Keyword).where(m.Keyword.key == keyword_key))

            if not keyword:
                log(log.ERROR, "Keyword [%s] not found", keyword_key)
                raise Exception(f"Keyword [{keyword_key}] not found")

            movie_keyword = (
                m.movie_keywords.update()
                .values({"percentage_match": percentage_match})
                .where(m.movie_keywords.c.movie_id == new_movie.id, m.movie_keywords.c.keyword_id == keyword.id)
            )
            db.execute(movie_keyword)

        # Action times percentage match
        for percentage_match_dict in form_data.action_times:
            action_time_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            action_time = db.scalar(sa.select(m.ActionTime).where(m.ActionTime.key == action_time_key))

            if not action_time:
                log(log.ERROR, "Action time [%s] not found", action_time_key)
                raise Exception(f"Action time [{action_time_key}] not found")

            movie_action_time = (
                m.movie_action_times.update()
                .values({"percentage_match": percentage_match})
                .where(
                    m.movie_action_times.c.movie_id == new_movie.id,
                    m.movie_action_times.c.action_time_id == action_time.id,
                )
            )
            db.execute(movie_action_time)
    except Exception as e:
        log(log.ERROR, "Error updating percentage match: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating percentage match")

    # # Create characters
    try:
        for character in form_data.actors_keys:
            new_character = m.Character(
                key=character.character_key,
                translations=[
                    m.CharacterTranslation(
                        language=s.Language.UK.value,
                        name=character.character_name_uk,
                    ),
                    m.CharacterTranslation(
                        language=s.Language.EN.value,
                        name=character.character_name_en,
                    ),
                ],
                actors=[db.scalar(sa.select(m.Actor).where(m.Actor.key == character.key))],
                movies=[db.scalar(sa.select(m.Movie).where(m.Movie.id == new_movie.id))],
            )

            db.add(new_character)
            db.commit()
            log(log.INFO, "Character [%s] successfully created", character.character_key)
    except Exception as e:
        log(log.ERROR, "Error creating character [%s]: %s", character.character_key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating character")

    # Save characters to json file
    try:
        characters = db.scalars(sa.select(m.Character)).all()
        if not characters:
            log(log.ERROR, "Characters not found")
            raise HTTPException(status_code=404, detail="Characters not found")

        characters_to_file = []
        for char in characters:
            characters_to_file.append(
                s.CharacterExportCreate(
                    id=char.id,
                    key=char.key,
                    name_uk=next((t.name for t in char.translations if t.language == s.Language.UK.value)),
                    name_en=next((t.name for t in char.translations if t.language == s.Language.EN.value)),
                    actors_ids=[actor.id for actor in char.actors],
                    movies_ids=[movie.id for movie in char.movies],
                )
            )

        with open("data/characters.json", "w") as file_json:
            json.dump(s.CharactersJSONFile(characters=characters_to_file).model_dump(mode="json"), file_json, indent=4)
            print("Characters data saved to [data/characters.json] file")
    except Exception as e:
        log(log.ERROR, "Error saving characters data to [data/characters.json] file: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error saving characters data to [data/characters.json] file",
        )

    # # Import characters to google spreadsheets
    from app.commands.imports_from_google_sheet.import_characters import import_characters_to_google_spreadsheets

    try:
        import_characters_to_google_spreadsheets(len(form_data.actors_keys))

        log(log.INFO, "Characters data imported to google spreadsheets")
    except Exception as e:
        log(log.ERROR, "Error importing characters data to google spreadsheets: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error importing characters data to google spreadsheets"
        )

    # Add rating
    try:
        new_rating = m.Rating(
            # id=rating.id,
            movie_id=new_movie.id,
            user_id=current_user,
            rating=form_data.rating,
            acting=form_data.rating_criteria.acting,
            plot_storyline=form_data.rating_criteria.plot_storyline,
            music=form_data.rating_criteria.music,
            re_watchability=form_data.rating_criteria.re_watchability,
            emotional_impact=form_data.rating_criteria.emotional_impact,
            dialogue=form_data.rating_criteria.dialogue,
            production_design=form_data.rating_criteria.production_design,
            duration=form_data.rating_criteria.duration,
            visual_effects=form_data.rating_criteria.visual_effects,
            scare_factor=form_data.rating_criteria.scare_factor,
            # comment=form_data.rating_criteria.comment,
        )

        db.add(new_rating)
        db.commit()
        log(log.INFO, "Rating [%s] successfully created")
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error creating rating for movie [%s]: %s", new_movie.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating rating")

    # Save ratings to json file
    try:
        ratings = db.scalars(sa.select(m.Rating).order_by(m.Rating.id)).all()
        if not ratings:
            log(log.ERROR, "Ratings not found")
            raise HTTPException(status_code=404, detail="Ratings not found")

        ratings_to_file = []

        for rating in ratings:
            ratings_to_file.append(
                s.RatingExportCreate(
                    id=rating.id,
                    rating=rating.rating,
                    movie_id=rating.movie_id,
                    user_id=current_user,
                    acting=rating.acting,
                    plot_storyline=rating.plot_storyline,
                    music=rating.music,
                    re_watchability=rating.re_watchability,
                    emotional_impact=rating.emotional_impact,
                    dialogue=rating.dialogue,
                    production_design=rating.production_design,
                    duration=rating.duration,
                    visual_effects=rating.visual_effects if rating.visual_effects else None,
                    scare_factor=rating.scare_factor if rating.scare_factor else None,
                    comment=rating.comment if rating.comment else None,
                )
            )

        with open("data/ratings.json", "w") as file_json:
            json.dump(s.RatingsJSONFile(ratings=ratings_to_file).model_dump(mode="json"), file_json, indent=4)
        print("Ratings data saved to [data/ratings.json] file")
    except Exception as e:
        db.rollback()
        log(log.ERROR, "Error saving ratings data to [data/ratings.json] file: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error saving ratings data to [data/ratings.json] file"
        )

    # Import rating to google spreadsheets
    from app.commands.imports_from_google_sheet.import_ratings import import_ratings_to_google_spreadsheets

    try:
        import_ratings_to_google_spreadsheets()

        log(log.INFO, "Ratings data imported to google spreadsheets")
    except Exception as e:
        log(log.ERROR, "Error importing ratings data to google spreadsheets: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error importing ratings data to google spreadsheets"
        )

    # Add movie to json file
    try:
        movies = db.scalars(sa.select(m.Movie)).all()

        movies_to_file = []

        for movie in movies:
            movies_to_file.append(
                s.MovieExportCreate(
                    id=movie.id,
                    key=movie.key,
                    title_uk=next((t.title for t in movie.translations if t.language == s.Language.UK.value)),
                    title_en=next((t.title for t in movie.translations if t.language == s.Language.EN.value)),
                    description_uk=next(
                        (t.description for t in movie.translations if t.language == s.Language.UK.value)
                    ),
                    description_en=next(
                        (t.description for t in movie.translations if t.language == s.Language.EN.value)
                    ),
                    # release_date=datetime.strptime(movie.release_date, "%d.%m.%Y"),
                    release_date=movie.release_date,
                    duration=int(movie.duration),
                    budget=int(movie.budget),
                    domestic_gross=int(movie.domestic_gross) if movie.domestic_gross else None,
                    worldwide_gross=int(movie.worldwide_gross) if movie.worldwide_gross else None,
                    poster=movie.poster,
                    actors_ids=[actor.id for actor in movie.actors],
                    directors_ids=[director.id for director in movie.directors],
                    location_uk=next((t.location for t in movie.translations if t.language == s.Language.UK.value)),
                    location_en=next((t.location for t in movie.translations if t.language == s.Language.EN.value)),
                    # Genres
                    genres_list=[
                        {
                            genre.id: next(
                                (
                                    mg.percentage_match
                                    for mg in db.query(m.movie_genres).filter_by(movie_id=movie.id, genre_id=genre.id)
                                ),
                                0.0,
                            )
                        }
                        for genre in movie.genres
                    ],
                    genres_ids=[genre.id for genre in movie.genres],
                    # Subgenres
                    subgenres_list=[
                        {
                            subgenre.id: next(
                                (
                                    mg.percentage_match
                                    for mg in db.query(m.movie_subgenres).filter_by(
                                        movie_id=movie.id, subgenre_id=subgenre.id
                                    )
                                ),
                                0.0,
                            )
                        }
                        for subgenre in movie.subgenres
                    ]
                    if movie.subgenres
                    else None,
                    subgenres_ids=[subgenre.id for subgenre in movie.subgenres] if movie.subgenres else None,
                    # users_ratings=users_rating,
                    rating_criterion=s.RatingCriterion(movie.rating_criterion),
                    # Specifications
                    specifications_ids=[specification.id for specification in movie.specifications],
                    specifications_list=[
                        {
                            specification.id: next(
                                (
                                    mg.percentage_match
                                    for mg in db.query(m.movie_specifications).filter_by(
                                        movie_id=movie.id, specification_id=specification.id
                                    )
                                ),
                                0.0,
                            )
                        }
                        for specification in movie.specifications
                    ],
                    # Keyword
                    keywords_ids=[keyword.id for keyword in movie.keywords],
                    keywords_list=[
                        {
                            keyword.id: next(
                                (
                                    mg.percentage_match
                                    for mg in db.query(m.movie_keywords).filter_by(
                                        movie_id=movie.id, keyword_id=keyword.id
                                    )
                                ),
                                0.0,
                            )
                        }
                        for keyword in movie.keywords
                    ],
                    # Action times
                    action_times_ids=[action_time.id for action_time in movie.action_times],
                    action_times_list=[
                        {
                            action_time.id: next(
                                (
                                    mg.percentage_match
                                    for mg in db.query(m.movie_action_times).filter_by(
                                        movie_id=movie.id, action_time_id=action_time.id
                                    )
                                ),
                                0.0,
                            )
                        }
                        for action_time in movie.action_times
                    ],
                    # rating_criterion=s.RatingCriterion(rating_criterion),
                )
            )

        print("Movies COUNT: ", len(movies_to_file))

        with open("data/movies.json", "w") as file_json:
            json.dump(s.MoviesJSONFile(movies=movies_to_file).model_dump(mode="json"), file_json, indent=4)
            print("Movies data saved to [data/movies.json] file")
    except Exception as e:
        log(log.ERROR, "Error saving movies data to [data/movies.json] file: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error saving movies data to [data/movies.json] file"
        )

    from app.commands.imports_from_google_sheet.import_movies import append_data_to_google_spreadsheets

    try:
        append_data_to_google_spreadsheets()

        log(log.INFO, "Movies data imported to google spreadsheets")
    except Exception as e:
        log(log.ERROR, "Error importing movies data to google spreadsheets: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error importing movies data to google spreadsheets"
        )

    return {"info": "Movie created successfully"}


@movie_router.get(
    "/pre-create/",
    response_model=s.MoviePreCreateData,
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Data not found"}},
)
def get_pre_create_data(
    # movie_in: s.MovieIn,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get pre-create data for a new movie"""

    last_movie_id = db.scalar(sa.select(m.Movie.id).order_by(sa.desc(m.Movie.id)).limit(1))
    if not last_movie_id:
        log(log.ERROR, "Last movie ID not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data not found")

    next_movie_id = last_movie_id + 1

    actors = db.scalars(sa.select(m.Actor)).all()
    if not actors:
        log(log.ERROR, "Actors [%s] not found")
        raise HTTPException(status_code=404, detail="Actors not found")

    directors = db.scalars(sa.select(m.Director)).all()
    if not directors:
        log(log.ERROR, "Director [%s] not found")
        raise HTTPException(status_code=404, detail="Director not found")

    genres = (
        db.scalars(sa.select(m.Genre).options(joinedload(m.Genre.subgenres), joinedload(m.Genre.translations)))
        .unique()
        .all()
    )
    if not genres:
        log(log.ERROR, "Genres [%s] not found")
        raise HTTPException(status_code=404, detail="Genres not found")

    specifications = db.scalars(sa.select(m.Specification)).all()
    if not specifications:
        log(log.ERROR, "Specifications [%s] not found")
        raise HTTPException(status_code=404, detail="Specifications not found")

    keywords = db.scalars(sa.select(m.Keyword)).all()
    if not keywords:
        log(log.ERROR, "Keywords [%s] not found")
        raise HTTPException(status_code=404, detail="Keywords not found")

    action_times = db.scalars(sa.select(m.ActionTime)).all()
    if not action_times:
        log(log.ERROR, "Action times [%s] not found")
        raise HTTPException(status_code=404, detail="Action times not found")

    actors_out = []

    for actor in actors:
        actors_out.append(
            s.ActorOut(
                key=actor.key,
                full_name=actor.full_name(lang),
            )
        )

    directors_out = []

    for director in directors:
        directors_out.append(
            s.DirectorOut(
                key=director.key,
                full_name=director.full_name(lang),
            )
        )

    specifications_out = []

    for specification in specifications:
        specifications_out.append(
            s.SpecificationOut(
                key=specification.key,
                name=next((t.name for t in specification.translations if t.language == lang.value)),
                description=next((t.description for t in specification.translations if t.language == lang.value)),
            )
        )

    genres_out = []

    for genre in genres:
        genres_out.append(
            s.GenreOut(
                key=genre.key,
                name=next((t.name for t in genre.translations if t.language == lang.value)),
                description=next((t.description for t in genre.translations if t.language == lang.value)),
                subgenres=[
                    s.SubgenreOut(
                        key=subgenre.key,
                        name=next((t.name for t in subgenre.translations if t.language == lang.value)),
                        description=next((t.description for t in subgenre.translations if t.language == lang.value)),
                        parent_genre_key=subgenre.genre.key,
                    )
                    for subgenre in genre.subgenres
                ],
            )
        )

    keywords_out = []
    for keyword in keywords:
        keywords_out.append(
            s.KeywordOut(
                key=keyword.key,
                name=next((t.name for t in keyword.translations if t.language == lang.value)),
                description=next((t.description for t in keyword.translations if t.language == lang.value)),
            )
        )

    action_times_out = []
    for action_time in action_times:
        action_times_out.append(
            s.ActionTimeOut(
                key=action_time.key,
                name=next((t.name for t in action_time.translations if t.language == lang.value)),
                description=next((t.description for t in action_time.translations if t.language == lang.value)),
            )
        )

    return s.MoviePreCreateData(
        next_movie_id=next_movie_id,
        actors=actors_out,
        directors=directors_out,
        specifications=specifications_out,
        genres=genres_out,
        keywords=keywords_out,
        action_times=action_times_out,
    )
