"""turmas e student_name

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("turmas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String, nullable=False),
        sa.Column("codigo", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime),
    )
    op.add_column("exams", sa.Column("turma_id", sa.Integer, sa.ForeignKey("turmas.id"), nullable=True))
    op.add_column("submissions", sa.Column("student_name", sa.String, nullable=True))


def downgrade():
    op.drop_column("submissions", "student_name")
    op.drop_column("exams", "turma_id")
    op.drop_table("turmas")
