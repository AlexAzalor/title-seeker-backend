import json
import sqlalchemy as sa

from googleapiclient.discovery import build

from app import models as m
from app import schema as s
from app.commands.utility import authorized_user_in_google_spreadsheets
from app.database import db
from app.logger import log
from config import config


CFG = config()

ID = "ID"
KEY = "key"
CATEGORY_ID = "category_id"
NAME = "name"
DESCRIPTION = "description"

# Last column need to be filled!
LAST_SHEET_COLUMN = "F"
TITLE_CATEGORIES_RANGE_NAME = f"KB Technology!A1:{LAST_SHEET_COLUMN}"


def write_kb_technologies_in_db(kb_technologies: list[s.KnowledgeBaseTechnologyCreate]):
    with db.begin() as session:
        if not session.scalar(sa.select(m.KnowledgeBaseCategory)):
            log(log.ERROR, "KB Category table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-kb-categories` first")
            raise Exception("KnowledgeBaseCategory table is empty. Please run `flask fill-db-with-kb-categories` first")

        for technology in kb_technologies:
            new_technology = m.KnowledgeBaseTechnology(
                key=technology.key,
                category_id=technology.category_id,
                name=technology.name,
                description=technology.description,
            )

            session.add(new_technology)
            session.flush()
            log(log.DEBUG, "KnowledgeBaseTechnology [%s] created", technology.key)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_kb_technologies_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=TITLE_CATEGORIES_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    technologies: list[s.KnowledgeBaseTechnologyCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    KEY_INDEX = values[0].index(KEY)
    CATEGORY_ID_INDEX = values[0].index(CATEGORY_ID)
    NAME_INDEX = values[0].index(NAME)
    DESCRIPTION_INDEX = values[0].index(DESCRIPTION)

    for row in values[1:]:
        if not row[INDEX_ID]:
            continue

        id = row[INDEX_ID]
        assert id, f"The id {id} is missing"

        key = row[KEY_INDEX]
        assert key, f"The key {key} is missing"

        category_id = row[CATEGORY_ID_INDEX]
        assert category_id, f"The category_id {category_id} is missing"

        name = row[NAME_INDEX]
        assert name, f"The question {name} is missing"

        description = row[DESCRIPTION_INDEX]
        assert description, f"The short_answer {description} is missing"

        technologies.append(
            s.KnowledgeBaseTechnologyCreate(
                key=key,
                category_id=int(category_id),
                name=name,
                description=description,
            )
        )

    print("Technologies COUNT: ", len(technologies))

    with open("data/knowledge_base/technologies.json", "w") as file:
        json.dump(s.KBTechnologyJSONFile(technologies=technologies).model_dump(mode="json"), file, indent=4)
        print("KB Technologies data saved to [data/knowledge_base/technologies.json] file")

    write_kb_technologies_in_db(technologies)


def export_kb_technologies_from_json_file(max_data_limit: int | None = None):
    """Fill kb technologies with data from json file"""

    with open("data/knowledge_base/technologies.json", "r") as file:
        file_data = s.KBTechnologyJSONFile.model_validate(json.load(file))

    technologies = file_data.technologies
    if max_data_limit:
        technologies = technologies[:max_data_limit]
    write_kb_technologies_in_db(technologies)
