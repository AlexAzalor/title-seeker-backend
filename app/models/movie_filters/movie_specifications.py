import sqlalchemy as sa

from app.database import db

movie_specifications = sa.Table(
    "movie_specifications",
    db.Model.metadata,
    sa.Column("movie_id", sa.ForeignKey("movies.id"), primary_key=True),
    sa.Column("specification_id", sa.ForeignKey("specifications.id"), primary_key=True),
    sa.Column("percentage_match", sa.Float, nullable=False, default=0.0),
)
