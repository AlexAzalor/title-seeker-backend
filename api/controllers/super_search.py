import sqlalchemy as sa
import app.models as m
from sqlalchemy.orm import Session

from api.utils import extract_values, extract_word, string_to_number_list


def get_rating_query_conditions(
    rating: str | None,
    visual_effects: str | None,
    scare_factor: str | None,
    humor: str | None,
    animation_cartoon: str | None,
) -> list:
    """
    Build rating search conditions. All conditions are "AND" inside a single
    Movie.ratings.any(...) call.

    - rating: "min,max" range string (e.g. "7.24,10")
    - additional criteria (mutually exclusive): visual_effects, scare_factor,
      humor, animation_cartoon — minimum score; also restricts to movies that
      HAVE that criterion (IS NOT NULL)
    """
    row_conditions: list = []

    # Rating range
    if rating:
        parts = [p.strip() for p in rating.split(",") if p.strip()]
        if len(parts) == 2:
            try:
                min_r = float(parts[0])
                max_r = float(parts[1])
                if min_r < max_r:
                    row_conditions.append(m.Rating.rating >= min_r)
                    row_conditions.append(m.Rating.rating <= max_r)
            except ValueError:
                pass

    # Additional criteria (mutually exclusive)
    # Selecting one restricts to movies that HAVE this criterion (NOT NULL) + minimum score
    additional = [
        (visual_effects, m.Rating.visual_effects),
        (scare_factor, m.Rating.scare_factor),
        (humor, m.Rating.humor),
        (animation_cartoon, m.Rating.animation_cartoon),
    ]
    for raw_val, field in additional:
        if raw_val:
            row_conditions.append(field.isnot(None))
            try:
                v = float(raw_val)
                if v > 0:
                    row_conditions.append(field >= v)
            except ValueError:
                pass

    if not row_conditions:
        return []

    return [m.Movie.ratings.any(sa.and_(*row_conditions))]


def get_genre_query_conditions(genre: list[str], subgenre: list[str], db: Session):
    genres_keys = extract_word(genre)
    genres_values: list[list[int]] = extract_values(genre)

    subgenres_keys: list[str] = extract_word(subgenre)
    subgenres_values: list[list[int]] = extract_values(subgenre)

    genre_conditions = []
    subgenre_conditions = []

    if genres_keys and genres_values:
        for genre_key, value_range in zip(genres_keys, genres_values):
            if value_range:
                genre_conditions.append(
                    m.Movie.genres.any(
                        sa.and_(
                            m.Genre.key == genre_key,
                            m.movie_genres.c.percentage_match >= value_range[0],
                            m.movie_genres.c.percentage_match <= value_range[1],
                        )
                    )
                )

    if subgenres_keys and subgenres_values:
        for subgenre_key, value_range in zip(subgenres_keys, subgenres_values):
            if value_range:
                subgenre_conditions.append(
                    m.Movie.subgenres.any(
                        sa.and_(
                            m.Subgenre.key == subgenre_key,
                            m.movie_subgenres.c.percentage_match >= value_range[0],
                            m.movie_subgenres.c.percentage_match <= value_range[1],
                        )
                    )
                )

    return genre_conditions, subgenre_conditions


def get_filter_query_conditions(specification: list[str], keyword: list[str], action_time: list[str], db: Session):
    specifications_keys: list[str] = extract_word(specification)
    specifications_values = extract_values(specification)

    keywords_keys: list[str] = extract_word(keyword)
    keywords_values = extract_values(keyword)

    action_times_keys: list[str] = extract_word(action_time)
    action_times_values = extract_values(action_time)

    spec_conditions = []
    keyword_conditions = []
    at_conditions = []

    if specifications_keys and specifications_values:
        for specification_key, value_range in zip(specifications_keys, specifications_values):
            if value_range:
                spec_conditions.append(
                    m.Movie.specifications.any(
                        sa.and_(
                            m.Specification.key == specification_key,
                            m.movie_specifications.c.percentage_match >= value_range[0],
                            m.movie_specifications.c.percentage_match <= value_range[1],
                        )
                    )
                )
    if keywords_keys and keywords_values:
        for keyword_key, value_range in zip(keywords_keys, keywords_values):
            if value_range:
                keyword_conditions.append(
                    m.Movie.keywords.any(
                        sa.and_(
                            m.Keyword.key == keyword_key,
                            m.movie_keywords.c.percentage_match >= value_range[0],
                            m.movie_keywords.c.percentage_match <= value_range[1],
                        )
                    )
                )

    if action_times_keys and action_times_values:
        for at_key, value_range in zip(action_times_keys, action_times_values):
            if value_range:
                at_conditions.append(
                    m.Movie.action_times.any(
                        sa.and_(
                            m.ActionTime.key == at_key,
                            m.movie_action_times.c.percentage_match >= value_range[0],
                            m.movie_action_times.c.percentage_match <= value_range[1],
                        )
                    )
                )

    return spec_conditions, keyword_conditions, at_conditions


