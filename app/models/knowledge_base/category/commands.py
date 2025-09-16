"""
This module contains the command functions for the CategoryProtocolAssignment model.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base.category.orm import KnowledgeBaseCategory


async def create(session: AsyncSession) -> KnowledgeBaseCategory:
    """Create a new CategoryProtocolAssignmentRow, ensuring it's active."""
    new_assignment = KnowledgeBaseCategory()
    session.add(new_assignment)
    await session.flush()
    await session.refresh(new_assignment)
    return new_assignment
