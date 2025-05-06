import json
import ast
from datetime import datetime
import sqlalchemy as sa

from googleapiclient.discovery import build

from api.utils import process_movie_rating
from app import models as m
from app import schema as s
from app.database import db
from app.logger import log
from config import config

from .utility import authorized_user_in_google_spreadsheets

CFG = config()

# Table columns
ID = "ID"
KEY = "key"
TITLE_UK = "title_uk"
TITLE_EN = "title_en"
DESCRIPTION_UK = "description_uk"
DESCRIPTION_EN = "description_en"
RELEASE_DATE = "release_date"
DURATION = "duration"
BUDGET = "budget"
DOMESTIC_GROSS = "domestic_gross"
WORLDWIDE_GROSS = "worldwide_gross"
POSTER = "poster"
ACTORS_IDS = "actors_ids"
DIRECTORS_IDS = "directors_ids"
GENRES = "genres"
SUBGENRES = "subgenres"
SPECIFICATIONS = "specifications"
KEYWORDS = "keywords"
ACTION_TIMES = "action_times"
LOCATION_UK = "location_uk"
LOCATION_EN = "location_en"
RATING_CRITERION = "rating_criterion"
# Related movies
RELATION_TYPE = "relation_type"
BASE_MOVIE_ID = "base_movie_id"
COLLECTION_ORDER = "collection_order"
# Shared Universe
SHARED_UNIVERSE_ID = "shared_universe_id"
SHARED_UNIVERSE_ORDER = "shared_universe_order"

LAST_SHEET_COLUMN = "AB"
MOVIES_RANGE_NAME = f"Movies!A1:{LAST_SHEET_COLUMN}"


