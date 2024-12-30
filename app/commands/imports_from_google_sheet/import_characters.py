import json
from googleapiclient.discovery import build

from app import schema as s
from app.logger import log
from config import config
from ..export_characters import CHARS_RANGE_NAME

from ..utility import authorized_user_in_google_spreadsheets

CFG = config()


def import_characters_to_google_spreadsheets(new_chars_count: int = 1):
    """Import characters to google spreadsheets"""

    with open("data/characters.json", "r") as file:
        file_data = s.CharactersJSONFile.model_validate(json.load(file))

    characters = file_data.characters
    assert characters, "Characters are empty!"
    print("Characters COUNT: ", len(characters))

    new_characters = characters[-new_chars_count:]
    print("New Characters: ", new_characters)

    values = []

    for character in new_characters:
        values.append(
            [
                character.id,
                character.key,
                character.name_uk,
                character.name_en,
                ", ".join(map(str, character.actors_ids)),
                ", ".join(map(str, character.movies_ids)),
                character.id,
            ]
        )

    assert values[0], "Values are empty!"
    print("values: ", values)

    try:
        credentials = authorized_user_in_google_spreadsheets()

        resource = build("sheets", "v4", credentials=credentials)
        sheets = resource.spreadsheets()

        body = {"values": values}

        sheets.values().append(
            spreadsheetId=CFG.SPREADSHEET_ID, range=CHARS_RANGE_NAME, valueInputOption="RAW", body=body
        ).execute()
    except Exception as e:
        log(log.ERROR, "Error occurred while appending data to google spreadsheets - [%s]", e)
        log(log.INFO, "===== Perhaps you need update [VALUES] fields =====")
        raise e
