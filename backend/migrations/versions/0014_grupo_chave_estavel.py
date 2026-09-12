"""identidade estável do grupo e carimbo do último agrupamento

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-12

`cluster_label` é um contador posicional: ele depende da ordem em que as
submissões entram e do tamanho de cada categoria, então re-agrupar renumera os
grupos. Enquanto re-agrupar apagava tudo isso era só perda do insight. A partir
do momento em que o grupo passa a guardar texto que o professor escreveu, o
label deixa de servir como identidade, porque a resposta migraria para o grupo
errado.

`chave` é a identidade real do grupo, a mesma coisa que o define: a categoria de
erro e a assinatura de falha. Ela sobrevive a re-agrupamento.

`atualizado_em` diz quando o grupo foi formado pela última vez, para a tela
saber se chegou submissão depois disso.
"""
import sqlalchemy as sa
from alembic import op

revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('question_clusters', sa.Column('chave', sa.String, nullable=True))
    op.add_column('question_clusters', sa.Column('atualizado_em', sa.DateTime, nullable=True))
    op.create_index(
        'ix_question_clusters_question_chave',
        'question_clusters', ['question_id', 'chave'])


def downgrade():
    op.drop_index('ix_question_clusters_question_chave', table_name='question_clusters')
    op.drop_column('question_clusters', 'atualizado_em')
    op.drop_column('question_clusters', 'chave')
