from sqlalchemy.orm import Session
import sqlalchemy as sa
import app.models as m
from fastapi import HTTPException, status


def get_answer(session: Session, id: int) -> m.KnowledgeBaseQuestionAnswer:
    statement = sa.select(m.KnowledgeBaseQuestionAnswer).where(m.KnowledgeBaseQuestionAnswer.id == id)
    result = session.scalar(statement)

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Q&A not found")

    return result
