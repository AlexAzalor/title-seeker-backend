import os

os.environ["APP_ENV"] = "testing"

from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "test.env")
load_dotenv(env_path, override=True)

from config import config

from typing import Generator
from sqlalchemy import event
from sqlalchemy.engine import Engine
import pytest
from fastapi import status
from moto import mock_aws
from mypy_boto3_s3 import S3Client
from mypy_boto3_sns import SNSClient

from test_api.utils import do_nothing, regexp_replace

# ruff: noqa: F401 E402
import boto3

from fastapi.testclient import TestClient
from sqlalchemy import orm, select

from api import app
from app import models as m
from app import schema as s


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
