from datetime import datetime
import sqlalchemy as sa
from fastapi import UploadFile

import app.schema as s
import app.models as m
from app.logger import log


from sqlalchemy.orm import Session


def create_new_movie(db: Session, form_data: s.MovieFormData) -> m.Movie:
    translations = [
        m.MovieTranslation(
            language=s.Language.UK.value,
            title=form_data.title_uk,
            description=form_data.description_uk,
            location=form_data.location_uk,
        ),
        m.MovieTranslation(
            language=s.Language.EN.value,
            title=form_data.title_en,
            description=form_data.description_en,
            location=form_data.location_en,
        ),
    ]

    return m.Movie(
        key=form_data.key,
        release_date=datetime.fromisoformat(form_data.release_date),
        budget=form_data.budget,
        duration=form_data.duration,
        domestic_gross=form_data.domestic_gross,
        worldwide_gross=form_data.worldwide_gross,
        rating_criterion=form_data.rating_criterion_type.value,
        translations=translations,
        actors=[
            db.scalar(sa.select(m.Actor).where(m.Actor.key == actor_key))
            for actor_key in [actor_key.key for actor_key in form_data.actors_keys]
        ],
        directors=[
            db.scalar(sa.select(m.Director).where(m.Director.key == director_key))
            for director_key in form_data.directors_keys
        ],
        genres=[db.scalar(sa.select(m.Genre).where(m.Genre.key == genre_key.key)) for genre_key in form_data.genres],
        subgenres=[
            db.scalar(sa.select(m.Subgenre).where(m.Subgenre.key == subgenre_key.key))
            for subgenre_key in form_data.subgenres
        ],
        specifications=[
            db.scalar(sa.select(m.Specification).where(m.Specification.key == specification_key.key))
            for specification_key in form_data.specifications
        ],
        keywords=[
            db.scalar(sa.select(m.Keyword).where(m.Keyword.key == keyword_key.key))
            for keyword_key in form_data.keywords
        ],
        action_times=[
            db.scalar(sa.select(m.ActionTime).where(m.ActionTime.key == action_time_key.key))
            for action_time_key in form_data.action_times
        ],
    )


def add_poster_to_new_movie(new_movie: m.Movie, file: UploadFile, UPLOAD_DIRECTORY: str):
    try:
        file_name = f"{new_movie.id}_{file.filename}"
        file_location = f"{UPLOAD_DIRECTORY}{file_name}"

        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())

        new_movie.poster = file_name
    except Exception as e:
        log(log.ERROR, "Error uploading poster [%s]: %s", new_movie.key, e)
        e.args = (*e.args, "Error uploading poster")
        raise e


