import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

import app.models as m
import app.schema as s
from app.database import get_db
from app.logger import log
from config import config

CFG = config()

movie_router = APIRouter(prefix="/movies", tags=["Movies"])


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
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get movies by query params"""

    db_movies = (
        db.scalars(
            sa.select(m.Movie)
            .where(m.Movie.is_deleted.is_(False))
            .options(joinedload(m.Movie.translations))
            .order_by(m.Movie.release_date.desc())
        )
        .unique()
        .all()
    )

    movies_out = []
    for movie in db_movies:
        movies_out.append(
            s.MovieOut(
                uuid=movie.uuid,
                title=next((t.title for t in movie.translations if t.language == lang.value)),
                description=next((t.description for t in movie.translations if t.language == lang.value)),
                budget=movie.formatted_budget,
                duration=movie.formatted_duration(lang.value),
                domestic_gross=movie.formatted_domestic_gross,
                worldwide_gross=movie.formatted_worldwide_gross,
                release_date=movie.release_date,
                actors=[
                    s.MovieActor(
                        uuid=actor.uuid,
                        first_name=next((t.first_name for t in actor.translations if t.language == lang.value)),
                        last_name=next((t.last_name for t in actor.translations if t.language == lang.value)),
                        character_name=next((t.character_name for t in actor.translations if t.language == lang.value)),
                        avatar_url=actor.avatar,
                    )
                    for actor in movie.actors
                ],
            )
        )

    return s.MovieOutList(movies=movies_out)


@movie_router.get(
    "/{movie_uuid}",
    status_code=status.HTTP_200_OK,
    response_model=s.MovieOut,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Movie not found"},
    },
)
def get_movie(
    movie_uuid: str,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    movie: m.Movie | None = db.scalar(
        sa.select(m.Movie).where(m.Movie.uuid == movie_uuid).options(joinedload(m.Movie.translations))
    )
    if not movie:
        log(log.ERROR, "Movie [%s] not found", movie_uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found")

    return s.MovieOut(
        uuid=movie.uuid,
        title=next((t.title for t in movie.translations if t.language == lang.value)),
        description=next((t.description for t in movie.translations if t.language == lang.value)),
        budget=movie.formatted_budget,
        duration=movie.formatted_duration(lang.value),
        domestic_gross=movie.formatted_domestic_gross,
        worldwide_gross=movie.formatted_worldwide_gross,
        release_date=movie.release_date,
        actors=[
            s.MovieActor(
                uuid=actor.uuid,
                first_name=next((t.first_name for t in actor.translations if t.language == lang.value)),
                last_name=next((t.last_name for t in actor.translations if t.language == lang.value)),
                character_name=next((t.character_name for t in actor.translations if t.language == lang.value)),
                avatar_url=actor.avatar,
            )
            for actor in movie.actors
        ],
    )
