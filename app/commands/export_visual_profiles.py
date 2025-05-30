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
MOVIE_ID = "movie_id"
USER_ID = "user_id"
CATEGORY_ID = "category_id"

# Last column need to be filled!
LAST_SHEET_COLUMN = "E"
TITLE_VP_RANGE_NAME = f"Title Visual Profile!A1:{LAST_SHEET_COLUMN}"


def write_title_vp_in_db(title_vp: list[s.VPRatingExportCreate]):
    with db.begin() as session:
        if not session.scalar(sa.select(m.VisualProfileCategory)):
            log(log.ERROR, "Genre table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-genres` first")
            raise Exception("Genre table is empty. Please run `flask fill-db-with-genres` first")

        for visual_profile in title_vp:
            new_vp = m.VisualProfile(
                movie_id=visual_profile.movie_id,
                user_id=visual_profile.user_id,
                category_id=visual_profile.category_id,
            )

            session.add(new_vp)
            session.flush()

            log(log.DEBUG, "VisualProfileCategoryCriterion created")

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_title_vp_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill visual profile rating table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=TITLE_VP_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"
    print("values: ", values[:1])

    title_vp: list[s.VPRatingExportCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    MOVIE_ID_INDEX = values[0].index(MOVIE_ID)
    USER_ID_INDEX = values[0].index(USER_ID)
    CATEGORY_ID_INDEX = values[0].index(CATEGORY_ID)

    for row in values[1:]:
        if not row[INDEX_ID]:
            continue

        id = row[INDEX_ID]
        assert id, f"The id {id} is missing"

        movie_id = row[MOVIE_ID_INDEX]
        assert movie_id, f"The movie_id {movie_id} is missing"

        user_id = row[USER_ID_INDEX]
        assert user_id, f"The user_id {user_id} is missing"

        category_id = row[CATEGORY_ID_INDEX]
        assert category_id, f"The criterion_id {category_id} is missing"

        title_vp.append(
            s.VPRatingExportCreate(
                movie_id=int(movie_id),
                category_id=int(category_id),
                user_id=int(user_id),
            )
        )

    print("VP Ratings COUNT: ", len(title_vp))

    with open("data/visual_profiles.json", "w") as file:
        json.dump(s.VPRatingJSONFile(ratings=title_vp).model_dump(mode="json"), file, indent=4)
        print("Title visual profile ratings data saved to [data/visual_profiles.json] file")

    write_title_vp_in_db(title_vp)


def export_title_vp_from_json_file(max_limit: int | None = None):
    """Fill title visual profile with data from json file"""

    with open("data/visual_profiles.json", "r") as file:
        file_data = s.VPRatingJSONFile.model_validate(json.load(file))

    title_vp = file_data.ratings
    if max_limit:
        title_vp = title_vp[:max_limit]
    write_title_vp_in_db(title_vp)
