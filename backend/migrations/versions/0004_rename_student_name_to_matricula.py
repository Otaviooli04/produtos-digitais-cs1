"""rename student_name to matricula

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-07

"""
from alembic import op

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('submissions', 'student_name', new_column_name='matricula')


def downgrade():
    op.alter_column('submissions', 'matricula', new_column_name='student_name')
