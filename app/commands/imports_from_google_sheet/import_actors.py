import json
from googleapiclient.discovery import build

from app import schema as s
from app.logger import log
from config import config

from ..utility import authorized_user_in_google_spreadsheets

CFG = config()

# [['ID', 'key', 'first_name_uk', 'last_name_uk', 'first_name_en', 'last_name_en', 'born', 'died', 'born_in_uk', 'born_in_en', 'avatar', 'ID-2']]


def import_actors_to_google_spreadsheets():
    """Import actors to google spreadsheets"""

    with open("data/actors.json", "r") as file:
        file_data = s.ActorsJSONFile.model_validate(json.load(file))

    actors = file_data.actors
    assert actors, "Actors are empty!"
    print("Actors COUNT: ", len(actors))

    actor = actors[-1]
    print("Current actor: ", actor.key)

    values = [
        [
            actor.id,
            actor.key,
            actor.first_name_uk,
            actor.last_name_uk,
            actor.first_name_en,
            actor.last_name_en,
            actor.born.strftime("%d.%m.%Y"),
            actor.died.strftime("%d.%m.%Y") if actor.died else "",
            actor.born_in_uk,
            actor.born_in_en,
            actor.avatar,
            actor.id,
        ]
    ]

    assert values[0], "Values are empty!"
    print("values: ", values)

    try:
        credentials = authorized_user_in_google_spreadsheets()

        # Last column need to be filled!
        LAST_SHEET_COLUMN = "L"
        RANGE_NAME = f"Actors!A1:{LAST_SHEET_COLUMN}"

        resource = build("sheets", "v4", credentials=credentials)
        sheets = resource.spreadsheets()

        body = {"values": values}

        sheets.values().append(
            spreadsheetId=CFG.SPREADSHEET_ID, range=RANGE_NAME, valueInputOption="RAW", body=body
        ).execute()
    except Exception as e:
        log(log.ERROR, "Error occurred while appending data to google spreadsheets - [%s]", e)
        log(log.INFO, "===== Perhaps you need update [VALUES] data =====")
        raise e
