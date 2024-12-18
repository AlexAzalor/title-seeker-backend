import sqlalchemy as sa

from app.database import db

movie_keywords = sa.Table(
    "movie_keywords",
    db.Model.metadata,
    sa.Column("movie_id", sa.ForeignKey("movies.id"), primary_key=True),
    sa.Column("keyword_id", sa.ForeignKey("keywords.id"), primary_key=True),
    sa.Column("percentage_match", sa.Float, nullable=False, default=0.0),
)
