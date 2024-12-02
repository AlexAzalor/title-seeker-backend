import pytest

import sqlalchemy as sa

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m

from config import config

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_actors(client: TestClient, db: Session):
    actor: m.Actor | None = db.scalar(sa.select(m.Actor).where(m.Actor.id == 1))
    assert actor

    UPLOAD_DIRECTORY = "./uploads/avatars/"
    test_file = "1_Morgan Freeman.png"
    avatar_name = "Morgan Freeman.png"

    files = {"file": (avatar_name, open(UPLOAD_DIRECTORY + test_file, "rb"))}
    response = client.post(f"/api/avatars/upload-avatar/{actor.id}", files=files)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"info": "Avatar uploaded successfully"}
    assert actor.avatar == test_file

    response = client.get(f"/api/avatars/{test_file}")
    assert response.status_code == status.HTTP_200_OK
