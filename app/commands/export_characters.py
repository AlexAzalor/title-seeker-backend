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
ACTORS_IDS = "actors_ids"
MOVIES_IDS = "movies_ids"

# Last column need to be filled!
LAST_SHEET_COLUMN = "G"
CHARS_RANGE_NAME = f"Characters!A1:{LAST_SHEET_COLUMN}"


def write_characters_in_db(characters: list[s.CharacterExportCreate]):
    with db.begin() as session:
        for character in characters:
            if not session.scalar(sa.select(m.Actor)):
                log(log.ERROR, "Actor table is empty")
                log(log.ERROR, "Please run `flask fill-db-with-actors` first")
                raise Exception("Actor table is empty. Please run `flask fill-db-with-actors` first")
            if not session.scalar(sa.select(m.Movie)):
                log(log.ERROR, "Movie table is empty")
                log(log.ERROR, "Please run `flask fill-db-with-movies` first")
                raise Exception("Movie table is empty. Please run `flask fill-db-with-movies` first")

            if not session.scalar(sa.select(m.Movie).where(sa.and_(m.Movie.id.in_(character.movies_ids)))):
                log(log.ERROR, "Movies with ids %s not found", character.movies_ids)
                raise Exception("Movies not found")

            if session.scalar(sa.select(m.Character).where(m.Character.key == character.key)):
                continue

            new_character = m.Character(
                key=character.key,
                translations=[
                    m.CharacterTranslation(
                        language=s.Language.UK.value,
                        name=character.name_uk,
                    ),
                    m.CharacterTranslation(
                        language=s.Language.EN.value,
                        name=character.name_en,
                    ),
                ],
            )
            session.add(new_character)
            session.flush()

            log(log.DEBUG, "Character [%s] created", new_character.key)

        # This flag for adding item when actors_ids column has 2 values
        second_movie = False
        for character in characters:
            a_ids = character.actors_ids
            m_ids = character.movies_ids

            for idx, actor_id in enumerate(character.actors_ids):
                if second_movie:
                    second_movie = False

                for movie_id in m_ids:
                    if second_movie:
                        second_movie = False
                        continue

                    character_db = session.scalar(sa.select(m.Character).where(m.Character.key == character.key))
                    if not character_db:
                        raise Exception(f"Character with key {character.key} not found")
                    new_character_relation = m.MovieActorCharacter(
                        # key=character_db.key,
                        actor_id=actor_id,
                        movie_id=movie_id,
                        character_id=character_db.id,
                        order=idx,
                    )

                    session.add(new_character_relation)
                    session.flush()

                    if len(character.actors_ids) == 2 and second_movie is False:
                        a_ids = a_ids[1:]
                        m_ids = m_ids[1:]
                        second_movie = True

                    log(log.DEBUG, "new_character_relation [%s] created", new_character_relation.id)
        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_characters_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill characters table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=CHARS_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    characters: list[s.CharacterExportCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    INDEX_KEY = values[0].index(KEY)
    INDEX_NAME_UK = values[0].index(NAME_UK)
    INDEX_NAME_EN = values[0].index(NAME_EN)
    INDEX_ACTORS_IDS = values[0].index(ACTORS_IDS)
    INDEX_MOVIES_IDS = values[0].index(MOVIES_IDS)

    for row in values[1:]:
        if not row[INDEX_ID]:
            continue

        id = int(row[INDEX_ID])
        assert id, f"The id {id} is missing"

        key = row[INDEX_KEY]
        assert key, f"The key {key} is missing"

        name_uk = row[INDEX_NAME_UK]
        assert name_uk, f"The name_uk {name_uk} is missing"

        name_en = row[INDEX_NAME_EN]
        assert name_en, f"The name_en {name_en} is missing"

        actors_ids = row[INDEX_ACTORS_IDS]
        assert actors_ids, f"The actors_ids {actors_ids} is missing"
        actors_ids = convert_string_to_list_of_integers(actors_ids)

        movies_ids = row[INDEX_MOVIES_IDS]
        assert movies_ids, f"The movies_ids {movies_ids} is missing"
        movies_ids = convert_string_to_list_of_integers(movies_ids)

        characters.append(
            s.CharacterExportCreate(
                id=id,
                key=key,
                name_uk=name_uk,
                name_en=name_en,
                actors_ids=actors_ids,
                movies_ids=movies_ids,
            )
        )

    print("Characters COUNT: ", len(characters))

    with open("data/characters.json", "w") as file:
        json.dump(s.CharactersJSONFile(characters=characters).model_dump(mode="json"), file, indent=4)
        print("Characters data saved to [data/characters.json] file")

    write_characters_in_db(characters)


def export_characters_from_json_file(max_characters_limit: int | None = None):
    """Fill characters with data from json file"""

    with open("data/characters.json", "r") as file:
        file_data = s.CharactersJSONFile.model_validate(json.load(file))

    characters = file_data.characters
    if max_characters_limit:
        characters = characters[:max_characters_limit]
    write_characters_in_db(characters)
