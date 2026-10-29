"""tamanho da turma informado pelo professor

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-26

O funil da turma compara quem entrou com quem deveria entrar. O sistema só
conhece o primeiro número. O segundo vem do professor, é opcional e fica nulo
nas turmas que já existem.
"""
import sqlalchemy as sa
from alembic import op

revision = '0017'
down_revision = '0016'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('turmas', sa.Column('alunos_previstos', sa.Integer, nullable=True))


def downgrade():
    op.drop_column('turmas', 'alunos_previstos')
