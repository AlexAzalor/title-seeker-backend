from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import app.schema as s
import sqlalchemy as sa
import app.models as m
from app.models.knowledge_base.category.orm import KnowledgeBaseCategory


def create(session: Session, form_data: s.KBCategoryOut):
    """Create a new knowledge base category"""
    new_category = KnowledgeBaseCategory(
        key=form_data.key,
        name=form_data.name,
        description=form_data.description,
    )
    session.add(new_category)
    session.commit()


def update(session: Session, form_data: s.KBCategoryPutIn):
    """Update a knowledge base category"""

    category = session.scalar(sa.select(m.KnowledgeBaseCategory).where(m.KnowledgeBaseCategory.id == form_data.id))
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    category.key = form_data.key
    category.name = form_data.name
    category.description = form_data.description

    session.commit()
