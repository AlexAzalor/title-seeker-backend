import sqlalchemy as sa
from sqlalchemy.orm import Session
import app.models as m
import app.schema as s
from fastapi import HTTPException
from app.logger import log


def get_filters(db: Session, lang: s.Language):
    """Get all filters for movies."""

    actors = db.scalars(
        sa.select(m.Actor)
        .join(m.Actor.translations)
        .where(m.ActorTranslation.language == lang.value)
        .order_by(sa.func.concat(m.ActorTranslation.first_name, " ", m.ActorTranslation.last_name))
    ).all()

    if not actors:
        log(log.ERROR, "Actors [%s] not found")
        raise HTTPException(status_code=404, detail="Actors not found")

    directors = db.scalars(
        sa.select(m.Director)
        .join(m.Director.translations)
        .where(m.DirectorTranslation.language == lang.value)
        .order_by(sa.func.concat(m.DirectorTranslation.first_name, " ", m.DirectorTranslation.last_name))
    ).all()
    if not directors:
        log(log.ERROR, "Director [%s] not found")
        raise HTTPException(status_code=404, detail="Director not found")

    genres = db.scalars(
        sa.select(m.Genre)
        .join(m.Genre.translations)
        .where(m.GenreTranslation.language == lang.value)
        .order_by(m.GenreTranslation.name)
    ).all()
    if not genres:
        log(log.ERROR, "Genres [%s] not found")
        raise HTTPException(status_code=404, detail="Genres not found")

    specifications = db.scalars(
        sa.select(m.Specification)
        .join(m.Specification.translations)
        .where(m.SpecificationTranslation.language == lang.value)
        .order_by(m.SpecificationTranslation.name)
    ).all()
    if not specifications:
        log(log.ERROR, "Specifications [%s] not found")
        raise HTTPException(status_code=404, detail="Specifications not found")

    keywords = db.scalars(
        sa.select(m.Keyword)
        .join(m.Keyword.translations)
        .where(m.KeywordTranslation.language == lang.value)
        .order_by(m.KeywordTranslation.name)
    ).all()
    if not keywords:
        log(log.ERROR, "Keywords [%s] not found")
        raise HTTPException(status_code=404, detail="Keywords not found")

    action_times = db.scalars(
        sa.select(m.ActionTime)
        .join(m.ActionTime.translations)
        .where(m.ActionTimeTranslation.language == lang.value)
        .order_by(m.ActionTimeTranslation.name)
    ).all()
    if not action_times:
        log(log.ERROR, "Action times [%s] not found")
        raise HTTPException(status_code=404, detail="Action times not found")

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

    return (
        genres_out,
        specifications_out,
        keywords_out,
        action_times_out,
        actors_out,
        directors_out,
    )
