import sqlalchemy as sa

from app.database import db

movie_actors = sa.Table(
    "movie_actors",
    db.Model.metadata,
    sa.Column("actor_id", sa.ForeignKey("actors.id"), primary_key=True),
    sa.Column("movie_id", sa.ForeignKey("movies.id"), primary_key=True),
)
