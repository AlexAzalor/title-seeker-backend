import sqlalchemy as sa
from sqlalchemy.orm import Session, selectinload
import app.models as m
import app.schema as s
from fastapi import HTTPException, status
from app.logger import log


def get_people_filters(db: Session, lang: s.Language):
    total_movies = db.scalar(sa.select(sa.func.count(m.Movie.id))) or 0
    min_movies = max(1, int(total_movies * 0.01))

    actor_movie_count_sq = (
        sa.select(m.Actor.id, sa.func.count(m.Movie.id).label("movie_count"))
        .join(m.Movie.actors)
        .group_by(m.Actor.id)
        .subquery()
    )

    actors_with_counts = db.execute(
        sa.select(m.Actor, actor_movie_count_sq.c.movie_count)
        .options(selectinload(m.Actor.translations))
        .join(m.Actor.translations)
        .join(actor_movie_count_sq, m.Actor.id == actor_movie_count_sq.c.id)
        .where(m.ActorTranslation.language == lang.value)
        .where(actor_movie_count_sq.c.movie_count >= min_movies)
        .order_by(actor_movie_count_sq.c.movie_count.desc())
    ).all()
    if not actors_with_counts:
        log(log.ERROR, "Actors [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actors not found")

    director_movie_count_sq = (
        sa.select(m.Director.id, sa.func.count(m.Movie.id).label("movie_count"))
        .join(m.Movie.directors)
        .group_by(m.Director.id)
        .subquery()
    )

    directors_with_counts = db.execute(
        sa.select(m.Director, director_movie_count_sq.c.movie_count)
        .options(selectinload(m.Director.translations))
        .join(m.Director.translations)
        .join(director_movie_count_sq, m.Director.id == director_movie_count_sq.c.id)
        .where(m.DirectorTranslation.language == lang.value)
        .where(director_movie_count_sq.c.movie_count >= 2)
        .order_by(director_movie_count_sq.c.movie_count.desc())
    ).all()
    if not directors_with_counts:
        log(log.ERROR, "Director [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Director not found")

    character_movie_count_sq = (
        sa.select(
            m.Character.id,
            sa.func.count(sa.distinct(m.MovieActorCharacter.movie_id)).label("movie_count"),
        )
        .join(m.Character.characters)
        .group_by(m.Character.id)
        .subquery()
    )

    characters_with_counts = db.execute(
        sa.select(m.Character, character_movie_count_sq.c.movie_count)
        .options(selectinload(m.Character.translations))
        .join(m.Character.translations)
        .join(character_movie_count_sq, m.Character.id == character_movie_count_sq.c.id)
        .where(m.CharacterTranslation.language == lang.value)
        .where(character_movie_count_sq.c.movie_count >= 2)
        .order_by(character_movie_count_sq.c.movie_count.desc())
    ).all()
    if not characters_with_counts:
        log(log.ERROR, "Characters [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Characters not found")

    another_lang = s.Language.EN if lang == s.Language.UK else s.Language.UK

    actors_out = [
        s.MainItemMenu(
            key=actor.key,
            name=actor.full_name(lang),
            another_lang_name=actor.full_name(another_lang),
            movie_count=movie_count,
        )
        for actor, movie_count in actors_with_counts
    ]

    directors_out = [
        s.MainItemMenu(
            key=director.key,
            name=director.full_name(lang),
            another_lang_name=director.full_name(another_lang),
            movie_count=movie_count,
        )
        for director, movie_count in directors_with_counts
    ]

    characters_out = [
        s.MainItemMenu(
            key=character.key,
            name=character.get_name(lang),
            another_lang_name=character.get_name(another_lang),
            movie_count=movie_count,
        )
        for character, movie_count in characters_with_counts
    ]

    return actors_out, directors_out, characters_out


