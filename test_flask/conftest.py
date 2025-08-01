import pytest
from dotenv import load_dotenv
from flask import Flask
from flask.testing import FlaskClient

from app import create_app, db
from app import models as m
from test_flask.utils import register

load_dotenv("test_flask/test.env")


@pytest.fixture()
def app():
    app = create_app("testing")
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///database-test-flask.sqlite3",
        }
    )
    db.initialize(url=app.config["SQLALCHEMY_DATABASE_URI"])
    yield app


@pytest.fixture()
def client(app: Flask):
    with app.test_client() as client:
        app_ctx = app.app_context()
        app_ctx.push()

        db.drop_all()
        db.create_all()
        register()

        yield client
        db.drop_all()
        app_ctx.pop()


@pytest.fixture()
def runner(app, client):
    from app import commands

    commands.init(app)

    yield app.test_cli_runner()


@pytest.fixture
def populate(client: FlaskClient):
    NUM_TEST_USERS = 100
    for i in range(NUM_TEST_USERS):
        m.Admin(
            username=f"user{i+1}",
            email=f"user{i+1}@mail.com",
            password_hash="*",
        ).save(False)
    db.session.commit()

    yield client