def set_percentage_match(movie_id: int, db: Session, form_data: s.MovieFormData):
    try:
        filter_error_message = "Error updating percentage match"

        # Genres percentage match
        for percentage_match_dict in form_data.genres:
            genre_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            genre = db.scalar(sa.select(m.Genre).where(m.Genre.key == genre_key))

            if not genre:
                log(log.ERROR, "Genre [%s] not found", genre_key)
                filter_error_message = f"Genre [{genre_key}] not found"
                raise Exception

            movie_genre = (
                m.movie_genres.update()
                .values({"percentage_match": percentage_match})
                .where(m.movie_genres.c.movie_id == movie_id, m.movie_genres.c.genre_id == genre.id)
            )
            db.execute(movie_genre)

        # Subgenres percentage match
        for percentage_match_dict in form_data.subgenres:
            subgenre_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            subgenre = db.scalar(sa.select(m.Subgenre).where(m.Subgenre.key == subgenre_key))

            if not subgenre:
                log(log.ERROR, "Subgenre [%s] not found", subgenre_key)
                filter_error_message = f"Subgenre [{subgenre_key}] not found"
                raise Exception

            movie_subgenre = (
                m.movie_subgenres.update()
                .values({"percentage_match": percentage_match})
                .where(m.movie_subgenres.c.movie_id == movie_id, m.movie_subgenres.c.subgenre_id == subgenre.id)
            )
            db.execute(movie_subgenre)

        # Specifications percentage match
        for percentage_match_dict in form_data.specifications:
            specification_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            specification = db.scalar(sa.select(m.Specification).where(m.Specification.key == specification_key))

            if not specification:
                log(log.ERROR, "Specification [%s] not found", specification_key)
                filter_error_message = f"Specification [{specification_key}] not found"
                raise Exception

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
        for percentage_match_dict in form_data.keywords:
            keyword_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            keyword = db.scalar(sa.select(m.Keyword).where(m.Keyword.key == keyword_key))

            if not keyword:
                log(log.ERROR, "Keyword [%s] not found", keyword_key)
                filter_error_message = f"Keyword [{keyword_key}] not found"
                raise Exception

            movie_keyword = (
                m.movie_keywords.update()
                .values({"percentage_match": percentage_match})
                .where(m.movie_keywords.c.movie_id == movie_id, m.movie_keywords.c.keyword_id == keyword.id)
            )
            db.execute(movie_keyword)

        # Action times percentage match
        for percentage_match_dict in form_data.action_times:
            action_time_key = percentage_match_dict.key
            percentage_match = percentage_match_dict.percentage_match
            action_time = db.scalar(sa.select(m.ActionTime).where(m.ActionTime.key == action_time_key))

            if not action_time:
                log(log.ERROR, "Action time [%s] not found", action_time_key)
                filter_error_message = f"Action time [{action_time_key}] not found"
                raise Exception

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
        e.args = (*e.args, filter_error_message)
        raise e


def add_new_characters(
    new_movie_id: int, db: Session, actors_keys: list[s.MoviePersonFilterField], import_to_google_sheet: bool
):
    # # Create characters
    try:
        for character in actors_keys:
            new_character = m.Character(
                key=character.character_key,
                translations=[
                    m.CharacterTranslation(
                        language=s.Language.UK.value,
                        name=character.character_name_uk,
                    ),
                    m.CharacterTranslation(
                        language=s.Language.EN.value,
                        name=character.character_name_en,
                    ),
                ],
                actors=[db.scalar(sa.select(m.Actor).where(m.Actor.key == character.key))],
                movies=[db.scalar(sa.select(m.Movie).where(m.Movie.id == new_movie_id))],
            )

            db.add(new_character)
            log(log.INFO, "Character [%s] successfully created", character.character_key)
    except Exception as e:
        log(log.ERROR, "Error creating character [%s]: %s", character.character_key, e)
        e.args = (*e.args, "Error creating character")
        raise e

    if import_to_google_sheet:
        # Save characters to json file
        try:
            character_error_message = "Error saving characters data to [data/characters.json] file"
            characters = db.scalars(sa.select(m.Character)).all()

            if not characters:
                character_error_message = "Characters not found"

            characters_to_file = []
            for char in characters:
                characters_to_file.append(
                    s.CharacterExportCreate(
                        id=char.id,
                        key=char.key,
                        name_uk=next((t.name for t in char.translations if t.language == s.Language.UK.value)),
                        name_en=next((t.name for t in char.translations if t.language == s.Language.EN.value)),
                        actors_ids=[actor.id for actor in char.actors],
                        movies_ids=[movie.id for movie in char.movies],
                    )
                )

            # with open("data/characters.json", "w") as file_json:
            #     json.dump(
            #         s.CharactersJSONFile(characters=characters_to_file).model_dump(mode="json"), file_json, indent=4
            #     )
            characters_data = s.CharactersJSONFile(characters=characters_to_file)
            from app.commands.imports_from_google_sheet.import_characters import (
                import_characters_to_google_spreadsheets,
            )

            import_characters_to_google_spreadsheets(len(actors_keys), characters_data)

        except Exception as e:
            log(log.ERROR, "%s: %s", character_error_message, e)
            e.args = (*e.args, character_error_message)
            raise e


