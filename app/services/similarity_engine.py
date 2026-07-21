"""Deterministic semantic movie similarity engine.

Philosophy
----------
This is NOT a recommendation system. It is a semantic matching system.
The goal is to find movies that share a similar experience/atmosphere/feeling,
not movies with identical metadata.

Scoring pipeline for a (movie_a, movie_b) pair:
  1. For each filter type (genres, subgenres, specifications, keywords):
     a. Identify which filters overlap between the two movies.
     b. For each overlapping filter, compute a raw contribution:
        - percentage agreement: how close their percentage_match values are
          within the allowed tolerance for that filter type.
        - rarity bonus: rare filters (low movie_count) contribute more.
     c. Sum contributions → raw type score.
     d. Normalize by the number of filters compared → type score in [0, 1].
  2. Multiply each type score by its configured weight.
  3. Sum weighted type scores → raw total.
  4. Normalize raw total by total possible weight → final score in [0, 1].

Range matching
--------------
Genres:      ±60  — covers the full 40–100 spread in the 5-step percentage system
                    (20 is filtered out as noise before scoring)
Subgenres:   exact key overlap, no range — they ARE the structural signal
Specifications: ±20 — vibe can overlap even with moderate difference
Keywords:    ±25  — loosest, just supporting enrichment

Rarity weighting
----------------
A filter used by 3 movies is a much stronger signal than one used by 150.
We use a simple inverse-frequency weight: 1 / log2(movie_count + 2)
  - movie_count=1  → weight ≈ 1.00
  - movie_count=5  → weight ≈ 0.56
  - movie_count=20 → weight ≈ 0.23
  - movie_count=100→ weight ≈ 0.15

log2 is used instead of raw 1/N to prevent extreme outliers (single-use
filters) from dominating. The +2 prevents division by zero.

Tuning guide
------------
The safest knobs to turn first:
  - SimilarityConfig.subgenre_weight: raise to 3.0 to make subgenre the dominant signal
  - SimilarityConfig.specification_weight: raise to 2.5 to emphasize vibe matching
  - GENRE_RANGE, SPEC_RANGE, KEYWORD_RANGE constants below
  - SimilarityConfig.min_score_threshold: lower to 0.05 to surface more pairs
"""

import math
from dataclasses import dataclass

from app import models as m
from app.services.similarity_config import SimilarityConfig, DEFAULT_SIMILARITY_CONFIG

# ── Matching tolerances ────────────────────────────────────────────────────────
# How far two percentage_match values can differ and still count as a match.
# Subgenres have no range — they must share the same key.
#
# With the 5-step percentage system (20/40/60/80/100) and 20 treated as noise,
# the meaningful values span 40–100 (max diff = 60). GENRE_RANGE must be ≥ 60
# so that e.g. Action@40 and Action@100 still count as overlapping genres.
# Narrower ranges would silently zero out most genre matches.
GENRE_RANGE: float = 60.0
SPEC_RANGE: float = 40.0
KEYWORD_RANGE: float = 20.0


# ── Data containers ────────────────────────────────────────────────────────────


@dataclass
class FilterEntry:
    """One filter association for a movie: key + its percentage_match."""

    key: str
    percentage_match: float
    movie_count: int  # used for rarity weighting


@dataclass
class MovieFeatures:
    """Extracted feature data for a single movie, ready for comparison."""

    movie_id: int
    excluded_keys: set[str]  # collection + shared-universe keys to exclude as neighbors
    genres: list[FilterEntry]
    subgenres: list[FilterEntry]
    specifications: list[FilterEntry]
    keywords: list[FilterEntry]


# ── Rarity weight ──────────────────────────────────────────────────────────────


def _rarity_weight(movie_count: int) -> float:
    """Inverse log-frequency weight.

    Rare filters (small movie_count) get a higher weight.
    Capped at 1.0, never zero.

    Tuning: increase the divisor (currently log2) to flatten the curve,
    making rarity matter less. Switch to log10 for a gentler slope.
    """
    return 1.0 / math.log2(max(movie_count, 1) + 2)


# ── Per-filter-type scoring ────────────────────────────────────────────────────


