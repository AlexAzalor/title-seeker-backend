import json
from datetime import datetime
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
FIRST_NAME_UK = "first_name_uk"
LAST_NAME_UK = "last_name_uk"
FIRST_NAME_EN = "first_name_en"
LAST_NAME_EN = "last_name_en"
BORN = "born"
DIED = "died"
BORN_IN_UK = "born_in_uk"
BORN_IN_EN = "born_in_en"
CHARACTER_NAME_UK = "character_name_uk"
CHARACTER_NAME_EN = "character_name_en"
MOVIES = "movies"


def write_actors_in_db(actors: list[s.ActorExportCreate]):
    with db.begin() as session:
        if not session.scalar(sa.select(m.Movie)):
            log(log.ERROR, "Movie table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-movies` first")
            raise Exception("Movie table is empty. Please run `flask fill-db-with-movies` first")

        for actor in actors:
            new_actor = m.Actor(
                born=actor.born,
                died=actor.died,
                translations=[
                    m.ActorTranslation(
                        first_name=actor.first_name_uk,
                        last_name=actor.last_name_uk,
                        born_in=actor.born_in_uk,
                        character_name=actor.character_name_uk,
                    ),
                    m.ActorTranslation(
                        first_name=actor.first_name_en,
                        last_name=actor.last_name_en,
                        born_in=actor.born_in_en,
                        character_name=actor.character_name_en,
                    ),
                ],
            )

            session.add(new_actor)
            session.flush()

            for movie_id in actor.movies:
                movie = session.scalar(sa.select(m.Movie).filter(m.Movie.id == movie_id))
                if not movie:
                    log(log.ERROR, "Movie with ID [%s] not found", movie_id)
                    raise Exception(f"Movie with ID [{movie_id}] not found")
                movie.actors.append(new_actor)

            log(log.DEBUG, "Job with title [%s] created", actor.first_name_uk)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_actors_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill actors table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()
    RANGE_NAME = "Actors!A1:L"

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    actors: list[s.ActorExportCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    FIRST_NAME_UK_INDEX = values[0].index(FIRST_NAME_UK)
    LAST_NAME_UK_INDEX = values[0].index(LAST_NAME_UK)
    FIRST_NAME_EN_INDEX = values[0].index(FIRST_NAME_EN)
    LAST_NAME_EN_INDEX = values[0].index(LAST_NAME_EN)
    BORN_INDEX = values[0].index(BORN)
    DIED_INDEX = values[0].index(DIED)
    BORN_IN_UK_INDEX = values[0].index(BORN_IN_UK)
    BORN_IN_EN_INDEX = values[0].index(BORN_IN_EN)
    CHARACTER_NAME_UK_INDEX = values[0].index(CHARACTER_NAME_UK)
    CHARACTER_NAME_EN_INDEX = values[0].index(CHARACTER_NAME_EN)
    MOVIES_INDEX = values[0].index(MOVIES)

    print("values: ", values[:1])
    for row in values[1:]:
        if not row[INDEX_ID]:
            continue

        first_name_uk = row[FIRST_NAME_UK_INDEX]
        assert first_name_uk, f"The first_name_uk {first_name_uk} is missing"
        print("=== first_name_uk ===", first_name_uk)

        last_name_uk = row[LAST_NAME_UK_INDEX]
        assert last_name_uk, f"The last_name_uk {last_name_uk} is missing"

        first_name_en = row[FIRST_NAME_EN_INDEX]
        assert first_name_en, f"The first_name_en {first_name_en} is missing"

        last_name_en = row[LAST_NAME_EN_INDEX]
        assert last_name_en, f"The last_name_en {last_name_en} is missing"

        born = row[BORN_INDEX]
        assert born, f"The born {born} is missing"

        died = row[DIED_INDEX]

        born_in_uk = row[BORN_IN_UK_INDEX]
        assert born_in_uk, f"The born_in_uk {born_in_uk} is missing"

        born_in_en = row[BORN_IN_EN_INDEX]
        assert born_in_en, f"The born_in_en {born_in_en} is missing"

        character_name_uk = row[CHARACTER_NAME_UK_INDEX]
        assert character_name_uk, f"The character_name_uk {character_name_uk} is missing"

        character_name_en = row[CHARACTER_NAME_EN_INDEX]
        assert character_name_en, f"The character_name_en {character_name_en} is missing"

        movies = row[MOVIES_INDEX]
        assert movies, f"The movies {movies} is missing"
        movies_ids = convert_string_to_list_of_integers(movies)

        print("movies: ", movies_ids)

        actors.append(
            s.ActorExportCreate(
                first_name_uk=first_name_uk,
                last_name_uk=last_name_uk,
                first_name_en=first_name_en,
                last_name_en=last_name_en,
                born=datetime.strptime(born, "%d.%m.%Y"),
                died=datetime.strptime(died, "%d.%m.%Y") if died else None,
                born_in_uk=born_in_uk,
                born_in_en=born_in_en,
                character_name_uk=character_name_uk,
                character_name_en=character_name_en,
                movies=movies_ids,
            )
        )

    print("Actors COUNT: ", len(actors))

    with open("data/actors.json", "w") as file:
        json.dump(s.ActorsJSONFile(actors=actors).model_dump(mode="json"), file, indent=4)
        print("Actors data saved to [data/actors.json] file")

    write_actors_in_db(actors)


def export_actors_from_json_file(max_actors_limit: int | None = None):
    """Fill actors with data from json file"""

    with open("data/actors.json", "r") as file:
        file_data = s.ActorsJSONFile.model_validate(json.load(file))

    actors = file_data.actors
    if max_actors_limit:
        actors = actors[:max_actors_limit]
    write_actors_in_db(actors)
