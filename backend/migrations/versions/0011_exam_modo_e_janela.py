"""modo treino/prova, janela de disponibilidade e limite de tentativas na atividade

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-17

Até aqui toda prova era implicitamente uma prova: aberta o tempo todo e sem
limite de tentativas, porque o aluno só submetia pelo link público. Com a conta
do aluno a atividade precisa dizer o que ela é. `modo='treino'` libera tentativas
ilimitadas fora da semana de prova, `modo='prova'` respeita a janela e o teto de
tentativas definidos pelo professor. Provas já existentes viram 'prova' sem
janela, que é exatamente o comportamento atual.
"""
import sqlalchemy as sa
from alembic import op

revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('exams', sa.Column('modo', sa.String, server_default='prova'))
    op.add_column('exams', sa.Column('abre_em', sa.DateTime, nullable=True))
    op.add_column('exams', sa.Column('fecha_em', sa.DateTime, nullable=True))
    op.add_column('exams', sa.Column('max_tentativas', sa.Integer, nullable=True))


def downgrade():
    op.drop_column('exams', 'max_tentativas')
    op.drop_column('exams', 'fecha_em')
    op.drop_column('exams', 'abre_em')
    op.drop_column('exams', 'modo')
