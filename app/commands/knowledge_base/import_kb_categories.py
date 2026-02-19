import json

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
NAME = "name"
DESCRIPTION = "description"

# Last column need to be filled!
LAST_SHEET_COLUMN = "E"
TITLE_CATEGORIES_RANGE_NAME = f"KB Category!A1:{LAST_SHEET_COLUMN}"


def write_kb_categories_in_db(kb_categories: list[s.KnowledgeBaseCategoryCreate]):
    with db.begin() as session:
        for category in kb_categories:
            new_category = m.KnowledgeBaseCategory(
                key=category.key,
                name=category.name,
                description=category.description,
            )

            session.add(new_category)
            session.flush()
            log(log.DEBUG, "KnowledgeBaseCategory [%s] created", category.key)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_kb_categories_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=TITLE_CATEGORIES_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    categories: list[s.KnowledgeBaseCategoryCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    KEY_INDEX = values[0].index(KEY)
    NAME_INDEX = values[0].index(NAME)
    DESCRIPTION_INDEX = values[0].index(DESCRIPTION)

    for row in values[1:]:
        if not row[INDEX_ID]:
            continue

        id = row[INDEX_ID]
        assert id, f"The id {id} is missing"

        key = row[KEY_INDEX]
        assert key, f"The key {key} is missing"

        name = row[NAME_INDEX]
        assert name, f"The question {name} is missing"

        description = row[DESCRIPTION_INDEX]
        assert description, f"The short_answer {description} is missing"

        categories.append(
            s.KnowledgeBaseCategoryCreate(
                key=key,
                name=name,
                description=description,
            )
        )

    print("Categories COUNT: ", len(categories))

    with open("data/knowledge_base/categories.json", "w") as file:
        json.dump(s.KBCategoryJSONFile(categories=categories).model_dump(mode="json"), file, indent=4)
        print("KB Categories data saved to [data/knowledge_base/categories.json] file")

    write_kb_categories_in_db(categories)


def export_kb_categories_from_json_file(max_data_limit: int | None = None):
    """Fill kb categories with data from json file"""

    with open("data/knowledge_base/categories.json", "r") as file:
        file_data = s.KBCategoryJSONFile.model_validate(json.load(file))

    categories = file_data.categories
    if max_data_limit:
        categories = categories[:max_data_limit]
    write_kb_categories_in_db(categories)
