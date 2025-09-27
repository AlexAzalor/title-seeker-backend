import json

from googleapiclient.discovery import build

from app import models as m
from app import schema as s
import sqlalchemy as sa
from app.commands.utility import authorized_user_in_google_spreadsheets
from app.database import db
from app.logger import log
from config import config


CFG = config()

ID = "ID"
TECHNOLOGY_ID = "technology_id"
QUESTION = "question"
SCORE = "score"
SHORT_ANSWER = "short_answer"
ANSWER = "answer"

# Last column need to be filled!
LAST_SHEET_COLUMN = "F"
TITLE_CATEGORIES_RANGE_NAME = f"KB QuestionAnswer!A1:{LAST_SHEET_COLUMN}"


def write_kb_q_and_a_in_db(kb_qs_and_as: list[s.KnowledgeBaseQuestionAnswerCreate]):
    with db.begin() as session:
        if not session.scalar(sa.select(m.KnowledgeBaseTechnology)):
            log(log.ERROR, "KB Technology table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-kb-q-a` first")
            raise Exception("KB Technology table is empty. Please run `flask fill-db-with-kb-q-a` first")

        for q_and_a in kb_qs_and_as:
            existing_q_and_a = session.scalar(
                sa.select(m.KnowledgeBaseQuestionAnswer).where(m.KnowledgeBaseQuestionAnswer.id == q_and_a.id)
            )
            if existing_q_and_a:
                print(f"KnowledgeBaseQuestionAnswer [{q_and_a.id}] already exists. Skipping...")
                continue
            new_q_and_a = m.KnowledgeBaseQuestionAnswer(
                technology_id=q_and_a.technology_id,
                question=q_and_a.question,
                score=q_and_a.score,
                short_answer=q_and_a.short_answer,
                answer=q_and_a.answer,
            )

            session.add(new_q_and_a)
            session.flush()
            log(log.DEBUG, "KnowledgeBaseQuestionAnswer [%s] created", q_and_a.id)

        session.commit()


def convert_string_to_list_of_integers(input_string):
    string_numbers = input_string.split(", ")
    return [int(num) for num in string_numbers]


def export_kb_q_and_a_from_google_spreadsheets(with_print: bool = True, in_json: bool = False):
    """Fill title categories table with data from google spreadsheets"""

    credentials = authorized_user_in_google_spreadsheets()

    # get data from google spreadsheets
    resource = build("sheets", "v4", credentials=credentials)
    sheets = resource.spreadsheets()

    # get all values from sheet Users
    result = sheets.values().get(spreadsheetId=CFG.SPREADSHEET_ID, range=TITLE_CATEGORIES_RANGE_NAME).execute()
    values = result.get("values", [])

    assert values, "No data found"

    questions_answers: list[s.KnowledgeBaseQuestionAnswerCreate] = []

    # indexes of row values
    INDEX_ID = values[0].index(ID)
    TECHNOLOGY_ID_INDEX = values[0].index(TECHNOLOGY_ID)
    QUESTION_INDEX = values[0].index(QUESTION)
    SCORE_INDEX = values[0].index(SCORE)
    SHORT_ANSWER_INDEX = values[0].index(SHORT_ANSWER)
    ANSWER_INDEX = values[0].index(ANSWER)

    for row in values[1:]:
        if not row[INDEX_ID]:
            continue

        id = row[INDEX_ID]
        assert id, f"The id {id} is missing"

        technology_id = row[TECHNOLOGY_ID_INDEX]
        assert technology_id, f"The technology_id {technology_id} is missing"

        question = row[QUESTION_INDEX]
        assert question, f"The question {question} is missing"

        score = row[SCORE_INDEX]
        assert score, f"The score {score} is missing"

        short_answer = row[SHORT_ANSWER_INDEX]
        assert short_answer, f"The short_answer {short_answer} is missing"

        answer = row[ANSWER_INDEX]
        assert answer, f"The answer {answer} is missing"

        questions_answers.append(
            s.KnowledgeBaseQuestionAnswerCreate(
                id=int(id),
                technology_id=int(technology_id),
                question=question,
                score=int(score),
                short_answer=short_answer,
                answer=answer,
            )
        )

    print("Q&A COUNT: ", len(questions_answers))

    with open("data/knowledge_base/questions_answers.json", "w") as file:
        json.dump(
            s.KBQuestionAnswerJSONFile(questions_answers=questions_answers).model_dump(mode="json"), file, indent=4
        )
        print("KB Q&A data saved to [data/knowledge_base/questions_answers.json] file")

    write_kb_q_and_a_in_db(questions_answers)


def export_kb_qa_from_json_file(max_limit: int | None = None):
    """Fill KB Q&A with data from json file"""

    with open("data/knowledge_base/questions_answers.json", "r") as file:
        file_data = s.KBQuestionAnswerJSONFile.model_validate(json.load(file))

    qa = file_data.questions_answers
    if max_limit:
        qa = qa[:max_limit]
    write_kb_q_and_a_in_db(qa)
