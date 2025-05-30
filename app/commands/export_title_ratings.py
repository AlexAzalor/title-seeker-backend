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
TITLE_VISUAL_PROFILE_ID = "title_visual_profile_id"
CRITERION_ID = "criterion_id"
RATING = "rating"
ORDER = "order"

# Last column need to be filled!
LAST_SHEET_COLUMN = "F"
TITLE_RATING_RANGE_NAME = f"Title Criterion Rating!A1:{LAST_SHEET_COLUMN}"


def write_title_ratings_in_db(visual_profile_ratings: list[s.VPCriterionRatingExportCreate]):
    with db.begin() as session:
        if not session.scalar(sa.select(m.VisualProfile)):
            log(log.ERROR, "VisualProfile table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-genres` first")
            raise Exception("VisualProfile table is empty. Please run `flask fill-***` first")

        movies = session.scalars(sa.select(m.Movie)).all()

        for movie in movies:
            if not movie.visual_profiles:
                print(f"Movie {movie.key} has no visual profiles")
                continue

            for rating in visual_profile_ratings:
                new_rating = m.VisualProfileRating(
                    title_visual_profile_id=movie.visual_profiles[0].id,
                    criterion_id=rating.criterion_id,
                    rating=rating.rating,
                    order=rating.order,
                )

                session.add(new_rating)
                session.flush()

                log(log.DEBUG, "VisualProfileCategoryCriterion created")

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_title_ratings_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill title rating table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=TITLE_RATING_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"
    print("values: ", values[:1])

    visual_profile_ratings: list[s.VPCriterionRatingExportCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    TITLE_VISUAL_PROFILE_ID_INDEX = values[0].index(TITLE_VISUAL_PROFILE_ID)
    CRITERION_ID_INDEX = values[0].index(CRITERION_ID)
    RATING_INDEX = values[0].index(RATING)
    ORDER_INDEX = values[0].index(ORDER)

    for row in values[1:]:
        if not row[INDEX_ID]:
            continue

        id = row[INDEX_ID]
        assert id, f"The id {id} is missing"

        title_visual_profile_id = row[TITLE_VISUAL_PROFILE_ID_INDEX]
        assert title_visual_profile_id, f"The title_visual_profile_id {title_visual_profile_id} is missing"
        criterion_id = row[CRITERION_ID_INDEX]
        assert criterion_id, f"The criterion_id {criterion_id} is missing"
        rating = row[RATING_INDEX]
        assert rating, f"The rating {rating} is missing"

        order = row[ORDER_INDEX]
        assert order, f"The order {order} is missing"

        visual_profile_ratings.append(
            s.VPCriterionRatingExportCreate(
                title_visual_profile_id=title_visual_profile_id,
                criterion_id=criterion_id,
                rating=rating,
                order=order,
            )
        )

    print("Title Ratings COUNT: ", len(visual_profile_ratings))

    with open("data/visual_profile_ratings.json", "w") as file:
        json.dump(s.VPCriterionRatingJSONFile(ratings=visual_profile_ratings).model_dump(mode="json"), file, indent=4)
        print("Title title ratings data saved to [data/visual_profile_ratings.json] file")

    write_title_ratings_in_db(visual_profile_ratings)


def export_title_criterion_ratings_from_json_file(max_limit: int | None = None):
    """Fill title criterion ratings with data from json file"""

    with open("data/visual_profile_ratings.json", "r") as file:
        file_data = s.VPCriterionRatingJSONFile.model_validate(json.load(file))

    visual_profile_ratings = file_data.ratings
    if max_limit:
        visual_profile_ratings = visual_profile_ratings[:max_limit]
    write_title_ratings_in_db(visual_profile_ratings)
