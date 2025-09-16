# Authorization schema
from pydantic import BaseModel


class KnowledgeBaseCategoryCreate(BaseModel):
    key: str
    name: str
    description: str


class KBCategoryJSONFile(BaseModel):
    categories: list[KnowledgeBaseCategoryCreate]


class KnowledgeBaseTechnologyCreate(BaseModel):
    key: str
    category_id: int
    name: str
    description: str


class KBTechnologyJSONFile(BaseModel):
    technologies: list[KnowledgeBaseTechnologyCreate]


class KnowledgeBaseQuestionAnswerCreate(BaseModel):
    id: int
    technology_id: int
    question: str
    score: int
    short_answer: str
    answer: str


class KBQuestionAnswerJSONFile(BaseModel):
    questions_answers: list[KnowledgeBaseQuestionAnswerCreate]


class KBCategoryOut(BaseModel):
    key: str
    name: str
    description: str


class KBCategoryListOut(BaseModel):
    categories: list[KBCategoryOut]


class KBQuestionAnswerOut(BaseModel):
    id: int
    technology_id: int
    question: str
    score: int
    short_answer: str
    answer: str


class KBTechnologyOut(BaseModel):
    key: str
    name: str
    description: str
    mastery_progress: int
    questions_answers: list[KBQuestionAnswerOut]


class KBTechnologyListOut(BaseModel):
    technologies: list[KBTechnologyOut]
