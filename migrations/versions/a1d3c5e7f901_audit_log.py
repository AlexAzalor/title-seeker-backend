"""audit_log

Revision ID: a1d3c5e7f901
Revises: 7e65849c9863
Create Date: 2026-10-17 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a1d3c5e7f901'
down_revision = '7e65849c9863'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('entity_id', sa.BigInteger(), nullable=False),
        sa.Column('event_type', sa.String(length=128), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('changes', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_audit_logs_entity_history',
        'audit_logs',
        ['entity_type', 'entity_id', sa.text('created_at DESC'), sa.text('id DESC')],
        unique=False,
    )


def downgrade():
    op.drop_index('ix_audit_logs_entity_history', table_name='audit_logs')
    op.drop_table('audit_logs')
