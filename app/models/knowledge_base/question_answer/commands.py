"""
This module contains the command functions for the CategoryProtocolAssignment model.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base.question_answer.orm import KnowledgeBaseQuestionAnswer


async def create(session: AsyncSession) -> KnowledgeBaseQuestionAnswer:
    """Create a new CategoryProtocolAssignmentRow, ensuring it's active."""
    new_assignment = KnowledgeBaseQuestionAnswer()
    session.add(new_assignment)
    await session.flush()
    await session.refresh(new_assignment)
    return new_assignment
