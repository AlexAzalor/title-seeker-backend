"""Recalculates the denormalized movie_count on all filter entities.

Run after bulk-importing movies or modifying filter assignments:
    flask recalculate-filter-counts

movie_count is used by the similarity engine for rarity weighting:
a filter used by 3 movies is a stronger signal than one used by 300.
"""

import sqlalchemy as sa
from app.database import db
from app import models as m


def recalculate_filter_counts() -> None:
    with db.begin() as session:
        _update_genre_counts(session)
        _update_subgenre_counts(session)
        _update_specification_counts(session)
        _update_keyword_counts(session)
        _update_action_time_counts(session)
    print("Filter counts recalculated.")


def _update_genre_counts(session) -> None:
    counts = dict(
        session.execute(
            sa.select(
                m.movie_genres.c.genre_id,
                sa.func.count(m.movie_genres.c.movie_id).label("cnt"),
            ).group_by(m.movie_genres.c.genre_id)
        ).all()
    )
    genres = session.scalars(sa.select(m.Genre)).all()
    for genre in genres:
        genre.movie_count = counts.get(genre.id, 0)


def _update_subgenre_counts(session) -> None:
    counts = dict(
        session.execute(
            sa.select(
                m.movie_subgenres.c.subgenre_id,
                sa.func.count(m.movie_subgenres.c.movie_id).label("cnt"),
            ).group_by(m.movie_subgenres.c.subgenre_id)
        ).all()
    )
    subgenres = session.scalars(sa.select(m.Subgenre)).all()
    for subgenre in subgenres:
        subgenre.movie_count = counts.get(subgenre.id, 0)


def _update_specification_counts(session) -> None:
    counts = dict(
        session.execute(
            sa.select(
                m.movie_specifications.c.specification_id,
                sa.func.count(m.movie_specifications.c.movie_id).label("cnt"),
            ).group_by(m.movie_specifications.c.specification_id)
        ).all()
    )
    specifications = session.scalars(sa.select(m.Specification)).all()
    for spec in specifications:
        spec.movie_count = counts.get(spec.id, 0)


def _update_keyword_counts(session) -> None:
    counts = dict(
        session.execute(
            sa.select(
                m.movie_keywords.c.keyword_id,
                sa.func.count(m.movie_keywords.c.movie_id).label("cnt"),
            ).group_by(m.movie_keywords.c.keyword_id)
        ).all()
    )
    keywords = session.scalars(sa.select(m.Keyword)).all()
    for keyword in keywords:
        keyword.movie_count = counts.get(keyword.id, 0)


def _update_action_time_counts(session) -> None:
    counts = dict(
        session.execute(
            sa.select(
                m.movie_action_times.c.action_time_id,
                sa.func.count(m.movie_action_times.c.movie_id).label("cnt"),
            ).group_by(m.movie_action_times.c.action_time_id)
        ).all()
    )
    action_times = session.scalars(sa.select(m.ActionTime)).all()
    for action_time in action_times:
        action_time.movie_count = counts.get(action_time.id, 0)
