from flask.testing import FlaskClient
# from test_flask.utils import login


def test_policy(populate: FlaskClient):
    response = populate.get("/policy")
    assert response
    assert response.status_code == 200
    html = response.data.decode()
    assert "Privacy Policy" in html
    assert "TitleHunt" in html


# def test_create_new_user(populate: FlaskClient):
#     login(populate)
#     response = populate.post(
#         "/user/create",
#         data=dict(
#             first_name="John",
#             last_name="Doe",
#             password="password",
#             password_confirmation="password",
#             follow_redirects=True,
#         ),
#     )
#     assert response
#     assert response.status_code == 302
