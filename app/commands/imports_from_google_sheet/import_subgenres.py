import json
from googleapiclient.discovery import build

from app import schema as s

from app.logger import log
from config import config
from ..export_subgenres import SUBGENRES_RANGE_NAME

from ..utility import authorized_user_in_google_spreadsheets

CFG = config()


def import_subgenres_to_google_spreadsheets():
    """Import subgenres to google spreadsheets"""

    with open("data/subgenres.json", "r") as file:
        file_data = s.SubgenresJSONFile.model_validate(json.load(file))

    subgenres = file_data.subgenres
    assert subgenres, "subgenres are empty!"
    print("Subgenres COUNT: ", len(subgenres))

    subgenre = subgenres[-1]
    print("Current subgenre: ", subgenre.key)

    values = [
        [
            subgenre.id,
            subgenre.key,
            subgenre.name_uk,
            subgenre.name_en,
            subgenre.description_uk,
            subgenre.description_en,
            subgenre.parent_genre_id,
            subgenre.id,
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
            spreadsheetId=CFG.SPREADSHEET_ID, range=SUBGENRES_RANGE_NAME, valueInputOption="RAW", body=body
        ).execute()
    except Exception as e:
        log(log.ERROR, "Error occurred while appending data to google spreadsheets - [%s]", e)
        log(log.INFO, "===== Perhaps you need update [VALUES] data =====")
        raise e
