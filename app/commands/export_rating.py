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
ACTING = "acting"
PLOT_STORYLINE = "plot_storyline"
MUSIC = "music"
RE_WATCHABILITY = "re_watchability"
EMOTIONAL_IMPACT = "emotional_impact"
DIALOGUE = "dialogue"
PRODUCTION_DESIGN = "production_design"
DURATION = "duration"
VISUAL_EFFECTS = "visual_effects"
SCARE_FACTOR = "scare_factor"
RATING = "rating"
COMMENT = "comment"

# Last column need to be filled!
LAST_SHEET_COLUMN = "P"
RATING_RANGE_NAME = f"Rating!A1:{LAST_SHEET_COLUMN}"


def write_ratings_in_db(ratings: list[s.RatingExportCreate]):
    with db.begin() as session:
        for rating in ratings:
            if session.scalar(
                sa.select(m.Rating).where(m.Rating.user_id == rating.user_id, m.Rating.movie_id == rating.movie_id)
            ):
                log(log.DEBUG, "Rating [%s] already exists", rating.id)
                # Update rating
                session.execute(
                    sa.update(m.Rating)
                    .where(m.Rating.user_id == rating.user_id, m.Rating.movie_id == rating.movie_id)
                    .values(
                        rating=rating.rating,
                        acting=rating.acting,
                        plot_storyline=rating.plot_storyline,
                        music=rating.music,
                        re_watchability=rating.re_watchability,
                        emotional_impact=rating.emotional_impact,
                        dialogue=rating.dialogue,
                        production_design=rating.production_design,
                        duration=rating.duration,
                        visual_effects=rating.visual_effects,
                        scare_factor=rating.scare_factor,
                        comment=rating.comment if rating.comment else "",
                    )
                )
                session.flush()
                continue

            new_rating = m.Rating(
                # id=rating.id,
                movie_id=rating.movie_id,
                user_id=rating.user_id,
                rating=rating.rating,
                acting=rating.acting,
                plot_storyline=rating.plot_storyline,
                music=rating.music,
                re_watchability=rating.re_watchability,
                emotional_impact=rating.emotional_impact,
                dialogue=rating.dialogue,
                production_design=rating.production_design,
                duration=rating.duration,
                visual_effects=rating.visual_effects,
                scare_factor=rating.scare_factor,
                comment=rating.comment,
            )

            session.add(new_rating)
            session.flush()

            log(log.DEBUG, "Rating [%s] created", rating.id)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_ratings_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill ratings table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=RATING_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    ratings: list[s.RatingExportCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    INDEX_MOVIE_ID = values[0].index(MOVIE_ID)
    INDEX_USER_ID = values[0].index(USER_ID)
    INDEX_ACTING = values[0].index(ACTING)
    INDEX_PLOT_STORYLINE = values[0].index(PLOT_STORYLINE)
    INDEX_MUSIC = values[0].index(MUSIC)
    INDEX_RE_WATCHABILITY = values[0].index(RE_WATCHABILITY)
    INDEX_EMOTIONAL_IMPACT = values[0].index(EMOTIONAL_IMPACT)
    INDEX_DIALOGUE = values[0].index(DIALOGUE)
    INDEX_PRODUCTION_DESIGN = values[0].index(PRODUCTION_DESIGN)
    INDEX_DURATION = values[0].index(DURATION)
    INDEX_VISUAL_EFFECTS = values[0].index(VISUAL_EFFECTS)
    INDEX_SCARE_FACTOR = values[0].index(SCARE_FACTOR)
    INDEX_RATING = values[0].index(RATING)
    INDEX_COMMENT = values[0].index(COMMENT)

    print("values: ", values[:1])
    for row in values[1:]:
        if not row[INDEX_ID]:
            continue

        id = int(row[INDEX_ID])
        assert id, f"The id {id} is missing"

        movie_id = row[INDEX_MOVIE_ID]
        assert movie_id, f"The movie_id {movie_id} is missing"

        user_id = row[INDEX_USER_ID]
        assert user_id, f"The user_id {user_id} is missing"

        acting = row[INDEX_ACTING]
        assert acting, f"The acting {acting} is missing"
        acting = float(acting.replace(",", "."))

        # print('acting', acting, type(acting), float(acting.replace(",", ".")))

        plot_storyline = row[INDEX_PLOT_STORYLINE]
        assert plot_storyline, f"The plot_storyline {plot_storyline} is missing"
        plot_storyline = float(plot_storyline.replace(",", "."))

        music = row[INDEX_MUSIC]
        assert music, f"The music {music} is missing"
        music = float(music.replace(",", "."))

        re_watchability = row[INDEX_RE_WATCHABILITY]
        assert re_watchability, f"The re_watchability {re_watchability} is missing"
        re_watchability = float(re_watchability.replace(",", "."))

        emotional_impact = row[INDEX_EMOTIONAL_IMPACT]
        assert emotional_impact, f"The emotional_impact {emotional_impact} is missing"
        emotional_impact = float(emotional_impact.replace(",", "."))

        dialogue = row[INDEX_DIALOGUE]
        assert dialogue, f"The dialogue {dialogue} is missing"
        dialogue = float(dialogue.replace(",", "."))

        production_design = row[INDEX_PRODUCTION_DESIGN]
        assert production_design, f"The production_design {production_design} is missing"
        production_design = float(production_design.replace(",", "."))

        duration = row[INDEX_DURATION]
        assert duration, f"The duration {duration} is missing"
        duration = float(duration.replace(",", "."))

        visual_effects = row[INDEX_VISUAL_EFFECTS]
        if visual_effects:
            visual_effects = float(visual_effects.replace(",", "."))

        scare_factor = row[INDEX_SCARE_FACTOR]
        if scare_factor:
            scare_factor = float(scare_factor.replace(",", "."))

        rating = row[INDEX_RATING]
        assert rating, f"The rating {rating} is missing"
        rating = float(rating.replace(",", "."))

        comment = row[INDEX_COMMENT]

        ratings.append(
            s.RatingExportCreate(
                id=id,
                rating=rating,
                movie_id=movie_id,
                user_id=user_id,
                acting=acting,
                plot_storyline=plot_storyline,
                music=music,
                re_watchability=re_watchability,
                emotional_impact=emotional_impact,
                dialogue=dialogue,
                production_design=production_design,
                duration=duration,
                visual_effects=visual_effects if visual_effects else None,
                scare_factor=scare_factor if scare_factor else None,
                comment=comment if comment else None,
            )
        )

    print("Users COUNT: ", len(ratings))

    with open("data/ratings.json", "w") as file:
        json.dump(s.RatingsJSONFile(ratings=ratings).model_dump(mode="json"), file, indent=4)
        print("Ratings data saved to [data/ratings.json] file")

    write_ratings_in_db(ratings)


def export_ratings_from_json_file(max_ratings_limit: int | None = None):
    """Fill ratings with data from json file"""

    with open("data/ratings.json", "r") as file:
        file_data = s.RatingsJSONFile.model_validate(json.load(file))

    ratings = file_data.ratings
    if max_ratings_limit:
        ratings = ratings[:max_ratings_limit]
    write_ratings_in_db(ratings)
