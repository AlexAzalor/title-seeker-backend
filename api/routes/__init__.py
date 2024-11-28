from fastapi import APIRouter, Request

# from .auth import router as auth_router
from .movie import movie_router

router = APIRouter(prefix="/api", tags=["API"])

router.include_router(movie_router)
# router.include_router(auth_router)


@router.get("/list-endpoints/")
def list_endpoints(request: Request):
    url_list = [{"path": route.path, "name": route.name} for route in request.app.routes]
    return url_list
