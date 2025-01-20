from app.database import db
import sqlalchemy as sa
from app import models as m


def calculate_movie_rating():
    with db.begin() as session:
        movies = session.scalars(sa.select(m.Movie)).all()

        for movie in movies:
            movie_ratings = movie.ratings
            average_rating = round(sum([rating.rating for rating in movie_ratings]) / len(movie_ratings), 2)

            movie.average_rating = average_rating
            movie.ratings_count = len(movie_ratings)

            session.flush()

        session.commit()
