import json
from datetime import datetime

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


def write_movies_in_db(movies: list[s.MovieExportCreate]):
    with db.begin() as session:
        for movie in movies:
            new_movie: m.Movie = m.Movie(
                poster=movie.poster,
                release_date=movie.release_date,
                duration=movie.duration,
                budget=movie.budget,
                domestic_gross=movie.domestic_gross,
                worldwide_gross=movie.worldwide_gross,
                translations=[
                    m.MovieTranslation(
                        language=s.Language.UK.value, title=movie.title_uk, description=movie.description_uk
                    ),
                    m.MovieTranslation(
                        language=s.Language.EN.value, title=movie.title_en, description=movie.description_en
                    ),
                ],
            )

            session.add(new_movie)
            session.flush()
            log(log.DEBUG, "Job with title [%s] created", movie.title_uk)

        session.commit()


def export_movies_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill movies with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    LAST_SHEET_COLUMN = "L"
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

    for row in values[1:]:
        # if len(row) < 12:
        #     continue

        if not row[INDEX_ID]:
            continue

        title_uk = row[TITLE_UK_INDEX]
        assert title_uk, f"The title_uk {title_uk} is missing"
        print("=== TITLE ===", title_uk)

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

        movies.append(
            s.MovieExportCreate(
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
            )
        )

    print("Movies COUNT: ", len(movies))

    # if in_json:
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
