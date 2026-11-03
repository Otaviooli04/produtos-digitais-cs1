"""acessos do aluno e origem da matrícula

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-29

A retenção passa a ser medida pela abertura do app, e não só pelo envio. Cada
abertura vira uma linha em `acessos`, com a origem que veio no link. A matrícula
ganha a origem da entrada (convite ou código), nula nas que já existem.
"""
import sqlalchemy as sa
from alembic import op

revision = '0018'
down_revision = '0017'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'acessos',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('student_id', sa.Integer, sa.ForeignKey('students.id'), nullable=False),
        sa.Column('momento', sa.DateTime, nullable=False),
        sa.Column('via', sa.String(32), nullable=True),
    )
    op.create_index('ix_acessos_student_id_momento', 'acessos', ['student_id', 'momento'])
    op.add_column('enrollments', sa.Column('origem', sa.String(16), nullable=True))


def downgrade():
    op.drop_column('enrollments', 'origem')
    op.drop_index('ix_acessos_student_id_momento', table_name='acessos')
    op.drop_table('acessos')
