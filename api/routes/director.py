from datetime import datetime
import json
import os
from typing import Annotated
from fastapi import APIRouter, File, Form, HTTPException, Depends, UploadFile, status
from api.routes.avatar import UPLOAD_DIRECTORY
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

director_router = APIRouter(prefix="/directorrs", tags=["Directors"])


@director_router.get("/", status_code=status.HTTP_200_OK, response_model=s.DirectorListOut)
def get_directors(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all directors"""

    directors = db.scalars(sa.select(m.Director)).all()
    if not directors:
        log(log.ERROR, "Director [%s] not found")
        raise HTTPException(status_code=404, detail="Director not found")

    directors_out = []

    for director in directors:
        directors_out.append(
            s.DirectorOut(
                key=director.key,
                name=director.full_name(lang),
            )
        )
    return s.DirectorListOut(directors=directors_out)


@director_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.DirectorOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Director already exists"},
        status.HTTP_201_CREATED: {"description": "Director successfully created"},
    },
)
def create_director(
    key: Annotated[str, Form()],
    first_name_uk: Annotated[str, Form()],
    last_name_uk: Annotated[str, Form()],
    first_name_en: Annotated[str, Form()],
    last_name_en: Annotated[str, Form()],
    born: Annotated[str, Form()],
    born_in_uk: Annotated[str, Form()],
    born_in_en: Annotated[str, Form()],
    died: Annotated[str | None, Form()] = None,
    file: UploadFile = File(None),
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new director"""

    director = db.scalar(sa.select(m.Director).where(m.Director.key == key))

    if director:
        log(log.ERROR, "Director [%s] already exists")
        raise HTTPException(status_code=400, detail="Director already exists")

    try:
        new_director = m.Director(
            key=key,
            born=datetime.strptime(born, "%d.%m.%Y"),
            died=datetime.strptime(died, "%d.%m.%Y") if died else None,
            translations=[
                m.DirectorTranslation(
                    language=s.Language.UK.value,
                    first_name=first_name_uk,
                    last_name=last_name_uk,
                    born_in=born_in_uk,
                ),
                m.DirectorTranslation(
                    language=s.Language.EN.value,
                    first_name=first_name_en,
                    last_name=last_name_en,
                    born_in=born_in_en,
                ),
            ],
        )

        db.add(new_director)
        db.commit()
        log(log.INFO, "Director [%s] successfully created", key)
    except Exception as e:
        log(log.ERROR, "Error creating director [%s]: %s", key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating director")

    db.refresh(new_director)

    try:
        directory_path = UPLOAD_DIRECTORY + "directors/"

        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        file_name = f"{new_director.id}_{file.filename}"
        file_location = f"{directory_path}{file_name}"

        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())

        new_director.avatar = file_name
        db.commit()

        log(log.INFO, "Avatar for director [%s] successfully uploaded", key)
    except Exception as e:
        log(log.ERROR, "Error uploading avatar for director [%s]: %s", key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error uploading avatar for director")

    try:
        directors = db.scalars(sa.select(m.Director)).all()

        directors_to_file = []

        for director in directors:
            directors_to_file.append(
                s.DirectorExportCreate(
                    id=director.id,
                    key=director.key,
                    first_name_uk=next(
                        (t.first_name for t in director.translations if t.language == s.Language.UK.value)
                    ),
                    last_name_uk=next(
                        (t.last_name for t in director.translations if t.language == s.Language.UK.value)
                    ),
                    first_name_en=next(
                        (t.first_name for t in director.translations if t.language == s.Language.EN.value)
                    ),
                    last_name_en=next(
                        (t.last_name for t in director.translations if t.language == s.Language.EN.value)
                    ),
                    born=director.born,
                    died=director.died if director.died else None,
                    born_in_uk=next((t.born_in for t in director.translations if t.language == s.Language.UK.value)),
                    born_in_en=next((t.born_in for t in director.translations if t.language == s.Language.EN.value)),
                    avatar=director.avatar,
                )
            )

        print("Directors COUNT: ", len(directors))

        with open("data/directors.json", "w") as filejson:
            json.dump(s.DirectorsJSONFile(directors=directors_to_file).model_dump(mode="json"), filejson, indent=4)
            print("Directors data saved to [data/directors.json] file")
    except Exception as e:
        log(log.ERROR, "Error saving directors data to [data/directors.json] file: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error saving directors data to [data/directors.json] file"
        )

    from app.commands.imports_from_google_sheet.import_directors import import_directors_to_google_spreadsheets

    try:
        import_directors_to_google_spreadsheets()

        log(log.INFO, "Directors data imported to google spreadsheets")
    except Exception as e:
        log(log.ERROR, "Error importing directors data to google spreadsheets: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error importing directors data to google spreadsheets"
        )

    return s.DirectorOut(
        key=new_director.key,
        name=new_director.full_name(lang),
    )
