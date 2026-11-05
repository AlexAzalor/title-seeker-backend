import sqlalchemy as sa
from sqlalchemy.orm import Session

import app.models as m
import app.schema as s

BASE = s.RelatedMovie.BASE.value


class CollectionError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_movie_or_error(db: Session, key: str) -> m.Movie:
    movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == key, m.Movie.is_deleted.is_(False)))
    if not movie:
        raise CollectionError(f"Movie [{key}] not found", 404)
    return movie


def get_collection_base(movie: m.Movie) -> m.Movie | None:
    """Base movie of the collection the movie belongs to (None for standalone movies)"""
    if movie.collection_base_movie_id:
        return movie.collection_base_movie
    if movie.relation_type == BASE:
        return movie
    return None


def get_collection_movies(db: Session, base: m.Movie) -> list[m.Movie]:
    members = db.scalars(sa.select(m.Movie).where(m.Movie.collection_base_movie_id == base.id)).all()
    return sorted(
        [base, *members],
        key=lambda mov: (mov.collection_order if mov.collection_order is not None else float("inf"), mov.id),
    )


def _renumber(movies: list[m.Movie], moved: m.Movie | None = None, position: int | None = None):
    """Make orders contiguous (1..n). The moved movie is placed at `position` (1-based)."""
    rest = [mov for mov in movies if mov is not moved]
    if moved is not None:
        index = len(rest) if position is None else max(0, min(position - 1, len(rest)))
        rest.insert(index, moved)
    for i, mov in enumerate(rest, start=1):
        mov.collection_order = i


def build_collection_out(db: Session, movie: m.Movie) -> s.MovieCollectionOut:
    base = get_collection_base(movie)
    movies = get_collection_movies(db, base) if base else [movie]
    return s.MovieCollectionOut(
        base_movie_key=base.key if base else None,
        movies=[
            s.MovieCollectionItemOut(
                key=mov.key,
                title=mov.get_title(),
                poster=mov.poster,
                relation_type=s.RelatedMovie(mov.relation_type) if mov.relation_type else None,
                collection_order=mov.collection_order,
            )
            for mov in movies
        ],
    )


def add_movie_to_collection(db: Session, form_data: s.MovieCollectionAdd) -> m.Movie:
    """Link a movie to the target's collection. A standalone target becomes the base of a new collection."""
    if form_data.relation_type == s.RelatedMovie.BASE:
        raise CollectionError("Relation type 'base' is assigned automatically")

    movie = get_movie_or_error(db, form_data.movie_key)
    target = get_movie_or_error(db, form_data.target_movie_key)

    if movie.id == target.id:
        raise CollectionError("A movie cannot be linked to itself")
    if movie.relation_type or movie.collection_base_movie_id:
        raise CollectionError("Movie is already in a collection")

    base = get_collection_base(target)
    if base is None:
        base = target
        base.relation_type = BASE
        base.collection_base_movie_id = None
        base.collection_order = 1

    movies = get_collection_movies(db, base)
    movie.relation_type = form_data.relation_type.value
    movie.collection_base_movie_id = base.id
    _renumber(movies, movie, form_data.collection_order)
    db.flush()
    return base


def update_collection_movie(db: Session, form_data: s.MovieCollectionUpdate) -> m.Movie:
    movie = get_movie_or_error(db, form_data.movie_key)
    base = get_collection_base(movie)
    if base is None:
        raise CollectionError("Movie is not in a collection", 404)

    if form_data.relation_type is not None:
        if movie.id == base.id:
            if form_data.relation_type != s.RelatedMovie.BASE:
                raise CollectionError("Base movie relation type cannot be changed")
        elif form_data.relation_type == s.RelatedMovie.BASE:
            raise CollectionError("Only one base movie is allowed in a collection")
        else:
            movie.relation_type = form_data.relation_type.value

    if form_data.collection_order is not None:
        _renumber(get_collection_movies(db, base), movie, form_data.collection_order)

    db.flush()
    return base


def remove_movie_from_collection(db: Session, movie_key: str) -> m.Movie | None:
    """Unlink a movie. Returns the collection base left, or None if the collection was dissolved."""
    movie = get_movie_or_error(db, movie_key)
    base = get_collection_base(movie)
    if base is None:
        raise CollectionError("Movie is not in a collection", 404)

    movies = get_collection_movies(db, base)
    remaining = [mov for mov in movies if mov is not movie]

    movie.relation_type = None
    movie.collection_base_movie_id = None
    movie.collection_order = None

    if len(remaining) <= 1:
        # A collection of one movie makes no sense: dissolve it
        for mov in remaining:
            mov.relation_type = None
            mov.collection_base_movie_id = None
            mov.collection_order = None
        db.flush()
        return None

    if movie.id == base.id:
        # Promote the first remaining movie to base
        new_base = remaining[0]
        new_base.relation_type = BASE
        new_base.collection_base_movie_id = None
        for mov in remaining[1:]:
            mov.collection_base_movie_id = new_base.id
        base = new_base

    _renumber(remaining)
    db.flush()
    return base
