"""resposta que o professor escreve para o grupo inteiro

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-12

O grupo já guardava o `insight`, que é o texto que o Gemini escreve PARA o
professor e nunca sai do painel dele. Esta é a outra ponta: o que o professor
escreve uma vez e chega a todo mundo que errou daquele jeito.

São campos separados de propósito. Um é máquina, outro é pessoa, e a diferença
entre os dois é parte do que o produto promete.

A resposta se ancora na `chave` do grupo, que a revisão 0014 criou, então
re-agrupar não faz ela migrar para o grupo errado.
"""
import sqlalchemy as sa
from alembic import op

revision = '0015'
down_revision = '0014'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('question_clusters', sa.Column('resposta_professor', sa.Text, nullable=True))
    op.add_column('question_clusters', sa.Column('resposta_em', sa.DateTime, nullable=True))
    op.add_column('question_clusters', sa.Column(
        'resposta_por', sa.Integer, sa.ForeignKey('professors.id'), nullable=True))


def downgrade():
    op.drop_column('question_clusters', 'resposta_por')
    op.drop_column('question_clusters', 'resposta_em')
    op.drop_column('question_clusters', 'resposta_professor')
