from fastapi import APIRouter, Request

# from .auth import router as auth_router
from .movie import movie_router
from .avatar import avatar_router
from .genre import genre_router
from .actor import actor_router
from .director import director_router
from .user import user_router
from .subgenre import subgenre_router
from .specification import specification_router
from .keyword import keyword_router
from .action_time import action_time_router
from .shared_universe import shared_universe_router

router = APIRouter(prefix="/api", tags=["API"])

router.include_router(movie_router)
# router.include_router(auth_router)
router.include_router(avatar_router)
router.include_router(genre_router)
router.include_router(actor_router)
router.include_router(director_router)
router.include_router(user_router)
router.include_router(subgenre_router)
router.include_router(specification_router)
router.include_router(keyword_router)
router.include_router(action_time_router)
router.include_router(shared_universe_router)


@router.get("/list-endpoints/")
def list_endpoints(request: Request):
    url_list = [{"path": route.path, "name": route.name} for route in request.app.routes]
    return url_list
