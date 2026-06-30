"""Populates the movie_similarities pre-computed cache table.

Run after adding new movies or after any bulk filter-assignment change:
    flask recalculate-filter-counts   # refresh movie_count first
    flask calculate-similarities      # then recompute scores

Process:
  1. Load all non-deleted movies with collection/universe relationships.
  2. Extract MovieFeatures for each (filter keys + percentage_match + movie_count).
  3. Iterate every unique pair (movie_a, movie_b) where movie_a.id < movie_b.id.
  4. Skip pairs where either movie excludes the other (collection / shared universe).
  5. Compute similarity score via the engine.
  6. Skip pairs below min_score_threshold.
  7. Upsert into movie_similarities (insert new, update score + computed_at if changed).
  8. Delete stale pairs (pairs that no longer exist or fell below threshold).

For 500 movies: ~125k pairs, ~2k filter queries for extraction.
Typical runtime: 5–30 seconds depending on DB latency. Acceptable for an offline command.
"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session, selectinload

from app.database import db
from app import models as m
from app.services.similarity_config import DEFAULT_SIMILARITY_CONFIG
from app.services.similarity_engine import compute_similarity, extract_features


def calculate_similarities() -> None:
    """Entry point called by the Flask CLI command."""
    config = DEFAULT_SIMILARITY_CONFIG

    with db.begin() as session:
        movies = _load_movies(session)
        total = len(movies)
        print(f"Loaded {total} movies. Computing pairwise similarities...")

        features_map = {}
        for movie in movies:
            features_map[movie.id] = extract_features(session, movie)

        pairs_upserted = 0
        pairs_skipped = 0

        # Collect all computed pairs: {(a_id, b_id): score}
        computed: dict[tuple[int, int], float] = {}

        for i, movie_a in enumerate(movies):
            fa = features_map[movie_a.id]

            for movie_b in movies[i + 1 :]:
                fb = features_map[movie_b.id]

                # Skip pairs where either movie excludes the other
                if movie_b.key in fa.excluded_keys or movie_a.key in fb.excluded_keys:
                    pairs_skipped += 1
                    continue

                score = compute_similarity(fa, fb, config)

                if score < config.min_score_threshold:
                    pairs_skipped += 1
                    continue

                # Enforce invariant: movie_a_id < movie_b_id
                a_id = min(movie_a.id, movie_b.id)
                b_id = max(movie_a.id, movie_b.id)
                computed[(a_id, b_id)] = round(score, 6)

        # Upsert computed pairs
        existing = {
            (row.movie_a_id, row.movie_b_id): row for row in session.scalars(sa.select(m.MovieSimilarity)).all()
        }

        now = datetime.utcnow()

        for (a_id, b_id), score in computed.items():
            if (a_id, b_id) in existing:
                row = existing[(a_id, b_id)]
                row.score = score
                row.computed_at = now
            else:
                session.add(
                    m.MovieSimilarity(
                        movie_a_id=a_id,
                        movie_b_id=b_id,
                        score=score,
                        computed_at=now,
                    )
                )
            pairs_upserted += 1

        # Clean up stale pairs (movies deleted or dropped below threshold)
        stale_keys = set(existing.keys()) - set(computed.keys())
        if stale_keys:
            stale_ids = [existing[k].id for k in stale_keys]
            session.execute(sa.delete(m.MovieSimilarity).where(m.MovieSimilarity.id.in_(stale_ids)))
            print(f"Removed {len(stale_ids)} stale similarity pairs.")

        print(f"Done. Upserted: {pairs_upserted} pairs. " f"Skipped (related/low-score): {pairs_skipped} pairs.")


def _load_movies(session: Session) -> list[m.Movie]:
    """Load all non-deleted movies with relationships needed for exclusion logic."""
    return list(
        session.scalars(
            sa.select(m.Movie)
            .where(m.Movie.is_deleted.is_(False))
            .options(
                selectinload(m.Movie.collection_base_movie),
                # collection_members is a backref — loaded via collection_base_movie
                selectinload(m.Movie.shared_universe).selectinload(m.SharedUniverse.movies),
            )
            .order_by(m.Movie.id)
        )
        .unique()
        .all()
    )
