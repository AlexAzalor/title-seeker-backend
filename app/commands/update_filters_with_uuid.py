from uuid import uuid4
import sqlalchemy as sa

from app import models as m
from app.database import db
from app.logger import log
from config import config

CFG = config()


def update_filters_with_uuid():
    with db.begin() as session:
        genres = session.scalars(sa.select(m.Genre)).all()
        if not genres:
            log(log.ERROR, "Genre table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-***` first")
            raise Exception("Genre table is empty. Please run `flask fill-db-with-***` first")

        subgenres = session.scalars(sa.select(m.Subgenre)).all()
        if not subgenres:
            log(log.ERROR, "Subgenre table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-***` first")
            raise Exception("Subgenre table is empty. Please run `flask fill-db-with-***` first")

        specifications = session.scalars(sa.select(m.Specification)).all()
        if not specifications:
            log(log.ERROR, "Specification table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-***` first")
            raise Exception("Specification table is empty. Please run `flask fill-db-with-***` first")

        keywords = session.scalars(sa.select(m.Keyword)).all()
        if not keywords:
            log(log.ERROR, "Keyword table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-***` first")
            raise Exception("Keyword table is empty. Please run `flask fill-db-with-***` first")

        actionTimes = session.scalars(sa.select(m.ActionTime)).all()
        if not actionTimes:
            log(log.ERROR, "ActionTime table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-***` first")
            raise Exception("ActionTime table is empty. Please run `flask fill-db-with-***` first")

        def add_uuid_to_items(items):
            for item in items:
                if item.uuid:
                    print(f"Item {item.key} already has UUID")
                    continue

                item.uuid = str(uuid4())

        add_uuid_to_items(genres)
        add_uuid_to_items(subgenres)
        add_uuid_to_items(specifications)
        add_uuid_to_items(keywords)
        add_uuid_to_items(actionTimes)

        session.commit()
        log(log.INFO, "All filters have been updated with UUIDs")
