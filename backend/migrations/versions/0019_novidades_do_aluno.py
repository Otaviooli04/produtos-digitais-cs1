"""novidades do aluno

Revision ID: 0019
Revises: 0018
Create Date: 2026-11-04

O Início do aluno mostra o que chegou para ele e ele ainda não abriu: a resposta
do professor ao erro dele e o exercício da trilha pronto antes de ele pedir. Cada
novidade guarda quando chegou e quando foi vista, que é o dado do experimento 1
do Plano de Growth. Tabela nova e vazia, nada do que já existe muda.
"""
import sqlalchemy as sa
from alembic import op

revision = '0019'
down_revision = '0018'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'novidades',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('student_id', sa.Integer, sa.ForeignKey('students.id'), nullable=False),
        sa.Column('tipo', sa.String(16), nullable=False),
        sa.Column('question_id', sa.Integer, sa.ForeignKey('questions.id'), nullable=True),
        sa.Column('grupo_chave', sa.String, nullable=True),
        sa.Column('exercicio_id', sa.Integer, sa.ForeignKey('exercicios_gerados.id'),
                  nullable=True),
        sa.Column('chegou_em', sa.DateTime, nullable=False),
        sa.Column('vista_em', sa.DateTime, nullable=True),
    )
    op.create_index('ix_novidades_student_id', 'novidades', ['student_id'])
    op.create_index('ix_novidades_question_id', 'novidades', ['question_id'])
    op.create_index(
        'uq_novidade_retorno_aberta', 'novidades',
        ['student_id', 'question_id', 'grupo_chave'], unique=True,
        postgresql_where=sa.text("tipo = 'retorno' AND vista_em IS NULL"))
    op.create_index(
        'uq_novidade_exercicio_aberta', 'novidades',
        ['student_id', 'exercicio_id'], unique=True,
        postgresql_where=sa.text("tipo = 'exercicio' AND vista_em IS NULL"))


def downgrade():
    op.drop_index('uq_novidade_exercicio_aberta', table_name='novidades')
    op.drop_index('uq_novidade_retorno_aberta', table_name='novidades')
    op.drop_index('ix_novidades_question_id', table_name='novidades')
    op.drop_index('ix_novidades_student_id', table_name='novidades')
    op.drop_table('novidades')
