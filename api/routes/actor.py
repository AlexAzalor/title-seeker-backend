from fastapi import APIRouter, HTTPException, Depends, status
import app.models as m
import sqlalchemy as sa

import app.schema as s
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db

actor_router = APIRouter(prefix="/actors", tags=["Actors"])


@actor_router.get("/", status_code=status.HTTP_200_OK, response_model=s.ActorListOut)
async def get_actors(
    lang: s.Language = s.Language.UK,
    db: Session = Depends(get_db),
):
    """Get all actors"""

    actors = db.scalars(sa.select(m.Actor)).all()
    if not actors:
        log(log.ERROR, "Actors [%s] not found")
        raise HTTPException(status_code=404, detail="Actors not found")

    actors_out = []

    for actor in actors:
        actors_out.append(
            s.ActorOut(
                key=actor.key,
                full_name=actor.full_name(lang),
            )
        )
    return s.ActorListOut(actors=actors_out)
