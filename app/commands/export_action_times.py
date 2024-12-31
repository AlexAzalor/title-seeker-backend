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
ACT_TIME_RANGE_NAME = f"Action time!A1:{LAST_SHEET_COLUMN}"


def write_action_times_in_db(action_times: list[s.ActionTimeExportCreate]):
    with db.begin() as session:
        if not session.scalar(sa.select(m.Genre)):
            log(log.ERROR, "Genre table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-genres` first")
            raise Exception("Genre table is empty. Please run `flask fill-db-with-genres` first")

        for action_time in action_times:
            new_action_time = m.ActionTime(
                key=action_time.key,
                translations=[
                    m.ActionTimeTranslation(
                        language=s.Language.UK.value,
                        name=action_time.name_uk,
                        description=action_time.description_uk,
                    ),
                    m.ActionTimeTranslation(
                        language=s.Language.EN.value,
                        name=action_time.name_en,
                        description=action_time.description_en,
                    ),
                ],
            )

            session.add(new_action_time)
            session.flush()

            log(log.DEBUG, "ActionTime [%s] created", action_time.name_uk)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_action_times_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill ActionTime table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=ACT_TIME_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"
    print("values: ", values[:1])

    action_times: list[s.ActionTimeExportCreate] = []

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

        action_times.append(
            s.ActionTimeExportCreate(
                id=id,
                key=key,
                name_uk=name_uk,
                name_en=name_en,
                description_uk=description_uk,
                description_en=description_en,
            )
        )

    print("Action Times COUNT: ", len(action_times))

    with open("data/action_times.json", "w") as file:
        json.dump(s.ActionTimesJSONFile(action_times=action_times).model_dump(mode="json"), file, indent=4)
        print("Action Times data saved to [data/action_times.json] file")

    write_action_times_in_db(action_times)


def export_action_times_from_json_file(max_action_times_limit: int | None = None):
    """Fill action_times with data from json file"""

    with open("data/action_times.json", "r") as file:
        file_data = s.ActionTimesJSONFile.model_validate(json.load(file))

    action_times = file_data.action_times
    if max_action_times_limit:
        action_times = action_times[:max_action_times_limit]
    write_action_times_in_db(action_times)
