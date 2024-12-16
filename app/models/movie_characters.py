import sqlalchemy as sa

from app.database import db

movie_characters = sa.Table(
    "movie_characters",
    db.Model.metadata,
    sa.Column("character_id", sa.ForeignKey("characters.id"), primary_key=True),
    sa.Column("movie_id", sa.ForeignKey("movies.id"), primary_key=True),
)
