from fastapi import APIRouter, Depends, status

from api.controllers.knowledge_base import get_technologies_dto

import app.schema as s
from sqlalchemy.orm import Session
from app.database import get_db
from config import config

from app.models.knowledge_base.category import queries, commands
from app.models.knowledge_base.technology import queries as tech_queries, commands as tech_commands
from app.models.knowledge_base.question_answer import commands as qa_commands

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


@knowledge_base_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Category successfully created"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input"},
    },
)
def create_category(
    form_data: s.KBCategoryOut,
    db: Session = Depends(get_db),
):
    """Get all knowledge base categories"""

    commands.create(db, form_data)


@knowledge_base_router.post(
    "/technologies",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Technology successfully created"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input"},
    },
)
def create_technology(
    form_data: s.KBTechnologyIn,
    db: Session = Depends(get_db),
):
    """Get all knowledge base categories"""

    tech_commands.create(db, form_data)


@knowledge_base_router.post(
    "/question-answer",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Q&A successfully created"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input"},
    },
)
def create_question_answer(
    form_data: s.KBQuestionAnswerIn,
    db: Session = Depends(get_db),
):
    """Get all knowledge base categories"""

    qa_commands.create(db, form_data)


@knowledge_base_router.put(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Category successfully updated"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input"},
    },
)
def update_category(
    form_data: s.KBCategoryPutIn,
    db: Session = Depends(get_db),
):
    """Get all knowledge base categories"""

    commands.update(db, form_data)


@knowledge_base_router.put(
    "/technology",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Technology successfully updated"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input"},
    },
)
def update_technology(
    form_data: s.KBTechnologyPutIn,
    db: Session = Depends(get_db),
):
    """Get all knowledge base categories"""

    tech_commands.update(db, form_data)


@knowledge_base_router.put(
    "/question-answer",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Q&A successfully updated"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input"},
    },
)
def update_question_answer(
    form_data: s.KBQuestionAnswerPutIn,
    db: Session = Depends(get_db),
):
    """Update question & answer fields"""

    qa_commands.update(db, form_data)
