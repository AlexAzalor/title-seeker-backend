from sqlalchemy.orm import Session
import sqlalchemy as sa
import app.models as m
import app.schema as s
from fastapi import HTTPException, status


def create(session: Session, form_data: s.KBTechnologyIn):
    category = session.scalar(
        sa.select(m.KnowledgeBaseCategory).where(m.KnowledgeBaseCategory.key == form_data.category_key)
    )
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    new_tech = m.KnowledgeBaseTechnology(
        key=form_data.key,
        category_id=category.id,
        name=form_data.name,
        description=form_data.description,
    )
    session.add(new_tech)
    session.commit()


def update(session: Session, form_data: s.KBTechnologyPutIn):
    """Update a knowledge base category"""

    technology = session.scalar(
        sa.select(m.KnowledgeBaseTechnology).where(m.KnowledgeBaseTechnology.id == form_data.id)
    )
    if not technology:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    technology.key = form_data.key
    technology.name = form_data.name
    technology.description = form_data.description

    session.commit()
