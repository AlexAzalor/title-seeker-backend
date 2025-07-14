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
PARENT_GENRE_ID = "parent_genre_id"
KEY = "key"
NAME_UK = "name_uk"
NAME_EN = "name_en"
DESCRIPTION_UK = "description_uk"
DESCRIPTION_EN = "description_en"

# Last column need to be filled!
LAST_SHEET_COLUMN = "H"
SUBGENRES_RANGE_NAME = f"Subgenres!A1:{LAST_SHEET_COLUMN}"


def write_subgenres_in_db(subgenres: list[s.GenreFormFields]):
    with db.begin() as session:
        if not session.scalar(sa.select(m.Genre)):
            log(log.ERROR, "Genre table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-genres` first")
            raise Exception("Genre table is empty. Please run `flask fill-db-with-genres` first")

        for subgenre in subgenres:
            new_subgenre = m.Subgenre(
                genre_id=subgenre.parent_genre_id,
                key=subgenre.key,
                translations=[
                    m.SubgenreTranslation(
                        language=s.Language.UK.value,
                        name=subgenre.name_uk,
                        description=subgenre.description_uk,
                    ),
                    m.SubgenreTranslation(
                        language=s.Language.EN.value,
                        name=subgenre.name_en,
                        description=subgenre.description_en,
                    ),
                ],
            )

            session.add(new_subgenre)
            session.flush()

            log(log.DEBUG, "Subgenre [%s] created", subgenre.name_uk)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_subgenres_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill subgenres table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=SUBGENRES_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    subgenres: list[s.GenreFormFields] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    PARENT_GENRE_ID_INDEX = values[0].index(PARENT_GENRE_ID)
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

        name_en = row[NAME_EN_INDEX]
        assert name_en, f"The name_en {name_en} is missing"

        description_uk = row[DESCRIPTION_UK_INDEX]
        description_en = row[DESCRIPTION_EN_INDEX]
        parent_genre_id = row[PARENT_GENRE_ID_INDEX]
        assert parent_genre_id, f"The parent_genre_id {parent_genre_id} is missing"
        # parent_genre_id = convert_string_to_list_of_integers(parent_genre_id)

        subgenres.append(
            s.GenreFormFields(
                key=key,
                name_uk=name_uk,
                name_en=name_en,
                description_uk=description_uk,
                description_en=description_en,
                parent_genre_id=parent_genre_id,
            )
        )

    print("Subgenres COUNT: ", len(subgenres))

    with open("data/subgenres.json", "w") as file:
        json.dump(s.GenresJSONFile(items=subgenres).model_dump(mode="json"), file, indent=4)
        print("Subgenres data saved to [data/subgenres.json] file")

    write_subgenres_in_db(subgenres)


def export_subgenres_from_json_file(max_subgenres_limit: int | None = None):
    """Fill subgenres with data from json file"""

    with open("data/subgenres.json", "r") as file:
        file_data = s.GenresJSONFile.model_validate(json.load(file))

    subgenres = file_data.items
    if max_subgenres_limit:
        subgenres = subgenres[:max_subgenres_limit]
    write_subgenres_in_db(subgenres)
