import sqlalchemy as sa
from sqlalchemy.orm import Session, selectinload

import app.models as m
import app.schema as s
from api.controllers.super_search import genre_match_condition, specification_match_condition


def tournament_query(settings: s.MovieTournamentIn):
    query = sa.select(m.Movie, sa.func.count().over().label("total")).options(
        selectinload(m.Movie.translations), selectinload(m.Movie.ratings)
    )
    include_conditions = [
        genre_match_condition(key, settings.genre_threshold, 100) for key in settings.include_genres
    ] + [
        specification_match_condition(key, settings.specification_threshold, 100)
        for key in settings.include_specifications
    ]
    if include_conditions:
        query = query.where(sa.or_(*include_conditions))
    if settings.exclude_genres:
        query = query.where(~m.Movie.genres.any(m.Genre.key.in_(settings.exclude_genres)))
    if settings.exclude_specifications:
        query = query.where(~m.Movie.specifications.any(m.Specification.key.in_(settings.exclude_specifications)))
    if settings.exclude_movies:
        excluded_collection_bases = sa.select(m.Movie.id).where(m.Movie.key.in_(settings.exclude_movies))
        query = query.where(
            m.Movie.id.not_in(excluded_collection_bases),
            sa.or_(
                m.Movie.collection_base_movie_id.is_(None),
                m.Movie.collection_base_movie_id.not_in(excluded_collection_bases),
            ),
        )
    if settings.exclude_shared_universes:
        query = query.where(~m.Movie.shared_universe.has(m.SharedUniverse.key.in_(settings.exclude_shared_universes)))
    if settings.collection_type == s.TournamentCollectionType.STANDALONE:
        query = query.where(
            m.Movie.relation_type.is_(None),
            m.Movie.collection_base_movie_id.is_(None),
            ~m.Movie.collection_members.any(),
            m.Movie.shared_universe_id.is_(None),
        )
    elif settings.collection_type == s.TournamentCollectionType.BASE:
        query = query.where(m.Movie.relation_type == s.RelatedMovie.BASE.value)
    return query.order_by(sa.func.random()).limit(settings.size)


def get_tournament_pool(db: Session, settings: s.MovieTournamentIn) -> tuple[list[m.Movie], int]:
    rows = db.execute(tournament_query(settings)).all()
    return [row[0] for row in rows], rows[0].total if rows else 0
