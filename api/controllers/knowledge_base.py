from typing import Sequence
import app.models as m
import app.schema as s


def compute_technology_mastery(technology: m.KnowledgeBaseTechnology):
    total_answered = len(technology.questions_answers)
    if total_answered == 0:
        return 0

    MAX_STARS = 5
    MAX_QUESTIONS = 50
    PERCENTAGE_FACTOR = 100

    sum_scores = sum(q.score for q in technology.questions_answers)
    avg_stars = sum_scores / total_answered
    # Depth → how well you answered (stars average).
    depth = avg_stars / MAX_STARS
    # Coverage → how many questions you’ve answered compared to all you planned for that tech.
    coverage = total_answered / MAX_QUESTIONS
    mastery_fraction = depth * coverage
    return int(mastery_fraction * PERCENTAGE_FACTOR)


def get_technologies_dto(technologies: Sequence[m.KnowledgeBaseTechnology]):
    return s.KBTechnologyListOut(
        technologies=[
            s.KBTechnologyOut(
                key=tech.key,
                name=tech.name,
                description=tech.description,
                mastery_progress=compute_technology_mastery(tech),
                questions_answers=[
                    s.KBQuestionAnswerOut(
                        id=qa.id,
                        technology_id=qa.technology_id,
                        question=qa.question,
                        score=qa.score,
                        short_answer=qa.short_answer,
                        answer=qa.answer,
                    )
                    for qa in tech.questions_answers
                ],
            )
            for tech in technologies
        ]
    )
