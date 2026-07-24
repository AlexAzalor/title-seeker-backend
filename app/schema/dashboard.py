from typing import Annotated

from pydantic import BaseModel
from pydantic.json_schema import WithJsonSchema
from config import config

CFG = config()


class DashboardStatsOut(BaseModel):
    total_movies: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
    total_standalone_movies: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
    total_collections_movies: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
    total_actors: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
    total_directors: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
    total_characters: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
    total_genres: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
    total_subgenres: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
    total_specifications: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
    total_keywords: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
    total_action_times: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
    total_shared_universes: Annotated[int | None, WithJsonSchema({"type": "integer"})] = None
