from fastapi import APIRouter, Body, HTTPException, Depends, status

import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

character_router = APIRouter(prefix="/characters", tags=["Characters"])


@character_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=s.CharacterOut,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Character already exists"},
        status.HTTP_201_CREATED: {"description": "Character successfully created"},
    },
)
def create_character(
    form_data: s.CharacterFormIn = Body(...),
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new character"""

    character = db.scalar(sa.select(m.Character).where(m.Character.key == form_data.key))

    if character:
        log(log.ERROR, "Character [%s] already exists")
        raise HTTPException(status_code=400, detail="Character already exists")

    try:
        new_character = m.Character(
            key=form_data.key,
            translations=[
                m.CharacterTranslation(
                    language=s.Language.UK.value,
                    name=form_data.name_uk,
                ),
                m.CharacterTranslation(
                    language=s.Language.EN.value,
                    name=form_data.name_en,
                ),
            ],
        )

        db.add(new_character)
        db.commit()
        log(log.INFO, "Character [%s] successfully created", form_data.key)
    except Exception as e:
        log(log.ERROR, "Error creating Character [%s]: %s", form_data.key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating character")

    db.refresh(new_character)

    return s.CharacterOut(
        key=new_character.key,
        name=new_character.get_name(lang),
    )
