import json
from googleapiclient.discovery import build

from app import schema as s
from app.logger import log
from config import config
from ..export_rating import RATING_RANGE_NAME

from ..utility import authorized_user_in_google_spreadsheets

CFG = config()

# [['ID', 'movie_id', 'user_id', 'acting', 'plot_storyline', 'music', 're_watchability', 'emotional_impact', 'dialogue', 'production_design', 'duration', 'visual_effects', 'scare_factor', 'rating', 'comment', 'ID-2']]


def import_ratings_to_google_spreadsheets():
    """Import ratings to google spreadsheets"""

    with open("data/ratings.json", "r") as file:
        file_data = s.RatingsJSONFile.model_validate(json.load(file))

    ratings = file_data.ratings

    assert ratings, "Ratings are empty!"
    print("Ratings COUNT: ", len(ratings))

    values = []

    for rating in ratings:
        rating_row = [
            rating.id,
            rating.movie_id,
            rating.user_id,
            rating.acting,
            rating.plot_storyline,
            rating.music,
            rating.re_watchability,
            rating.emotional_impact,
            rating.dialogue,
            rating.production_design,
            rating.duration,
            rating.visual_effects if rating.visual_effects else "",
            rating.scare_factor if rating.scare_factor else "",
            rating.rating,
            rating.comment if rating.comment else "",
            rating.id,
        ]
        assert rating_row, "rating_row are empty!"

        values.append(rating_row)

    print("VALUES COUNT: ", len(values[0]))

    try:
        credentials = authorized_user_in_google_spreadsheets()

        resource = build("sheets", "v4", credentials=credentials)
        sheets = resource.spreadsheets()

        body = {"values": values}

        sheets.values().append(
            spreadsheetId=CFG.SPREADSHEET_ID, range=RATING_RANGE_NAME, valueInputOption="RAW", body=body
        ).execute()
    except Exception as e:
        log(log.ERROR, "Error occurred while appending data to google spreadsheets - [%s]", e)
        log(log.INFO, "===== Perhaps you need update [VALUES] data =====")
        raise e
