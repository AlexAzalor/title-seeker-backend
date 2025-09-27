from fastapi import APIRouter, Depends, status

from api.controllers.knowledge_base import get_technologies_dto

from api.dependency.user import get_owner
import app.schema as s
import app.models as m
from sqlalchemy.orm import Session
from app.database import get_db
from config import config

from app.models.knowledge_base.category import queries, commands
from app.models.knowledge_base.technology import queries as tech_queries, commands as tech_commands
from app.models.knowledge_base.question_answer import commands as qa_commands, queries as qa_queries

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
def get_kb_technologies(
    category_key: str,
    db: Session = Depends(get_db),
):
    """Get technologies by category"""

    technologies = tech_queries.find_by_category(db, category_key)

    return get_technologies_dto(technologies)


@knowledge_base_router.get(
    "/questions/{technology_key}",
    status_code=status.HTTP_200_OK,
    response_model=s.KBQuestionsListOut,
    responses={
        status.HTTP_200_OK: {"description": "Technologies successfully retrieved"},
        status.HTTP_404_NOT_FOUND: {"description": "No technologies found"},
    },
)
def get_kb_technology_questions(
    technology_key: str,
    db: Session = Depends(get_db),
):
    """Get technology questions list with short answers"""

    tech_questions = tech_queries.get_technology_questions(db, technology_key)

    return s.KBQuestionsListOut(
        questions=[
            s.KBQuestion(
                id=question.id,
                question=question.question,
                short_answer=question.short_answer,
                score=question.score,
            )
            for question in tech_questions
        ]
    )


@knowledge_base_router.get(
    "/question-answer/{id}",
    status_code=status.HTTP_200_OK,
    response_model=s.KBQuestionAnswerOut,
    responses={
        status.HTTP_200_OK: {"description": "Technologies successfully retrieved"},
        status.HTTP_404_NOT_FOUND: {"description": "No technologies found"},
    },
)
def get_kb_question_answer(
    id: int,
    db: Session = Depends(get_db),
):
    """Get answer by id"""

    technologies = qa_queries.get_answer(db, id)

    return s.KBQuestionAnswerOut(
        id=technologies.id,
        technology_id=technologies.technology_id,
        question=technologies.question,
        score=technologies.score,
        short_answer=technologies.short_answer,
        answer=technologies.answer,
    )


@knowledge_base_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Category successfully created"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid input"},
    },
)
def create_kb_category(
    form_data: s.KBCategoryOut,
    current_user: m.User = Depends(get_owner),
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
def create_kb_technology(
    form_data: s.KBTechnologyIn,
    current_user: m.User = Depends(get_owner),
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
def create_kb_question_answer(
    form_data: s.KBQuestionIn,
    current_user: m.User = Depends(get_owner),
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
def update_kb_category(
    form_data: s.KBCategoryPutIn,
    # current_user: m.User = Depends(get_owner),
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
def update_kb_technology(
    form_data: s.KBTechnologyPutIn,
    current_user: m.User = Depends(get_owner),
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
def update_kb_question_answer(
    form_data: s.KBQuestionAnswerPutIn,
    current_user: m.User = Depends(get_owner),
    db: Session = Depends(get_db),
):
    """Update question & answer fields"""

    qa_commands.update(db, form_data)


@knowledge_base_router.get(
    "/random-questions/{technology_key}",
    status_code=status.HTTP_200_OK,
    response_model=s.KBQuestionsListOut,
    responses={
        status.HTTP_200_OK: {"description": "Random questions successfully retrieved"},
        status.HTTP_404_NOT_FOUND: {"description": "No questions found"},
    },
)
def get_kb_random_questions(
    technology_key: str,
    db: Session = Depends(get_db),
):
    """Get 10 random questions by tech key with poor score"""

    questions = tech_queries.get_random_questions_by_technology(db, technology_key)

    return s.KBQuestionsListOut(
        questions=[
            s.KBQuestion(
                id=question.id,
                question=question.question,
                short_answer=question.short_answer,  # Need?
                score=question.score,
            )
            for question in questions
        ]
    )
