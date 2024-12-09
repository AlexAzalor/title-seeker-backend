import json
from datetime import datetime
import sqlalchemy as sa

from googleapiclient.discovery import build

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log
from config import config

from .utility import authorized_user_in_google_spreadsheets

CFG = config()

# ['ID', 'owner_id', 'worker_id', 'title', 'description', 'service', 'location', 'address', 'created_at', 'started_at', 'finished_at', 'rate_owner', 'rate_worker']
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
GENRES_IDS = "genres_ids"
SUBGENRES_IDS = "subgenres_ids"
LOCATION_UK = "location_uk"
LOCATION_EN = "location_en"


def write_movies_in_db(movies: list[s.MovieExportCreate]):
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
            print("[DB BLOCK] MOVIE KEY: ", movie.key)
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
                        log(log.ERROR, "Subgenre [%s] has not parent genre", subgenre.key)
                        raise Exception(f"Subgenre [{subgenre.key}] has not parent genre")

            new_movie: m.Movie = m.Movie(
                key=movie.key,
                poster=movie.poster,
                release_date=movie.release_date,
                duration=movie.duration,
                budget=movie.budget,
                domestic_gross=movie.domestic_gross,
                worldwide_gross=movie.worldwide_gross,
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
            )

            session.add(new_movie)
            session.flush()
            log(log.DEBUG, "Job with title [%s] created", movie.title_uk)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_movies_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill movies with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    LAST_SHEET_COLUMN = "S"
    RANGE_NAME = f"Movies!A1:{LAST_SHEET_COLUMN}"

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

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
    GENRES_IDS_INDEX = values[0].index(GENRES_IDS)
    SUBGENRES_IDS_INDEX = values[0].index(SUBGENRES_IDS)
    LOCATION_UK_INDEX = values[0].index(LOCATION_UK)
    LOCATION_EN_INDEX = values[0].index(LOCATION_EN)

    for row in values[1:]:
        # if len(row) < 12:
        #     continue

        if not row[INDEX_ID]:
            continue

        key = row[KEY_INDEX]
        assert key, f"The key {key} is missing"

        print("=== MOVIE KEY: ", key)

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
        actors_ids = convert_string_to_list_of_integers(actors_ids)

        directors_ids = row[DIRECTORS_IDS_INDEX]
        assert directors_ids, f"The directors_ids {directors_ids} is missing"
        directors_ids = convert_string_to_list_of_integers(directors_ids)

        genres_ids = row[GENRES_IDS_INDEX]
        assert genres_ids, f"The genres_ids {genres_ids} is missing"
        genres_ids = convert_string_to_list_of_integers(genres_ids)

        subgenres_ids = row[SUBGENRES_IDS_INDEX]
        if subgenres_ids:
            subgenres_ids = convert_string_to_list_of_integers(subgenres_ids)

        location_uk = row[LOCATION_UK_INDEX]
        assert location_uk, f"The location_uk {location_uk} is missing"

        location_en = row[LOCATION_EN_INDEX]
        assert location_en, f"The location_en {location_en} is missing"

        movies.append(
            s.MovieExportCreate(
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
                genres_ids=genres_ids,
                subgenres_ids=subgenres_ids if subgenres_ids else None,
                location_uk=location_uk,
                location_en=location_en,
            )
        )

    print("Movies COUNT: ", len(movies))

    with open("data/movies.json", "w") as file:
        json.dump(s.MoviesJSONFile(movies=movies).model_dump(mode="json"), file, indent=4)
        print("Movies data saved to [data/movies.json] file")

    write_movies_in_db(movies)


def export_movies_from_json_file(max_movies_limit: int | None = None):
    """Fill movies with data from json file"""

    with open("data/movies.json", "r") as file:
        file_data = s.MoviesJSONFile.model_validate(json.load(file))

    movies = file_data.movies
    if max_movies_limit:
        movies = movies[:max_movies_limit]
    write_movies_in_db(movies)
