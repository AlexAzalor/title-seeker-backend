import sqlalchemy as sa

from app.database import db

movie_action_times = sa.Table(
    "movie_action_times",
    db.Model.metadata,
    sa.Column("movie_id", sa.ForeignKey("movies.id"), primary_key=True),
    sa.Column("action_time_id", sa.ForeignKey("action_times.id"), primary_key=True),
    sa.Column("percentage_match", sa.Float, nullable=False, default=0.0),
)
