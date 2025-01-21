import json
from googleapiclient.discovery import build

from app import schema as s
from app.logger import log
from config import config
from ..export_rating import RATING_RANGE_NAME

from ..utility import authorized_user_in_google_spreadsheets

CFG = config()


def import_ratings_to_google_spreadsheets(rate_data: s.RatingsJSONFile | None = None):
    """Import ratings to google spreadsheets"""

    if not rate_data:
        with open("data/ratings.json", "r") as file:
            file_data = s.RatingsJSONFile.model_validate(json.load(file))
    else:
        file_data = rate_data

    ratings = file_data.ratings

    assert ratings, "Ratings are empty!"
    print("Ratings COUNT: ", len(ratings))

    rating = ratings[-1]

    values = [
        [
            rating.id,
            rating.movie_id,
            rating.user_id,
            rating.acting,
            rating.plot_storyline,
            rating.script_dialogue,
            rating.music,
            rating.enjoyment,
            rating.production_design,
            rating.visual_effects if rating.visual_effects else "",
            rating.scare_factor if rating.scare_factor else "",
            rating.humor if rating.humor else "",
            rating.animation_cartoon if rating.animation_cartoon else "",
            rating.rating,
            rating.comment if rating.comment else "",
            rating.id,
        ]
    ]
    assert values[0], "Values are empty!"
    print("values: ", values)

    try:
        credentials = authorized_user_in_google_spreadsheets()

        resource = build("sheets", "v4", credentials=credentials)
        sheets = resource.spreadsheets()

        body = {"values": values}

        sheets.values().append(
            spreadsheetId=CFG.SPREADSHEET_ID, range=RATING_RANGE_NAME, valueInputOption="RAW", body=body
        ).execute()

        log(log.INFO, "Ratings data imported to google spreadsheets")
    except Exception as e:
        log(
            log.ERROR,
            "Error occurred while appending data to google spreadsheets - [%s]",
            e,
        )
        log(log.INFO, "===== Perhaps you need update [VALUES] fields =====")
        message = "Error importing [RATINGS] data to Google spreadsheets"
        e.args = (*e.args, message)
        raise e
