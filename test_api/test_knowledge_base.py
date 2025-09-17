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


def test_create_update_kb_category(client: TestClient, db: Session):
    form_data = s.KBCategoryOut(
        key="new-category",
        name="New Category",
        description="This is a new category",
    )

    response = client.post(
        "/api/knowledge-base/",
        json=form_data.model_dump(),
    )
    assert response.status_code == status.HTTP_201_CREATED
    new_category = db.scalar(sa.select(m.KnowledgeBaseCategory).where(m.KnowledgeBaseCategory.key == form_data.key))
    assert new_category

    # Update
    new_form_data = s.KBCategoryPutIn(
        id=new_category.id,
        key="new-category 2",
        name="New Category 2",
        description="This is a new category 2",
    )

    response = client.put(
        "/api/knowledge-base/",
        json=new_form_data.model_dump(),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    upd_category = db.scalar(sa.select(m.KnowledgeBaseCategory).where(m.KnowledgeBaseCategory.key == new_form_data.key))
    assert upd_category


def test_create_kb_technology(client: TestClient, db: Session):
    CATEGORY_KEY = "frontend"
    form_data = s.KBTechnologyIn(
        key="new-tech",
        name="New Tech",
        description="This is a new tech",
        category_key=CATEGORY_KEY,
    )

    response = client.post(
        "/api/knowledge-base/technologies",
        json=form_data.model_dump(),
    )
    assert response.status_code == status.HTTP_201_CREATED
    new_tech = db.scalar(sa.select(m.KnowledgeBaseTechnology).where(m.KnowledgeBaseTechnology.key == form_data.key))
    assert new_tech

    # Update
    new_form_data = s.KBTechnologyPutIn(
        id=new_tech.id,
        key="new-tech 2",
        name="New Tech 2",
        description="This is a new tech 2",
        category_key=CATEGORY_KEY,
    )

    response = client.put(
        "/api/knowledge-base/technology",
        json=new_form_data.model_dump(),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    upd_tech = db.scalar(sa.select(m.KnowledgeBaseTechnology).where(m.KnowledgeBaseTechnology.key == new_form_data.key))
    assert upd_tech


def test_create_kb_question_answer(client: TestClient, db: Session):
    TECH_KEY = "react"
    technology = db.scalar(sa.select(m.KnowledgeBaseTechnology).where(m.KnowledgeBaseTechnology.key == TECH_KEY))
    assert technology

    form_data = s.KBQuestionAnswerIn(
        question="What is hook?",
        short_answer="A hook is a special function in React",
        answer="A hook is a special function in React that lets you use state and other React features without writing a class.",
        score=5,
        technology_key=TECH_KEY,
    )

    response = client.post(
        "/api/knowledge-base/question-answer",
        json=form_data.model_dump(),
    )
    assert response.status_code == status.HTTP_201_CREATED
    new_qa = db.scalar(
        sa.select(m.KnowledgeBaseQuestionAnswer).where(m.KnowledgeBaseQuestionAnswer.question == form_data.question)
    )
    assert new_qa

    # Update
    new_form_data = s.KBQuestionAnswerPutIn(
        id=technology.id,
        question="What is hook?",
        short_answer="A hook is a special function in React",
        answer="A hook is a special function in React that lets you use state and other React features without writing a class.",
        score=5,
        technology_key=TECH_KEY,
    )

    response = client.put(
        "/api/knowledge-base/question-answer",
        json=new_form_data.model_dump(),
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    upd_qa = db.scalar(
        sa.select(m.KnowledgeBaseQuestionAnswer).where(m.KnowledgeBaseQuestionAnswer.id == new_form_data.id)
    )
    assert upd_qa
