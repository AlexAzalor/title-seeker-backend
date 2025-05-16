import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


from app.schema import GoogleTokenVerification, AppleTokenVerification

from app import models as m
from app import schema as s
from config import config

CFG = config()

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


def test_google_auth(client: TestClient, db: Session):
    auth_data = s.GoogleAuthIn(
        email=DUMMY_GOOGLE_VALIDATION.email,
        given_name=DUMMY_GOOGLE_VALIDATION.given_name,
        family_name=DUMMY_GOOGLE_VALIDATION.family_name,
    )

    # Test new user creation
    user = db.scalar(sa.select(m.User).where(m.User.is_deleted.is_(False), m.User.email == auth_data.email))
    assert not user

    response = client.post(
        "/api/auth/google/",
        json=auth_data.model_dump(),
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.GoogleAuthOut.model_validate(response.json())
    assert data
    assert data.email == auth_data.email
    assert data.role == s.UserRole.USER

    # Test login
    user = db.scalar(sa.select(m.User).where(m.User.is_deleted.is_(False), m.User.email == auth_data.email))
    assert user

    response = client.post(
        "/api/auth/google/",
        json=auth_data.model_dump(),
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.GoogleAuthOut.model_validate(response.json())
    assert data
    assert data.email == auth_data.email
    assert data.role == s.UserRole.USER
    assert data.my_language == s.Language.UK

    # Test delete user
    response = client.delete(
        "/api/auth/google/",
        params={"user_uuid": user.uuid},
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    user = db.scalar(sa.select(m.User).where(m.User.is_deleted.is_(False), m.User.email == auth_data.email))
    assert not user


def test_prevent_delete_owner(client: TestClient, db: Session, auth_user_owner: m.User):
    response = client.delete(
        "/api/auth/google/",
        params={"user_uuid": auth_user_owner.uuid},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
