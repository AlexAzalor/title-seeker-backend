from fastapi import APIRouter, HTTPException, Depends, status

from api.dependency.user import get_admin
import app.models as m

import app.schema as s
import sqlalchemy as sa
from app.logger import log
from sqlalchemy.orm import Session
from app.database import get_db
from config import config

CFG = config()

dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@dashboard_router.get("/stats", response_model=s.DashboardStatsOut)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    user: m.User = Depends(get_admin),
):
    """Get dashboard stats"""
    try:
        total_movies = db.query(m.Movie).count()
        total_standalone_movies = db.scalars(
            sa.select(sa.func.count()).select_from(m.Movie).where(m.Movie.relation_type.is_(None))
        ).first()
        total_collections_movies = db.query(m.Movie).filter(m.Movie.relation_type == "base").count()

        total_actors = db.query(m.Actor).count()
        total_directors = db.query(m.Director).count()
        total_characters = db.query(m.Character).count()
        total_genres = db.query(m.Genre).count()
        total_subgenres = db.query(m.Subgenre).count()
        total_specifications = db.query(m.Specification).count()
        total_keywords = db.query(m.Keyword).count()
        total_action_times = db.query(m.ActionTime).count()
        total_shared_universes = db.query(m.SharedUniverse).count()

        return s.DashboardStatsOut(
            total_movies=total_movies,
            total_standalone_movies=total_standalone_movies,
            total_collections_movies=total_collections_movies,
            total_actors=total_actors,
            total_directors=total_directors,
            total_characters=total_characters,
            total_genres=total_genres,
            total_subgenres=total_subgenres,
            total_specifications=total_specifications,
            total_keywords=total_keywords,
            total_action_times=total_action_times,
            total_shared_universes=total_shared_universes,
        )
    except Exception as e:
        log(log.ERROR, f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting dashboard stats")
