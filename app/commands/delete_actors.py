import sqlalchemy as sa
from app import models as m
from app.database import db


def delete_actors_from_db():
    """Delete actors from db"""

    with db.begin() as session:
        session.execute(sa.delete(m.ActorTranslation))

        session.execute(sa.delete(m.movie_actors))

        session.execute(sa.delete(m.Actor))

        session.execute(sa.text("ALTER SEQUENCE actors_id_seq RESTART WITH 1;"))

        actors = session.scalars(sa.select(m.Actor)).all()
        print("Actors:", len(actors))

        session.commit()
