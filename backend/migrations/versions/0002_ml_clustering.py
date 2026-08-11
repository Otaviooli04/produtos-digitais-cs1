"""ml clustering — adiciona suporte a UMAP/HDBSCAN

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("submissions", sa.Column("ast_structures", sa.JSON, nullable=True))
    op.add_column("submissions", sa.Column("cluster_id", sa.Integer, nullable=True))
    op.add_column("submissions", sa.Column("umap_x", sa.String, nullable=True))
    op.add_column("submissions", sa.Column("umap_y", sa.String, nullable=True))

    op.create_table(
        "question_clusters",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("question_id", sa.Integer, sa.ForeignKey("questions.id")),
        sa.Column("cluster_label", sa.Integer),
        sa.Column("size", sa.Integer),
        sa.Column("dominant_error", sa.String, server_default=""),
        sa.Column(
            "representative_submission_id",
            sa.Integer,
            sa.ForeignKey("submissions.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("question_clusters")
    op.drop_column("submissions", "umap_y")
    op.drop_column("submissions", "umap_x")
    op.drop_column("submissions", "cluster_id")
    op.drop_column("submissions", "ast_structures")
