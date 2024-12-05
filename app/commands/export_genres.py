import json

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


def write_genres_in_db(genres: list[s.GenreExportCreate]):
    with db.begin() as session:
        for genre in genres:
            new_genre = m.Genre(
                key=genre.key,
                translations=[
                    m.GenreTranslation(
                        language=s.Language.UK.value,
                        name=genre.name_uk,
                        description=genre.description_uk,
                    ),
                    m.GenreTranslation(
                        language=s.Language.EN.value,
                        name=genre.name_en,
                        description=genre.description_en,
                    ),
                ],
            )

            session.add(new_genre)
            session.flush()

            log(log.DEBUG, "Genre [%s] created", genre.name_uk)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_genres_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill genres table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # Last column need to be filled!
    LAST_SHEET_COLUMN = "G"
    RANGE_NAME = f"Genres!A1:{LAST_SHEET_COLUMN}"

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    genres: list[s.GenreExportCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    KEY_INDEX = values[0].index(KEY)
    NAME_UK_INDEX = values[0].index(NAME_UK)
    NAME_EN_INDEX = values[0].index(NAME_EN)
    DESCRIPTION_UK_INDEX = values[0].index(DESCRIPTION_UK)
    DESCRIPTION_EN_INDEX = values[0].index(DESCRIPTION_EN)

    print("values: ", values[:1])
    for row in values[1:]:
        if not row[INDEX_ID]:
            continue

        key = row[KEY_INDEX]
        assert key, f"The key {key} is missing"

        name_uk = row[NAME_UK_INDEX]
        assert name_uk, f"The name_uk {name_uk} is missing"
        # print("name_uk: ", name_uk)

        name_en = row[NAME_EN_INDEX]
        assert name_en, f"The name_en {name_en} is missing"

        description_uk = row[DESCRIPTION_UK_INDEX]
        description_en = row[DESCRIPTION_EN_INDEX]

        genres.append(
            s.GenreExportCreate(
                key=key,
                name_uk=name_uk,
                name_en=name_en,
                description_uk=description_uk,
                description_en=description_en,
            )
        )

    print("Genres COUNT: ", len(genres))

    with open("data/genres.json", "w") as file:
        json.dump(s.GenresJSONFile(genres=genres).model_dump(mode="json"), file, indent=4)
        print("Genres data saved to [data/genres.json] file")

    write_genres_in_db(genres)


def export_genres_from_json_file(max_genres_limit: int | None = None):
    """Fill genres with data from json file"""

    with open("data/genres.json", "r") as file:
        file_data = s.GenresJSONFile.model_validate(json.load(file))

    genres = file_data.genres
    if max_genres_limit:
        genres = genres[:max_genres_limit]
    write_genres_in_db(genres)
