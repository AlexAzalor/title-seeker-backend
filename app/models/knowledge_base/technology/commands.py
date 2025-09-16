"""
This module contains the command functions for the CategoryProtocolAssignment model.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base.technology.orm import KnowledgeBaseTechnology


async def create(session: AsyncSession) -> KnowledgeBaseTechnology:
    new_assignment = KnowledgeBaseTechnology()
    session.add(new_assignment)
    await session.flush()
    await session.refresh(new_assignment)
    return new_assignment
