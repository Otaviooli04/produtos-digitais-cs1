"""processing jobs — rastreio de tarefas em segundo plano (upload Gemini, lote)

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-16

"""
import sqlalchemy as sa
from alembic import op

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'processing_jobs',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('kind', sa.String),
        sa.Column('status', sa.String, server_default='pending'),
        sa.Column('stage', sa.String, server_default=''),
        sa.Column('total', sa.Integer, server_default='0'),
        sa.Column('processed', sa.Integer, server_default='0'),
        sa.Column('message', sa.Text, server_default=''),
        sa.Column('result', sa.JSON),
        sa.Column('exam_id', sa.Integer, sa.ForeignKey('exams.id'), nullable=True),
        sa.Column('professor_id', sa.Integer, sa.ForeignKey('professors.id'), nullable=True),
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
    )


def downgrade():
    op.drop_table('processing_jobs')
