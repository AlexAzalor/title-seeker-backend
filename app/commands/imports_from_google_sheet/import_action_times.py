import json
from googleapiclient.discovery import build

from app import schema as s

from app.logger import log
from config import config
from ..export_action_times import ACT_TIME_RANGE_NAME

from ..utility import authorized_user_in_google_spreadsheets

CFG = config()


def import_action_times_to_google_spreadsheets():
    """Import action_times to google spreadsheets"""

    with open("data/action_times.json", "r") as file:
        file_data = s.ActionTimesJSONFile.model_validate(json.load(file))

    action_times = file_data.action_times
    assert action_times, "action_times are empty!"
    print("Action Times COUNT: ", len(action_times))

    action_time = action_times[-1]
    print("Current action_times: ", action_time.key)

    values = [
        [
            action_time.id,
            action_time.key,
            action_time.name_uk,
            action_time.name_en,
            action_time.description_uk,
            action_time.description_en,
            action_time.id,
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
            spreadsheetId=CFG.SPREADSHEET_ID, range=ACT_TIME_RANGE_NAME, valueInputOption="RAW", body=body
        ).execute()
    except Exception as e:
        log(log.ERROR, "Error occurred while appending data to google spreadsheets - [%s]", e)
        log(log.INFO, "===== Perhaps you need update [VALUES] data =====")
        raise e
