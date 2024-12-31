import json
from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, Depends, status

import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

specification_router = APIRouter(prefix="/specifications", tags=["Specifications"])


@specification_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.SpecificationOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Specification already exists"},
        status.HTTP_201_CREATED: {"description": "Specification successfully created"},
    },
)
def create_specification(
    key: Annotated[str, Form()],
    name_uk: Annotated[str, Form()],
    name_en: Annotated[str, Form()],
    description_uk: Annotated[str | None, Form()] = None,
    description_en: Annotated[str | None, Form()] = None,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new specification"""

    specification = db.scalar(sa.select(m.Specification).where(m.Specification.key == key))

    if specification:
        log(log.ERROR, "Specification [%s] already exists")
        raise HTTPException(status_code=400, detail="Specification already exists")

    try:
        new_specification = m.Specification(
            key=key,
            translations=[
                m.SpecificationTranslation(
                    language=s.Language.UK.value,
                    name=name_uk,
                    description=description_uk,
                ),
                m.SpecificationTranslation(
                    language=s.Language.EN.value,
                    name=name_en,
                    description=description_en,
                ),
            ],
        )

        db.add(new_specification)
        db.commit()
        log(log.INFO, "Specification [%s] successfully created", key)
    except Exception as e:
        log(log.ERROR, "Error creating specification [%s]: %s", key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating specification")

    db.refresh(new_specification)

    try:
        specifications = db.scalars(sa.select(m.Specification)).all()

        specifications_to_file = []

        for specification in specifications:
            specifications_to_file.append(
                s.SpecificationExportCreate(
                    id=specification.id,
                    key=specification.key,
                    name_uk=next((t.name for t in specification.translations if t.language == s.Language.UK.value)),
                    name_en=next((t.name for t in specification.translations if t.language == s.Language.EN.value)),
                    description_uk=next(
                        (t.description for t in specification.translations if t.language == s.Language.UK.value)
                    ),
                    description_en=next(
                        (t.description for t in specification.translations if t.language == s.Language.EN.value)
                    ),
                )
            )

        print("Specifications COUNT: ", len(specifications))

        with open("data/specifications.json", "w") as filejson:
            json.dump(
                s.SpecificationsJSONFile(specifications=specifications_to_file).model_dump(mode="json"),
                filejson,
                indent=4,
            )
            print("Specifications data saved to [data/specifications.json] file")
    except Exception as e:
        log(log.ERROR, "Error saving specifications data to [data/specifications.json] file: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error saving specifications data to [data/specifications.json] file",
        )

    from app.commands.imports_from_google_sheet.import_specifications import (
        import_specifications_to_google_spreadsheets,
    )

    try:
        import_specifications_to_google_spreadsheets()

        log(log.INFO, "Specifications data imported to google spreadsheets")
    except Exception as e:
        log(log.ERROR, "Error importing specifications data to google spreadsheets: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error importing specifications data to google spreadsheets"
        )

    return s.SpecificationOut(
        key=specification.key,
        name=next((t.name for t in specification.translations if t.language == lang.value)),
        description=next((t.description for t in specification.translations if t.language == lang.value)),
    )
