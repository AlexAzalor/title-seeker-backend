import os
from typing import Annotated

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile
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
    response_model=s.MovieOutList,
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
            s.MovieOut(
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
                        character_name=next((t.character_name for t in actor.translations if t.language == lang.value)),
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
                    )
                    for genre in movie.genres
                ],
                subgenres=[
                    s.MovieSubgenre(
                        key=subgenre.key,
                        parent_genre=s.MovieGenre(
                            key=subgenre.genre.key,
                            name=next((t.name for t in subgenre.genre.translations if t.language == lang.value)),
                            description=next(
                                (t.description for t in subgenre.genre.translations if t.language == lang.value)
                            ),
                        ),
                        name=next((t.name for t in subgenre.translations if t.language == lang.value)),
                        description=next((t.description for t in subgenre.translations if t.language == lang.value)),
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
                rating_criterion=s.RatingCriterion(movie.rating_criterion),
            )
        )

    return s.MovieOutList(movies=movies_out)


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
        sa.select(m.Movie).where(m.Movie.key == movie_key).options(joinedload(m.Movie.translations))
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
                character_name=next((t.character_name for t in actor.translations if t.language == lang.value)),
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
                ),
                name=next((t.name for t in subgenre.translations if t.language == lang.value)),
                description=next((t.description for t in subgenre.translations if t.language == lang.value)),
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
    )


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
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get movies by query params"""

    query = sa.select(m.Movie).options(joinedload(m.Movie.translations))

    if actor_name:
        query = query.where(sa.and_(*[m.Movie.actors.any(m.Actor.key == actor_key) for actor_key in actor_name]))

    if director_name:
        query = query.where(m.Movie.directors.any(m.Director.key.in_(director_name)))
        # query = query.where(
        #     sa.and_(*[m.Movie.directors.any(m.Director.key == director_key) for director_key in director_name])
        # )

    if genre_name:
        query = query.where(sa.and_(*[m.Movie.genres.any(m.Genre.key == genre_key) for genre_key in genre_name]))

    if subgenre_name:
        query = query.where(
            sa.and_(*[m.Movie.subgenres.any(m.Subgenre.key == subgenre_key) for subgenre_key in subgenre_name])
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
async def get_movie_filters(
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
                    )
                    for subgenre in genre.subgenres
                ],
            )
        )
    return s.MovieFiltersListOut(genres=genres_out, actors=actors_out, directors=directors_out)
