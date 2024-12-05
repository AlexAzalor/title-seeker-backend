import sqlalchemy as sa

from app.database import db

movie_genres = sa.Table(
    "movie_genres",
    db.Model.metadata,
    sa.Column("movie_id", sa.ForeignKey("movies.id"), primary_key=True),
    sa.Column("genre_id", sa.ForeignKey("genres.id"), primary_key=True),
)
