"""professor auth — tabela professors e professor_id em turmas

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-07

"""
import sqlalchemy as sa
from alembic import op

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'professors',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String, nullable=False, unique=True),
        sa.Column('nome', sa.String, nullable=False),
        sa.Column('senha_hash', sa.String, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=True),
    )
    op.add_column('turmas', sa.Column('professor_id', sa.Integer, sa.ForeignKey('professors.id'), nullable=True))


def downgrade():
    op.drop_column('turmas', 'professor_id')
    op.drop_table('professors')
