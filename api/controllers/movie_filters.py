import sqlalchemy as sa
from sqlalchemy.orm import Session, selectinload
import app.models as m
import app.schema as s
from fastapi import HTTPException, status
from app.logger import log


def get_people_filters(db: Session, lang: s.Language):
    actors = db.scalars(
        sa.select(m.Actor)
        .options(selectinload(m.Actor.translations))
        .join(m.Actor.translations)
        .where(m.ActorTranslation.language == lang.value)
        .order_by(
            sa.func.concat(
                m.ActorTranslation.first_name,
            )
        )
    ).all()
    if not actors:
        log(log.ERROR, "Actors [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actors not found")

    directors = db.scalars(
        sa.select(m.Director)
        .options(selectinload(m.Director.translations))
        .join(m.Director.translations)
        .where(m.DirectorTranslation.language == lang.value)
        .order_by(
            sa.func.concat(
                m.DirectorTranslation.first_name,
            )
        )
    ).all()
    if not directors:
        log(log.ERROR, "Director [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Director not found")

    characters = db.scalars(
        sa.select(m.Character)
        .options(selectinload(m.Character.translations))
        .join(m.Character.translations)
        .where(m.CharacterTranslation.language == lang.value)
        .order_by(m.CharacterTranslation.name)
    ).all()
    if not characters:
        log(log.ERROR, "Characters [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Characters not found")

    another_lang = s.Language.EN if lang == s.Language.UK else s.Language.UK

    actors_out = [
        s.MainItemMenu(
            key=actor.key,
            name=actor.full_name(lang),
            another_lang_name=actor.full_name(another_lang),
        )
        for actor in actors
    ]

    directors_out = [
        s.MainItemMenu(
            key=director.key,
            name=director.full_name(lang),
            another_lang_name=director.full_name(another_lang),
        )
        for director in directors
    ]

    characters_out = [
        s.MainItemMenu(
            key=character.key,
            name=character.get_name(lang),
            another_lang_name=character.get_name(another_lang),
        )
        for character in characters
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
        .order_by(m.GenreTranslation.name)
    ).all()
    if not genres:
        log(log.ERROR, "Genres [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Genres not found")

    genres_out = [
        s.GenreOut(
            key=genre.key,
            name=genre.get_name(lang),
            description=genre.get_description(lang),
            subgenres=sorted(
                [
                    s.SubgenreOut(
                        key=subgenre.key,
                        name=subgenre.get_name(lang),
                        description=subgenre.get_description(lang),
                        parent_genre_key=subgenre.genre.key,
                    )
                    for subgenre in genre.subgenres
                ],
                key=lambda x: x.name,
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
        .order_by(m.SpecificationTranslation.name)
    ).all()
    if not specifications:
        log(log.ERROR, "Specifications [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specifications not found")

    keywords = db.scalars(
        sa.select(m.Keyword)
        .options(selectinload(m.Keyword.translations))
        .join(m.Keyword.translations)
        .where(m.KeywordTranslation.language == lang.value)
        .order_by(m.KeywordTranslation.name)
    ).all()
    if not keywords:
        log(log.ERROR, "Keywords [%s] not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Keywords not found")

    action_times = db.scalars(
        sa.select(m.ActionTime)
        .options(selectinload(m.ActionTime.translations))
        .join(m.ActionTime.translations)
        .where(m.ActionTimeTranslation.language == lang.value)
        .order_by(m.ActionTimeTranslation.name)
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
        )
        for specification in specifications
    ]

    keywords_out = [
        s.FilterItemOut(
            key=keyword.key,
            name=keyword.get_name(lang),
            description=keyword.get_description(lang),
            percentage_match=0.0,
        )
        for keyword in keywords
    ]

    action_times_out = [
        s.FilterItemOut(
            key=action_time.key,
            name=action_time.get_name(lang),
            description=action_time.get_description(lang),
            percentage_match=0.0,
        )
        for action_time in action_times
    ]

    su_out = [
        s.BaseSharedUniverse(
            key=su.key,
            name=su.get_name(lang),
            description=su.get_description(lang),
        )
        for su in shared_universes
    ]

    return (
        specifications_out,
        keywords_out,
        action_times_out,
        su_out,
    )
