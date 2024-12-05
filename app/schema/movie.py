from datetime import datetime

from pydantic import BaseModel, ConfigDict

from config import config

CFG = config()


class MovieExportCreate(BaseModel):
    key: str
    title_uk: str
    title_en: str
    description_uk: str
    description_en: str
    release_date: datetime
    duration: int
    budget: int
    domestic_gross: int | None = None
    worldwide_gross: int | None = None
    poster: str | None = None
    genres_ids: list[int]
    subgenres_ids: list[int] | None = None
    location_uk: str
    location_en: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class MoviesJSONFile(BaseModel):
    movies: list[MovieExportCreate]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieActor(BaseModel):
    key: str
    first_name: str
    last_name: str
    character_name: str
    avatar_url: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieDirector(BaseModel):
    key: str
    first_name: str
    last_name: str
    avatar_url: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieGenre(BaseModel):
    key: str
    name: str
    description: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieSubgenre(BaseModel):
    key: str
    parent_genre: MovieGenre
    name: str
    description: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieGenres(BaseModel):
    genres: list[MovieGenre]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieOut(BaseModel):
    key: str
    title: str
    description: str
    release_date: datetime | None = None
    duration: str
    budget: str
    domestic_gross: str | None = None
    worldwide_gross: str | None = None
    actors: list[MovieActor] = []
    poster: str | None = None
    directors: list[MovieDirector] = []
    genres: list[MovieGenre] = []
    subgenres: list[MovieSubgenre] = []

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieOutList(BaseModel):
    movies: list[MovieOut]

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieSearchOut(BaseModel):
    key: str
    title: str
    poster: str | None = None
    release_date: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieByGenresList(BaseModel):
    movies: list[MovieSearchOut]
    genre: MovieGenre | None = None
    subgenre: MovieSubgenre | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ActorShort(BaseModel):
    key: str
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class MovieByActorsList(BaseModel):
    movies: list[MovieSearchOut]
    actor: list[ActorShort] | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
