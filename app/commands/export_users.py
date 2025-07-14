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
FIRST_NAME = "first_name"
LAST_NAME = "last_name"
ROLE = "role"
EMAIL = "email"


def write_users_in_db(users: list[s.UserExportCreate]):
    with db.begin() as session:
        for user in users:
            if session.scalar(sa.select(m.User).where(m.User.id == user.id)):
                log(log.DEBUG, "User [%s] already exists", user.id)
                continue

            new_user = m.User(
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role.value,
                email=user.email,
            )

            session.add(new_user)
            session.flush()

            log(log.DEBUG, "User [%s] created", new_user.full_name)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_users_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill users table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # Last column need to be filled!
    LAST_SHEET_COLUMN = "E"
    RANGE_NAME = f"Users!A1:{LAST_SHEET_COLUMN}"

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    users: list[s.UserExportCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    INDEX_FIRST_NAME = values[0].index(FIRST_NAME)
    INDEX_LAST_NAME = values[0].index(LAST_NAME)
    INDEX_ROLE = values[0].index(ROLE)
    INDEX_EMAIL = values[0].index(EMAIL)

    for row in values[1:]:
        if not row[INDEX_ID]:
            continue

        id = int(row[INDEX_ID])
        assert id, f"The id {id} is missing"

        first_name = row[INDEX_FIRST_NAME]
        assert first_name, f"The first_name {first_name} is missing"

        last_name = row[INDEX_LAST_NAME]
        assert last_name, f"The last_name {last_name} is missing"

        role = row[INDEX_ROLE]
        assert role, f"The role {role} is missing"

        email = row[INDEX_EMAIL]
        assert email, f"The email {email} is missing"

        users.append(
            s.UserExportCreate(
                id=id,
                first_name=first_name,
                last_name=last_name,
                role=role,
                email=email,
            )
        )

    print("Users COUNT: ", len(users))

    with open("data/users.json", "w") as file:
        json.dump(s.UsersJSONFile(users=users).model_dump(mode="json"), file, indent=4)
        print("Users data saved to [data/users.json] file")

    write_users_in_db(users)


def export_users_from_json_file(max_users_limit: int | None = None):
    """Fill users with data from json file"""

    with open("data/users.json", "r") as file:
        file_data = s.UsersJSONFile.model_validate(json.load(file))

    users = file_data.users
    if max_users_limit:
        users = users[:max_users_limit]
    write_users_in_db(users)
