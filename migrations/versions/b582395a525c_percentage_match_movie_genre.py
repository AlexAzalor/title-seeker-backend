"""percentage_match_movie_genre

Revision ID: b582395a525c
Revises: 4c482dab720d
Create Date: 2024-12-17 12:57:45.488273

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b582395a525c'
down_revision = '4c482dab720d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('movie_genres', schema=None) as batch_op:
        batch_op.add_column(sa.Column('percentage_match', sa.Float(), nullable=False))

    with op.batch_alter_table('movie_subgenres', schema=None) as batch_op:
        batch_op.add_column(sa.Column('percentage_match', sa.Float(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('movie_subgenres', schema=None) as batch_op:
        batch_op.drop_column('percentage_match')

    with op.batch_alter_table('movie_genres', schema=None) as batch_op:
        batch_op.drop_column('percentage_match')

    # ### end Alembic commands ###
