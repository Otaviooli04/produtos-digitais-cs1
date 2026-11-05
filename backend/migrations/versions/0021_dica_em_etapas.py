"""dica em etapas na tentativa

Revision ID: 0021
Revises: 0020
Create Date: 2026-11-05

Guarda as duas pistas que o Gemini gera junto da explicação, até onde o aluno
abriu a ajuda e quando pediu a primeira dica, que é o dado do experimento 2.
Colunas novas, as tentativas que já existem ficam com o nível 0.
"""
import sqlalchemy as sa
from alembic import op

revision = '0021'
down_revision = '0020'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('submissions', sa.Column('llm_pistas', sa.JSON(), nullable=True))
    op.add_column('submissions', sa.Column(
        'nivel_de_ajuda', sa.SmallInteger(), nullable=False, server_default='0'))
    op.add_column('submissions', sa.Column('ajuda_pedida_em', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('submissions', 'ajuda_pedida_em')
    op.drop_column('submissions', 'nivel_de_ajuda')
    op.drop_column('submissions', 'llm_pistas')
