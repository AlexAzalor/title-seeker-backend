import json
from datetime import datetime
from googleapiclient.discovery import build

import sqlalchemy as sa
from app import models as m
from app import schema as s
from app.database import db
from app.logger import log
from config import config

from .utility import authorized_user_in_google_spreadsheets

CFG = config()

ID = "ID"
KEY = "key"
FIRST_NAME_UK = "first_name_uk"
LAST_NAME_UK = "last_name_uk"
FIRST_NAME_EN = "first_name_en"
LAST_NAME_EN = "last_name_en"
BORN = "born"
DIED = "died"
BORN_IN_UK = "born_in_uk"
BORN_IN_EN = "born_in_en"
AVATAR = "avatar"


def write_directors_in_db(directors: list[s.DirectorExportCreate]):
    with db.begin() as session:
        for director in directors:
            if session.scalar(sa.select(m.Director).where(m.Director.key == director.key)):
                continue

            new_director = m.Director(
                key=director.key,
                born=director.born,
                died=director.died,
                avatar=director.avatar,
                translations=[
                    m.DirectorTranslation(
                        language=s.Language.UK.value,
                        first_name=director.first_name_uk,
                        last_name=director.last_name_uk,
                        born_in=director.born_in_uk,
                    ),
                    m.DirectorTranslation(
                        language=s.Language.EN.value,
                        first_name=director.first_name_en,
                        last_name=director.last_name_en,
                        born_in=director.born_in_en,
                    ),
                ],
            )

            session.add(new_director)
            session.flush()

            log(log.DEBUG, "Job with title [%s] created", director.first_name_uk)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_directors_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill directors table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # Last column need to be filled!
    LAST_SHEET_COLUMN = "L"
    RANGE_NAME = f"Directors!A1:{LAST_SHEET_COLUMN}"

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    directors: list[s.DirectorExportCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    KEY_INDEX = values[0].index(KEY)
    FIRST_NAME_UK_INDEX = values[0].index(FIRST_NAME_UK)
    LAST_NAME_UK_INDEX = values[0].index(LAST_NAME_UK)
    FIRST_NAME_EN_INDEX = values[0].index(FIRST_NAME_EN)
    LAST_NAME_EN_INDEX = values[0].index(LAST_NAME_EN)
    BORN_INDEX = values[0].index(BORN)
    DIED_INDEX = values[0].index(DIED)
    BORN_IN_UK_INDEX = values[0].index(BORN_IN_UK)
    BORN_IN_EN_INDEX = values[0].index(BORN_IN_EN)
    AVATAR_INDEX = values[0].index(AVATAR)

    print("values: ", values[:1])
    for row in values[1:]:
        if not row[INDEX_ID]:
            continue

        key = row[KEY_INDEX]
        assert key, f"The key {key} is missing"

        first_name_uk = row[FIRST_NAME_UK_INDEX]
        assert first_name_uk, f"The first_name_uk {first_name_uk} is missing"

        last_name_uk = row[LAST_NAME_UK_INDEX]
        assert last_name_uk, f"The last_name_uk {last_name_uk} is missing"

        first_name_en = row[FIRST_NAME_EN_INDEX]
        assert first_name_en, f"The first_name_en {first_name_en} is missing"

        last_name_en = row[LAST_NAME_EN_INDEX]
        assert last_name_en, f"The last_name_en {last_name_en} is missing"

        born = row[BORN_INDEX]
        assert born, f"The born {born} is missing"

        died = row[DIED_INDEX]

        born_in_uk = row[BORN_IN_UK_INDEX]
        assert born_in_uk, f"The born_in_uk {born_in_uk} is missing"

        born_in_en = row[BORN_IN_EN_INDEX]
        assert born_in_en, f"The born_in_en {born_in_en} is missing"

        avatar = row[AVATAR_INDEX]

        directors.append(
            s.DirectorExportCreate(
                key=key,
                first_name_uk=first_name_uk,
                last_name_uk=last_name_uk,
                first_name_en=first_name_en,
                last_name_en=last_name_en,
                born=datetime.strptime(born, "%d.%m.%Y"),
                died=datetime.strptime(died, "%d.%m.%Y") if died else None,
                born_in_uk=born_in_uk,
                born_in_en=born_in_en,
                avatar=avatar,
            )
        )

    print("Directors COUNT: ", len(directors))

    with open("data/directors.json", "w") as file:
        json.dump(s.DirectorsJSONFile(directors=directors).model_dump(mode="json"), file, indent=4)
        print("Directors data saved to [data/directors.json] file")

    write_directors_in_db(directors)


def export_directors_from_json_file(max_directors_limit: int | None = None):
    """Fill directors with data from json file"""

    with open("data/directors.json", "r") as file:
        file_data = s.DirectorsJSONFile.model_validate(json.load(file))

    directors = file_data.directors
    if max_directors_limit:
        directors = directors[:max_directors_limit]
    write_directors_in_db(directors)
