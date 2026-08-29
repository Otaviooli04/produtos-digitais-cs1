"""explicação individual da tentativa, gerada por LLM sob demanda e cacheada

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-17

O Gemini já explicava o erro por GRUPO, para o professor. Esta coluna guarda a
explicação individual pedida pelo aluno em uma tentativa específica. É cache: a
geração custa dinheiro, então cada tentativa é explicada no máximo uma vez.
"""
import sqlalchemy as sa
from alembic import op

revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('submissions', sa.Column('llm_explanation', sa.Text, nullable=True))


def downgrade():
    op.drop_column('submissions', 'llm_explanation')
