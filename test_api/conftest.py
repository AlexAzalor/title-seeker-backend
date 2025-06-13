from typing import Generator
from sqlalchemy import event
from sqlalchemy.engine import Engine
import pytest
from dotenv import load_dotenv
from fastapi import status
from moto import mock_aws
from mypy_boto3_s3 import S3Client
from mypy_boto3_sns import SNSClient

from test_api.utils import do_nothing, regexp_replace

load_dotenv("test_api/test.env")
# ruff: noqa: F401 E402
import os
import boto3

from fastapi.testclient import TestClient
from sqlalchemy import orm, select

from api import app
from app import models as m
from app import schema as s
from config import config


def pytest_configure():
    os.environ["APP_ENV"] = "testing"


CFG = config()


@pytest.fixture
def db() -> Generator[orm.Session, None, None]:
    from app.database import db, get_db

    with db.Session() as session:
        db.Model.metadata.create_all(bind=session.bind)

        from app.commands.export_users import export_users_from_json_file
        from app.commands.export_actors import export_actors_from_json_file
        from app.commands.export_directors import export_directors_from_json_file
        from app.commands.export_genres import export_genres_from_json_file
        from app.commands.export_subgenres import export_subgenres_from_json_file
        from app.commands.export_specifications import export_specifications_from_json_file
        from app.commands.export_keywords import export_keywords_from_json_file
        from app.commands.export_action_times import export_action_times_from_json_file
        from app.commands.export_shared_universe import export_su_from_json_file
        from app.commands.export_movies import export_movies_from_json_file
        from app.commands.export_rating import export_ratings_from_json_file
        from app.commands.export_characters import export_characters_from_json_file
        from app.commands.export_vp_category_criterion import export_title_criteria_from_json_file
        from app.commands.export_vp_categories import export_title_categories_from_json_file
        from app.commands.create_visual_profiles import create_visual_profiles

        export_users_from_json_file()
        export_actors_from_json_file()
        export_directors_from_json_file()
        export_genres_from_json_file()
        export_subgenres_from_json_file()
        export_specifications_from_json_file()
        export_keywords_from_json_file()
        export_action_times_from_json_file()
        export_su_from_json_file()
        export_movies_from_json_file()
        export_ratings_from_json_file()
        export_characters_from_json_file()
        export_title_criteria_from_json_file()
        export_title_categories_from_json_file()
        create_visual_profiles()

        def override_get_db() -> Generator:
            yield session

        app.dependency_overrides[get_db] = override_get_db
        yield session

        # Clean up
        db.Model.metadata.drop_all(bind=session.bind)


@pytest.fixture
def full_db(db: orm.Session) -> Generator[orm.Session, None, None]:
    yield db


@event.listens_for(Engine, "connect")
def register_sqlite_functions(dbapi_connection, connection_record):
    """Register custom SQLite functions for the connection.

    This is needed to fix the issue with regexp_replace function not being available in SQLite.
    **sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such function: regexp_replace**

    """
    try:
        # Just for protection from other engines
        if dbapi_connection.__class__.__module__.startswith("sqlite3"):
            dbapi_connection.create_function("regexp_replace", 4, regexp_replace)
    except Exception:
        pass  # Ignore for non-SQLite engines


# @pytest.fixture
# def s3_client() -> Generator[S3Client, None, None]:
#     """Returns a mock S3 client"""

#     with mock_aws():
#         from api.dependency.s3_client import get_s3_connect
#         from config import config

#         CFG = config()

#         client = get_s3_connect()
#         client.create_bucket(
#             Bucket=CFG.AWS_S3_BUCKET_NAME,
#             CreateBucketConfiguration={"LocationConstraint": CFG.AWS_REGION},  # type: ignore
#         )

#         yield client


# @pytest.fixture
# def sns_client() -> Generator[SNSClient, None, None]:
#     """Returns a mock SNS client"""

#     with mock_aws():
#         client = boto3.client("sns", region_name="us-east-1")

#         yield client


@pytest.fixture
def client(db, monkeypatch) -> Generator[TestClient, None, None]:
    """Returns a non-authorized test client for the API"""

    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_user_owner(
    client: TestClient,
    db: orm.Session,
):
    """Returns an authorized test client for the API"""
    # authorized_header: dict[str, str] = {}
    user = db.scalar(select(m.User).where(m.User.id == 1, m.User.role == s.UserRole.OWNER.value))
    assert user
    yield user


@pytest.fixture
def auth_simple_user(
    db: orm.Session,
):
    """Returns an authorized test user"""
    user = db.scalar(select(m.User).where(m.User.role.not_in(s.UserRole.get_admin_roles())))
    assert user
    yield user

    # response = client.post(
    #     "/api/auth/login",
    #     data={
    #         "username": user.first_name,
    #         "password": CFG.TEST_USER_PASSWORD,
    #     },
    # )
    # assert response.status_code == status.HTTP_200_OK
    # token = s.Token.model_validate(response.json())
    # authorized_header["Authorization"] = f"Bearer {token.access_token}"

    # yield authorized_header


# @pytest.fixture
# def worker_header(
#     client: TestClient,
#     db: orm.Session,
# ) -> Generator[dict[str, str], None, None]:
#     """Returns an authorized test client for the API"""
#     authorized_header: dict[str, str] = {}
#     user = db.scalar(select(m.User).where(m.User.id == 2))
#     assert user

#     response = client.post(
#         "/api/auth/login",
#         data={
#             "username": user.first_name,
#             "password": CFG.TEST_USER_PASSWORD,
#         },
#     )
#     assert response.status_code == status.HTTP_200_OK
#     token = s.Token.model_validate(response.json())
#     authorized_header["Authorization"] = f"Bearer {token.access_token}"

#     yield authorized_header
