"""
This module contains the query functions for the CategoryProtocolAssignment model.
"""

import sqlalchemy as sa

from typing import Sequence
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.knowledge_base.category.orm import KnowledgeBaseCategory
from app.models.knowledge_base.technology.orm import KnowledgeBaseTechnology


def find_by_category(session: Session, category_key: str) -> Sequence[KnowledgeBaseTechnology]:
    category = session.scalar(sa.select(KnowledgeBaseCategory).where(KnowledgeBaseCategory.key == category_key))
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    statement = select(KnowledgeBaseTechnology).where(KnowledgeBaseTechnology.category_id == category.id)
    result = session.scalars(statement).all()
    return result
