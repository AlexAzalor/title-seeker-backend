import sqlalchemy as sa

from app.database import db

# percentage = Column(Float, nullable=False, default=0.0)
movie_genres = sa.Table(
    "movie_genres",
    db.Model.metadata,
    sa.Column("movie_id", sa.ForeignKey("movies.id"), primary_key=True),
    sa.Column("genre_id", sa.ForeignKey("genres.id"), primary_key=True),
    sa.Column("percentage_match", sa.Float, nullable=False, default=0.0),
)
