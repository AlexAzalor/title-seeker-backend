import os

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
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
                poster=movie.poster,
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
                directors=[
                    s.MovieDirector(
                        uuid=director.uuid,
                        first_name=next((t.first_name for t in director.translations if t.language == lang.value)),
                        last_name=next((t.last_name for t in director.translations if t.language == lang.value)),
                        avatar_url=director.avatar,
                    )
                    for director in movie.directors
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
        poster=movie.poster,
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
        directors=[
            s.MovieDirector(
                uuid=director.uuid,
                first_name=next((t.first_name for t in director.translations if t.language == lang.value)),
                last_name=next((t.last_name for t in director.translations if t.language == lang.value)),
                avatar_url=director.avatar,
            )
            for director in movie.directors
        ],
    )


@movie_router.post("/upload-poster/{movie_id}", status_code=status.HTTP_200_OK)
async def upload_poster(movie_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload poster for movie"""

    file_name = f"{movie_id}_{file.filename}"
    file_location = f"{UPLOAD_DIRECTORY}{file_name}"

    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    movie = db.query(m.Movie).filter(m.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

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
