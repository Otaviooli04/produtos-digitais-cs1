"""cluster highlight lines — linhas problemáticas do código representativo

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-20

"""
import sqlalchemy as sa
from alembic import op

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'question_clusters',
        sa.Column('highlight_lines', sa.JSON, server_default='[]'),
    )


def downgrade():
    op.drop_column('question_clusters', 'highlight_lines')
