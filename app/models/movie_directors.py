import sqlalchemy as sa

from app.database import db

movie_directors = sa.Table(
    "movie_directors",
    db.Model.metadata,
    sa.Column("director_id", sa.ForeignKey("directors.id"), primary_key=True),
    sa.Column("movie_id", sa.ForeignKey("movies.id"), primary_key=True),
)
