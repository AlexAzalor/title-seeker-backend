import json
from googleapiclient.discovery import build

from app import schema as s

from app.logger import log
from config import config
from ..export_genres import GENRES_RANGE_NAME

from ..utility import authorized_user_in_google_spreadsheets

CFG = config()


def import_genres_to_google_spreadsheets():
    """Import genres to google spreadsheets"""

    with open("data/genres.json", "r") as file:
        file_data = s.GenresJSONFile.model_validate(json.load(file))

    genres = file_data.genres
    assert genres, "genres are empty!"
    print("Genres COUNT: ", len(genres))

    genre = genres[-1]
    print("Current genre: ", genre.key)

    values = [
        [
            1,
            genre.key,
            genre.name_uk,
            genre.name_en,
            genre.description_uk,
            genre.description_en,
            1,
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
            spreadsheetId=CFG.SPREADSHEET_ID, range=GENRES_RANGE_NAME, valueInputOption="RAW", body=body
        ).execute()
    except Exception as e:
        log(log.ERROR, "Error occurred while appending data to google spreadsheets - [%s]", e)
        log(log.INFO, "===== Perhaps you need update [VALUES] data =====")
        raise e
