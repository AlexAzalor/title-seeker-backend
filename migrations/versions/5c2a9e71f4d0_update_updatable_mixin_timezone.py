"""update updatable mixin timezone

Revision ID: 5c2a9e71f4d0
Revises: 8834d5be3da1
Create Date: 2026-11-19 13:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "5c2a9e71f4d0"
down_revision = "8834d5be3da1"
branch_labels = None
depends_on = None

UPDATABLE_TABLES = [
    "actors",
    "character_translations",
    "characters",
    "directors",
    "genres",
    "knowledge_base_categories",
    "knowledge_base_question_answers",
    "knowledge_base_technologies",
    "movies",
    "ratings",
    "shared_universes",
    "subgenres",
    "users",
]


def upgrade():
    for table in UPDATABLE_TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column(
                "updated_at",
                existing_type=postgresql.TIMESTAMP(),
                type_=sa.DateTime(timezone=True),
                existing_nullable=False,
            )


def downgrade():
    for table in reversed(UPDATABLE_TABLES):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column(
                "updated_at",
                existing_type=sa.DateTime(timezone=True),
                type_=postgresql.TIMESTAMP(),
                existing_nullable=False,
            )
