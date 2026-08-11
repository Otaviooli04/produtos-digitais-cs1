"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exams",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("filename", sa.String),
        sa.Column("raw_text", sa.Text),
        sa.Column("created_at", sa.DateTime),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("exam_id", sa.Integer, sa.ForeignKey("exams.id")),
        sa.Column("number", sa.String),
        sa.Column("statement", sa.Text),
        sa.Column("required_structures", sa.JSON),
        sa.Column("forbidden_structures", sa.JSON),
        sa.Column("requires_loop", sa.Boolean, server_default="false"),
    )

    op.create_table(
        "test_cases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("question_id", sa.Integer, sa.ForeignKey("questions.id")),
        sa.Column("input", sa.Text),
        sa.Column("expected_output", sa.Text),
    )

    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("question_id", sa.Integer, sa.ForeignKey("questions.id")),
        sa.Column("code", sa.Text),
        sa.Column("compile_error", sa.Text, server_default=""),
        sa.Column("warnings", sa.Text, server_default=""),
        sa.Column("all_tests_passed", sa.Boolean, nullable=True),
        sa.Column("error_category", sa.String, server_default=""),
        sa.Column("pedagogical_diagnosis", sa.Text, server_default=""),
        sa.Column("actionable_feedback", sa.Text, server_default=""),
        sa.Column("submitted_at", sa.DateTime),
    )

    op.create_table(
        "submission_test_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("submission_id", sa.Integer, sa.ForeignKey("submissions.id")),
        sa.Column("input", sa.Text),
        sa.Column("expected_output", sa.Text),
        sa.Column("actual_output", sa.Text),
        sa.Column("passed", sa.Boolean),
    )


def downgrade() -> None:
    op.drop_table("submission_test_results")
    op.drop_table("submissions")
    op.drop_table("test_cases")
    op.drop_table("questions")
    op.drop_table("exams")
