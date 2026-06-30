from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from app.database import db
from .utils import ModelMixin


class MovieSimilarity(db.Model, ModelMixin):
    """Pre-computed pairwise similarity scores between movies.

    Populated by the `flask calculate-similarities` command.
    movie_a_id is always the smaller ID to avoid duplicate reversed pairs.
    """

    __tablename__ = "movie_similarities"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)

    movie_a_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    movie_b_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    score: orm.Mapped[float] = orm.mapped_column(sa.Float, nullable=False)

    computed_at: orm.Mapped[datetime] = orm.mapped_column(
        sa.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=sa.func.now(),
    )

    __table_args__ = (
        sa.UniqueConstraint("movie_a_id", "movie_b_id", name="uq_movie_similarity_pair"),
        sa.Index("ix_movie_similarities_score", "score"),
        sa.CheckConstraint("movie_a_id < movie_b_id", name="ck_movie_similarity_ordered_pair"),
    )

    def __repr__(self):
        return f"<MovieSimilarity movie_a={self.movie_a_id} movie_b={self.movie_b_id} score={self.score:.4f}>"
