"""function support — required_functions em questions e ast_functions em submissions

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-28

"""
import sqlalchemy as sa
from alembic import op

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('questions', sa.Column('required_functions', sa.JSON, nullable=True))
    op.add_column('submissions', sa.Column('ast_functions', sa.JSON, nullable=True))


def downgrade():
    op.drop_column('submissions', 'ast_functions')
    op.drop_column('questions', 'required_functions')
