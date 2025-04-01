from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, Depends, status

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
    key: Annotated[str, Form()],
    name_uk: Annotated[str, Form()],
    name_en: Annotated[str, Form()],
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Create new character"""

    character = db.scalar(sa.select(m.Character).where(m.Character.key == key))

    if character:
        log(log.ERROR, "Character [%s] already exists")
        raise HTTPException(status_code=400, detail="Character already exists")

    try:
        new_character = m.Character(
            key=key,
            translations=[
                m.CharacterTranslation(
                    language=s.Language.UK.value,
                    name=name_uk,
                ),
                m.CharacterTranslation(
                    language=s.Language.EN.value,
                    name=name_en,
                ),
            ],
        )

        db.add(new_character)
        db.commit()
        log(log.INFO, "Character [%s] successfully created", key)
    except Exception as e:
        log(log.ERROR, "Error creating Character [%s]: %s", key, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating character")

    db.refresh(new_character)

    return s.CharacterOut(
        key=new_character.key,
        name=new_character.get_name(lang),
    )
