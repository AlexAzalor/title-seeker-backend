import strawberry
from typing import Optional, Sequence
from datetime import datetime
from enum import Enum

from fastapi import Request

# For Strawberry with FastAPI, we need to use GraphQLRouter instead
from strawberry.fastapi import GraphQLRouter
from sqlalchemy.orm import Session
import sqlalchemy as sa
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate

from api.controllers.movie import build_movie_query, get_main_genres_for_movies
from app.database import get_db
import app.models as m
import app.schema as s


@strawberry.type
class MoviePreview:
    key: str
    title: str
    poster: Optional[str]
    release_date: datetime
    duration: str
    main_genre: str
    rating: float


@strawberry.type
class MoviePageInfo:
    total: int
    page: int
    size: int
    pages: int


@strawberry.type
class MoviesResponse:
    items: list[MoviePreview]
    total: int
    page: int
    size: int
    pages: int


@strawberry.enum
class SortBy(Enum):
    RATING = "rating"
    RATINGS_COUNT = "ratings_count"
    RATED_AT = "rated_at"
    RELEASE_DATE = "release_date"
    RANDOM = "random"
    ID = "id"


@strawberry.enum
class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


@strawberry.enum
class Language(Enum):
    UK = "uk"
    EN = "en"


# http://127.0.0.1:5002/graphql - Swagger for GraphQL
@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"

    @strawberry.field
    def hello2(self) -> str:
        return "Hello World 2"

    @strawberry.field
    def movies(
        self,
        info: strawberry.Info,
        user_uuid: Optional[str] = None,
        sort_by: SortBy = SortBy.RATED_AT,
        sort_order: SortOrder = SortOrder.DESC,
        lang: Language = Language.UK,
        page: int = 1,
        size: int = 30,
    ) -> MoviesResponse:
        """Get movies by query params - GraphQL version"""

        # Get dependencies from context
        db: Session = info.context["db"]
        current_user: Optional[m.User] = info.context.get("current_user")

        # Convert GraphQL enums to app schema enums
        app_sort_by = s.SortBy(sort_by.value)
        is_reverse = sort_order == SortOrder.DESC
        app_lang = s.Language.UK if lang == Language.UK else s.Language.EN

        # Build query using existing controller logic
        base_query = build_movie_query(app_sort_by, is_reverse, current_user)

        # Create pagination params
        params = Params(page=page, size=size)

        def transform_movies_to_preview(movies: Sequence[m.Movie]) -> Sequence[MoviePreview]:
            movie_ids = [movie.id for movie in movies]
            main_genre_map = get_main_genres_for_movies(db, movie_ids, app_lang)

            return [
                MoviePreview(
                    key=movie.key,
                    title=movie.get_title(app_lang),
                    poster=movie.poster,
                    release_date=movie.release_date if movie.release_date else datetime.now(),
                    duration=movie.formatted_duration(app_lang.value),
                    main_genre=main_genre_map.get(movie.id, "No main genre"),
                    rating=next((t.rating for t in movie.ratings if t.user_id == current_user.id), 0.0)
                    if current_user
                    else 0.0,
                )
                for movie in movies
            ]

        # Get paginated results
        page_result = paginate(db, base_query, params, transformer=transform_movies_to_preview)

        return MoviesResponse(
            items=page_result.items,
            total=page_result.total,
            page=page_result.page,
            size=page_result.size,
            pages=page_result.pages,
        )


schema = strawberry.Schema(query=Query)


async def get_context(request: Request):
    """Context function to provide dependencies to GraphQL resolvers"""
    db = next(get_db())
    current_user = None

    # Try to get current user from request headers or query params
    user_uuid = request.headers.get("user-uuid") or request.query_params.get("user_uuid")
    if user_uuid:
        try:
            # Use the same logic as get_current_user dependency
            current_user = db.scalar(sa.select(m.User).where(m.User.uuid == user_uuid))
        except Exception:
            pass  # If user not found, continue with None

    return {"db": db, "current_user": current_user, "request": request}


graphql_app = GraphQLRouter(schema, context_getter=get_context)


# d7e39b7a-2868-43a4-b148-135c9c81c1a6
