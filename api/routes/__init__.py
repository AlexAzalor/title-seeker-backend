from fastapi import APIRouter, Request

from .auth import auth_router
from .movie import movie_router
from .file import file_router
from .genre import genre_router
from .people import people_router
from .user import user_router
from .filters import filter_router
from .shared_universe import shared_universe_router

router = APIRouter(prefix="/api", tags=["API"])

router.include_router(movie_router)
router.include_router(auth_router)
router.include_router(genre_router)
router.include_router(people_router)
router.include_router(filter_router)
router.include_router(shared_universe_router)
router.include_router(user_router)
router.include_router(file_router)


@router.get("/list-endpoints/")
def list_endpoints(request: Request):
    url_list = [{"path": route.path, "name": route.name} for route in request.app.routes]
    return url_list
