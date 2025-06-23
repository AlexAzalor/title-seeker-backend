import sqlalchemy as sa
import app.models as m
from sqlalchemy.orm import Session

from api.utils import extract_values, extract_word


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
