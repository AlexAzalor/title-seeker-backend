import json
import sqlalchemy as sa
import ast

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
CRITERIA_IDS = "criteria_ids"
NAME_UK = "name_uk"
NAME_EN = "name_en"
DESCRIPTION_UK = "description_uk"
DESCRIPTION_EN = "description_en"

# Last column need to be filled!
LAST_SHEET_COLUMN = "H"
TITLE_CATEGORIES_RANGE_NAME = f"Title Categories!A1:{LAST_SHEET_COLUMN}"


def write_title_categories_in_db(visual_profile_categories: list[s.VisualProfileExportCreate]):
    with db.begin() as session:
        if not session.scalar(sa.select(m.VisualProfileCategoryCriterion)):
            log(log.ERROR, "Genre table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-genres` first")
            raise Exception("Genre table is empty. Please run `flask fill-db-with-genres` first")

        for category in visual_profile_categories:
            new_category = m.VisualProfileCategory(
                key=category.key,
                criteria=[
                    session.scalar(
                        sa.select(m.VisualProfileCategoryCriterion).where(
                            m.VisualProfileCategoryCriterion.id == criterion_id
                        )
                    )
                    for criterion_id in category.criteria_ids
                ],
                translations=[
                    m.VPCategoryTranslation(
                        language=s.Language.UK.value,
                        name=category.name_uk,
                        description=category.description_uk,
                    ),
                    m.VPCategoryTranslation(
                        language=s.Language.EN.value,
                        name=category.name_en,
                        description=category.description_en,
                    ),
                ],
            )

            session.add(new_category)
            session.flush()
            log(log.DEBUG, "VisualProfileCategory [%s] created", category.name_uk)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_title_categories_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill title categories table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=TITLE_CATEGORIES_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"
    print("values: ", values[:1])

    visual_profile_categories: list[s.VisualProfileExportCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    KEY_INDEX = values[0].index(KEY)
    CRITERIA_IDS_INDEX = values[0].index(CRITERIA_IDS)
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

        criteria_ids = row[CRITERIA_IDS_INDEX]
        assert criteria_ids, f"The criteria_ids {criteria_ids} is missing"
        criteria_ids = ast.literal_eval(criteria_ids)

        name_uk = row[NAME_UK_INDEX]
        assert name_uk, f"The name_uk {name_uk} is missing"
        # print("name_uk: ", name_uk)

        name_en = row[NAME_EN_INDEX]
        assert name_en, f"The name_en {name_en} is missing"

        description_uk = row[DESCRIPTION_UK_INDEX]
        description_en = row[DESCRIPTION_EN_INDEX]

        visual_profile_categories.append(
            s.VisualProfileExportCreate(
                key=key,
                criteria_ids=criteria_ids,
                name_uk=name_uk,
                name_en=name_en,
                description_uk=description_uk,
                description_en=description_en,
            )
        )

    print("Categories COUNT: ", len(visual_profile_categories))

    with open("data/visual_profile_categories.json", "w") as file:
        json.dump(
            s.VisualProfileJSONFile(visual_profiles=visual_profile_categories).model_dump(mode="json"), file, indent=4
        )
        print("Title categories data saved to [data/visual_profile_categories.json] file")

    write_title_categories_in_db(visual_profile_categories)


def export_title_categories_from_json_file(max_tc_limit: int | None = None):
    """Fill visual_profile_categories with data from json file"""

    with open("data/visual_profile_categories.json", "r") as file:
        file_data = s.VisualProfileJSONFile.model_validate(json.load(file))

    visual_profile_categories = file_data.visual_profiles
    if max_tc_limit:
        visual_profile_categories = visual_profile_categories[:max_tc_limit]
    write_title_categories_in_db(visual_profile_categories)