def get_genre_filters(db: Session, lang: s.Language):
    genres = db.scalars(
        sa.select(m.Genre)
        .options(
            selectinload(m.Genre.translations), selectinload(m.Genre.subgenres).selectinload(m.Subgenre.translations)
        )
        .join(m.Genre.translations)
        .where(m.GenreTranslation.language == lang.value)
        .order_by(m.Genre.movie_count.desc())
    ).all()
    if not genres:
        log(log.ERROR, "Genres [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genres not found")

    genres_out = [
        s.GenreOut(
            key=genre.key,
            name=genre.get_name(lang),
            description=genre.get_description(lang),
            movie_count=genre.movie_count,
            subgenres=sorted(
                [
                    s.SubgenreOut(
                        key=subgenre.key,
                        name=subgenre.get_name(lang),
                        description=subgenre.get_description(lang),
                        parent_genre_key=subgenre.genre.key,
                        movie_count=subgenre.movie_count,
                    )
                    for subgenre in genre.subgenres
                ],
                key=lambda x: x.movie_count if x.movie_count is not None else 0,
                reverse=True,
            ),
        )
        for genre in genres
    ]

    return genres_out


def get_filters(db: Session, lang: s.Language):
    specifications = db.scalars(
        sa.select(m.Specification)
        .options(selectinload(m.Specification.translations))
        .join(m.Specification.translations)
        .where(m.SpecificationTranslation.language == lang.value)
        .order_by(m.Specification.movie_count.desc())
    ).all()
    if not specifications:
        log(log.ERROR, "Specifications [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specifications not found")

    keywords = db.scalars(
        sa.select(m.Keyword)
        .options(selectinload(m.Keyword.translations))
        .join(m.Keyword.translations)
        .where(m.KeywordTranslation.language == lang.value)
        .order_by(m.Keyword.movie_count.desc())
    ).all()
    if not keywords:
        log(log.ERROR, "Keywords [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keywords not found")

    action_times = db.scalars(
        sa.select(m.ActionTime)
        .options(selectinload(m.ActionTime.translations))
        .join(m.ActionTime.translations)
        .where(m.ActionTimeTranslation.language == lang.value)
        .order_by(m.ActionTime.order.desc())
    ).all()
    if not action_times:
        log(log.ERROR, "Action times [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action times not found")

    shared_universes = db.scalars(
        sa.select(m.SharedUniverse)
        .options(selectinload(m.SharedUniverse.translations))
        .join(m.SharedUniverse.translations)
        .where(m.SharedUniverseTranslation.language == lang.value)
        .order_by(m.SharedUniverseTranslation.name)
    ).all()
    if not shared_universes:
        log(log.ERROR, "Shared universes [%s] not found")
        raise HTTPException(status_code=404, detail="Shared universes not found")

    specifications_out = [
        s.FilterItemOut(
            key=specification.key,
            name=specification.get_name(lang),
            description=specification.get_description(lang),
            percentage_match=0.0,
            movie_count=specification.movie_count,
        )
        for specification in specifications
    ]

    keywords_out = [
        s.FilterItemOut(
            key=keyword.key,
            name=keyword.get_name(lang),
            description=keyword.get_description(lang),
            percentage_match=0.0,
            movie_count=keyword.movie_count,
        )
        for keyword in keywords
    ]

    action_times_out = [
        s.FilterItemOut(
            key=action_time.key,
            name=action_time.get_name(lang),
            description=action_time.get_description(lang),
            percentage_match=0.0,
            movie_count=action_time.movie_count,
        )
        for action_time in action_times
    ]

    su_movie_count_rows = (
        db.execute(
            sa.select(m.Movie.shared_universe_id, sa.func.count(m.Movie.id))
            .where(m.Movie.shared_universe_id.is_not(None))
            .group_by(m.Movie.shared_universe_id)
        )
        .tuples()
        .all()
    )
    su_movie_counts: dict[int, int] = {
        su_id: movie_count for su_id, movie_count in su_movie_count_rows if su_id is not None
    }

    su_out = sorted(
        [
            s.BaseSharedUniverse(
                key=su.key,
                name=su.get_name(lang),
                description=su.get_description(lang),
                movie_count=su_movie_counts.get(su.id, 0),
            )
            for su in shared_universes
        ],
        key=lambda su: su.movie_count,
        reverse=True,
    )

    return (
        specifications_out,
        keywords_out,
        action_times_out,
        su_out,
    )
