# import pytest
# import sqlalchemy as sa
# from fastapi import status
# from fastapi.testclient import TestClient
# from sqlalchemy.orm import Session
# from werkzeug.security import check_password_hash


from app.schema import GoogleTokenVerification, AppleTokenVerification

# from app import models as m
from app import schema as s
from config import config

CFG = config()


USER_PASSWORD = CFG.TEST_USER_PASSWORD

DUMMY_GOOGLE_VALIDATION = GoogleTokenVerification(
    iss="https://accounts.google.com",
    email="test@example.com",
    azp="str",
    aud="str",
    sub="str",
    email_verified=True,
    name="str",
    picture="str",
    given_name="str",
    family_name="str",
    locale="str",
    iat=1,
    exp=1,
)

DUMMY_IOS_VALIDATION = AppleTokenVerification(
    iss="https://appleid.apple.com",
    aud="str",
    exp=1,
    iat=1,
    sub="str",
    c_hash="str",
    email="apple.test@example.com",
    email_verified=True,
    auth_time=1,
    nonce_supported=True,
    fullName=s.AppleAuthenticationFullName(givenName="Apple", familyName="Test"),
)


# @pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
# def test_auth(db: Session, client: TestClient):
#     USER_NAME = db.scalar(sa.select(m.User.first_name).order_by(m.User.id))
#     assert USER_NAME
#     user_auth = s.Auth(first_name=USER_NAME, password=USER_PASSWORD)
#     response = client.post("/api/auth/token", json=user_auth.model_dump())
#     assert response.status_code == status.HTTP_200_OK
#     token = s.Token.model_validate(response.json())
#     assert token.access_token and token.token_type == "bearer"
#     header = dict(Authorization=f"Bearer {token.access_token}")
#     res = client.get("api/users/me", headers=header)
#     assert res.status_code == status.HTTP_200_OK

#     old_password = "Titlehunt2024"
#     new_password = "New_password1"

#     # change password
#     data_change_password: s.PasswordAuthIn = s.PasswordAuthIn(
#         old_password=old_password,
#         new_password=new_password,
#     )
#     response = client.post(
#         "/api/auth/change-password",
#         json=data_change_password.model_dump(),
#         headers=header,
#     )
#     assert response.status_code == status.HTTP_200_OK
#     user_db = db.scalar(sa.select(m.User).where(m.User.first_name == USER_NAME))
#     assert user_db
#     assert check_password_hash(user_db.password, new_password)

#     # auth with new password
#     user_auth = s.Auth(first_name=USER_NAME, password=new_password)
#     response = client.post("/api/auth/token", json=user_auth.model_dump())
#     assert response.status_code == status.HTTP_200_OK
#     token = s.Token.model_validate(response.json())
#     assert token.access_token and token.token_type == "bearer"
