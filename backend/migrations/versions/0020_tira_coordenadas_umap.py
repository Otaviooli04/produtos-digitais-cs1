"""tira as coordenadas do UMAP das submissões

Revision ID: 0020
Revises: 0019
Create Date: 2026-11-05

O mapa de dispersão saiu da tela em 12/09 e nada mais lê `umap_x` e `umap_y`.
Os valores guardados se perdem, e o downgrade recria as colunas vazias.
"""
import sqlalchemy as sa
from alembic import op

revision = '0020'
down_revision = '0019'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('submissions', 'umap_x')
    op.drop_column('submissions', 'umap_y')


def downgrade():
    op.add_column('submissions', sa.Column('umap_y', sa.String(), nullable=True))
    op.add_column('submissions', sa.Column('umap_x', sa.String(), nullable=True))
