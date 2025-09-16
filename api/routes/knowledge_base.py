from fastapi import APIRouter, Depends, status

from api.controllers.knowledge_base import get_technologies_dto

import app.schema as s
from sqlalchemy.orm import Session
from app.database import get_db
from config import config

from app.models.knowledge_base.category import queries
from app.models.knowledge_base.technology import queries as tech_queries

CFG = config()

knowledge_base_router = APIRouter(
    prefix="/knowledge-base",
    tags=["Knowledge Base"],
)


@knowledge_base_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=s.KBCategoryListOut,
    responses={
        status.HTTP_200_OK: {"description": "Categories successfully retrieved"},
        status.HTTP_404_NOT_FOUND: {"description": "No categories found"},
    },
)
def get_kb_categories(
    db: Session = Depends(get_db),
):
    """Get all knowledge base categories"""

    result = queries.get_categories(db)
    return s.KBCategoryListOut(
        categories=[s.KBCategoryOut(key=r.key, name=r.name, description=r.description) for r in result]
    )


@knowledge_base_router.get(
    "/technologies/{category_key}",
    status_code=status.HTTP_200_OK,
    response_model=s.KBTechnologyListOut,
    responses={
        status.HTTP_200_OK: {"description": "Technologies successfully retrieved"},
        status.HTTP_404_NOT_FOUND: {"description": "No technologies found"},
    },
)
def get_technologies(
    category_key: str,
    db: Session = Depends(get_db),
):
    """Get technologies by category"""

    technologies = tech_queries.find_by_category(db, category_key)

    return get_technologies_dto(technologies)