def _score_with_range(
    filters_a: list[FilterEntry],
    filters_b: list[FilterEntry],
    range_tolerance: float,
) -> float:
    """Score overlapping filters where percentage_match must be within ±range_tolerance.

    Algorithm:
      - Find filters present in both movies (by key).
      - For each overlapping filter, check that the two percentage_match values
        are within range_tolerance of each other.
      - If they are, compute contribution = rarity_weight * closeness_factor.
        closeness_factor = 1 - (|diff| / (range_tolerance + 1))
        The +1 prevents the edge of the window from returning exactly zero,
        and also prevents division by zero when range_tolerance=0.
      - Denominator: sum of rarity weights across the union of all filters
        (Jaccard-style). This naturally penalizes movies with very few
        overlapping filters relative to their total filter set.

    Returns a score in [0.0, 1.0].
    """
    if not filters_a or not filters_b:
        return 0.0

    map_a = {f.key: f for f in filters_a}
    map_b = {f.key: f for f in filters_b}

    shared_keys = set(map_a.keys()) & set(map_b.keys())
    union_keys = set(map_a.keys()) | set(map_b.keys())

    if not shared_keys:
        return 0.0

    numerator = 0.0

    for key in shared_keys:
        fa = map_a[key]
        fb = map_b[key]
        # E.g. 60 - 20 = 40 => 40- 60 +40 = 20, 40, 60, 80, 100
        diff = abs(fa.percentage_match - fb.percentage_match)

        if diff > range_tolerance:
            # Too far apart — not a meaningful match.
            continue

        # Closeness: 1.0 when identical, > 0 even at the edge of tolerance.
        # +1 in denominator avoids zero at the boundary and division-by-zero.
        closeness = 1.0 - (diff / (range_tolerance + 1.0))

        # Average rarity weight from both movies' perspective.
        rarity = _rarity_weight((fa.movie_count + fb.movie_count) // 2)

        numerator += closeness * rarity

    # Denominator: sum rarity weights across the full union.
    # For non-shared filters we use the single movie's count (other side is absent = 0 contribution).
    # This gives partial credit for partial overlap while penalizing weak overlap.
    denominator = 0.0
    for key in union_keys:
        if key in map_a and key in map_b:
            mc = (map_a[key].movie_count + map_b[key].movie_count) // 2
        elif key in map_a:
            mc = map_a[key].movie_count
        else:
            mc = map_b[key].movie_count
        denominator += _rarity_weight(mc)

    return numerator / denominator if denominator > 0 else 0.0


def _score_subgenres(
    subgenres_a: list[FilterEntry],
    subgenres_b: list[FilterEntry],
) -> float:
    """Score subgenre overlap — exact key match only, no range.

    Subgenres are the strongest structural signal. Two movies sharing
    'Heist Thriller' or 'Coming-of-Age Drama' are semantically close
    regardless of percentage differences.

    Returns a score in [0.0, 1.0].
    """
    if not subgenres_a or not subgenres_b:
        return 0.0

    map_a = {f.key: f for f in subgenres_a}
    map_b = {f.key: f for f in subgenres_b}

    shared_keys = set(map_a.keys()) & set(map_b.keys())
    union_keys = set(map_a.keys()) | set(map_b.keys())

    if not shared_keys:
        return 0.0

    numerator = sum(_rarity_weight((map_a[k].movie_count + map_b[k].movie_count) // 2) for k in shared_keys)

    denominator = 0.0
    for key in union_keys:
        if key in map_a and key in map_b:
            mc = (map_a[key].movie_count + map_b[key].movie_count) // 2
        elif key in map_a:
            mc = map_a[key].movie_count
        else:
            mc = map_b[key].movie_count
        denominator += _rarity_weight(mc)

    return numerator / denominator if denominator > 0 else 0.0


# ── Feature extraction ─────────────────────────────────────────────────────────


def _association_data(
    session,
    movie_id: int,
    table,
    fk_col_name: str,
    entity_model,
) -> list[FilterEntry]:
    """Load filter associations for one movie as FilterEntry list.

    This runs a single JOIN query per filter type per movie during feature
    extraction. At ~500 movies × 4 filter types this is ~2000 queries total
    for the full recalculation — acceptable for an offline command.

    fk_col_name: the FK column name on the association table, e.g. 'genre_id'
    """
    import sqlalchemy as sa

    fk_col = getattr(table.c, fk_col_name)

    rows = session.execute(
        sa.select(
            fk_col,
            table.c.percentage_match,
        ).where(table.c.movie_id == movie_id)
    ).all()

    if not rows:
        return []

    # Build id → movie_count map from the entity model
    entity_ids = [row[0] for row in rows]
    entities = session.scalars(sa.select(entity_model).where(entity_model.id.in_(entity_ids))).all()
    count_map = {e.id: e.movie_count for e in entities}
    key_map = {e.id: e.key for e in entities}

    return [
        FilterEntry(
            key=key_map[row[0]],
            percentage_match=row[1],
            movie_count=count_map.get(row[0], 1),
        )
        for row in rows
        if row[0] in key_map
    ]


def extract_features(session, movie: m.Movie) -> MovieFeatures:
    """Extract all filter data for one movie into a clean MovieFeatures struct.

    Also computes the exclusion set: all movie keys that belong to the same
    collection or shared universe, so they are never recommended as 'similar'
    (they already appear in the Related Titles block on the frontend).
    """
    excluded_keys: set[str] = set()

    # Exclude the movie itself
    excluded_keys.add(movie.key)

    # Exclude collection members (sequels, prequels, remakes, etc.)
    if movie.collection_base_movie_id or movie.collection_members:
        base = movie.collection_base_movie or movie
        excluded_keys.add(base.key)
        for member in base.collection_members:
            excluded_keys.add(member.key)

    # Exclude shared universe movies
    if movie.shared_universe_id and movie.shared_universe:
        for su_movie in movie.shared_universe.movies:
            excluded_keys.add(su_movie.key)

    return MovieFeatures(
        movie_id=movie.id,
        excluded_keys=excluded_keys,
        genres=_association_data(session, movie.id, m.movie_genres, "genre_id", m.Genre),
        subgenres=_association_data(session, movie.id, m.movie_subgenres, "subgenre_id", m.Subgenre),
        specifications=_association_data(
            session, movie.id, m.movie_specifications, "specification_id", m.Specification
        ),
        keywords=_association_data(session, movie.id, m.movie_keywords, "keyword_id", m.Keyword),
    )


# ── Final score computation ────────────────────────────────────────────────────


def compute_similarity(
    features_a: MovieFeatures,
    features_b: MovieFeatures,
    config: SimilarityConfig = DEFAULT_SIMILARITY_CONFIG,
) -> float:
    """Compute a similarity score in [0.0, 1.0] between two movies.

    Scoring pipeline:
      1. Strip noise: genres at or below min_genre_percentage are excluded.
      2. Strip excluded keys: administrative specs/keywords that should not influence score.
      3. Score each dimension independently.
      4. Combine with additive weighted sum (normalized to [0, 1]).
      5. Genre gate: if both movies have meaningful genres but share zero overlap,
         multiply the final score by genre_gate_penalty (default 0.15).
         This prevents genre-incompatible pairs from ranking above relevant ones.

    Genre gating rationale:
      Genres define the recommendation search space. A strong Specification match
      between a Sci-Fi/Comedy and a Horror/Drama should not produce a high similarity
      score — they are fundamentally different films. The gate does not hard-exclude
      such pairs (they may still appear at the bottom of a short list), but it ensures
      they never outrank genre-compatible movies.

    Additive formula is kept (not multiplicative) because:
      - Movies can be validly similar in 2 of 4 dimensions; multiplicative would
        zero out the score if any single dimension is 0.
      - Genre gating handles the cross-genre problem explicitly, so we don't need
        to rely on the formula structure to enforce it.

    Weight semantics (from SimilarityConfig):
      - subgenre_weight highest: exact structural signal
      - specification_weight second: vibe/atmosphere identity
      - genre_weight third: broad context, validated by the gate
      - keyword_weight lowest: supporting enrichment
    """
    # Step 1: Strip noise-level genres (e.g. Comedy@20 on an Action film)
    min_pct = config.min_genre_percentage
    genres_a = [f for f in features_a.genres if f.percentage_match > min_pct]
    genres_b = [f for f in features_b.genres if f.percentage_match > min_pct]

    min_subgenre_pct = config.min_subgenre_percentage
    subgenres_a = [f for f in features_a.subgenres if f.percentage_match > min_subgenre_pct]
    subgenres_b = [f for f in features_b.subgenres if f.percentage_match > min_subgenre_pct]

    # Step 2: Strip administrative/excluded filter keys
    excluded_specs = config.excluded_specification_keys
    specs_a = [f for f in features_a.specifications if f.key not in excluded_specs]
    specs_b = [f for f in features_b.specifications if f.key not in excluded_specs]

    excluded_keywords = config.excluded_keyword_keys
    keywords_a = [f for f in features_a.keywords if f.key not in excluded_keywords]
    keywords_b = [f for f in features_b.keywords if f.key not in excluded_keywords]

    # Step 3: Score each dimension
    genre_score = _score_with_range(genres_a, genres_b, GENRE_RANGE)
    subgenre_score = _score_subgenres(subgenres_a, subgenres_b)
    spec_score = _score_with_range(specs_a, specs_b, SPEC_RANGE)
    keyword_score = _score_with_range(keywords_a, keywords_b, KEYWORD_RANGE)

    # Step 4: Weighted sum
    total_weight = config.genre_weight + config.subgenre_weight + config.specification_weight + config.keyword_weight

    if total_weight == 0:
        return 0.0

    weighted_sum = (
        config.genre_weight * genre_score
        + config.subgenre_weight * subgenre_score
        + config.specification_weight * spec_score
        + config.keyword_weight * keyword_score
    )

    raw_score = weighted_sum / total_weight

    # Step 5: Specification overlap bonus.
    # When both movies have more than min_specs_for_bonus specs and share at
    # least min_shared_specs_for_bonus of them, reward the pair with a flat bonus.
    # This ensures that e.g. A(S1,S2,S3) vs C(S1,S2,S10) scores higher than
    # A(S1,S2,S3) vs B(S2,S4,S5) where only 1 spec is shared.
    if config.spec_overlap_bonus > 0.0:
        if len(specs_a) > config.min_specs_for_bonus and len(specs_b) > config.min_specs_for_bonus:
            shared_spec_keys = {f.key for f in specs_a} & {f.key for f in specs_b}
            if len(shared_spec_keys) >= config.min_shared_specs_for_bonus:
                raw_score = min(1.0, raw_score + config.spec_overlap_bonus)

    # Step 6: Keyword overlap bonus.
    # When both movies share at least min_shared_keywords_for_bonus keywords,
    # reward the pair with a flat bonus (analogous to spec_overlap_bonus).
    if config.keyword_overlap_bonus > 0.0:
        shared_keyword_keys = {f.key for f in keywords_a} & {f.key for f in keywords_b}
        if len(shared_keyword_keys) >= config.min_shared_keywords_for_bonus:
            raw_score = min(1.0, raw_score + config.keyword_overlap_bonus)

    # Step 7: Subgenre weight mismatch + spec mismatch penalty.
    # Fires when: any shared subgenre has a large percentage_match difference
    # (>= subgenre_weight_diff_threshold) AND both movies have specifications
    # but share none. Without a confirming spec overlap, a weak subgenre match
    # (one film only lightly belongs to that subgenre) is an unreliable signal.
    if config.subgenre_spec_mismatch_penalty < 1.0:
        shared_sg_keys = {f.key for f in subgenres_a} & {f.key for f in subgenres_b}
        if shared_sg_keys:
            map_sa = {f.key: f for f in subgenres_a}
            map_sb = {f.key: f for f in subgenres_b}
            has_weak_subgenre = any(
                abs(map_sa[k].percentage_match - map_sb[k].percentage_match) >= config.subgenre_weight_diff_threshold
                for k in shared_sg_keys
            )
            no_common_specs = spec_score == 0.0 and bool(specs_a) and bool(specs_b)
            if has_weak_subgenre and no_common_specs:
                raw_score *= config.subgenre_spec_mismatch_penalty

    # Step 8: Single-genre asymmetry penalty.
    # If one movie has exactly 1 genre and the other has >= single_genre_min_opposing
    # genres, the thin movie cannot claim strong similarity based on that single
    # shared genre alone.
    #
    # IMPORTANT: use the RAW genre lists (before noise filtering) to count genres.
    # A movie with Comedy@20, Drama@20, Western@80 has 3 genres in total — two of
    # them just happen to fall below the noise threshold. Using the filtered lists
    # would wrongly treat it as a single-genre movie and apply the penalty.
    n_genres_a = len(features_a.genres)
    n_genres_b = len(features_b.genres)
    min_genres = min(n_genres_a, n_genres_b)
    max_genres = max(n_genres_a, n_genres_b)
    if min_genres == 1 and max_genres >= config.single_genre_min_opposing:
        raw_score *= config.single_genre_asymmetry_penalty

    # Step 9: Genre gate
    # Only fires when BOTH sides have meaningful genres but share none.
    # If a movie has no genres at all, we skip the gate (nothing to compare against).
    if genre_score == 0.0 and genres_a and genres_b:
        return raw_score * config.genre_gate_penalty

    return raw_score
