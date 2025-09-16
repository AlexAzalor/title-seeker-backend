import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m
from app import schema as s
from config import config

CFG = config()


def test_get_kb_categories(client: TestClient, db: Session):
    categories = db.scalars(sa.select(m.KnowledgeBaseCategory)).all()
    assert categories

    response = client.get(
        "/api/knowledge-base/",
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.KBCategoryListOut.model_validate(response.json())
    assert data.categories


def test_get_kb_technologies(client: TestClient, db: Session):
    CATEGORY_KEY = "frontend"
    category = db.scalar(sa.select(m.KnowledgeBaseCategory).where(m.KnowledgeBaseCategory.key == CATEGORY_KEY))
    assert category

    response = client.get(
        f"/api/knowledge-base/technologies/{CATEGORY_KEY}",
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.KBTechnologyListOut.model_validate(response.json())
    assert data.technologies
