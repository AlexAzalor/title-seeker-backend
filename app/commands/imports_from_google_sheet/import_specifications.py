import json
from googleapiclient.discovery import build

from app import schema as s

from app.logger import log
from config import config
from ..export_specifications import SPEC_RANGE_NAME

from ..utility import authorized_user_in_google_spreadsheets

CFG = config()


def import_specifications_to_google_spreadsheets():
    """Import specifications to google spreadsheets"""

    with open("data/specifications.json", "r") as file:
        file_data = s.SpecificationsJSONFile.model_validate(json.load(file))

    specifications = file_data.specifications
    assert specifications, "specifications are empty!"
    print("Specifications COUNT: ", len(specifications))

    specification = specifications[-1]
    print("Current specifications: ", specification.key)

    values = [
        [
            1,
            specification.key,
            specification.name_uk,
            specification.name_en,
            specification.description_uk,
            specification.description_en,
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
            spreadsheetId=CFG.SPREADSHEET_ID, range=SPEC_RANGE_NAME, valueInputOption="RAW", body=body
        ).execute()
    except Exception as e:
        log(log.ERROR, "Error occurred while appending data to google spreadsheets - [%s]", e)
        log(log.INFO, "===== Perhaps you need update [VALUES] data =====")
        raise e
