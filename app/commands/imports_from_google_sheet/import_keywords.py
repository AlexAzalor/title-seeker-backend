import json
from googleapiclient.discovery import build

from app import schema as s

from app.logger import log
from config import config
from ..export_keywords import KEYWORDS_RANGE_NAME

from ..utility import authorized_user_in_google_spreadsheets

CFG = config()


def import_keywords_to_google_spreadsheets():
    """Import keywords to google spreadsheets"""

    with open("data/keywords.json", "r") as file:
        file_data = s.FilterJSONFile.model_validate(json.load(file))

    keywords = file_data.items
    assert keywords, "keywords are empty!"
    print("Keywords COUNT: ", len(keywords))

    keyword = keywords[-1]
    print("Current keywords: ", keyword.key)

    values = [
        [
            1,
            keyword.key,
            keyword.name_uk,
            keyword.name_en,
            keyword.description_uk,
            keyword.description_en,
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
            spreadsheetId=CFG.SPREADSHEET_ID, range=KEYWORDS_RANGE_NAME, valueInputOption="RAW", body=body
        ).execute()
    except Exception as e:
        log(log.ERROR, "Error occurred while appending data to google spreadsheets - [%s]", e)
        log(log.INFO, "===== Perhaps you need update [VALUES] data =====")
        raise e
