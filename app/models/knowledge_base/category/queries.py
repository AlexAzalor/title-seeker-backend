"""
This module contains the query functions for the CategoryProtocolAssignment model.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.knowledge_base.category.orm import KnowledgeBaseCategory


def get_categories(session: Session) -> list[KnowledgeBaseCategory]:
    statement = select(KnowledgeBaseCategory)
    result = session.execute(statement)
    # Implement global error handling/logging as needed
    return list(result.scalars().all())
