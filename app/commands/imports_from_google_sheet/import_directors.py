import json
from googleapiclient.discovery import build

from app import schema as s
from app.logger import log
from config import config
from ..export_directors import DIRECTORS_RANGE_NAME

from ..utility import authorized_user_in_google_spreadsheets

CFG = config()

# [['ID', 'key', 'first_name_uk', 'last_name_uk', 'first_name_en', 'last_name_en', 'born', 'died', 'born_in_uk', 'born_in_en', 'avatar', 'ID-2']]


def import_directors_to_google_spreadsheets():
    """Import directors to google spreadsheets"""

    with open("data/directors.json", "r") as file:
        file_data = s.PersonJSONFile.model_validate(json.load(file))

    directors = file_data.people
    assert directors, "dDirectors are empty!"
    print("Directors COUNT: ", len(directors))

    director = directors[-1]
    print("Current director: ", director.key)

    values = [
        [
            1,
            director.key,
            director.first_name_uk,
            director.last_name_uk,
            director.first_name_en,
            director.last_name_en,
            director.born.strftime("%d.%m.%Y"),
            director.died.strftime("%d.%m.%Y") if director.died else "",
            director.born_in_uk,
            director.born_in_en,
            director.avatar,
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
            spreadsheetId=CFG.SPREADSHEET_ID, range=DIRECTORS_RANGE_NAME, valueInputOption="RAW", body=body
        ).execute()
    except Exception as e:
        log(log.ERROR, "Error occurred while appending data to google spreadsheets - [%s]", e)
        log(log.INFO, "===== Perhaps you need update [VALUES] data =====")
        raise e
