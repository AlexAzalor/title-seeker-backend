import sqlalchemy as sa

from app.database import db

actor_characters = sa.Table(
    "actor_characters",
    db.Model.metadata,
    sa.Column("character_id", sa.ForeignKey("characters.id"), primary_key=True),
    sa.Column("actor_id", sa.ForeignKey("actors.id"), primary_key=True),
)
