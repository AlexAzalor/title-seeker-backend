import sqlalchemy as sa
from sqlalchemy.orm import Session, selectinload

import app.models as m
import app.schema as s

BASE = s.RelatedMovie.BASE.value


class CollectionError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _get_movie(db: Session, key: str) -> m.Movie:
    movie = db.scalar(sa.select(m.Movie).where(m.Movie.key == key, m.Movie.is_deleted.is_(False)))
    if not movie:
        raise CollectionError(f"Movie [{key}] not found", 404)
    return movie


def _item_out(movie: m.Movie) -> s.MovieStandaloneItemOut:
    return s.MovieStandaloneItemOut(
        key=movie.key,
        title=movie.get_title(),
        poster=movie.poster,
        relation_type=s.RelatedMovie(movie.relation_type) if movie.relation_type else None,
        collection_order=movie.collection_order,
        name=movie.get_title(),
    )


def _sort_key(movie: m.Movie):
    return (movie.collection_order if movie.collection_order is not None else float("inf"), movie.id)


def get_standalone_movies_data(db: Session, lang: s.Language = s.Language.UK) -> s.MovieStandaloneList:
    bases = db.scalars(
        sa.select(m.Movie)
        .options(selectinload(m.Movie.translations))
        .join(m.Movie.translations)
        .where(m.Movie.relation_type.is_(None), m.MovieTranslation.language == lang.value)
        .order_by(
            # Ignore "The" at the beginning of the title (not remove)
            sa.func.regexp_replace(m.MovieTranslation.title, r"^(The\s)", "", "i"),
        )
    ).all()
    return s.MovieStandaloneList(
        bases=[
            s.MovieStandaloneOut(
                **_item_out(base).model_dump(),
                movies=[_item_out(mov) for mov in sorted(base.collection_members, key=_sort_key)],
            )
            for base in bases
        ]
    )


def update_collection(db: Session, form_data: s.MovieEditCollection) -> None:
    """Sync collection members with the form. The base movie is never deleted and its type is fixed;
    only its order can change."""
    base = _get_movie(db, form_data.base_movie_key)

    if base.collection_base_movie_id:
        raise CollectionError("Movie is a member of another collection and cannot be a base")
    is_new_base = base.relation_type != BASE
    if is_new_base and base.relation_type:
        raise CollectionError("Movie has an invalid relation state")

    # The base may be in the list, but only to change its order (its type is fixed)
    base_item = next((item for item in form_data.movies if item.movie_key == base.key), None)
    if base_item and base_item.relation_type != s.RelatedMovie.BASE:
        raise CollectionError("Base movie type cannot be changed")
    items = [item for item in form_data.movies if item is not base_item]

    keys = [item.movie_key for item in items]
    if len(set(keys)) != len(keys):
        raise CollectionError("Duplicate movies in the list")
    if any(item.relation_type == s.RelatedMovie.BASE for item in items):
        raise CollectionError("Relation type 'base' cannot be assigned to a member")

    if base_item:
        base_order = base_item.collection_order
    else:
        base_order = 1 if is_new_base or base.collection_order is None else base.collection_order
        # Members removed before the base shift it up, like the members that follow them
        base_order -= sum(
            1
            for mov in base.collection_members
            if mov.key not in keys
            and mov.collection_order is not None
            and not is_new_base
            and mov.collection_order < base_order
        )
        base_order = max(base_order, 1)
        member_orders = {item.collection_order for item in items}
        if base_order in member_orders:
            # Members were reordered around the base: it takes the first free slot (e.g. 1,3 -> base 2)
            base_order = next(n for n in range(1, len(member_orders) + 2) if n not in member_orders)
    orders = [item.collection_order for item in items] + [base_order]
    if len(set(orders)) != len(orders):
        raise CollectionError("Duplicate order values in the list")

    current = {mov.key: mov for mov in base.collection_members}

    new_members: dict[str, m.Movie] = {}
    for key in keys:
        if key in current:
            continue
        movie = _get_movie(db, key)
        if movie.relation_type or movie.collection_base_movie_id:
            raise CollectionError(f"Movie [{key}] is already in a collection")
        new_members[key] = movie

    if not items:
        # A base without members is not a collection: dissolve it
        for movie in current.values():
            movie.relation_type = None
            movie.collection_base_movie_id = None
            movie.collection_order = None
        if not is_new_base:
            base.relation_type = None
            base.collection_order = None
        db.flush()
        return

    if is_new_base:
        base.relation_type = BASE
    base.collection_order = base_order

    for key, movie in current.items():
        if key not in keys:
            movie.relation_type = None
            movie.collection_base_movie_id = None
            movie.collection_order = None

    members = {**current, **new_members}
    for item in items:
        movie = members[item.movie_key]
        movie.relation_type = item.relation_type.value
        movie.collection_base_movie_id = base.id
        movie.collection_order = item.collection_order

    db.flush()
