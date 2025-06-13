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

# Last column need to be filled!
LAST_SHEET_COLUMN = "L"
ACTORS_RANGE_NAME = f"Actors!A1:{LAST_SHEET_COLUMN}"


def write_actors_in_db(actors: list[s.PersonExportCreate]):
    with db.begin() as session:
        for actor in actors:
            if session.scalar(sa.select(m.Actor).where(m.Actor.key == actor.key)):
                continue

            new_actor = m.Actor(
                key=actor.key,
                born=actor.born,
                died=actor.died,
                avatar=actor.avatar,
                translations=[
                    m.ActorTranslation(
                        language=s.Language.UK.value,
                        first_name=actor.first_name_uk,
                        last_name=actor.last_name_uk,
                        born_in=actor.born_in_uk,
                    ),
                    m.ActorTranslation(
                        language=s.Language.EN.value,
                        first_name=actor.first_name_en,
                        last_name=actor.last_name_en,
                        born_in=actor.born_in_en,
                    ),
                ],
            )

            session.add(new_actor)
            session.flush()

            log(log.DEBUG, "Job with title [%s] created", actor.first_name_uk)

        session.commit()


def export_actors_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill actors table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=ACTORS_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    actors: list[s.PersonExportCreate] = []

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

        id = row[INDEX_ID]
        assert id, f"The id {id} is missing"

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

        actors.append(
            s.PersonExportCreate(
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

    print("Actors COUNT: ", len(actors))

    with open("data/actors.json", "w") as file:
        json.dump(s.PersonJSONFile(people=actors).model_dump(mode="json"), file, indent=4)
        print("Actors data saved to [data/actors.json] file")

    write_actors_in_db(actors)


def export_actors_from_json_file(max_actors_limit: int | None = None):
    """Fill actors with data from json file"""

    with open("data/actors.json", "r") as file:
        file_data = s.PersonJSONFile.model_validate(json.load(file))

    actors = file_data.people
    if max_actors_limit:
        actors = actors[:max_actors_limit]
    write_actors_in_db(actors)