def add_new_movie_rating(
    new_movie: m.Movie, db: Session, current_user: int, form_data: s.MovieFormData, import_to_google_sheet: bool
):
    # Add rating
    try:
        new_rating = m.Rating(
            # id=rating.id,
            movie_id=new_movie.id,
            user_id=current_user,
            rating=form_data.rating,
            acting=form_data.rating_criteria.acting,
            plot_storyline=form_data.rating_criteria.plot_storyline,
            music=form_data.rating_criteria.music,
            re_watchability=form_data.rating_criteria.re_watchability,
            emotional_impact=form_data.rating_criteria.emotional_impact,
            dialogue=form_data.rating_criteria.dialogue,
            production_design=form_data.rating_criteria.production_design,
            duration=form_data.rating_criteria.duration,
            visual_effects=form_data.rating_criteria.visual_effects,
            scare_factor=form_data.rating_criteria.scare_factor,
            # comment=form_data.rating_criteria.comment,
        )

        db.add(new_rating)

        log(log.INFO, "Rating [%s] successfully created")
    except Exception as e:
        # db.rollback()
        log(log.ERROR, "Error creating rating for movie [%s]: %s", new_movie.key, e)
        e.args = (*e.args, "Error creating rating")
        raise e

    if import_to_google_sheet:
        # Save ratings to json file
        try:
            rating_error_message = "Error saving ratings data to [data/ratings.json] file"
            ratings = db.scalars(sa.select(m.Rating).order_by(m.Rating.id)).all()
            if not ratings:
                log(log.ERROR, "Ratings not found")
                rating_error_message = "Ratings not found"
                raise Exception

            ratings_to_file = []

            for rating in ratings:
                ratings_to_file.append(
                    s.RatingExportCreate(
                        id=rating.id,
                        rating=rating.rating,
                        movie_id=rating.movie_id,
                        user_id=current_user,
                        acting=rating.acting,
                        plot_storyline=rating.plot_storyline,
                        music=rating.music,
                        re_watchability=rating.re_watchability,
                        emotional_impact=rating.emotional_impact,
                        dialogue=rating.dialogue,
                        production_design=rating.production_design,
                        duration=rating.duration,
                        visual_effects=rating.visual_effects if rating.visual_effects else None,
                        scare_factor=rating.scare_factor if rating.scare_factor else None,
                        comment=rating.comment if rating.comment else None,
                    )
                )

            # with open("data/ratings.json", "w") as file_json:
            #     json.dump(s.RatingsJSONFile(ratings=ratings_to_file).model_dump(mode="json"), file_json, indent=4)
            rate_data = s.RatingsJSONFile(ratings=ratings_to_file)
            from app.commands.imports_from_google_sheet.import_ratings import import_ratings_to_google_spreadsheets

            import_ratings_to_google_spreadsheets(rate_data)

        except Exception as e:
            db.rollback()
            log(log.ERROR, "%s: %s", rating_error_message, e)
            e.args = (*e.args, rating_error_message)
            raise e


