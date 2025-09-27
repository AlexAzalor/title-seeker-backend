from sqlalchemy.orm import Session
import sqlalchemy as sa
import app.models as m
import app.schema as s
from fastapi import HTTPException, status


def create(session: Session, form_data: s.KBQuestionIn):
    """Create a new knowledge base Q&A"""

    technology = session.scalar(
        sa.select(m.KnowledgeBaseTechnology).where(m.KnowledgeBaseTechnology.key == form_data.technology_key)
    )
    if not technology:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technology not found")

    new_qa = m.KnowledgeBaseQuestionAnswer(
        technology_id=technology.id,
        question=form_data.question,
    )
    session.add(new_qa)
    session.commit()


def update(session: Session, form_data: s.KBQuestionAnswerPutIn):
    """Update a knowledge base Q&A"""

    question_answer = session.scalar(
        sa.select(m.KnowledgeBaseQuestionAnswer).where(m.KnowledgeBaseQuestionAnswer.id == form_data.id)
    )
    if not question_answer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Q&A not found")

    question_answer.answer = form_data.answer
    question_answer.short_answer = form_data.short_answer
    question_answer.question = form_data.question
    question_answer.score = form_data.score

    session.commit()