def write_movies_in_db(movies: list[s.MovieExportCreate]):
    skipped_movies = 0
    with db.begin() as session:
        if not session.scalar(sa.select(m.Actor)):
            log(log.ERROR, "Actor table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-actors` first")
            raise Exception("Actor table is empty. Please run `flask fill-db-with-actors` first")
        if not session.scalar(sa.select(m.Director)):
            log(log.ERROR, "Director table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-directors` first")
            raise Exception("Director table is empty. Please run `flask fill-db-with-directors` first")
        if not session.scalar(sa.select(m.Genre)):
            log(log.ERROR, "Genre table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-genres` first")
            raise Exception("Genre table is empty. Please run `flask fill-db-with-genres` first")

        for movie in movies:
            if session.scalar(sa.select(m.Movie).where(m.Movie.key == movie.key)):
                skipped_movies += 1
                continue

            # print('movie', movie.key)

            subgenres = (
                [
                    session.scalar(sa.select(m.Subgenre).where(m.Subgenre.id == subgenre_id))
                    for subgenre_id in movie.subgenres_ids
                ]
                if movie.subgenres_ids
                else []
            )
            if subgenres:
                for subgenre in subgenres:
                    if subgenre.genre_id not in movie.genres_ids:
                        log(
                            log.ERROR,
                            "Subgenre [%s] has not parent genre, see MOVIE [%s] table column!",
                            subgenre.key,
                            movie.title_en,
                        )
                        raise Exception(
                            f"Subgenre [{subgenre.key}] has not parent genre, see MOVIE [{movie.title_en}] table column!"
                        )

            new_movie: m.Movie = m.Movie(
                key=movie.key,
                poster=movie.poster,
                release_date=movie.release_date,
                duration=movie.duration,
                budget=movie.budget,
                domestic_gross=movie.domestic_gross,
                worldwide_gross=movie.worldwide_gross,
                rating_criterion=movie.rating_criterion.value,
                relation_type=movie.relation_type.value if movie.relation_type else None,
                collection_base_movie_id=movie.base_movie_id,
                collection_order=movie.collection_order,
                shared_universe_id=movie.shared_universe_id,
                shared_universe_order=movie.shared_universe_order,
                translations=[
                    m.MovieTranslation(
                        language=s.Language.UK.value,
                        title=movie.title_uk,
                        description=movie.description_uk,
                        location=movie.location_uk,
                    ),
                    m.MovieTranslation(
                        language=s.Language.EN.value,
                        title=movie.title_en,
                        description=movie.description_en,
                        location=movie.location_en,
                    ),
                ],
                actors=[
                    session.scalar(sa.select(m.Actor).where(m.Actor.id == actor_id)) for actor_id in movie.actors_ids
                ],
                directors=[
                    session.scalar(sa.select(m.Director).where(m.Director.id == director_id))
                    for director_id in movie.directors_ids
                ],
                genres=[
                    session.scalar(sa.select(m.Genre).where(m.Genre.id == genre_id)) for genre_id in movie.genres_ids
                ],
                subgenres=[
                    session.scalar(sa.select(m.Subgenre).where(m.Subgenre.id == subgenre_id))
                    for subgenre_id in movie.subgenres_ids
                ]
                if movie.subgenres_ids
                else [],
                specifications=[
                    session.scalar(sa.select(m.Specification).where(m.Specification.id == specification_id))
                    for specification_id in movie.specifications_ids
                ],
                keywords=[
                    session.scalar(sa.select(m.Keyword).where(m.Keyword.id == keyword_id))
                    for keyword_id in movie.keywords_ids
                ],
                action_times=[
                    session.scalar(sa.select(m.ActionTime).where(m.ActionTime.id == action_time_id))
                    for action_time_id in movie.action_times_ids
                ],
            )

            session.add(new_movie)
            session.flush()
            log(log.DEBUG, "Job with title [%s] created", movie.title_uk)

            # for rating in movie.users_ratings:
            #     for user_id, rating_value in rating.items():
            # user = session.scalar(sa.select(m.User).where(m.User.id == user_id))
            # if not user:
            #     log(log.ERROR, "User [%s] not found", user_id)
            #     raise Exception(f"User [{user_id}] not found")

            min_rate = 0.01
            min_rating = 0.08
            default_user_id = 1

            ve_rate = min_rate if movie.rating_criterion == s.RatingCriterion.VISUAL_EFFECTS else None
            sf_rate = min_rate if movie.rating_criterion == s.RatingCriterion.SCARE_FACTOR else None

            humor_rate = min_rate if movie.rating_criterion == s.RatingCriterion.HUMOR else None

            ac_rate = min_rate if movie.rating_criterion == s.RatingCriterion.ANIMATION_CARTOON else None

            if ve_rate:
                min_rating += ve_rate

            if sf_rate:
                min_rating += sf_rate

            if humor_rate:
                min_rating += humor_rate

            if ac_rate:
                min_rating += ac_rate

            new_rating = m.Rating(
                user_id=default_user_id,
                movie_id=new_movie.id,
                rating=min_rating,
                acting=min_rate,
                plot_storyline=min_rate,
                script_dialogue=min_rate,
                music=min_rate,
                enjoyment=min_rate,
                production_design=min_rate,
                visual_effects=ve_rate,
                scare_factor=sf_rate,
                humor=humor_rate,
                animation_cartoon=ac_rate,
            )

            session.add(new_rating)

            process_movie_rating(new_movie)

            for percentage_match_dict in movie.genres_list:
                for genre_id, percentage in percentage_match_dict.items():
                    genre = session.scalar(sa.select(m.Genre).where(m.Genre.id == genre_id))

                    if not genre:
                        log(log.ERROR, "Genre [%s] not found", genre_id)
                        raise Exception(f"Genre [{genre_id}] not found")

                    movie_genre = (
                        m.movie_genres.update()
                        .values({"percentage_match": percentage})
                        .where(m.movie_genres.c.movie_id == new_movie.id, m.movie_genres.c.genre_id == genre_id)
                    )
                    session.execute(movie_genre)

            if movie.subgenres_list:
                for subgenre_percentage_match_dict in movie.subgenres_list:
                    for subgenre_id, percentage in subgenre_percentage_match_dict.items():
                        subgenre = session.scalar(sa.select(m.Subgenre).where(m.Subgenre.id == subgenre_id))

                        if not subgenre:
                            log(log.ERROR, "Subgenre [%s] not found", subgenre_id)
                            raise Exception(f"Subgenre [{subgenre_id}] not found")

                        movie_subgenre = (
                            m.movie_subgenres.update()
                            .values({"percentage_match": percentage})
                            .where(
                                m.movie_subgenres.c.movie_id == new_movie.id,
                                m.movie_subgenres.c.subgenre_id == subgenre_id,
                            )
                        )
                        session.execute(movie_subgenre)

            for specification in movie.specifications_list:
                for specification_id, percentage in specification.items():
                    specification = session.scalar(
                        sa.select(m.Specification).where(m.Specification.id == specification_id)
                    )

                    if not specification:
                        log(log.ERROR, "Specification [%s] not found", specification_id)
                        raise Exception(f"Specification [{specification_id}] not found")

                    movie_specification = (
                        m.movie_specifications.update()
                        .values({"percentage_match": percentage})
                        .where(
                            m.movie_specifications.c.movie_id == new_movie.id,
                            m.movie_specifications.c.specification_id == specification_id,
                        )
                    )
                    session.execute(movie_specification)

            for keyword in movie.keywords_list:
                for keyword_id, percentage in keyword.items():
                    keyword = session.scalar(sa.select(m.Keyword).where(m.Keyword.id == keyword_id))

                    if not keyword:
                        log(log.ERROR, "Keyword [%s] not found", keyword_id)
                        raise Exception(f"Keyword [{keyword_id}] not found")

                    movie_keyword = (
                        m.movie_keywords.update()
                        .values({"percentage_match": percentage})
                        .where(
                            m.movie_keywords.c.movie_id == new_movie.id,
                            m.movie_keywords.c.keyword_id == keyword_id,
                        )
                    )
                    session.execute(movie_keyword)

            for action_time in movie.action_times_list:
                for action_time_id, percentage in action_time.items():
                    action_time = session.scalar(sa.select(m.ActionTime).where(m.ActionTime.id == action_time_id))

                    if not action_time:
                        log(log.ERROR, "Action Time [%s] not found", action_time_id)
                        raise Exception(f"Action Time [{action_time_id}] not found")

                    movie_action_time = (
                        m.movie_action_times.update()
                        .values({"percentage_match": percentage})
                        .where(
                            m.movie_action_times.c.movie_id == new_movie.id,
                            m.movie_action_times.c.action_time_id == action_time_id,
                        )
                    )
                    session.execute(movie_action_time)

        session.commit()

    log(log.INFO, "Skipped movies: %s", skipped_movies)


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_movies_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill movies with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=MOVIES_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    print("movies table row", values[:1])
    movies: list[s.MovieExportCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    KEY_INDEX = values[0].index(KEY)
    TITLE_UK_INDEX = values[0].index(TITLE_UK)
    TITLE_EN_INDEX = values[0].index(TITLE_EN)
    DESCRIPTION_UK_INDEX = values[0].index(DESCRIPTION_UK)
    DESCRIPTION_EN_INDEX = values[0].index(DESCRIPTION_EN)
    RELEASE_DATE_INDEX = values[0].index(RELEASE_DATE)
    DURATION_INDEX = values[0].index(DURATION)
    BUDGET_INDEX = values[0].index(BUDGET)
    DOMESTIC_GROSS_INDEX = values[0].index(DOMESTIC_GROSS)
    WORLDWIDE_GROSS_INDEX = values[0].index(WORLDWIDE_GROSS)
    POSTER_INDEX = values[0].index(POSTER)
    ACTORS_IDS_INDEX = values[0].index(ACTORS_IDS)
    DIRECTORS_IDS_INDEX = values[0].index(DIRECTORS_IDS)
    GENRES_INDEX = values[0].index(GENRES)
    SUBGENRES_INDEX = values[0].index(SUBGENRES)
    SPECIFICATIONS_INDEX = values[0].index(SPECIFICATIONS)
    KEYWORDS_INDEX = values[0].index(KEYWORDS)
    ACTION_TIMES_INDEX = values[0].index(ACTION_TIMES)
    LOCATION_UK_INDEX = values[0].index(LOCATION_UK)
    LOCATION_EN_INDEX = values[0].index(LOCATION_EN)
    # USERS_RATINGS_INDEX = values[0].index(USERS_RATINGS)
    RATING_CRITERION_INDEX = values[0].index(RATING_CRITERION)
    RELATION_TYPE_INDEX = values[0].index(RELATION_TYPE)
    BASE_MOVIE_ID_INDEX = values[0].index(BASE_MOVIE_ID)
    COLLECTION_ORDER_INDEX = values[0].index(COLLECTION_ORDER)
    SHARED_UNIVERSE_ID_INDEX = values[0].index(SHARED_UNIVERSE_ID)
    SHARED_UNIVERSE_ORDER_INDEX = values[0].index(SHARED_UNIVERSE_ORDER)

    for row in values[1:]:
        # if len(row) < 12:
        #     continue

        if not row[INDEX_ID]:
            continue

        id = row[INDEX_ID]
        assert id, f"The id {id} is missing"

        key = row[KEY_INDEX]
        assert key, f"The key {key} is missing"

        title_uk = row[TITLE_UK_INDEX]
        assert title_uk, f"The title_uk {title_uk} is missing"

        title_en = row[TITLE_EN_INDEX]
        assert title_en, f"The title_en {title_en} is missing"

        description_uk = row[DESCRIPTION_UK_INDEX]
        assert description_uk, f"The description_uk {description_uk} is missing"

        description_en = row[DESCRIPTION_EN_INDEX]
        assert description_en, f"The description_en {description_en} is missing"

        release_date = row[RELEASE_DATE_INDEX]
        assert release_date, f"The release_date {release_date} is missing"

        duration = row[DURATION_INDEX]
        assert duration, f"The duration {duration} is missing"

        budget = row[BUDGET_INDEX]
        assert budget, f"The budget {budget} is missing"

        domestic_gross = row[DOMESTIC_GROSS_INDEX]
        assert domestic_gross, f"The domestic_gross {domestic_gross} is missing"

        worldwide_gross = row[WORLDWIDE_GROSS_INDEX]
        assert worldwide_gross, f"The worldwide_gross {worldwide_gross} is missing"

        poster = row[POSTER_INDEX]

        actors_ids = row[ACTORS_IDS_INDEX]
        assert actors_ids, f"The actors_ids {actors_ids} is missing"
        actors_ids = ast.literal_eval(actors_ids)

        directors_ids = row[DIRECTORS_IDS_INDEX]
        assert directors_ids, f"The directors_ids {directors_ids} is missing"
        directors_ids = ast.literal_eval(directors_ids)

        # Genres
        genres = row[GENRES_INDEX]
        assert genres, f"The genres {genres} is missing"
        genres_list: list[dict] = ast.literal_eval(genres)

        genres_ids = [list(genre_id.keys())[0] for genre_id in genres_list]
        assert genres_ids, f"The genres_ids {genres_ids} is missing"

        # Subgenres
        subgenres = row[SUBGENRES_INDEX]
        subgenres_list = None
        subgenres_ids = None

        if subgenres:
            subgenres_list = ast.literal_eval(subgenres)

        if subgenres_list:
            subgenres_ids = [list(subgenre_id.keys())[0] for subgenre_id in subgenres_list]
            assert subgenres_ids, f"The subgenres_ids {subgenres_ids} is missing"

        # Specifications
        specifications = row[SPECIFICATIONS_INDEX]
        assert specifications, f"The specifications {specifications} is missing"
        specifications_list: list[dict] = ast.literal_eval(specifications)

        specifications_ids = [list(specification_id.keys())[0] for specification_id in specifications_list]
        assert specifications_ids, f"The specifications_ids {specifications_ids} is missing"

        # Keywords
        keywords = row[KEYWORDS_INDEX]
        assert keywords, f"The keywords {keywords} is missing"
        keywords_list: list[dict] = ast.literal_eval(keywords)

        keywords_ids = [list(keyword_id.keys())[0] for keyword_id in keywords_list]

        # Action Times
        action_times = row[ACTION_TIMES_INDEX]
        assert action_times, f"The action_times {action_times} is missing"
        action_times_list: list[dict] = ast.literal_eval(action_times)

        action_times_ids = [list(action_time_id.keys())[0] for action_time_id in action_times_list]
        assert action_times_ids, f"The action_times_ids {action_times_ids} is missing"

        # print('1', action_times_ids)
        # print('2', action_times_list)

        location_uk = row[LOCATION_UK_INDEX]
        assert location_uk, f"The location_uk {location_uk} is missing"

        location_en = row[LOCATION_EN_INDEX]
        assert location_en, f"The location_en {location_en} is missing"

        # users_ratings = row[USERS_RATINGS_INDEX]
        # assert users_ratings, f"The users_ratings {users_ratings} is missing"

        # users_rating: list[dict] = ast.literal_eval(users_ratings)

        rating_criterion = row[RATING_CRITERION_INDEX]
        assert rating_criterion, f"The rating_criterion {rating_criterion} is missing"

        relation_type = row[RELATION_TYPE_INDEX]
        # assert relation_type, f"The relation_type {relation_type} is missing"

        base_movie_id = row[BASE_MOVIE_ID_INDEX]

        collection_order = row[COLLECTION_ORDER_INDEX]

        shared_universe_id = row[SHARED_UNIVERSE_ID_INDEX]
        shared_universe_order = row[SHARED_UNIVERSE_ORDER_INDEX]

        # Can be issues with empty values and None
        # Can be issues with LAST COLUMN letter

        movies.append(
            s.MovieExportCreate(
                id=id,
                key=key,
                title_uk=title_uk,
                title_en=title_en,
                description_uk=description_uk,
                description_en=description_en,
                release_date=datetime.strptime(release_date, "%d.%m.%Y"),
                duration=int(duration),
                budget=int(budget),
                domestic_gross=int(domestic_gross),
                worldwide_gross=int(worldwide_gross),
                poster=poster,
                actors_ids=actors_ids,
                directors_ids=directors_ids,
                location_uk=location_uk,
                location_en=location_en,
                # Genres
                genres_list=genres_list,
                genres_ids=genres_ids,
                # Subgenres
                subgenres_list=subgenres_list if subgenres_list else None,
                subgenres_ids=subgenres_ids if subgenres_ids else None,
                # users_ratings=users_rating,
                rating_criterion=rating_criterion,
                # Specifications
                specifications_ids=specifications_ids,
                specifications_list=specifications_list,
                # Keyword
                keywords_ids=keywords_ids,
                keywords_list=keywords_list,
                # Action times
                action_times_ids=action_times_ids,
                action_times_list=action_times_list,
                # rating_criterion=s.RatingCriterion(rating_criterion),
                relation_type=relation_type if relation_type else None,
                base_movie_id=base_movie_id if base_movie_id else None,
                collection_order=collection_order if collection_order else None,
                shared_universe_id=shared_universe_id if shared_universe_id else None,
                shared_universe_order=shared_universe_order if shared_universe_order else None,
            )
        )

    print("Movies COUNT: ", len(movies))

    with open("data/movies.json", "w") as file:
        json.dump(s.MoviesJSONFile(movies=movies).model_dump(mode="json"), file, indent=4)
        print("Movies data saved to [data/movies.json] file")

    write_movies_in_db(movies)
    log(log.INFO, "Movies data SUCCESSFULLY saved to database")


def export_movies_from_json_file(max_movies_limit: int | None = None):
    """Fill movies with data from json file"""

    with open("data/movies.json", "r") as file:
        file_data = s.MoviesJSONFile.model_validate(json.load(file))

    movies = file_data.movies
    if max_movies_limit:
        movies = movies[:max_movies_limit]
    write_movies_in_db(movies)
