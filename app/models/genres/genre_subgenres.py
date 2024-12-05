import sqlalchemy as sa

from app.database import db

genre_subgenres = sa.Table(
    "genre_subgenres",
    db.Model.metadata,
    sa.Column("genre_id", sa.ForeignKey("genres.id"), primary_key=True),
    sa.Column("subgenre_id", sa.ForeignKey("subgenres.id"), primary_key=True),
)
