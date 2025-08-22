from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi_pagination import add_pagination
import redis
from config import config

from .utils import custom_generate_unique_id
from .routes import router

CFG = config()


app = FastAPI(
    version=CFG.VERSION,
    generate_unique_id_function=custom_generate_unique_id,
    openapi_tags=[
        {
            "name": "Filters",
            "description": "Filters are the names of unique entities (created by me) by which movies are searched.",
        },
    ],
)

r = redis.Redis(host="localhost", port=6379, db=0)


app.include_router(router)
add_pagination(app)


@app.get("/", tags=["root"])
async def root():
    return RedirectResponse(url="/docs")


# TODO: add basic auth to swagger
# security = HTTPBasic()
# def swagger_auth(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
#     """Protects Swagger UI with basic auth"""
#     if credentials.username != CFG.FASTAPI_USERNAME or credentials.password != CFG.FASTAPI_PASSWORD:
#         raise HTTPException(status_code=401, detail="Unauthorized")

#     return RedirectResponse(url="/docs")
