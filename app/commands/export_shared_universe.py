import json
import sqlalchemy as sa

from googleapiclient.discovery import build

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log
from config import config

from .utility import authorized_user_in_google_spreadsheets

CFG = config()

ID = "ID"
KEY = "key"
NAME_UK = "name_uk"
NAME_EN = "name_en"
DESCRIPTION_UK = "description_uk"
DESCRIPTION_EN = "description_en"

# Last column need to be filled!
LAST_SHEET_COLUMN = "G"
SHARED_UNIVERSE_RANGE_NAME = f"Shared Universe!A1:{LAST_SHEET_COLUMN}"


def write_su_in_db(universes: list[s.SharedUniverseExportCreate]):
    with db.begin() as session:
        if not session.scalar(sa.select(m.Genre)):
            log(log.ERROR, "Genre table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-genres` first")
            raise Exception("Genre table is empty. Please run `flask fill-db-with-genres` first")

        for universe in universes:
            new_universe = m.SharedUniverse(
                key=universe.key,
                translations=[
                    m.SharedUniverseTranslation(
                        language=s.Language.UK.value,
                        name=universe.name_uk,
                        description=universe.description_uk,
                    ),
                    m.SharedUniverseTranslation(
                        language=s.Language.EN.value,
                        name=universe.name_en,
                        description=universe.description_en,
                    ),
                ],
            )

            session.add(new_universe)
            session.flush()

            log(log.DEBUG, "Universe [%s] created", universe.name_uk)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_su_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill SharedUniverse table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=SHARED_UNIVERSE_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"
    print("values: ", values[:1])

    shared_universes: list[s.SharedUniverseExportCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    KEY_INDEX = values[0].index(KEY)
    NAME_UK_INDEX = values[0].index(NAME_UK)
    NAME_EN_INDEX = values[0].index(NAME_EN)
    DESCRIPTION_UK_INDEX = values[0].index(DESCRIPTION_UK)
    DESCRIPTION_EN_INDEX = values[0].index(DESCRIPTION_EN)

    for row in values[1:]:
        if not row[INDEX_ID]:
            continue

        id = row[INDEX_ID]
        assert id, f"The id {id} is missing"

        key = row[KEY_INDEX]
        assert key, f"The key {key} is missing"

        name_uk = row[NAME_UK_INDEX]
        assert name_uk, f"The name_uk {name_uk} is missing"
        # print("name_uk: ", name_uk)

        name_en = row[NAME_EN_INDEX]
        assert name_en, f"The name_en {name_en} is missing"

        description_uk = row[DESCRIPTION_UK_INDEX]
        description_en = row[DESCRIPTION_EN_INDEX]

        shared_universes.append(
            s.SharedUniverseExportCreate(
                key=key,
                name_uk=name_uk,
                name_en=name_en,
                description_uk=description_uk,
                description_en=description_en,
            )
        )

    print("Shared Universe COUNT: ", len(shared_universes))

    with open("data/shared_universes.json", "w") as file:
        json.dump(s.SharedUniversesJSONFile(shared_universes=shared_universes).model_dump(mode="json"), file, indent=4)
        print("Shared Universes data saved to [data/shared_universes.json] file")

    write_su_in_db(shared_universes)


def export_su_from_json_file(max_su_limit: int | None = None):
    """Fill SharedUniverse with data from json file"""

    with open("data/shared_universes.json", "r") as file:
        file_data = s.SharedUniversesJSONFile.model_validate(json.load(file))

    shared_universes = file_data.shared_universes
    if max_su_limit:
        shared_universes = shared_universes[:max_su_limit]
    write_su_in_db(shared_universes)
