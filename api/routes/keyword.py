import json
from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, Depends, status

import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

keyword_router = APIRouter(prefix="/keywords", tags=["Keywords"])


@keyword_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.KeywordOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Keyword already exists"},
        status.HTTP_201_CREATED: {"description": "Keyword successfully created"},
    },
)
def create_keyword(
    key: Annotated[str, Form()],
    name_uk: Annotated[str, Form()],
    name_en: Annotated[str, Form()],
    description_uk: Annotated[str | None, Form()] = None,
    description_en: Annotated[str | None, Form()] = None,
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new keyword"""

    keyword = db.scalar(sa.select(m.Keyword).where(m.Keyword.key == key))

    if keyword:
        log(log.ERROR, "Keyword [%s] already exists")
        raise HTTPException(status_code=400, detail="Keyword already exists")

    try:
        new_keyword = m.Keyword(
            key=key,
            translations=[
                m.KeywordTranslation(
                    language=s.Language.UK.value,
                    name=name_uk,
                    description=description_uk,
                ),
                m.KeywordTranslation(
                    language=s.Language.EN.value,
                    name=name_en,
                    description=description_en,
                ),
            ],
        )

        db.add(new_keyword)
        db.commit()
        log(log.INFO, "Keyword [%s] successfully created", key)
    except Exception as e:
        log(log.ERROR, "Error creating keyword [%s]: %s", key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating keyword")

    db.refresh(new_keyword)

    try:
        keywords = db.scalars(sa.select(m.Keyword)).all()

        keywords_to_file = []

        for keyword in keywords:
            keywords_to_file.append(
                s.KeywordExportCreate(
                    id=keyword.id,
                    key=keyword.key,
                    name_uk=next((t.name for t in keyword.translations if t.language == s.Language.UK.value)),
                    name_en=next((t.name for t in keyword.translations if t.language == s.Language.EN.value)),
                    description_uk=next(
                        (t.description for t in keyword.translations if t.language == s.Language.UK.value)
                    ),
                    description_en=next(
                        (t.description for t in keyword.translations if t.language == s.Language.EN.value)
                    ),
                )
            )

        print("Keywords COUNT: ", len(keywords))

        with open("data/keywords.json", "w") as filejson:
            json.dump(
                s.KeywordsJSONFile(keywords=keywords_to_file).model_dump(mode="json"),
                filejson,
                indent=4,
            )
            print("Keywords data saved to [data/keywords.json] file")
    except Exception as e:
        log(log.ERROR, "Error saving keywords data to [data/keywords.json] file: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error saving keywords data to [data/keywords.json] file",
        )

    from app.commands.imports_from_google_sheet.import_keywords import (
        import_keywords_to_google_spreadsheets,
    )

    try:
        import_keywords_to_google_spreadsheets()

        log(log.INFO, "Keywords data imported to google spreadsheets")
    except Exception as e:
        log(log.ERROR, "Error importing Keywords data to google spreadsheets: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error importing Keywords data to google spreadsheets"
        )

    return s.KeywordOut(
        key=keyword.key,
        name=next((t.name for t in keyword.translations if t.language == lang.value)),
        description=next((t.description for t in keyword.translations if t.language == lang.value)),
    )
