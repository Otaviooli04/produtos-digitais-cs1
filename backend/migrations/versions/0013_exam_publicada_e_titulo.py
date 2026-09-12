"""publicação da atividade e título próprio, separado do nome do arquivo

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-12

Até aqui toda atividade da turma aparecia para o aluno no instante em que era
criada, com as questões que o extrator acabou de produzir e o professor ainda
não revisou. `publicada` é o portão que faltava. Atividades existentes nascem
publicadas, porque já estavam visíveis e sumir delas seria a mudança errada.

`titulo` separa o que a atividade é ("Lista 3 · Vetores e laços") do arquivo de
onde ela saiu ("prova1_2026.pdf"), que era o único nome que o aluno via.
"""
import sqlalchemy as sa
from alembic import op

revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade():
    # server_default='true' preenche as linhas que já existem. Logo depois o
    # default vira 'false', então atividade nova nasce rascunho.
    op.add_column('exams', sa.Column(
        'publicada', sa.Boolean, nullable=False, server_default=sa.text('true')))
    op.alter_column('exams', 'publicada', server_default=sa.text('false'))
    op.add_column('exams', sa.Column('titulo', sa.String, nullable=True))


def downgrade():
    op.drop_column('exams', 'titulo')
    op.drop_column('exams', 'publicada')
