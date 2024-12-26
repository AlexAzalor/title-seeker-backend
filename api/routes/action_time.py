import json
from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, Depends, status

import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

action_time_router = APIRouter(prefix="/action-times", tags=["Action Times"])


@action_time_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.ActionTimeOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Action Time already exists"},
        status.HTTP_201_CREATED: {"description": "Action Time successfully created"},
    },
)
def create_action_time(
    key: Annotated[str, Form()],
    name_uk: Annotated[str, Form()],
    name_en: Annotated[str, Form()],
    description_uk: Annotated[str | None, Form()] = None,
    description_en: Annotated[str | None, Form()] = None,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new action time"""

    action_time = db.scalar(sa.select(m.ActionTime).where(m.ActionTime.key == key))

    if action_time:
        log(log.ERROR, "ActionTime [%s] already exists")
        raise HTTPException(status_code=400, detail="ActionTime already exists")

    try:
        new_action_time = m.ActionTime(
            key=key,
            translations=[
                m.ActionTimeTranslation(
                    language=s.Language.UK.value,
                    name=name_uk,
                    description=description_uk,
                ),
                m.ActionTimeTranslation(
                    language=s.Language.EN.value,
                    name=name_en,
                    description=description_en,
                ),
            ],
        )

        db.add(new_action_time)
        db.commit()
        log(log.INFO, "ActionTime [%s] successfully created", key)
    except Exception as e:
        log(log.ERROR, "Error creating action time [%s]: %s", key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating action time")

    db.refresh(new_action_time)

    try:
        action_times = db.scalars(sa.select(m.ActionTime)).all()

        action_times_to_file = []

        for action_time in action_times:
            action_times_to_file.append(
                s.ActionTimeExportCreate(
                    id=action_time.id,
                    key=action_time.key,
                    name_uk=next((t.name for t in action_time.translations if t.language == s.Language.UK.value)),
                    name_en=next((t.name for t in action_time.translations if t.language == s.Language.EN.value)),
                    description_uk=next(
                        (t.description for t in action_time.translations if t.language == s.Language.UK.value)
                    ),
                    description_en=next(
                        (t.description for t in action_time.translations if t.language == s.Language.EN.value)
                    ),
                )
            )

        print("ActionTimes COUNT: ", len(action_times))

        with open("data/action_times.json", "w") as filejson:
            json.dump(
                s.ActionTimesJSONFile(action_times=action_times_to_file).model_dump(mode="json"),
                filejson,
                indent=4,
            )
            print("Action Times data saved to [data/action_times.json] file")
    except Exception as e:
        log(log.ERROR, "Error saving action_times data to [data/action_times.json] file: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error saving action_times data to [data/action_times.json] file",
        )

    from app.commands.imports_from_google_sheet.import_action_times import (
        import_action_times_to_google_spreadsheets,
    )

    try:
        import_action_times_to_google_spreadsheets()

        log(log.INFO, "Action Times data imported to google spreadsheets")
    except Exception as e:
        log(log.ERROR, "Error importing Action Times data to google spreadsheets: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error importing Action Times data to google spreadsheets"
        )

    return s.ActionTimeOut(
        key=action_time.key,
        name=next((t.name for t in action_time.translations if t.language == lang.value)),
        description=next((t.description for t in action_time.translations if t.language == lang.value)),
    )
