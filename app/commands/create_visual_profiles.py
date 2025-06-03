import sqlalchemy as sa

from app import models as m
from app import schema as s
from app.database import db
from app.logger import log
from config import config

CFG = config()

ID = "ID"
MOVIE_ID = "movie_id"
USER_ID = "user_id"
CATEGORY_ID = "category_id"

# Last column need to be filled!
LAST_SHEET_COLUMN = "E"
TITLE_VP_RANGE_NAME = f"Title Visual Profile!A1:{LAST_SHEET_COLUMN}"


def create_visual_profiles():
    with db.begin() as session:
        movies = session.scalars(sa.select(m.Movie)).all()

        if not movies:
            log(log.ERROR, "Movie table is empty")
            log(log.ERROR, "Please run `flask fill-db-with-***` first")
            raise Exception("Movie table is empty. Please run `flask fill-db-with-***` first")

        for movie in movies:
            if movie.visual_profiles:
                print(f"Movie {movie.key} has already visual profiles")
                continue

            owner = session.scalar(sa.select(m.User).where(m.User.role == s.UserRole.OWNER.value))
            if not owner:
                log(log.ERROR, "Owner user not found")
                raise Exception("Owner user not found")

            category = session.scalar(sa.select(m.VisualProfileCategory))
            if not category:
                log(log.ERROR, "Category table is empty")
                log(log.ERROR, "Please run `flask fill-db-with-genres` first")
                raise Exception("Category table is empty. Please run `flask fill-db-with-genres` first")

            new_vp = m.VisualProfile(
                movie_id=movie.id,
                user_id=owner.id,
                category_id=category.id,
            )
            session.add(new_vp)
            session.flush()

            for idx, criterion in enumerate(category.criteria):
                new_rating = m.VisualProfileRating(
                    title_visual_profile_id=new_vp.id,
                    criterion_id=criterion.id,
                    rating=3,
                    order=idx + 1,
                )
                session.add(new_rating)
                session.flush()
            print(f"Visual profile for movie {movie.key} created!")

        log(log.INFO, "Visual profiles created successfully")
        session.commit()
