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
TITLE_CRITERIA_RANGE_NAME = f"Title Criteria!A1:{LAST_SHEET_COLUMN}"


def write_title_criteria_in_db(title_criteria: list[s.TitleCriterionExportCreate]):
    with db.begin() as session:
        categories = session.scalars(sa.select(m.Movie)).all()

        if not categories:
            log(log.ERROR, "Movie table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-***` first")
            raise Exception("Movie table is empty. Please run `flask fill-db-with-***` first")

        for criterion in title_criteria:
            new_criterion = m.TitleCriterion(
                key=criterion.key,
                translations=[
                    m.TitleCriterionTranslation(
                        language=s.Language.UK.value,
                        name=criterion.name_uk,
                        description=criterion.description_uk,
                    ),
                    m.TitleCriterionTranslation(
                        language=s.Language.EN.value,
                        name=criterion.name_en,
                        description=criterion.description_en,
                    ),
                ],
            )

            session.add(new_criterion)
            session.flush()

            log(log.DEBUG, "TitleCriterion [%s] created", criterion.name_uk)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_title_criteria_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill title criteria table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=TITLE_CRITERIA_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"
    print("values: ", values[:1])

    title_criteria: list[s.TitleCriterionExportCreate] = []

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

        title_criteria.append(
            s.TitleCriterionExportCreate(
                id=id,
                key=key,
                name_uk=name_uk,
                name_en=name_en,
                description_uk=description_uk,
                description_en=description_en,
            )
        )

    print("Criteria COUNT: ", len(title_criteria))

    with open("data/title_criteria.json", "w") as file:
        json.dump(s.TitleCriterionJSONFile(criteria=title_criteria).model_dump(mode="json"), file, indent=4)
        print("Title criteria data saved to [data/title_criteria.json] file")

    write_title_criteria_in_db(title_criteria)


def export_title_criteria_from_json_file(max_limit: int | None = None):
    """Fill title_criteria with data from json file"""

    with open("data/title_criteria.json", "r") as file:
        file_data = s.TitleCriterionJSONFile.model_validate(json.load(file))

    title_criteria = file_data.criteria
    if max_limit:
        title_criteria = title_criteria[:max_limit]
    write_title_criteria_in_db(title_criteria)
