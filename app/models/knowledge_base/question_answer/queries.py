"""
This module contains the query functions for the CategoryProtocolAssignment model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base.question_answer.orm import KnowledgeBaseQuestionAnswer


async def find_by_technology(session: AsyncSession, technology_id: str) -> list[KnowledgeBaseQuestionAnswer]:
    statement = select(KnowledgeBaseQuestionAnswer).where(KnowledgeBaseQuestionAnswer.technology_id == technology_id)
    result = await session.execute(statement)
    return list(result.scalars().all())