def import_new_movie_to_google_sheet(db: Session):
    try:
        movie_error_message = "Error saving movies data to [data/movies.json] file"

        movies = db.scalars(sa.select(m.Movie)).all()

        if not movies:
            log(log.ERROR, "Movies not found")
            movie_error_message = "Movies not found"
            raise Exception

        movies_to_file = []

        for movie in movies:
            movies_to_file.append(
                s.MovieExportCreate(
                    id=movie.id,
                    key=movie.key,
                    title_uk=next((t.title for t in movie.translations if t.language == s.Language.UK.value)),
                    title_en=next((t.title for t in movie.translations if t.language == s.Language.EN.value)),
                    description_uk=next(
                        (t.description for t in movie.translations if t.language == s.Language.UK.value)
                    ),
                    description_en=next(
                        (t.description for t in movie.translations if t.language == s.Language.EN.value)
                    ),
                    # release_date=datetime.strptime(movie.release_date, "%d.%m.%Y"),
                    release_date=movie.release_date,
                    duration=int(movie.duration),
                    budget=int(movie.budget),
                    domestic_gross=int(movie.domestic_gross) if movie.domestic_gross else None,
                    worldwide_gross=int(movie.worldwide_gross) if movie.worldwide_gross else None,
                    poster=movie.poster,
                    actors_ids=[actor.id for actor in movie.actors],
                    directors_ids=[director.id for director in movie.directors],
                    location_uk=next((t.location for t in movie.translations if t.language == s.Language.UK.value)),
                    location_en=next((t.location for t in movie.translations if t.language == s.Language.EN.value)),
                    # Genres
                    genres_list=[
                        {
                            genre.id: next(
                                (
                                    mg.percentage_match
                                    for mg in db.query(m.movie_genres).filter_by(movie_id=movie.id, genre_id=genre.id)
                                ),
                                0.0,
                            )
                        }
                        for genre in movie.genres
                    ],
                    genres_ids=[genre.id for genre in movie.genres],
                    # Subgenres
                    subgenres_list=[
                        {
                            subgenre.id: next(
                                (
                                    mg.percentage_match
                                    for mg in db.query(m.movie_subgenres).filter_by(
                                        movie_id=movie.id, subgenre_id=subgenre.id
                                    )
                                ),
                                0.0,
                            )
                        }
                        for subgenre in movie.subgenres
                    ]
                    if movie.subgenres
                    else None,
                    subgenres_ids=[subgenre.id for subgenre in movie.subgenres] if movie.subgenres else None,
                    # users_ratings=users_rating,
                    rating_criterion=s.RatingCriterion(movie.rating_criterion),
                    # Specifications
                    specifications_ids=[specification.id for specification in movie.specifications],
                    specifications_list=[
                        {
                            specification.id: next(
                                (
                                    mg.percentage_match
                                    for mg in db.query(m.movie_specifications).filter_by(
                                        movie_id=movie.id, specification_id=specification.id
                                    )
                                ),
                                0.0,
                            )
                        }
                        for specification in movie.specifications
                    ],
                    # Keyword
                    keywords_ids=[keyword.id for keyword in movie.keywords],
                    keywords_list=[
                        {
                            keyword.id: next(
                                (
                                    mg.percentage_match
                                    for mg in db.query(m.movie_keywords).filter_by(
                                        movie_id=movie.id, keyword_id=keyword.id
                                    )
                                ),
                                0.0,
                            )
                        }
                        for keyword in movie.keywords
                    ],
                    # Action times
                    action_times_ids=[action_time.id for action_time in movie.action_times],
                    action_times_list=[
                        {
                            action_time.id: next(
                                (
                                    mg.percentage_match
                                    for mg in db.query(m.movie_action_times).filter_by(
                                        movie_id=movie.id, action_time_id=action_time.id
                                    )
                                ),
                                0.0,
                            )
                        }
                        for action_time in movie.action_times
                    ],
                    # rating_criterion=s.RatingCriterion(rating_criterion),
                )
            )

        # with open("data/movies.json", "w") as file_json:
        #     json.dump(s.MoviesJSONFile(movies=movies_to_file).model_dump(mode="json"), file_json, indent=4)
        # Import movie to google spreadsheets
        movies_data = s.MoviesJSONFile(movies=movies_to_file)
        from app.commands.imports_from_google_sheet.import_movies import append_data_to_google_spreadsheets

        append_data_to_google_spreadsheets(movies_data)

    except Exception as e:
        log(log.ERROR, "%s: %s", movie_error_message, e)
        e.args = (*e.args, movie_error_message)
        raise e
