"""Similarity engine configuration.

All weight values are floats in [0.0, 1.0]. They do NOT need to sum to 1.0 —
the algorithm will normalize them at computation time.

Design notes:
- Weights are editorial decisions that change infrequently → keep in code, not DB.
- If runtime configurability is ever needed, this dataclass maps cleanly to a DB row.
- FILTER_TYPE_WEIGHTS controls how much each filter category contributes to the score.
- TOP_N_FILTERS_PER_TYPE limits how many filters per type are considered (uses rank
  first, then falls back to percentage_match ordering). Max 5 per current data policy.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimilarityConfig:
    # Relative contribution of each filter type to the overall similarity score.
    # Ratios are what matter — these are normalized at computation time.
    #
    # Philosophy:
    #   subgenres    = strongest structural signal (exact match)
    #   specifications = vibe/atmosphere identity (second most important)
    #   genres       = broad context (matters, but not distinctive)
    #   keywords     = supporting enrichment (lowest weight)
    #
    # Safe tuning: try subgenre_weight=4.0 or specification_weight=3.0
    # to amplify those axes further.
    # genre_weight = 3.5
    # subgenre_weight = 3.0
    # specification_weight = 2.5
    # keyword_weight = 1.0

    # genre_weight = 3.5
    # specification_weight = 3.0
    # subgenre_weight = 2.5
    # keyword_weight = 1.0

    genre_weight: float = 2
    subgenre_weight: float = 2.5
    specification_weight: float = 4.0
    keyword_weight: float = 1.0

    # How many top filters per type to include in comparison.
    # Respects rank first; falls back to percentage_match descending.
    top_n_genres: int = 3
    top_n_subgenres: int = 5
    top_n_specifications: int = 5
    top_n_keywords: int = 5

    # Specification keys to exclude from similarity scoring entirely.
    # These filters are meta/administrative and should not influence recommendations.
    # Example: 'rewatch' says something about the viewer's habit, not the movie's content.
    excluded_specification_keys: frozenset[str] = frozenset({"rewatch", "didnt-watch"})
    excluded_keyword_keys: frozenset[str] = frozenset({"rewatch", "ordinary-world", "franchise"})

    # Genre gating — genres at or below this percentage_match are ignored as noise.
    # With the 5-step system (20/40/60/80/100), 20 means the genre is barely present
    # and should not contribute to similarity or act as a gate.
    min_genre_percentage: float = 20.0
    min_subgenre_percentage: float = 20.0

    # Score multiplier applied when both movies have meaningful genres but share none.
    # Prevents a strong Specification or Keyword match from surfacing genre-incompatible
    # movies into recommendations.
    # 0.15 → at most 15% of the raw score survives a zero-genre-overlap pair.
    # Set to 1.0 to disable gating entirely; 0.0 to make genre overlap strictly required.
    genre_gate_penalty: float = 0.15

    # Single-genre asymmetry penalty.
    # Applied when one movie has exactly 1 meaningful genre and the other has
    # >= single_genre_min_opposing genres. The single shared genre is not enough
    # structural evidence to justify a high similarity against a genre-rich film.
    # 0.3 → the score is cut to 30% of its raw value in that case.
    # Raise toward 1.0 to weaken the penalty; lower toward 0.0 to strengthen it.
    single_genre_asymmetry_penalty: float = 0.3
    # Minimum number of genres the other movie must have for the penalty to apply.
    # With the default of 3: B(1 genre) vs A(3+ genres) → penalty fires.
    # B(1 genre) vs A(2 genres) → no penalty (reasonable partial match).
    single_genre_min_opposing: int = 3

    # Specification overlap bonus.
    # Applied when both movies have more than `min_specs_for_bonus` specifications
    # (after excluding administrative keys) AND share at least
    # `min_shared_specs_for_bonus` of them. This rewards strong vibe alignment.
    # The bonus is additive and the final score is clamped to 1.0.
    # Set spec_overlap_bonus=0.0 to disable.
    min_specs_for_bonus: int = 2
    min_shared_specs_for_bonus: int = 2
    spec_overlap_bonus: float = 0.15

    # Keyword overlap bonus.
    # Applied when both movies share at least `min_shared_keywords_for_bonus`
    # keywords (after excluding administrative keys). A large shared keyword set
    # is a strong thematic signal that the weighted score alone may undervalue.
    # The bonus is additive and the final score is clamped to 1.0.
    # Set keyword_overlap_bonus=0.0 to disable.
    min_shared_keywords_for_bonus: int = 4
    keyword_overlap_bonus: float = 0.15

    # Subgenre weight mismatch + spec mismatch penalty.
    # Fires when movies share a subgenre BUT the two percentage_match values differ
    # by >= subgenre_weight_diff_threshold AND both movies have specifications that
    # share none in common.
    # Rationale: a large pct difference means one film only lightly belongs to that
    # subgenre; without any confirming spec overlap the shared subgenre label is a
    # weak signal and should not drive a high similarity score.
    # Example: A(Cyberpunk@100, Spec1) vs B(Cyberpunk@40, Spec2) → penalty fires.
    # Set subgenre_spec_mismatch_penalty=1.0 to disable.
    subgenre_weight_diff_threshold: float = 40.0
    subgenre_spec_mismatch_penalty: float = 0.7

    # Minimum score [0.0–1.0] to store a pair in movie_similarities.
    # Pairs below this threshold are not saved (reduces table noise).
    min_score_threshold: float = 0.1

    # How many similar movies to return per movie in API responses.
    default_similar_count: int = 12


# Module-level default instance. Import and use directly:
#   from app.services.similarity_config import DEFAULT_SIMILARITY_CONFIG
DEFAULT_SIMILARITY_CONFIG = SimilarityConfig()
