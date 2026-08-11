"""question points — valor (peso) da questão na nota da prova

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-20

A coluna `questions.points` foi introduzida no modelo sem migration; em bancos
existentes ela já está presente (criada fora do alembic), mas um banco novo
montado pela cadeia de migrations ficaria sem ela. Esta migration é idempotente:
só adiciona/remove quando o estado diverge, então é segura tanto no banco já
carimbado quanto num banco do zero.
"""
import sqlalchemy as sa
from alembic import context, op

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def _has_points(bind) -> bool:
    return 'points' in {c['name'] for c in sa.inspect(bind).get_columns('questions')}


def upgrade():
    # Offline (--sql): sem conexão p/ inspecionar — emite o ADD direto (banco novo).
    # Online: só adiciona se a coluna ainda não existe (banco já carimbado).
    if context.is_offline_mode() or not _has_points(op.get_bind()):
        op.add_column(
            'questions',
            sa.Column('points', sa.Float, server_default='1.0'),
        )


def downgrade():
    if context.is_offline_mode() or _has_points(op.get_bind()):
        op.drop_column('questions', 'points')
