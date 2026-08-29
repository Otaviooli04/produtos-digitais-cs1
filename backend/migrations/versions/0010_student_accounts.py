"""conta do aluno — students, enrollments, vínculo nas submissões e código de acesso da turma

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-12

Abre o lado do aluno: antes ele era apenas a string `submissions.matricula`.
A coluna `matricula` continua existindo e serve de ponte — as submissões antigas
ficam com `student_id` nulo e são religadas quando o aluno criar a conta.
"""
import random
import string

import sqlalchemy as sa
from alembic import context, op

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None

# Alfabeto sem caracteres ambíguos (O/0, I/1), porque o código é ditado em sala.
_ALFABETO = ''.join(c for c in string.ascii_uppercase + string.digits if c not in 'O0I1')
_TAMANHO_CODIGO = 6


def _gerar_codigo(usados: set[str]) -> str:
    while True:
        codigo = ''.join(random.choices(_ALFABETO, k=_TAMANHO_CODIGO))
        if codigo not in usados:
            usados.add(codigo)
            return codigo


def upgrade():
    op.create_table(
        'students',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String, nullable=False, unique=True),
        sa.Column('nome', sa.String, nullable=False),
        sa.Column('matricula', sa.String, nullable=True),
        sa.Column('senha_hash', sa.String, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_students_email', 'students', ['email'])
    op.create_index('ix_students_matricula', 'students', ['matricula'])

    op.create_table(
        'enrollments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('student_id', sa.Integer, sa.ForeignKey('students.id'), nullable=False),
        sa.Column('turma_id', sa.Integer, sa.ForeignKey('turmas.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.UniqueConstraint('student_id', 'turma_id', name='uq_enrollment_student_turma'),
    )
    op.create_index('ix_enrollments_student_id', 'enrollments', ['student_id'])
    op.create_index('ix_enrollments_turma_id', 'enrollments', ['turma_id'])

    op.add_column('submissions', sa.Column('student_id', sa.Integer, sa.ForeignKey('students.id'), nullable=True))
    op.create_index('ix_submissions_student_id', 'submissions', ['student_id'])
    op.add_column('submissions', sa.Column('attempt_number', sa.Integer, server_default='1'))

    op.add_column('turmas', sa.Column('codigo_acesso', sa.String, nullable=True))

    if not context.is_offline_mode():
        bind = op.get_bind()

        # Numera as tentativas já existentes por (questão, matrícula) na ordem de envio.
        bind.execute(sa.text("""
            WITH numeradas AS (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY question_id, matricula ORDER BY submitted_at, id
                ) AS n
                FROM submissions
                WHERE matricula IS NOT NULL
            )
            UPDATE submissions SET attempt_number = numeradas.n
            FROM numeradas WHERE submissions.id = numeradas.id
        """))

        usados: set[str] = set()
        for (turma_id,) in bind.execute(sa.text("SELECT id FROM turmas ORDER BY id")):
            bind.execute(
                sa.text("UPDATE turmas SET codigo_acesso = :codigo WHERE id = :id"),
                {"codigo": _gerar_codigo(usados), "id": turma_id},
            )

    op.create_index('ix_turmas_codigo_acesso', 'turmas', ['codigo_acesso'], unique=True)


def downgrade():
    op.drop_index('ix_turmas_codigo_acesso', table_name='turmas')
    op.drop_column('turmas', 'codigo_acesso')

    op.drop_column('submissions', 'attempt_number')
    op.drop_index('ix_submissions_student_id', table_name='submissions')
    op.drop_column('submissions', 'student_id')

    op.drop_index('ix_enrollments_turma_id', table_name='enrollments')
    op.drop_index('ix_enrollments_student_id', table_name='enrollments')
    op.drop_table('enrollments')

    op.drop_index('ix_students_matricula', table_name='students')
    op.drop_index('ix_students_email', table_name='students')
    op.drop_table('students')
