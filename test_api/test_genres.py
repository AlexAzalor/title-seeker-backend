import pytest

import sqlalchemy as sa

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models as m

from config import config

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_all_genres(client: TestClient, db: Session):
    genre: m.Genre | None = db.scalar(sa.select(m.Genre).where(m.Genre.id == 1))
    assert genre
    assert genre.subgenres

    response = client.get("/api/genres/")
    assert response.status_code == status.HTTP_200_OK
