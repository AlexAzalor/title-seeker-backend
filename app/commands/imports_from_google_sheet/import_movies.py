import json
from googleapiclient.discovery import build

from app import schema as s
from ..export_movies import MOVIES_RANGE_NAME
from app.logger import log
from config import config

from ..utility import authorized_user_in_google_spreadsheets

CFG = config()

# [['ID', 'key', 'title_uk', 'title_en', 'description_uk', 'description_en', 'release_date', 'duration', 'budget', 'domestic_gross', 'worldwide_gross', 'poster', 'actors_ids', 'directors_ids', 'genres_ids_with_percentage_match', 'subgenres_ids_with_percentage_match', 'specifications', 'keywords', 'action_times', 'location_uk', 'location_en', 'users_ratings', 'rating_criterion', 'ID-2']]


def append_data_to_google_spreadsheets():
    """Append data to google spreadsheets"""

    with open("data/movies.json", "r") as file:
        file_data = s.MoviesJSONFile.model_validate(json.load(file))

    movies = file_data.movies
    print("Movies COUNT: ", len(movies))

    movie = movies[-1]
    print("Current movie: ", movie.key)

    values = [
        [
            movie.id,
            movie.key,
            movie.title_uk,
            movie.title_en,
            movie.description_uk,
            movie.description_en,
            movie.release_date.strftime("%d.%m.%Y"),
            movie.duration,
            movie.budget,
            movie.domestic_gross,
            movie.worldwide_gross,
            movie.poster,
            str(movie.actors_ids),
            str(movie.directors_ids),
            str(movie.genre_percentage_match_list),
            str(movie.subgenre_percentage_match_list) if movie.subgenre_percentage_match_list else "",
            str(movie.specifications_list),
            str(movie.keywords_list),
            str(movie.action_times_list),
            movie.location_uk,
            movie.location_en,
            # str(movie.users_ratings),
            movie.rating_criterion.value,
            movie.id,
        ]
    ]

    assert values[0], "Values are empty!"
    print("values: ", values)

    try:
        credentials = authorized_user_in_google_spreadsheets()

        resource = build("sheets", "v4", credentials=credentials)
        sheets = resource.spreadsheets()

        body = {"values": values}

        sheets.values().append(
            spreadsheetId=CFG.SPREADSHEET_ID, range=MOVIES_RANGE_NAME, valueInputOption="RAW", body=body
        ).execute()
    except Exception as e:
        log(log.ERROR, "Error occurred while appending data to google spreadsheets - [%s]", e)
        log(log.INFO, "===== Perhaps you need update [VALUES] data =====")
        raise e
