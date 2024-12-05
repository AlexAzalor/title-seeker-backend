import sqlalchemy as sa

from app.database import db

movie_subgenres = sa.Table(
    "movie_subgenres",
    db.Model.metadata,
    sa.Column("movie_id", sa.ForeignKey("movies.id"), primary_key=True),
    sa.Column("subgenre_id", sa.ForeignKey("subgenres.id"), primary_key=True),
)
