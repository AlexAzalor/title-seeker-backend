import sqlalchemy as sa
from fastapi import HTTPException, status

import app.schema as s
import app.models as m
from app.logger import log


from sqlalchemy.orm import Session


def update_percentage_match(
    movie_id: int,
    db: Session,
    genres: list[s.MovieFilterField],
    subgenres: list[s.MovieFilterField],
    specifications: list[s.MovieFilterField],
    keywords: list[s.MovieFilterField],
    action_times: list[s.MovieFilterField],
):
    # Genres percentage match
    try:
        for percentage_match_dict in genres:
            genre_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            genre = db.scalar(sa.select(m.Genre).where(m.Genre.key == genre_key))

            if not genre:
                log(log.ERROR, "Genre [%s] not found", genre_key)
                raise Exception(f"Genre [{genre_key}] not found")

            movie_genre = (
                m.movie_genres.update()
                .values({"percentage_match": percentage_match})
                .where(m.movie_genres.c.movie_id == movie_id, m.movie_genres.c.genre_id == genre.id)
            )
            db.execute(movie_genre)

        # Subgenres percentage match
        for percentage_match_dict in subgenres:
            subgenre_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            subgenre = db.scalar(sa.select(m.Subgenre).where(m.Subgenre.key == subgenre_key))

            if not subgenre:
                log(log.ERROR, "Subgenre [%s] not found", subgenre_key)
                raise Exception(f"Subgenre [{subgenre_key}] not found")

            movie_subgenre = (
                m.movie_subgenres.update()
                .values({"percentage_match": percentage_match})
                .where(m.movie_subgenres.c.movie_id == movie_id, m.movie_subgenres.c.subgenre_id == subgenre.id)
            )
            db.execute(movie_subgenre)

        # Specifications percentage match
        for percentage_match_dict in specifications:
            specification_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            specification = db.scalar(sa.select(m.Specification).where(m.Specification.key == specification_key))

            if not specification:
                log(log.ERROR, "Specification [%s] not found", specification_key)
                raise Exception(f"Specification [{specification_key}] not found")

            movie_specification = (
                m.movie_specifications.update()
                .values({"percentage_match": percentage_match})
                .where(
                    m.movie_specifications.c.movie_id == movie_id,
                    m.movie_specifications.c.specification_id == specification.id,
                )
            )
            db.execute(movie_specification)

        # Keywords percentage match
        for percentage_match_dict in keywords:
            keyword_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            keyword = db.scalar(sa.select(m.Keyword).where(m.Keyword.key == keyword_key))

            if not keyword:
                log(log.ERROR, "Keyword [%s] not found", keyword_key)
                raise Exception(f"Keyword [{keyword_key}] not found")

            movie_keyword = (
                m.movie_keywords.update()
                .values({"percentage_match": percentage_match})
                .where(m.movie_keywords.c.movie_id == movie_id, m.movie_keywords.c.keyword_id == keyword.id)
            )
            db.execute(movie_keyword)

        # Action times percentage match
        for percentage_match_dict in action_times:
            action_time_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            action_time = db.scalar(sa.select(m.ActionTime).where(m.ActionTime.key == action_time_key))

            if not action_time:
                log(log.ERROR, "Action time [%s] not found", action_time_key)
                raise Exception(f"Action time [{action_time_key}] not found")

            movie_action_time = (
                m.movie_action_times.update()
                .values({"percentage_match": percentage_match})
                .where(
                    m.movie_action_times.c.movie_id == movie_id,
                    m.movie_action_times.c.action_time_id == action_time.id,
                )
            )
            db.execute(movie_action_time)
    except Exception as e:
        log(log.ERROR, "Error updating percentage match: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating percentage match")