def get_exclude_genre_conditions(exclude_genre: list[str]) -> list:
    """Build conditions to exclude movies that have any of the given genres."""
    keys = extract_word(exclude_genre)
    return [sa.not_(m.Movie.genres.any(m.Genre.key == key)) for key in keys]


def get_exclude_subgenre_conditions(exclude_subgenre: list[str]) -> list:
    """Build conditions to exclude movies that have any of the given subgenres."""
    keys = extract_word(exclude_subgenre)
    return [sa.not_(m.Movie.subgenres.any(m.Subgenre.key == key)) for key in keys]


def get_exclude_specification_conditions(exclude_specification: list[str]) -> list:
    """Build conditions to exclude movies that have any of the given specifications."""
    keys = extract_word(exclude_specification)
    return [sa.not_(m.Movie.specifications.any(m.Specification.key == key)) for key in keys]


def get_exclude_keyword_conditions(exclude_keyword: list[str]) -> list:
    """Build conditions to exclude movies that have any of the given keywords."""
    keys = extract_word(exclude_keyword)
    return [sa.not_(m.Movie.keywords.any(m.Keyword.key == key)) for key in keys]


def get_exclude_action_time_conditions(exclude_action_time: list[str]) -> list:
    """Build conditions to exclude movies that have any of the given action times."""
    keys = extract_word(exclude_action_time)
    return [sa.not_(m.Movie.action_times.any(m.ActionTime.key == key)) for key in keys]


def get_shared_universe_query_conditions(shared_universe: list[str], db: Session):
    su_conditions = []
    for su_key in shared_universe:
        su_conditions.append(
            m.Movie.shared_universe.has(
                sa.and_(
                    m.SharedUniverse.key == su_key,
                )
            )
        )
    return su_conditions


def get_visual_profile_query_conditions(visual_profile: list[str], db: Session):
    vp_ids = db.scalars(
        sa.select(m.VisualProfileCategory.id).where(m.VisualProfileCategory.key.in_(visual_profile))
    ).all()

    vp_conditions = []
    for vp_id in vp_ids:
        vp_conditions.append(
            m.Movie.visual_profiles.any(
                sa.and_(
                    m.Movie.visual_profiles.any(m.VisualProfile.category_id == vp_id),
                )
            )
        )
    return vp_conditions


def get_people_query_conditions(actor: list[str], director: list[str], character: list[str], db: Session):
    actor_conditions = []
    director_conditions = []
    char_conditions = []

    if actor:
        for actor_key in actor:
            actor_conditions.append(
                m.Movie.actors.any(
                    sa.and_(
                        m.Actor.key == actor_key,
                    )
                )
            )

    if director:
        for director_key in director:
            director_conditions.append(
                m.Movie.directors.any(
                    sa.and_(
                        m.Director.key == director_key,
                    )
                )
            )

    if character:
        for char_key in character:
            char_conditions.append(
                m.Movie.characters.any(
                    sa.and_(
                        m.MovieActorCharacter.character.has(m.Character.key == char_key),
                    )
                )
            )

    return actor_conditions, director_conditions, char_conditions


def get_duration_query_conditions(duration_query: str):
    duration_values = string_to_number_list(duration_query)

    # NOTE: Duration values connected to frontend slider limits
    # NOTE: Duration is in minutes
    MIN_LIMIT = 1
    MAX_LIMIT = 300

    min = duration_values[0]
    max = duration_values[1]

    duration_conditions = []

    if min >= max:
        return []

    if min != MIN_LIMIT and max != MAX_LIMIT:
        duration_conditions.append(
            sa.and_(
                m.Movie.duration >= min,
                m.Movie.duration <= max,
            )
        )

    if min == MIN_LIMIT:
        duration_conditions.append(m.Movie.duration <= max)
        return duration_conditions

    if max == MAX_LIMIT:
        duration_conditions.append(m.Movie.duration >= min)
        return duration_conditions

    return duration_conditions
