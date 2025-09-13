from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi_pagination import add_pagination

from config import config

from .utils import custom_generate_unique_id
from .routes import router
from .routes.graphql_routes import graphql_app

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


# Include GraphQL router
app.include_router(graphql_app, prefix="/graphql", tags=["GraphQL"])
app.include_router(router)
add_pagination(app)

origins = [
    "http://localhost:3000",  # Your React app's URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(graphql_app, prefix="/graphql")


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
