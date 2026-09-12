"""trilha de treino: exercícios gerados para o erro que o aluno repete

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-12

O painel de erros recorrentes já dizia ao aluno o que ele repete. O que faltava
era o que fazer com isso. A trilha gera exercício sob medida para a categoria
que ele mais erra, e o treino ali é ilimitado.

Tabelas próprias, separadas de `questions` e `submissions`, de propósito: o
gerado nunca vale nota, não entra na análise da turma e não aparece no painel do
professor. Misturar com a prova apagaria essa fronteira.
"""
import sqlalchemy as sa
from alembic import op

revision = '0016'
down_revision = '0015'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'exercicios_gerados',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('student_id', sa.Integer, sa.ForeignKey('students.id'), nullable=False, index=True),
        sa.Column('error_category', sa.String, nullable=False, index=True),
        sa.Column('titulo', sa.String, nullable=False),
        sa.Column('enunciado', sa.Text, nullable=False),
        sa.Column('casos_teste', sa.JSON, nullable=False),
        sa.Column('required_structures', sa.JSON, nullable=True),
        sa.Column('resolvido', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('reportado', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('reportado_motivo', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
    )
    op.create_table(
        'tentativas_de_treino',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('exercicio_id', sa.Integer, sa.ForeignKey('exercicios_gerados.id'),
                  nullable=False, index=True),
        sa.Column('student_id', sa.Integer, sa.ForeignKey('students.id'), nullable=False, index=True),
        sa.Column('code', sa.Text, nullable=False),
        sa.Column('compile_error', sa.Text, nullable=True),
        sa.Column('warnings', sa.Text, nullable=True),
        sa.Column('all_tests_passed', sa.Boolean, nullable=True),
        sa.Column('error_category', sa.String, nullable=True),
        sa.Column('pedagogical_diagnosis', sa.Text, nullable=True),
        sa.Column('actionable_feedback', sa.Text, nullable=True),
        sa.Column('test_results', sa.JSON, nullable=True),
        sa.Column('attempt_number', sa.Integer, nullable=False, server_default='1'),
        sa.Column('submitted_at', sa.DateTime, nullable=True),
    )


def downgrade():
    op.drop_table('tentativas_de_treino')
    op.drop_table('exercicios_gerados')
