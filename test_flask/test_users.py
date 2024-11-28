from flask import current_app as app
from flask.testing import FlaskClient, FlaskCliRunner
from click.testing import Result
from app import models as m, db
from test_flask.utils import login
from .utility import create_users


def test_policy(populate: FlaskClient):
    response = populate.get("/policy")
    assert response
    assert response.status_code == 200
    html = response.data.decode()
    assert "Privacy Policy" in html
    assert "Simple2B" in html


def test_create_new_user(populate: FlaskClient):
    login(populate)
    response = populate.post(
        "/user/create",
        data=dict(
            first_name="John",
            last_name="Doe",
            password="password",
            password_confirmation="password",
            follow_redirects=True,
        ),
    )
    assert response
    assert response.status_code == 302
