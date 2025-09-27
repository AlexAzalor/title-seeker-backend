import sqlalchemy as sa

from typing import Sequence
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.knowledge_base.category.orm import KnowledgeBaseCategory
from app.models.knowledge_base.technology.orm import KnowledgeBaseTechnology
import app.models as m


# order questions by empty answer first, then by score ascending
def find_by_category(session: Session, category_key: str) -> Sequence[KnowledgeBaseTechnology]:
    category = session.scalar(sa.select(KnowledgeBaseCategory).where(KnowledgeBaseCategory.key == category_key))
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    statement = select(KnowledgeBaseTechnology).where(KnowledgeBaseTechnology.category_id == category.id)
    result = session.scalars(statement).all()
    return result


def get_technology_questions(session: Session, tech_key: str) -> list[m.KnowledgeBaseQuestionAnswer]:
    technology = session.scalar(
        sa.select(KnowledgeBaseTechnology)
        .where(KnowledgeBaseTechnology.key == tech_key)
        .order_by(KnowledgeBaseTechnology.id)
    )
    if not technology:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technology not found")

    # statement = select(KnowledgeBaseTechnology).where(KnowledgeBaseTechnology.id == technology.id)
    # result = session.scalars(statement).all()
    return technology.questions_answers[::-1]


def get_random_questions_by_technology(
    session: Session, tech_key: str, limit: int = 10
) -> Sequence[m.KnowledgeBaseQuestionAnswer]:
    technology = session.scalar(sa.select(KnowledgeBaseTechnology).where(KnowledgeBaseTechnology.key == tech_key))
    if not technology:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technology not found")

    # exclude current question-answer
    statement = (
        select(m.KnowledgeBaseQuestionAnswer)
        .where(m.KnowledgeBaseQuestionAnswer.technology_id == technology.id, m.KnowledgeBaseQuestionAnswer.score <= 3)
        .order_by(sa.func.random())
        .limit(limit)
    )
    result = session.scalars(statement).all()
    return result
