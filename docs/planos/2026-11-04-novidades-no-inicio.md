# Novidades no Início do aluno: plano de implementação

> **Para quem executa:** usar a skill `sdd` (recomendado) ou a execução sem subagentes descrita nela. Passos com caixa de seleção (`- [ ]`).

**Objetivo:** o aluno abre o app num Início com as novidades que chegaram para ele (resposta do professor e exercício pronto na trilha), onde ele parou e o que vence logo, e cada novidade fica gravada com `chegou_em` e `vista_em`.

**Arquitetura:** uma tabela nova (`novidades`, migração 0019) e um serviço que é o único a gravar e ler nela (`novidades_service`), chamado por ganchos de uma linha na rota da resposta do professor, na tela da questão e na trilha. Um segundo serviço (`inicio_service`) monta o painel sem gravar nada, com a regra em funções puras sobre o histórico unificado (`ler_historico`). No front, uma página nova de Início e a bolinha no menu do `AlunoLayout`.

**Stack:** FastAPI, SQLAlchemy 2.0 (`insert ... on_conflict_do_nothing` do dialeto PostgreSQL), Alembic, pytest, React 19, React Router, Tailwind v4.

**Spec:** `docs/specs/2026-11-04-novidades-no-inicio.md`

## Restrições globais

- Migração `0019`, `down_revision = '0018'`. Só cria a tabela `novidades`. Nenhuma tabela existente muda, então o banco de teste não precisa de `ALTER TABLE` (o `create_all` do `conftest.py` cria a tabela nova).
- Colunas de `novidades`: `id`, `student_id` (FK `students.id`, obrigatório), `tipo` (`String(16)`, obrigatório), `question_id` (FK `questions.id`, opcional), `grupo_chave` (`String`, opcional), `exercicio_id` (FK `exercicios_gerados.id`, opcional), `chegou_em` (`DateTime`, obrigatório), `vista_em` (`DateTime`, opcional).
- Índices únicos parciais: `uq_novidade_retorno_aberta` em `(student_id, question_id, grupo_chave)` onde `tipo = 'retorno' AND vista_em IS NULL`, e `uq_novidade_exercicio_aberta` em `(student_id, exercicio_id)` onde `tipo = 'exercicio' AND vista_em IS NULL`.
- Tipos: `"retorno"` e `"exercicio"` (constantes `Novidade.TIPO_RETORNO` e `Novidade.TIPO_EXERCICIO`).
- Título da questão em novidade e no cartão de continuar: `f"Questão {questao.number} · {titulo_da_atividade(exam)}"`.
- `JANELA_DO_PRAZO = timedelta(days=7)` em `inicio_service`. A janela de abertura é `ANTECEDENCIA_DA_PROVA` (3 dias), importada de `app.services.funil_regras`.
- Textos que o aluno vê: "Seu professor respondeu ao seu erro", "Exercício novo pronto na trilha", "Continuar de onde parou", "Próxima atividade", "Continuar", "Começar", "Prazos próximos", "Tudo em dia. Que tal treinar?", "Comece entrando na sua turma".
- Falha ao gravar ou marcar novidade vai para o log com `rollback` e nunca derruba a rota (`_sem_derrubar` em `novidades_service`).
- Datas saem em ISO e em UTC (`.isoformat()` de `datetime` sem fuso), como no resto da API.
- RN07: nada fala de grupo para o aluno. RN01: sem ponto, sequência ou sorteio. RN04: nada sai do app. RNF04: cada aluno só lê as próprias novidades e o professor não vê quem leu.
- Testes: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q`. Nunca `rtk pytest`. Uma suíte por vez (o banco de teste é um só).
- Git dentro do worktree: `/usr/bin/git`, um comando por chamada, a partir da raiz do worktree. O `git` puro vira `rtk git` pelo gancho e a trava do worktree recusa.
- Lint do front: `cd frontend && rtk proxy ./node_modules/.bin/eslint .` (a base tem 4 erros antigos em `QuestionPage.jsx` e `TestCasesPage.jsx`, só erro novo bloqueia). O `npx eslint` pegou um ESLint errado neste worktree.
- Base: 404 testes. Final esperado: 467.

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/models/orm.py` (alterar) | Modelo `Novidade` com os dois índices parciais |
| `backend/migrations/versions/0019_novidades_do_aluno.py` (criar) | Cria a tabela e os índices |
| `backend/app/services/novidades_service.py` (criar) | Único que grava e lê `novidades`: registrar resposta e exercício, marcar visto, listar as que valem, contar |
| `backend/app/services/inicio_service.py` (criar) | Regras puras do continuar, da próxima atividade e dos prazos, e o `painel` |
| `backend/app/api/routes/exam.py` (alterar) | `put_resposta_do_grupo` chama `registrar_resposta` |
| `backend/app/services/exam_service.py` (alterar) | `_delete_questions` apaga as novidades das questões |
| `backend/app/services/student_activity_service.py` (alterar) | `resposta_do_grupo` devolve a chave, `historico_questao` e `submeter` marcam a resposta como vista |
| `backend/app/services/treino_service.py` (alterar) | A pré-geração registra o exercício, e `detalhe`, `treinar` e o pendente de `gerar_para_categoria` marcam como visto |
| `backend/app/models/schemas.py` (alterar) | `NovidadeItem`, `ContinuarItem`, `PrazoItem`, `InicioResponse`, `ContagemNovidadesResponse` |
| `backend/app/api/routes/student_activity.py` (alterar) | `GET /aluno/inicio` e `GET /aluno/novidades/contagem` |
| `backend/tests/test_novidades.py` (criar) | Tabela, serviço de novidades e ganchos da lista e do professor |
| `backend/tests/test_treino.py` (alterar) | Ganchos da trilha |
| `backend/tests/test_inicio.py` (criar) | Regras puras, painel e rotas |
| `frontend/src/components/EntrarNaTurma.jsx` (criar) | Formulário do código da turma, saído da `TurmasPage` |
| `frontend/src/pages/aluno/TurmasPage.jsx` (alterar) | Passa a importar `EntrarNaTurma` |
| `frontend/src/pages/aluno/InicioPage.jsx` (criar) | Página do Início |
| `frontend/src/api/aluno.js` (alterar) | `getInicio()` e `contarNovidades()` |
| `frontend/src/utils/datas.js` (alterar) | `prazoRelativo(iso, agora)` |
| `frontend/src/App.jsx` (alterar) | `/aluno` abre o Início |
| `frontend/src/components/AlunoLayout.jsx` (alterar) | Link "Início" com a bolinha |

## Lotes

- Lote A, Tasks 1 a 3: tabela, migração e serviço de novidades (backend, dados e serviço)
- Lote B, Tasks 4 a 6: ganchos do professor, da exclusão, da tela da questão e da trilha (backend, serviços existentes)
- Lote C, Tasks 7 e 8: regras do Início, painel, esquemas e rotas (backend)
- Lote D, Tasks 9 e 10: página do Início e bolinha no menu (frontend)

## Varredura

### Pares que dividem arquivo ou interface

| Par | O que uma produz x o que a outra consome | Situação |
|---|---|---|
| T1 → T2 | modelo `Novidade` (`TIPO_RETORNO`, `TIPO_EXERCICIO`, colunas e índices) usado por `_gravar`, `_registrar_resposta` e `_marcar` | bate |
| T1 → T3 | `Novidade.chegou_em`, `vista_em`, `question_id`, `grupo_chave`, `exercicio_id` lidos por `novidades_do_aluno` | bate |
| T2 x T3 | as duas mexem em `novidades_service.py`. T2 cria o arquivo e T3 troca a linha de import do orm (acrescenta `Student`) e acrescenta funções no fim | sem conflito |
| T2 x T3 (testes) | as duas mexem em `test_novidades.py`. T3 troca a linha `from app.services.novidades_service import (...)` e acrescenta uma classe no fim | sem conflito |
| T2 → T4 | `registrar_resposta(grupo, db)` chamada pela rota, e `_alcancados` substituída no teste de falha | bate |
| T2 → T5 | `marcar_resposta_vista(student_id, question_id, chave, db)` chamada por `_marcar_resposta_vista`, e `_marcar` substituída nos testes de falha | bate |
| T2 → T6 | `registrar_exercicio(exercicio, db)` e `marcar_exercicio_visto(student_id, exercicio_id, db)` chamadas pela trilha | bate |
| T4 x T5 (testes) | as duas acrescentam classes em `test_novidades.py`. T5 acrescenta um import no topo | sem conflito |
| T5 x T8 | T5 mexe em `student_activity_service.py`. T8 importa `titulo_da_atividade` dele, que não muda | sem conflito |
| T3 → T8 | `novidades_do_aluno(student, db)` e `contar(student, db)` usadas por `painel` e pela rota de contagem | bate |
| T7 → T8 | `ItemDisponivel`, `AtividadeDoPainel`, `escolher_continuar`, `proxima_atividade`, `prazos_proximos` usados por `painel`. T8 troca o bloco de imports do topo de `inicio_service.py` e acrescenta funções no fim | bate |
| T7 x T8 (testes) | as duas mexem em `test_inicio.py`. T8 troca o bloco de imports do topo e acrescenta fixtures e classes no fim | sem conflito |
| T8 → T9 | formato de `InicioResponse` (`tem_turma`, `novidades`, `continuar`, `prazos`) e dos itens, consumidos pela `InicioPage` | bate |
| T8 → T10 | `ContagemNovidadesResponse` (`{ "total": n }`) consumido pelo `AlunoLayout` | bate |
| T9 → T10 | `contarNovidades()` em `api/aluno.js`, criada na T9 e usada na T10 | bate |

### O teste de cada tarefa bate com o código dela?

| Tarefa | Conferência | Situação |
|---|---|---|
| T1 | 3 testes: duplicada não vista recusada pelo índice, vista libera outra, exercício com índice próprio. 404 + 3 = 407 | bate |
| T2 | 11 testes. Os valores de `chegou_em` saem de `grupo.resposta_em` (AGORA) e de `exercicio.created_at` (AGORA). Editar antes de ver cai no `ON CONFLICT DO NOTHING` e mantém AGORA. 407 + 11 = 418 | bate |
| T3 | 9 testes (um parametrizado em 2). O título "Questão 1 · Lista 3" sai de `exam_factory(titulo="Lista 3")` e `titulo_da_atividade`. A ordem sai de `chegou_em desc`. 418 + 9 = 427 | bate |
| T4 | 5 testes. O de falha passa já antes do gancho (é guarda). Os 3 de exclusão falham antes com `IntegrityError` da FK. 427 + 5 = 432 | bate |
| T5 | 6 testes. Os de "sem resposta" e os 2 de falha passam antes do gancho (guardas). O envio real usa `cluster_question` com 3 envios "Saída Incorreta" (menos de 6, chave `cat:Saída Incorreta`). 432 + 6 = 438 | bate |
| T6 | 5 testes em `test_treino.py`. O de "pedido na hora" passa antes do gancho (guarda). O pendente sai de `_categorias` com off-by-one como mais frequente na fixture `erros_do_aluno`. 438 + 5 = 443 | bate |
| T7 | 14 testes de funções puras. Contas conferidas à mão em cada caso (ver comentários dos testes). 443 + 14 = 457 | bate |
| T8 | 10 testes (2 parametrizados em 2). `turma_nome` "Turma Teste" e `modo` "prova" saem da `exam_factory` e do padrão da coluna. 457 + 10 = 467 | bate |
| T9 | front sem suíte: lint sem erro novo e build ok. Conferência no smoke do `fechamento` | bate |
| T10 | idem | bate |

---

### Task 1: Modelo `Novidade` e migração 0019

**Arquivos:**
- Alterar: `backend/app/models/orm.py:1-5` (import) e fim do arquivo (classe nova depois de `TentativaDeTreino`)
- Criar: `backend/migrations/versions/0019_novidades_do_aluno.py`
- Teste: `backend/tests/test_novidades.py` (criar)

**Interfaces:**
- Consome: nada de tarefas anteriores.
- Produz: `app.models.orm.Novidade` com `TIPO_RETORNO = "retorno"`, `TIPO_EXERCICIO = "exercicio"` e as colunas `id`, `student_id`, `tipo`, `question_id`, `grupo_chave`, `exercicio_id`, `chegou_em`, `vista_em`. Os helpers de teste `prova`, `aluno`, `colega`, `_matricular`, `_questao`, `_envio`, `_grupo`, `_exercicio`, `_novidade`, `AGORA`, `CHAVE`, `OUTRA_CHAVE` em `tests/test_novidades.py`, usados pelas Tasks 2 a 5.

- [ ] **Passo 1: escrever o teste que falha**

Criar `backend/tests/test_novidades.py`:

```python
"""Novidades do aluno: o que chegou para ele e ele ainda não abriu.

A resposta do professor vira novidade para quem tem a tentativa mais recente no
grupo, e o exercício pré-gerado da trilha também. A tela que entrega a resposta
ou o exercício marca como vista, e a leitura só mostra a que ainda vale."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.orm import (
    Enrollment, ExercicioGerado, Novidade, QuestionCluster, Student, Submission,
)

AGORA = datetime(2026, 11, 4, 12, 0)
CHAVE = "cat:Saída Incorreta"
OUTRA_CHAVE = "cat:Tudo no Main"


@pytest.fixture()
def prova(exam_factory):
    return exam_factory(questions=[{"number": "1"}, {"number": "2"}], titulo="Lista 3")


def _matricular(db, nome, email, turma_id):
    s = Student(email=email, nome=nome, senha_hash="x")
    db.add(s)
    db.flush()
    db.add(Enrollment(student_id=s.id, turma_id=turma_id))
    db.commit()
    db.refresh(s)
    return s


@pytest.fixture()
def aluno(db, prova):
    return _matricular(db, "Ana", "ana@teste.com", prova.turma_id)


@pytest.fixture()
def colega(db, prova):
    return _matricular(db, "Bia", "bia@teste.com", prova.turma_id)


def _questao(prova, numero="1"):
    return next(q for q in prova.questions if q.number == numero)


def _envio(db, questao, student_id, tentativa, cluster_id, categoria="Saída Incorreta"):
    sub = Submission(
        question_id=questao.id, code="int main(){}", error_category=categoria,
        all_tests_passed=False, student_id=student_id, attempt_number=tentativa,
        cluster_id=cluster_id, submitted_at=AGORA - timedelta(hours=1),
    )
    db.add(sub)
    db.commit()
    return sub


def _grupo(db, questao, label=0, chave=CHAVE, resposta="Revejam a condição de parada.",
           em=AGORA):
    grupo = QuestionCluster(
        question_id=questao.id, cluster_label=label, chave=chave, size=1,
        dominant_error="Saída Incorreta", resposta_professor=resposta, resposta_em=em,
    )
    db.add(grupo)
    db.commit()
    db.refresh(grupo)
    return grupo


def _exercicio(db, student_id, resolvido=False, reportado=False, titulo="Soma dos pares"):
    exercicio = ExercicioGerado(
        student_id=student_id, error_category="Tudo no Main", titulo=titulo,
        enunciado="Some os pares.", casos_teste=[], resolvido=resolvido,
        reportado=reportado, created_at=AGORA,
    )
    db.add(exercicio)
    db.commit()
    db.refresh(exercicio)
    return exercicio


def _novidade(db, student_id, questao=None, chave=CHAVE, exercicio=None, chegou_em=AGORA,
              vista_em=None):
    novidade = Novidade(
        student_id=student_id,
        tipo="exercicio" if exercicio else "retorno",
        question_id=None if exercicio else questao.id,
        grupo_chave=None if exercicio else chave,
        exercicio_id=exercicio.id if exercicio else None,
        chegou_em=chegou_em,
        vista_em=vista_em,
    )
    db.add(novidade)
    db.commit()
    db.refresh(novidade)
    return novidade


class TestTabela:
    def test_duas_nao_vistas_do_mesmo_grupo_sao_recusadas(self, db, aluno, prova):
        _novidade(db, aluno.id, _questao(prova))
        db.add(Novidade(student_id=aluno.id, tipo="retorno", question_id=_questao(prova).id,
                        grupo_chave=CHAVE, chegou_em=AGORA))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_depois_de_vista_aceita_outra_do_mesmo_grupo(self, db, aluno, prova):
        _novidade(db, aluno.id, _questao(prova), vista_em=AGORA)
        _novidade(db, aluno.id, _questao(prova), chegou_em=AGORA + timedelta(hours=1))
        assert db.query(Novidade).count() == 2

    def test_exercicio_nao_visto_e_um_so_por_exercicio(self, db, aluno):
        exercicio = _exercicio(db, aluno.id)
        _novidade(db, aluno.id, exercicio=exercicio)
        db.add(Novidade(student_id=aluno.id, tipo="exercicio", exercicio_id=exercicio.id,
                        chegou_em=AGORA))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_novidades.py -q`
Esperado: FALHA na coleta com `ImportError: cannot import name 'Novidade'`

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/models/orm.py`, trocar o import do topo:

```python
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float, Index,
    UniqueConstraint,
)
```

por:

```python
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float, Index,
    UniqueConstraint, text,
)
```

No fim de `backend/app/models/orm.py`, depois da classe `TentativaDeTreino`, acrescentar:

```python


class Novidade(Base):
    """O que chegou para o aluno e ele ainda não abriu: a resposta do professor
    ao erro dele ou um exercício da trilha pronto antes de ele pedir.

    `chegou_em` e `vista_em` são o dado do experimento 1 do Plano de Growth. A
    linha que deixa de valer (o aluno corrigiu o erro antes de abrir) não é
    apagada, porque foi isso que aconteceu: chegou e não foi vista. No retorno,
    o grupo é guardado pela `chave`, que vale mesmo depois de os grupos serem
    refeitos ou de a linha do grupo ser apagada."""
    __tablename__ = "novidades"
    __table_args__ = (
        Index("uq_novidade_retorno_aberta", "student_id", "question_id", "grupo_chave",
              unique=True,
              postgresql_where=text("tipo = 'retorno' AND vista_em IS NULL")),
        Index("uq_novidade_exercicio_aberta", "student_id", "exercicio_id",
              unique=True,
              postgresql_where=text("tipo = 'exercicio' AND vista_em IS NULL")),
    )

    TIPO_RETORNO = "retorno"
    TIPO_EXERCICIO = "exercicio"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    tipo = Column(String(16), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    grupo_chave = Column(String, nullable=True)
    exercicio_id = Column(Integer, ForeignKey("exercicios_gerados.id"), nullable=True)
    chegou_em = Column(DateTime, nullable=False)
    vista_em = Column(DateTime, nullable=True)
```

Criar `backend/migrations/versions/0019_novidades_do_aluno.py`:

```python
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
```

Os índices de `student_id` e `question_id` vão por `create_index` explícito, sem `index=True` na coluna, porque o `create_table` do Alembic já cria o índice de toda coluna com `index=True` e o explícito daria nome repetido. O `index=True` do `id` fica, como na 0018, para casar com o `ix_novidades_id` que o ORM cria.

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: `3 passed`

Depois a suíte inteira: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q`
Esperado: `407 passed`

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/models/orm.py backend/migrations/versions/0019_novidades_do_aluno.py backend/tests/test_novidades.py
```
```bash
/usr/bin/git commit -m "feat(novidades): tabela de novidades do aluno na migracao 0019"
```

---

### Task 2: Registro das novidades e marcação de visto

**Arquivos:**
- Criar: `backend/app/services/novidades_service.py`
- Teste: `backend/tests/test_novidades.py` (acrescentar import e classes no fim)

**Interfaces:**
- Consome: `Novidade` da Task 1 e os helpers de teste da Task 1.
- Produz, em `app.services.novidades_service`:
  - `RETORNO = "retorno"`, `EXERCICIO = "exercicio"`
  - `registrar_resposta(grupo: QuestionCluster, db: Session) -> None`
  - `registrar_exercicio(exercicio: ExercicioGerado, db: Session) -> None`
  - `marcar_resposta_vista(student_id: int, question_id: int, chave: str | None, db: Session, agora: datetime | None = None) -> None`
  - `marcar_exercicio_visto(student_id: int, exercicio_id: int, db: Session, agora: datetime | None = None) -> None`
  - internas usadas nos testes de falha das Tasks 4 e 5: `_alcancados(question_id, cluster_label, db)` e `_marcar(filtros, db, agora)`

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/test_novidades.py`, acrescentar ao bloco de imports do topo, depois de `from app.models.orm import (...)`:

```python
from app.services.novidades_service import (
    marcar_exercicio_visto, marcar_resposta_vista, registrar_exercicio, registrar_resposta,
)
```

No fim do arquivo, acrescentar:

```python


class TestNascimento:
    def test_resposta_cria_para_quem_tem_a_tentativa_mais_recente_no_grupo(
        self, db, aluno, colega, prova
    ):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        _envio(db, q, colega.id, 1, cluster_id=0)
        registrar_resposta(_grupo(db, q), db)
        novidades = db.query(Novidade).order_by(Novidade.student_id).all()
        assert [n.student_id for n in novidades] == sorted([aluno.id, colega.id])
        assert all(n.tipo == "retorno" for n in novidades)
        assert all(n.question_id == q.id and n.grupo_chave == CHAVE for n in novidades)
        assert all(n.chegou_em == AGORA and n.vista_em is None for n in novidades)

    def test_tentativa_antiga_no_grupo_nao_basta(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        _envio(db, q, aluno.id, 2, cluster_id=1, categoria="Tudo no Main")
        registrar_resposta(_grupo(db, q), db)
        assert db.query(Novidade).count() == 0

    def test_envio_sem_conta_nao_cria(self, db, prova):
        q = _questao(prova)
        _envio(db, q, None, 1, cluster_id=0)
        registrar_resposta(_grupo(db, q), db)
        assert db.query(Novidade).count() == 0

    def test_atividade_nao_publicada_nao_cria(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        prova.publicada = False
        db.commit()
        registrar_resposta(_grupo(db, q), db)
        assert db.query(Novidade).count() == 0

    def test_grupo_sem_chave_nao_cria(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        registrar_resposta(_grupo(db, q, chave=None), db)
        assert db.query(Novidade).count() == 0

    def test_editar_antes_de_ver_nao_duplica(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        grupo = _grupo(db, q)
        registrar_resposta(grupo, db)
        grupo.resposta_professor = "Texto corrigido."
        grupo.resposta_em = AGORA + timedelta(hours=1)
        db.commit()
        registrar_resposta(grupo, db)
        (novidade,) = db.query(Novidade).all()
        assert novidade.chegou_em == AGORA

    def test_editar_depois_de_ver_cria_outra(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        grupo = _grupo(db, q)
        registrar_resposta(grupo, db)
        marcar_resposta_vista(aluno.id, q.id, CHAVE, db, agora=AGORA + timedelta(minutes=5))
        grupo.resposta_professor = "Texto corrigido."
        grupo.resposta_em = AGORA + timedelta(hours=1)
        db.commit()
        registrar_resposta(grupo, db)
        novidades = db.query(Novidade).order_by(Novidade.chegou_em).all()
        assert [n.chegou_em for n in novidades] == [AGORA, AGORA + timedelta(hours=1)]
        assert novidades[0].vista_em == AGORA + timedelta(minutes=5)
        assert novidades[1].vista_em is None

    def test_apagar_a_resposta_remove_so_as_nao_vistas(self, db, aluno, colega, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        _envio(db, q, colega.id, 1, cluster_id=0)
        grupo = _grupo(db, q)
        registrar_resposta(grupo, db)
        marcar_resposta_vista(aluno.id, q.id, CHAVE, db, agora=AGORA)
        grupo.resposta_professor = None
        grupo.resposta_em = None
        db.commit()
        registrar_resposta(grupo, db)
        (ficou,) = db.query(Novidade).all()
        assert ficou.student_id == aluno.id
        assert ficou.vista_em == AGORA

    def test_exercicio_gravado_duas_vezes_fica_um(self, db, aluno):
        exercicio = _exercicio(db, aluno.id)
        registrar_exercicio(exercicio, db)
        registrar_exercicio(exercicio, db)
        (novidade,) = db.query(Novidade).all()
        assert novidade.tipo == "exercicio"
        assert novidade.exercicio_id == exercicio.id
        assert novidade.chegou_em == AGORA


class TestMarcarComoVista:
    def test_marcar_a_resposta_so_mexe_no_grupo_dela(self, db, aluno, prova):
        q = _questao(prova)
        _novidade(db, aluno.id, q, chave=CHAVE)
        _novidade(db, aluno.id, q, chave=OUTRA_CHAVE)
        marcar_resposta_vista(aluno.id, q.id, CHAVE, db, agora=AGORA)
        vistas = {n.grupo_chave: n.vista_em for n in db.query(Novidade).all()}
        assert vistas == {CHAVE: AGORA, OUTRA_CHAVE: None}

    def test_marcar_o_exercicio_preenche_vista_em(self, db, aluno):
        exercicio = _exercicio(db, aluno.id)
        _novidade(db, aluno.id, exercicio=exercicio)
        marcar_exercicio_visto(aluno.id, exercicio.id, db, agora=AGORA)
        assert db.query(Novidade).one().vista_em == AGORA
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_novidades.py -q`
Esperado: FALHA na coleta com `ModuleNotFoundError: No module named 'app.services.novidades_service'`

- [ ] **Passo 3: escrever o mínimo para passar**

Criar `backend/app/services/novidades_service.py`:

```python
"""Novidades do aluno: o que chegou para ele e ele ainda não abriu.

São dois tipos: a resposta do professor ao grupo do erro do aluno e o exercício
da trilha que ficou pronto antes de ele pedir. Cada novidade guarda quando
chegou e quando foi vista, que é o dado do experimento 1 do Plano de Growth.

Este módulo é o único que grava e lê a tabela. A novidade é o registro em volta
do que a rota entrega, então falha aqui vai para o log e não derruba a rota."""
import logging
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.orm import ExercicioGerado, Novidade, Question, QuestionCluster, Submission

logger = logging.getLogger(__name__)

RETORNO = Novidade.TIPO_RETORNO
EXERCICIO = Novidade.TIPO_EXERCICIO


def _sem_derrubar(acao, o_que: str, db: Session) -> None:
    """O aluno precisa do diagnóstico e o professor da resposta salva. A
    novidade vem depois, e a falha dela fica no log."""
    try:
        acao()
    except Exception:  # noqa: BLE001, a novidade é secundária ao que a rota entrega
        logger.exception("Falha ao %s", o_que)
        db.rollback()


def _gravar(linhas: list[dict], db: Session) -> None:
    """Grava ignorando a repetida: o índice único parcial deixa uma só novidade
    não vista por aluno e origem."""
    if not linhas:
        return
    db.execute(insert(Novidade).values(linhas).on_conflict_do_nothing())
    db.commit()


def _alcancados(question_id: int, cluster_label: int, db: Session) -> list[int]:
    """Alunos com conta cuja tentativa mais recente na questão está no grupo.
    É a regra da tela da questão, que só mostra a resposta na mais recente."""
    envios = (
        db.query(Submission.student_id, Submission.cluster_id)
        .filter(Submission.question_id == question_id, Submission.student_id.isnot(None))
        .order_by(Submission.attempt_number, Submission.id)
        .all()
    )
    ultimo_grupo: dict[int, int | None] = {}
    for student_id, cluster_id in envios:
        ultimo_grupo[student_id] = cluster_id
    return [s for s, grupo in ultimo_grupo.items() if grupo == cluster_label]


def _registrar_resposta(grupo: QuestionCluster, db: Session) -> None:
    if not grupo.chave:
        return
    if not grupo.resposta_professor:
        db.query(Novidade).filter(
            Novidade.tipo == RETORNO,
            Novidade.question_id == grupo.question_id,
            Novidade.grupo_chave == grupo.chave,
            Novidade.vista_em.is_(None),
        ).delete(synchronize_session=False)
        db.commit()
        return
    questao = db.get(Question, grupo.question_id)
    if not questao or not questao.exam or not questao.exam.publicada:
        return
    _gravar([
        {"student_id": student_id, "tipo": RETORNO, "question_id": grupo.question_id,
         "grupo_chave": grupo.chave, "chegou_em": grupo.resposta_em or datetime.utcnow()}
        for student_id in _alcancados(grupo.question_id, grupo.cluster_label, db)
    ], db)


def registrar_resposta(grupo: QuestionCluster, db: Session) -> None:
    """Chamado depois de o professor salvar a resposta de um grupo.

    Com texto, cria a novidade de cada aluno alcançado. Quem ainda não viu a
    anterior fica com ela, e quem já viu ganha uma nova, porque o texto mudou.
    Sem texto, a resposta foi desfeita e as novidades não vistas dela somem.
    Grupo sem `chave` é linha antiga, sem como ancorar a novidade."""
    _sem_derrubar(lambda: _registrar_resposta(grupo, db),
                  f"gravar as novidades do grupo {grupo.id}", db)


def registrar_exercicio(exercicio: ExercicioGerado, db: Session) -> None:
    """Chamado pela pré-geração da trilha. O exercício que o aluno pede e abre
    na hora não passa por aqui, porque não fica esperando por ele."""
    _sem_derrubar(lambda: _gravar([{
        "student_id": exercicio.student_id, "tipo": EXERCICIO, "exercicio_id": exercicio.id,
        "chegou_em": exercicio.created_at or datetime.utcnow(),
    }], db), f"gravar a novidade do exercício {exercicio.id}", db)


def _marcar(filtros: list, db: Session, agora: datetime | None) -> None:
    db.query(Novidade).filter(Novidade.vista_em.is_(None), *filtros).update(
        {Novidade.vista_em: agora or datetime.utcnow()}, synchronize_session=False)
    db.commit()


def marcar_resposta_vista(student_id: int, question_id: int, chave: str | None,
                          db: Session, agora: datetime | None = None) -> None:
    """A tela da questão entregou a resposta do grupo `chave`. Só a novidade
    desse grupo conta como vista."""
    if not chave:
        return
    _sem_derrubar(lambda: _marcar([
        Novidade.student_id == student_id,
        Novidade.tipo == RETORNO,
        Novidade.question_id == question_id,
        Novidade.grupo_chave == chave,
    ], db, agora), "marcar a resposta como vista", db)


def marcar_exercicio_visto(student_id: int, exercicio_id: int, db: Session,
                           agora: datetime | None = None) -> None:
    _sem_derrubar(lambda: _marcar([
        Novidade.student_id == student_id,
        Novidade.tipo == EXERCICIO,
        Novidade.exercicio_id == exercicio_id,
    ], db, agora), "marcar o exercício como visto", db)
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: `14 passed`

Depois a suíte inteira: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q`
Esperado: `418 passed`

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/novidades_service.py backend/tests/test_novidades.py
```
```bash
/usr/bin/git commit -m "feat(novidades): registro da resposta e do exercicio e marcacao de visto"
```

---

### Task 3: Leitura das novidades que ainda valem

**Arquivos:**
- Alterar: `backend/app/services/novidades_service.py` (linha de import do orm e funções novas no fim)
- Teste: `backend/tests/test_novidades.py` (trocar o import do serviço e acrescentar classe no fim)

**Interfaces:**
- Consome: `Novidade` (Task 1), `RETORNO` e `EXERCICIO` (Task 2), `titulo_da_atividade(exam)` de `app.services.student_activity_service` (já existe).
- Produz, em `app.services.novidades_service`:
  - `novidades_do_aluno(student: Student, db: Session) -> list[dict]`, cada item com as chaves `tipo`, `titulo`, `chegou_em`, `exam_id`, `question_number`, `exercicio_id`
  - `contar(student: Student, db: Session) -> int`

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/test_novidades.py`, trocar:

```python
from app.services.novidades_service import (
    marcar_exercicio_visto, marcar_resposta_vista, registrar_exercicio, registrar_resposta,
)
```

por:

```python
from app.services.novidades_service import (
    contar, marcar_exercicio_visto, marcar_resposta_vista, novidades_do_aluno,
    registrar_exercicio, registrar_resposta,
)
```

No fim do arquivo, acrescentar:

```python


class TestLeitura:
    def _retorno_valido(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        grupo = _grupo(db, q)
        _novidade(db, aluno.id, q)
        return q, grupo

    def test_retorno_que_vale_aparece_com_titulo_e_link(self, db, aluno, prova):
        self._retorno_valido(db, aluno, prova)
        assert novidades_do_aluno(aluno, db) == [{
            "tipo": "retorno", "titulo": "Questão 1 · Lista 3",
            "chegou_em": AGORA.isoformat(), "exam_id": prova.id,
            "question_number": "1", "exercicio_id": None,
        }]

    def test_grupo_apagado_some_e_a_linha_fica(self, db, aluno, prova):
        _, grupo = self._retorno_valido(db, aluno, prova)
        db.delete(grupo)
        db.commit()
        assert novidades_do_aluno(aluno, db) == []
        assert db.query(Novidade).one().vista_em is None

    def test_aluno_que_mudou_de_grupo_com_envio_novo_nao_ve(self, db, aluno, prova):
        q, _ = self._retorno_valido(db, aluno, prova)
        _envio(db, q, aluno.id, 2, cluster_id=1, categoria="Tudo no Main")
        assert novidades_do_aluno(aluno, db) == []

    def test_atividade_despublicada_some(self, db, aluno, prova):
        self._retorno_valido(db, aluno, prova)
        prova.publicada = False
        db.commit()
        assert novidades_do_aluno(aluno, db) == []

    def test_aluno_que_saiu_da_turma_nao_ve(self, db, aluno, prova):
        self._retorno_valido(db, aluno, prova)
        db.query(Enrollment).filter_by(student_id=aluno.id).delete()
        db.commit()
        db.refresh(aluno)
        assert novidades_do_aluno(aluno, db) == []

    @pytest.mark.parametrize("estado", ["resolvido", "reportado"])
    def test_exercicio_resolvido_ou_reportado_some(self, db, aluno, estado):
        exercicio = _exercicio(db, aluno.id, **{estado: True})
        _novidade(db, aluno.id, exercicio=exercicio)
        assert novidades_do_aluno(aluno, db) == []

    def test_mais_recente_primeiro_e_contagem_igual(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        _grupo(db, q)
        _novidade(db, aluno.id, q, chegou_em=AGORA)
        exercicio = _exercicio(db, aluno.id)
        _novidade(db, aluno.id, exercicio=exercicio, chegou_em=AGORA + timedelta(hours=2))
        itens = novidades_do_aluno(aluno, db)
        assert [i["tipo"] for i in itens] == ["exercicio", "retorno"]
        assert itens[0] == {
            "tipo": "exercicio", "titulo": "Soma dos pares",
            "chegou_em": (AGORA + timedelta(hours=2)).isoformat(),
            "exam_id": None, "question_number": None, "exercicio_id": exercicio.id,
        }
        assert contar(aluno, db) == 2

    def test_novidade_de_outro_aluno_nao_aparece(self, db, aluno, colega, prova):
        self._retorno_valido(db, aluno, prova)
        assert novidades_do_aluno(colega, db) == []
        assert contar(colega, db) == 0
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_novidades.py -q`
Esperado: FALHA na coleta com `ImportError: cannot import name 'contar'`

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/novidades_service.py`, trocar:

```python
from app.models.orm import ExercicioGerado, Novidade, Question, QuestionCluster, Submission
```

por:

```python
from app.models.orm import (
    ExercicioGerado, Novidade, Question, QuestionCluster, Student, Submission,
)
```

No fim do arquivo, acrescentar:

```python


def _iso(valor) -> str | None:
    return valor.isoformat() if valor else None


def _retorno_que_vale(novidade: Novidade, student_id: int, turma_ids: set[int],
                      db: Session) -> dict | None:
    """A resposta ainda está lá e ainda é para ele: atividade publicada de uma
    turma dele, grupo existente com resposta e a tentativa mais recente nele."""
    # Import tardio: o student_activity_service importa este módulo para marcar
    # a resposta como vista.
    from app.services.student_activity_service import titulo_da_atividade

    questao = db.get(Question, novidade.question_id)
    exam = questao.exam if questao else None
    if not exam or not exam.publicada or exam.turma_id not in turma_ids:
        return None
    grupo = db.query(QuestionCluster).filter(
        QuestionCluster.question_id == questao.id,
        QuestionCluster.chave == novidade.grupo_chave,
    ).first()
    if not grupo or not grupo.resposta_professor:
        return None
    ultima = (
        db.query(Submission.cluster_id)
        .filter(Submission.question_id == questao.id, Submission.student_id == student_id)
        .order_by(Submission.attempt_number.desc(), Submission.id.desc())
        .first()
    )
    if ultima is None or ultima.cluster_id != grupo.cluster_label:
        return None
    return {
        "tipo": RETORNO,
        "titulo": f"Questão {questao.number} · {titulo_da_atividade(exam)}",
        "chegou_em": _iso(novidade.chegou_em),
        "exam_id": exam.id,
        "question_number": questao.number,
        "exercicio_id": None,
    }


def _exercicio_que_vale(novidade: Novidade, db: Session) -> dict | None:
    exercicio = db.get(ExercicioGerado, novidade.exercicio_id)
    if not exercicio or exercicio.resolvido or exercicio.reportado:
        return None
    return {
        "tipo": EXERCICIO,
        "titulo": exercicio.titulo,
        "chegou_em": _iso(novidade.chegou_em),
        "exam_id": None,
        "question_number": None,
        "exercicio_id": exercicio.id,
    }


def novidades_do_aluno(student: Student, db: Session) -> list[dict]:
    """As não vistas que ainda valem, da que chegou por último para a primeira.

    A que deixou de valer some daqui e fica no banco como está: ela chegou e
    não foi vista, que é o que o experimento precisa enxergar."""
    turma_ids = {e.turma_id for e in student.enrollments}
    abertas = (
        db.query(Novidade)
        .filter(Novidade.student_id == student.id, Novidade.vista_em.is_(None))
        .order_by(Novidade.chegou_em.desc(), Novidade.id.desc())
        .all()
    )
    itens = []
    for novidade in abertas:
        item = (_retorno_que_vale(novidade, student.id, turma_ids, db)
                if novidade.tipo == RETORNO else _exercicio_que_vale(novidade, db))
        if item:
            itens.append(item)
    return itens


def contar(student: Student, db: Session) -> int:
    """O número da bolinha do menu. Passa pela mesma conferência da lista."""
    return len(novidades_do_aluno(student, db))
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: `23 passed`

Depois a suíte inteira: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q`
Esperado: `427 passed`

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/novidades_service.py backend/tests/test_novidades.py
```
```bash
/usr/bin/git commit -m "feat(novidades): leitura das novidades que ainda valem"
```

---

### Task 4: Resposta do professor cria a novidade e a exclusão apaga

**Arquivos:**
- Alterar: `backend/app/api/routes/exam.py` (import depois do bloco `from app.services.exam_service import (...)`, por volta da linha 49, e `put_resposta_do_grupo`, por volta da linha 493)
- Alterar: `backend/app/services/exam_service.py:6-9` (import) e `_delete_questions` (por volta da linha 80)
- Teste: `backend/tests/test_novidades.py` (classes no fim)

**Interfaces:**
- Consome: `registrar_resposta(grupo, db)` e `_alcancados` (Task 2), `Novidade` (Task 1).
- Produz: nada novo para outras tarefas.

- [ ] **Passo 1: escrever o teste que falha**

No fim de `backend/tests/test_novidades.py`, acrescentar:

```python


class TestGanchoDoProfessor:
    def test_resposta_pela_rota_cria_a_novidade(self, client, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        _grupo(db, q, resposta=None, em=None)
        resp = client.put(f"/exam/{prova.id}/questions/1/grupos/0/resposta",
                          json={"texto": "Revejam a condição de parada."})
        assert resp.status_code == 200
        (novidade,) = db.query(Novidade).all()
        assert novidade.student_id == aluno.id
        assert novidade.grupo_chave == CHAVE
        assert novidade.vista_em is None

    def test_falha_ao_gravar_nao_desfaz_a_resposta(self, client, db, aluno, prova, monkeypatch):
        from app.services import novidades_service

        def explode(*a, **k):
            raise RuntimeError("banco caiu")

        monkeypatch.setattr(novidades_service, "_alcancados", explode)
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        grupo = _grupo(db, q, resposta=None, em=None)
        resp = client.put(f"/exam/{prova.id}/questions/1/grupos/0/resposta",
                          json={"texto": "Revejam a condição de parada."})
        assert resp.status_code == 200
        db.expire_all()
        assert db.get(QuestionCluster, grupo.id).resposta_professor == (
            "Revejam a condição de parada.")
        assert db.query(Novidade).count() == 0


class TestExclusao:
    def _com_novidade(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        _grupo(db, q)
        _novidade(db, aluno.id, q)

    def test_apagar_a_atividade_remove_as_novidades(self, client, db, aluno, prova):
        self._com_novidade(db, aluno, prova)
        assert client.delete(f"/exam/{prova.id}").status_code == 204
        assert db.query(Novidade).count() == 0

    def test_apagar_a_questao_remove_so_as_novidades_dela(self, client, db, aluno, prova):
        self._com_novidade(db, aluno, prova)
        segunda = _questao(prova, "2")
        _novidade(db, aluno.id, segunda)
        assert client.delete(f"/exam/{prova.id}/questions/1").status_code == 204
        (ficou,) = db.query(Novidade).all()
        assert ficou.question_id == segunda.id

    def test_apagar_a_turma_remove_as_novidades(self, client, db, aluno, prova):
        self._com_novidade(db, aluno, prova)
        assert client.delete(f"/turmas/{prova.turma_id}").status_code == 204
        assert db.query(Novidade).count() == 0
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_novidades.py -q -k "GanchoDoProfessor or Exclusao"`
Esperado: `test_resposta_pela_rota_cria_a_novidade` FALHA (nenhuma novidade), os três de `TestExclusao` FALHAM com `IntegrityError` da FK de `novidades.question_id`, e `test_falha_ao_gravar_nao_desfaz_a_resposta` PASSA já agora, porque é guarda do comportamento.

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/api/routes/exam.py`, logo depois do bloco:

```python
from app.services.exam_service import (
    add_test_cases,
    create_question,
    delete_exam,
    delete_question,
    get_exam_results,
    get_exam_students,
    get_student_detail,
    impedimentos_para_publicar,
    start_exam_processing,
    update_exam,
    update_question,
)
```

acrescentar a linha:

```python
from app.services.novidades_service import registrar_resposta
```

Em `put_resposta_do_grupo`, trocar:

```python
    grupo.resposta_por = professor.id if texto else None
    db.commit()
    db.refresh(grupo)
```

por:

```python
    grupo.resposta_por = professor.id if texto else None
    db.commit()
    db.refresh(grupo)
    registrar_resposta(grupo, db)
```

Em `backend/app/services/exam_service.py`, trocar:

```python
from app.models.orm import (
    Exam, Question, TestCase, ProcessingJob,
    Submission, SubmissionTestResult, QuestionCluster,
)
```

por:

```python
from app.models.orm import (
    Exam, Novidade, Question, TestCase, ProcessingJob,
    Submission, SubmissionTestResult, QuestionCluster,
)
```

Em `_delete_questions`, trocar:

```python
    db.query(QuestionCluster).filter(
        QuestionCluster.question_id.in_(question_ids)).delete(synchronize_session=False)
```

por:

```python
    db.query(Novidade).filter(
        Novidade.question_id.in_(question_ids)).delete(synchronize_session=False)
    db.query(QuestionCluster).filter(
        QuestionCluster.question_id.in_(question_ids)).delete(synchronize_session=False)
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: `5 passed`

Depois a suíte inteira: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q`
Esperado: `432 passed`

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/api/routes/exam.py backend/app/services/exam_service.py backend/tests/test_novidades.py
```
```bash
/usr/bin/git commit -m "feat(novidades): resposta do professor cria novidade e exclusao apaga"
```

---

### Task 5: A tela da questão marca a resposta como vista

**Arquivos:**
- Alterar: `backend/app/services/student_activity_service.py` (imports, `submeter`, `resposta_do_grupo`, helper novo `_marcar_resposta_vista`, `tentativa_to_dict`, `historico_questao`)
- Teste: `backend/tests/test_novidades.py` (import no topo e classe no fim)

**Interfaces:**
- Consome: `marcar_resposta_vista(student_id, question_id, chave, db)`, `registrar_resposta` e `_marcar` (Task 2).
- Produz: `resposta_do_grupo(sub, db) -> tuple[str | None, str | None, str | None]` (texto, momento, chave). Nenhuma outra tarefa usa.

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/test_novidades.py`, acrescentar ao bloco de imports do topo, antes de `from app.models.orm import (...)`:

```python
from app.auth.student_service import create_student_token
```

No fim do arquivo, acrescentar:

```python


def _auth(student):
    return {"Authorization": f"Bearer {create_student_token(student.id)}"}


ERRO_DE_SAIDA = {
    "compile_error": "",
    "warnings": "",
    "all_tests_passed": False,
    "diagnosis": {
        "error_category": "Saída Incorreta",
        "pedagogical_diagnosis": "diagnóstico",
        "actionable_feedback": "o que fazer",
    },
    "ast_structures": [],
    "ast_functions": [],
    "test_results": [],
}


def _explode(*a, **k):
    raise RuntimeError("banco caiu")


class TestGanchosDaLista:
    def _historico(self, client, aluno, prova):
        return client.get(f"/aluno/atividades/{prova.id}/questoes/1/tentativas",
                          headers=_auth(aluno))

    def _grupo_respondido_pelo_agrupamento(self, db, aluno, prova, submission_factory):
        """Três envios de "Saída Incorreta" (menos de 6) formam o grupo
        `cat:Saída Incorreta` no agrupamento de verdade, e a resposta do
        professor vira a novidade do aluno."""
        from app.ml.cluster import cluster_question

        q = _questao(prova)
        for i in range(2):
            submission_factory(q.id, code=f"int main(){{return {i};}}",
                               error_category="Saída Incorreta", all_tests_passed=False)
        _envio(db, q, aluno.id, 1, cluster_id=None)
        cluster_question(q.id, db)
        grupo = db.query(QuestionCluster).filter_by(question_id=q.id, chave=CHAVE).one()
        grupo.resposta_professor = "Revejam a condição de parada."
        grupo.resposta_em = AGORA
        db.commit()
        registrar_resposta(grupo, db)
        assert db.query(Novidade).one().vista_em is None

    def _envia(self, client, aluno, prova, monkeypatch):
        from app.services import student_activity_service as svc

        monkeypatch.setattr(svc, "evaluate_code", lambda *a, **k: dict(ERRO_DE_SAIDA))
        return client.post(f"/aluno/atividades/{prova.id}/questoes/1/submissoes",
                           json={"code": "int main(){return 3;}"}, headers=_auth(aluno))

    def test_historico_com_resposta_marca_como_vista(self, client, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        _grupo(db, q)
        _novidade(db, aluno.id, q)
        resp = self._historico(client, aluno, prova)
        assert resp.json()["tentativas"][0]["resposta_do_professor"] == (
            "Revejam a condição de parada.")
        db.expire_all()
        assert db.query(Novidade).one().vista_em is not None

    def test_historico_sem_resposta_nao_marca(self, client, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        _grupo(db, q, resposta=None, em=None)
        _novidade(db, aluno.id, q)
        self._historico(client, aluno, prova)
        db.expire_all()
        assert db.query(Novidade).one().vista_em is None

    def test_historico_nao_marca_a_novidade_de_outro_grupo(self, client, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=1, categoria="Tudo no Main")
        _envio(db, q, aluno.id, 2, cluster_id=0)
        _grupo(db, q, label=0, chave=CHAVE)
        _grupo(db, q, label=1, chave=OUTRA_CHAVE, resposta="Separe em funções.")
        _novidade(db, aluno.id, q, chave=CHAVE)
        _novidade(db, aluno.id, q, chave=OUTRA_CHAVE)
        self._historico(client, aluno, prova)
        db.expire_all()
        vistas = {n.grupo_chave: n.vista_em is not None for n in db.query(Novidade).all()}
        assert vistas == {CHAVE: True, OUTRA_CHAVE: False}

    def test_envio_que_cai_em_grupo_respondido_marca(
        self, client, db, aluno, prova, monkeypatch, submission_factory
    ):
        self._grupo_respondido_pelo_agrupamento(db, aluno, prova, submission_factory)
        resp = self._envia(client, aluno, prova, monkeypatch)
        assert resp.status_code == 201
        assert resp.json()["tentativa"]["resposta_do_professor"] == (
            "Revejam a condição de parada.")
        db.expire_all()
        assert db.query(Novidade).one().vista_em is not None

    def test_falha_na_marcacao_nao_derruba_o_historico(
        self, client, db, aluno, prova, monkeypatch
    ):
        from app.services import novidades_service

        monkeypatch.setattr(novidades_service, "_marcar", _explode)
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        _grupo(db, q)
        _novidade(db, aluno.id, q)
        resp = self._historico(client, aluno, prova)
        assert resp.status_code == 200
        assert resp.json()["tentativas"][0]["resposta_do_professor"] == (
            "Revejam a condição de parada.")

    def test_falha_na_marcacao_nao_derruba_o_envio(
        self, client, db, aluno, prova, monkeypatch, submission_factory
    ):
        from app.services import novidades_service

        self._grupo_respondido_pelo_agrupamento(db, aluno, prova, submission_factory)
        monkeypatch.setattr(novidades_service, "_marcar", _explode)
        resp = self._envia(client, aluno, prova, monkeypatch)
        assert resp.status_code == 201
        assert resp.json()["tentativa"]["error_category"] == "Saída Incorreta"
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_novidades.py -q -k GanchosDaLista`
Esperado: FALHAM `test_historico_com_resposta_marca_como_vista`, `test_historico_nao_marca_a_novidade_de_outro_grupo` e `test_envio_que_cai_em_grupo_respondido_marca` (a novidade continua com `vista_em` vazio). PASSAM já agora `test_historico_sem_resposta_nao_marca` e os dois de falha, que são guardas.

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/student_activity_service.py`, logo depois do bloco `from app.services.historico_do_aluno import (...)`, acrescentar:

```python
from app.services.novidades_service import marcar_resposta_vista
```

No fim de `submeter`, trocar:

```python
    _agrupar_em_silencio(question.id, db)

    usadas = len(anteriores) + 1
    return {
        "tentativa": tentativa_to_dict(submissao, db, com_resposta=True),
        "tentativas": usadas,
        "tentativas_restantes": _restantes(exam, usadas),
        "resolvida": _resolvida(anteriores + [submissao]),
        "structure_check": result.get("structure_check"),
        "function_check": result.get("function_check"),
    }
```

por:

```python
    _agrupar_em_silencio(question.id, db)

    usadas = len(anteriores) + 1
    entrega = {
        "tentativa": tentativa_to_dict(submissao, db, com_resposta=True),
        "tentativas": usadas,
        "tentativas_restantes": _restantes(exam, usadas),
        "resolvida": _resolvida(anteriores + [submissao]),
        "structure_check": result.get("structure_check"),
        "function_check": result.get("function_check"),
    }
    _marcar_resposta_vista(student, submissao, db)
    return entrega
```

Trocar a função `resposta_do_grupo` inteira:

```python
def resposta_do_grupo(sub: Submission, db: Session) -> tuple[str | None, str | None]:
    """O retorno que o professor escreveu para o grupo desta tentativa.

    O aluno nunca vê que está em um grupo, nem quem mais está nele. Ele vê um
    retorno do professor dele, porque é o que é: dizer ao aluno que a resposta
    foi escrita para um grupo seria dizer que ela não é dele."""
    from app.models.orm import QuestionCluster

    if sub.cluster_id is None:
        return None, None
    grupo = db.query(QuestionCluster).filter(
        QuestionCluster.question_id == sub.question_id,
        QuestionCluster.cluster_label == sub.cluster_id,
    ).first()
    if not grupo or not grupo.resposta_professor:
        return None, None
    return grupo.resposta_professor, _iso(grupo.resposta_em)
```

por:

```python
def resposta_do_grupo(sub: Submission, db: Session) -> tuple[str | None, str | None, str | None]:
    """O retorno que o professor escreveu para o grupo desta tentativa: o texto,
    quando foi escrito e a `chave` do grupo, que marca a novidade como vista.

    O aluno nunca vê que está em um grupo, nem quem mais está nele. Ele vê um
    retorno do professor dele, porque é o que é: dizer ao aluno que a resposta
    foi escrita para um grupo seria dizer que ela não é dele. A chave fica no
    servidor e não vai para a resposta da API."""
    from app.models.orm import QuestionCluster

    if sub.cluster_id is None:
        return None, None, None
    grupo = db.query(QuestionCluster).filter(
        QuestionCluster.question_id == sub.question_id,
        QuestionCluster.cluster_label == sub.cluster_id,
    ).first()
    if not grupo or not grupo.resposta_professor:
        return None, None, None
    return grupo.resposta_professor, _iso(grupo.resposta_em), grupo.chave


def _marcar_resposta_vista(student: Student, sub: Submission, db: Session) -> None:
    """A tela da questão acabou de entregar a resposta do professor nesta
    tentativa: a novidade dela conta como vista. Só a do grupo desta tentativa."""
    _, _, chave = resposta_do_grupo(sub, db)
    if chave:
        marcar_resposta_vista(student.id, sub.question_id, chave, db)
```

Em `tentativa_to_dict`, trocar:

```python
    resposta, resposta_em = (
        resposta_do_grupo(sub, db) if (com_resposta and db is not None) else (None, None))
```

por:

```python
    resposta, resposta_em, _ = (
        resposta_do_grupo(sub, db) if (com_resposta and db is not None)
        else (None, None, None))
```

Em `historico_questao`, trocar:

```python
    tentativas = _tentativas_por_questao(student, db, [question.id]).get(question.id, [])
    return {
        "question_number": question.number,
        "statement": question.statement or "",
        "resolvida": _resolvida(tentativas),
        # Mais recente primeiro: é o que o aluno quer ver ao abrir a tela. Só ela
        # carrega o retorno do professor, senão o mesmo texto apareceria repetido
        # em toda tentativa antiga que caiu no mesmo grupo.
        "tentativas": [
            tentativa_to_dict(s, db, com_resposta=(i == 0))
            for i, s in enumerate(reversed(tentativas))
        ],
    }
```

por:

```python
    tentativas = _tentativas_por_questao(student, db, [question.id]).get(question.id, [])
    recentes = list(reversed(tentativas))
    entrega = {
        "question_number": question.number,
        "statement": question.statement or "",
        "resolvida": _resolvida(tentativas),
        # Mais recente primeiro: é o que o aluno quer ver ao abrir a tela. Só ela
        # carrega o retorno do professor, senão o mesmo texto apareceria repetido
        # em toda tentativa antiga que caiu no mesmo grupo.
        "tentativas": [
            tentativa_to_dict(s, db, com_resposta=(i == 0))
            for i, s in enumerate(recentes)
        ],
    }
    if recentes:
        _marcar_resposta_vista(student, recentes[0], db)
    return entrega
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: `6 passed`

Depois a suíte inteira: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q`
Esperado: `438 passed`

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/student_activity_service.py backend/tests/test_novidades.py
```
```bash
/usr/bin/git commit -m "feat(novidades): tela da questao marca a resposta como vista"
```

---

### Task 6: Exercício pré-gerado vira novidade e abrir marca como visto

**Arquivos:**
- Alterar: `backend/app/services/treino_service.py` (import, `gerar_para_categoria`, `_tarefa` dentro de `preparar_proximo`, `detalhe`, fim de `treinar`)
- Teste: `backend/tests/test_treino.py` (import do topo e classe no fim)

**Interfaces:**
- Consome: `registrar_exercicio(exercicio, db)` e `marcar_exercicio_visto(student_id, exercicio_id, db)` (Task 2), `Novidade` (Task 1). Fixtures já existentes em `test_treino.py`: `aluno`, `erros_do_aluno`, `gemini_ok`, `sem_thread`, `_resultado_referencia`.
- Produz: nada novo para outras tarefas.

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/test_treino.py`, trocar:

```python
from app.models.orm import ExercicioGerado, Student, Submission, TentativaDeTreino
```

por:

```python
from app.models.orm import ExercicioGerado, Novidade, Student, Submission, TentativaDeTreino
```

No fim do arquivo, acrescentar:

```python


class TestNovidadesDaTrilha:
    """O exercício que a pré-geração deixa pronto espera pelo aluno no Início,
    e abrir, tentar ou receber o exercício conta como visto."""

    def _pendente_com_novidade(self, db, aluno):
        exercicio = ExercicioGerado(
            student_id=aluno.id, error_category="Acesso Fora dos Limites: Off-by-One",
            titulo="Soma", enunciado="Some os n primeiros inteiros.",
            casos_teste=[{"input": "3", "expected_output": "6"}],
            created_at=datetime.utcnow())
        db.add(exercicio)
        db.flush()
        db.add(Novidade(student_id=aluno.id, tipo="exercicio", exercicio_id=exercicio.id,
                        chegou_em=exercicio.created_at))
        db.commit()
        db.refresh(exercicio)
        return exercicio

    def _vista(self, db):
        db.expire_all()
        return db.query(Novidade).one().vista_em

    def test_pre_geracao_cria_a_novidade(
        self, db, aluno, erros_do_aluno, gemini_ok, sem_thread
    ):
        from app.services.treino_service import trilha

        trilha(aluno, db)
        db.expire_all()
        (gerado,) = db.query(ExercicioGerado).all()
        (novidade,) = db.query(Novidade).all()
        assert novidade.tipo == "exercicio"
        assert novidade.exercicio_id == gerado.id
        assert novidade.chegou_em == gerado.created_at
        assert novidade.vista_em is None

    def test_exercicio_pedido_na_hora_nao_cria(self, db, aluno, erros_do_aluno, gemini_ok):
        from app.services import treino_service

        treino_service.gerar_para_categoria(aluno, None, db)
        assert db.query(Novidade).count() == 0

    def test_abrir_o_exercicio_marca_como_visto(self, db, aluno):
        from app.services import treino_service

        exercicio = self._pendente_com_novidade(db, aluno)
        treino_service.detalhe(aluno, exercicio.id, db)
        assert self._vista(db) is not None

    def test_tentar_o_exercicio_marca_como_visto(self, db, aluno, monkeypatch):
        from app.services import treino_service

        exercicio = self._pendente_com_novidade(db, aluno)
        monkeypatch.setattr(treino_service, "evaluate_code",
                            lambda *a, **k: _resultado_referencia([False]))
        treino_service.treinar(aluno, exercicio.id, "int main(){}", db)
        assert self._vista(db) is not None

    def test_pendente_devolvido_pela_trilha_marca_como_visto(
        self, db, aluno, erros_do_aluno, gemini_ok
    ):
        from app.services import treino_service

        exercicio = self._pendente_com_novidade(db, aluno)
        devolvido = treino_service.gerar_para_categoria(aluno, None, db)
        assert devolvido["id"] == exercicio.id
        assert devolvido["reaproveitado"] is True
        assert self._vista(db) is not None
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_treino.py -q -k NovidadesDaTrilha`
Esperado: FALHAM `test_pre_geracao_cria_a_novidade` (nenhuma novidade), `test_abrir_o_exercicio_marca_como_visto`, `test_tentar_o_exercicio_marca_como_visto` e `test_pendente_devolvido_pela_trilha_marca_como_visto` (`vista_em` continua vazio). PASSA já agora `test_exercicio_pedido_na_hora_nao_cria`, que é guarda. O Gemini é simulado por `gemini_ok` nos testes que poderiam gerar.

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/treino_service.py`, logo depois de:

```python
from app.services.historico_do_aluno import Erro, erros_do_aluno, ler_historico, superados
```

acrescentar:

```python
from app.services.novidades_service import marcar_exercicio_visto, registrar_exercicio
```

Em `gerar_para_categoria`, trocar:

```python
    if pendente:
        return _exercicio_detalhe(pendente, db, reaproveitado=True)
```

por:

```python
    if pendente:
        entrega = _exercicio_detalhe(pendente, db, reaproveitado=True)
        marcar_exercicio_visto(student.id, pendente.id, db)
        return entrega
```

Em `_tarefa`, dentro de `preparar_proximo`, trocar:

```python
            diagnostico = next(
                (e.o_que_fazer for e in _erros(student, db) if e.categoria == categoria), "")
            _gerar_e_salvar(student, categoria, diagnostico, db)
```

por:

```python
            diagnostico = next(
                (e.o_que_fazer for e in _erros(student, db) if e.categoria == categoria), "")
            exercicio = _gerar_e_salvar(student, categoria, diagnostico, db)
            registrar_exercicio(exercicio, db)
```

Trocar a função `detalhe`:

```python
def detalhe(student: Student, exercicio_id: int, db: Session) -> dict:
    return _exercicio_detalhe(_meu_exercicio(student, exercicio_id, db), db)
```

por:

```python
def detalhe(student: Student, exercicio_id: int, db: Session) -> dict:
    exercicio = _meu_exercicio(student, exercicio_id, db)
    entrega = _exercicio_detalhe(exercicio, db)
    marcar_exercicio_visto(student.id, exercicio.id, db)
    return entrega
```

No fim de `treinar`, trocar:

```python
    return {
        "tentativa": _tentativa_dict(tentativa),
        "tentativas": len(anteriores) + 1,
        "resolvido": bool(exercicio.resolvido),
        "structure_check": resultado.get("structure_check"),
    }
```

por:

```python
    entrega = {
        "tentativa": _tentativa_dict(tentativa),
        "tentativas": len(anteriores) + 1,
        "resolvido": bool(exercicio.resolvido),
        "structure_check": resultado.get("structure_check"),
    }
    marcar_exercicio_visto(student.id, exercicio.id, db)
    return entrega
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: `5 passed`

Depois a suíte inteira: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q`
Esperado: `443 passed`

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/treino_service.py backend/tests/test_treino.py
```
```bash
/usr/bin/git commit -m "feat(novidades): exercicio pre-gerado vira novidade e abrir marca como visto"
```

---

### Task 7: Regras do Início (continuar, próxima atividade e prazos)

**Arquivos:**
- Criar: `backend/app/services/inicio_service.py`
- Teste: `backend/tests/test_inicio.py` (criar)

**Interfaces:**
- Consome: `ACERTO`, `FALHA`, `LISTA`, `Envio` de `app.services.historico_do_aluno` e `ANTECEDENCIA_DA_PROVA` de `app.services.funil_regras` (já existem).
- Produz, em `app.services.inicio_service`:
  - `JANELA_DO_PRAZO = timedelta(days=7)`, `EM_ANDAMENTO = "em_andamento"`, `PROXIMA = "proxima"`
  - `ItemDisponivel(origem: str, item_id: int, titulo: str, turma_nome: str = "", exam_id: int | None = None, question_number: str | None = None, exercicio_id: int | None = None)`
  - `AtividadeDoPainel(exam_id: int, titulo: str, turma_nome: str, modo: str, situacao: str, abre_em: datetime | None, fecha_em: datetime | None, criada_em: datetime | None, com_o_que_fazer: bool)`
  - `escolher_continuar(envios: list[Envio], disponiveis: dict[tuple[str, int], ItemDisponivel], proxima: dict | None) -> dict | None`
  - `proxima_atividade(atividades: list[AtividadeDoPainel]) -> dict | None`
  - `prazos_proximos(atividades: list[AtividadeDoPainel], agora: datetime) -> list[dict]`
  - O cartão de continuar tem as chaves `origem`, `situacao`, `titulo`, `turma_nome`, `tentativas`, `ultimo_erro`, `exam_id`, `question_number`, `exercicio_id`. O prazo tem `exam_id`, `titulo`, `turma_nome`, `modo`, `tipo`, `quando`.

- [ ] **Passo 1: escrever o teste que falha**

Criar `backend/tests/test_inicio.py`:

```python
"""Início do aluno: o cartão de continuar, a próxima atividade, os prazos e o
painel.

As regras são funções puras, testadas com listas montadas à mão. O painel e as
rotas são testados no banco."""
from datetime import datetime, timedelta

from app.services.historico_do_aluno import ACERTO, ERRO, FALHA, LISTA, TRILHA, Envio
from app.services.inicio_service import (
    AtividadeDoPainel, ItemDisponivel, escolher_continuar, prazos_proximos, proxima_atividade,
)

AGORA = datetime(2026, 11, 4, 12, 0)


def _envio(origem, item_id, minuto, resultado, categoria="Saída Incorreta"):
    return Envio(origem=origem, item_id=item_id, momento=AGORA + timedelta(minutes=minuto),
                 categoria=categoria, resultado=resultado)


def _questao(item_id, numero="1"):
    return ItemDisponivel(origem=LISTA, item_id=item_id, titulo=f"Questão {numero} · Lista 3",
                          turma_nome="Turma A", exam_id=10, question_number=numero)


def _exercicio(item_id, titulo="Soma dos pares"):
    return ItemDisponivel(origem=TRILHA, item_id=item_id, titulo=titulo, exercicio_id=item_id)


def _disponiveis(*itens):
    return {(i.origem, i.item_id): i for i in itens}


def _atividade(exam_id, situacao="aberta", fecha_em=None, abre_em=None, criada_em=AGORA,
               com_o_que_fazer=True):
    return AtividadeDoPainel(
        exam_id=exam_id, titulo=f"Lista {exam_id}", turma_nome="Turma A", modo="prova",
        situacao=situacao, abre_em=abre_em, fecha_em=fecha_em, criada_em=criada_em,
        com_o_que_fazer=com_o_que_fazer)


class TestContinuar:
    def test_pega_o_item_mais_recente_sem_acerto(self):
        envios = [_envio(LISTA, 1, 0, ERRO), _envio(LISTA, 2, 1, ERRO)]
        cartao = escolher_continuar(envios, _disponiveis(_questao(1), _questao(2, "2")), None)
        assert cartao == {
            "origem": "lista", "situacao": "em_andamento", "titulo": "Questão 2 · Lista 3",
            "turma_nome": "Turma A", "tentativas": 1, "ultimo_erro": "Saída Incorreta",
            "exam_id": 10, "question_number": "2", "exercicio_id": None,
        }

    def test_pula_o_resolvido_mesmo_sendo_o_mais_recente(self):
        # A questão 2 tem erro e depois acerto: resolvida, mesmo sendo a última mexida.
        envios = [_envio(LISTA, 1, 0, ERRO), _envio(LISTA, 2, 1, ERRO),
                  _envio(LISTA, 2, 2, ACERTO, "Correto")]
        cartao = escolher_continuar(envios, _disponiveis(_questao(1), _questao(2, "2")), None)
        assert cartao["question_number"] == "1"
        assert cartao["tentativas"] == 1

    def test_pula_o_que_nao_aceita_mais_envio(self):
        # Atividade encerrada ou tentativas esgotadas: o item fica fora dos disponíveis.
        envios = [_envio(LISTA, 1, 0, ERRO), _envio(LISTA, 2, 1, ERRO)]
        cartao = escolher_continuar(envios, _disponiveis(_questao(1)), None)
        assert cartao["question_number"] == "1"

    def test_pula_o_exercicio_resolvido(self):
        envios = [_envio(LISTA, 1, 0, ERRO), _envio(TRILHA, 7, 1, ERRO),
                  _envio(TRILHA, 7, 2, ACERTO, "Correto")]
        cartao = escolher_continuar(envios, _disponiveis(_questao(1), _exercicio(7)), None)
        assert cartao["origem"] == "lista"

    def test_mistura_lista_e_trilha_pela_ordem_do_tempo(self):
        # O exercício 7 teve envio antes e depois da questão 1: ele é o mais recente.
        envios = [_envio(TRILHA, 7, 0, ERRO, "Tudo no Main"), _envio(LISTA, 1, 1, ERRO),
                  _envio(TRILHA, 7, 2, ERRO, "Tudo no Main")]
        cartao = escolher_continuar(envios, _disponiveis(_questao(1), _exercicio(7)), None)
        assert cartao == {
            "origem": "trilha", "situacao": "em_andamento", "titulo": "Soma dos pares",
            "turma_nome": "", "tentativas": 2, "ultimo_erro": "Tudo no Main",
            "exam_id": None, "question_number": None, "exercicio_id": 7,
        }

    def test_ultimo_erro_vazio_quando_foi_falha_tecnica(self):
        envios = [_envio(LISTA, 1, 0, ERRO), _envio(LISTA, 1, 1, FALHA, "Erro Desconhecido")]
        cartao = escolher_continuar(envios, _disponiveis(_questao(1)), None)
        assert cartao["ultimo_erro"] == ""
        assert cartao["tentativas"] == 2

    def test_sem_item_em_andamento_devolve_a_proxima(self):
        proxima = {"situacao": "proxima", "exam_id": 20}
        envios = [_envio(LISTA, 1, 0, ACERTO, "Correto")]
        assert escolher_continuar(envios, _disponiveis(_questao(1)), proxima) is proxima

    def test_sem_nada_devolve_vazio(self):
        assert escolher_continuar([], {}, None) is None


class TestPrazos:
    def test_janela_de_fechamento_de_7_dias(self):
        atividades = [
            _atividade(1, fecha_em=AGORA + timedelta(days=7)),
            _atividade(2, fecha_em=AGORA + timedelta(days=8)),
            _atividade(3, situacao="encerrada", fecha_em=AGORA - timedelta(hours=1)),
        ]
        assert prazos_proximos(atividades, AGORA) == [{
            "exam_id": 1, "titulo": "Lista 1", "turma_nome": "Turma A", "modo": "prova",
            "tipo": "fecha", "quando": (AGORA + timedelta(days=7)).isoformat(),
        }]

    def test_janela_de_abertura_de_3_dias(self):
        atividades = [
            _atividade(1, situacao="agendada", abre_em=AGORA + timedelta(days=3)),
            _atividade(2, situacao="agendada", abre_em=AGORA + timedelta(days=4)),
        ]
        prazos = prazos_proximos(atividades, AGORA)
        assert [(p["exam_id"], p["tipo"]) for p in prazos] == [(1, "abre")]

    def test_sem_o_que_fazer_fica_de_fora(self):
        atividades = [_atividade(1, fecha_em=AGORA + timedelta(days=2), com_o_que_fazer=False)]
        assert prazos_proximos(atividades, AGORA) == []

    def test_ordem_pela_data_e_uma_vez_so(self):
        # A 2 ainda não abriu: entra só pela abertura (1 dia), não pelo fechamento.
        atividades = [
            _atividade(1, fecha_em=AGORA + timedelta(days=5)),
            _atividade(2, situacao="agendada", abre_em=AGORA + timedelta(days=1),
                       fecha_em=AGORA + timedelta(days=6)),
            _atividade(3, fecha_em=AGORA + timedelta(days=2)),
        ]
        prazos = prazos_proximos(atividades, AGORA)
        assert [(p["exam_id"], p["tipo"]) for p in prazos] == [
            (2, "abre"), (3, "fecha"), (1, "fecha")]


class TestProximaAtividade:
    def test_a_que_fecha_primeiro_e_depois_as_sem_prazo_da_mais_nova(self):
        a1 = _atividade(1, fecha_em=AGORA + timedelta(days=5))
        a2 = _atividade(2, fecha_em=AGORA + timedelta(days=2))
        a3 = _atividade(3, criada_em=AGORA - timedelta(days=1))
        a4 = _atividade(4, criada_em=AGORA)
        assert proxima_atividade([a1, a2, a3, a4]) == {
            "origem": "lista", "situacao": "proxima", "titulo": "Lista 2",
            "turma_nome": "Turma A", "tentativas": 0, "ultimo_erro": "", "exam_id": 2,
            "question_number": None, "exercicio_id": None,
        }
        assert proxima_atividade([a3, a4])["exam_id"] == 4

    def test_ignora_a_agendada_e_a_sem_o_que_fazer(self):
        atividades = [_atividade(1, situacao="agendada", abre_em=AGORA + timedelta(days=1)),
                      _atividade(2, com_o_que_fazer=False)]
        assert proxima_atividade(atividades) is None
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_inicio.py -q`
Esperado: FALHA na coleta com `ModuleNotFoundError: No module named 'app.services.inicio_service'`

- [ ] **Passo 3: escrever o mínimo para passar**

Criar `backend/app/services/inicio_service.py`:

```python
"""Início do aluno: o que chegou para ele, onde ele parou e o que vence logo.

Monta o painel e não grava nada. As novidades vêm do `novidades_service`, e o
resto sai do histórico unificado (`ler_historico`), o mesmo do progresso e da
trilha, para os três concordarem sobre o que está resolvido. A regra mora em
funções puras sobre registros simples, testadas sem banco."""
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.services.funil_regras import ANTECEDENCIA_DA_PROVA
from app.services.historico_do_aluno import ACERTO, FALHA, LISTA, Envio

# Quanto antes de fechar uma atividade aberta aparece em "Prazos próximos".
JANELA_DO_PRAZO = timedelta(days=7)

EM_ANDAMENTO = "em_andamento"
PROXIMA = "proxima"


@dataclass(frozen=True)
class ItemDisponivel:
    """Questão ou exercício que ainda aceita envio, com o que o cartão mostra."""
    origem: str
    item_id: int
    titulo: str
    turma_nome: str = ""
    exam_id: int | None = None
    question_number: str | None = None
    exercicio_id: int | None = None


@dataclass(frozen=True)
class AtividadeDoPainel:
    """Atividade publicada de uma turma do aluno, com a situação no instante do
    painel e se ainda há questão sem acerto e com tentativa sobrando."""
    exam_id: int
    titulo: str
    turma_nome: str
    modo: str
    situacao: str
    abre_em: datetime | None
    fecha_em: datetime | None
    criada_em: datetime | None
    com_o_que_fazer: bool


def escolher_continuar(envios: list[Envio], disponiveis: dict[tuple[str, int], ItemDisponivel],
                       proxima: dict | None) -> dict | None:
    """O item mais recente em que o aluno enviou algo, ainda sem acerto e que
    ainda aceita envio. Sem nenhum, a próxima atividade, que pode ser vazia."""
    resolvidos = {(e.origem, e.item_id) for e in envios if e.resultado == ACERTO}
    for envio in reversed(envios):
        chave = (envio.origem, envio.item_id)
        if chave in resolvidos or chave not in disponiveis:
            continue
        do_item = [e for e in envios if (e.origem, e.item_id) == chave]
        item = disponiveis[chave]
        return {
            "origem": item.origem,
            "situacao": EM_ANDAMENTO,
            "titulo": item.titulo,
            "turma_nome": item.turma_nome,
            "tentativas": len(do_item),
            "ultimo_erro": "" if do_item[-1].resultado == FALHA else do_item[-1].categoria,
            "exam_id": item.exam_id,
            "question_number": item.question_number,
            "exercicio_id": item.exercicio_id,
        }
    return proxima


def proxima_atividade(atividades: list[AtividadeDoPainel]) -> dict | None:
    """Entre as abertas com o que fazer, a que fecha primeiro. As sem data de
    fechamento vêm depois, da criada mais recentemente para a mais antiga."""
    abertas = [a for a in atividades if a.situacao == "aberta" and a.com_o_que_fazer]
    com_prazo = sorted((a for a in abertas if a.fecha_em), key=lambda a: a.fecha_em)
    sem_prazo = sorted((a for a in abertas if not a.fecha_em),
                       key=lambda a: a.criada_em or datetime.min, reverse=True)
    fila = com_prazo + sem_prazo
    if not fila:
        return None
    atividade = fila[0]
    return {
        "origem": LISTA,
        "situacao": PROXIMA,
        "titulo": atividade.titulo,
        "turma_nome": atividade.turma_nome,
        "tentativas": 0,
        "ultimo_erro": "",
        "exam_id": atividade.exam_id,
        "question_number": None,
        "exercicio_id": None,
    }


def prazos_proximos(atividades: list[AtividadeDoPainel], agora: datetime) -> list[dict]:
    """O que fecha nos próximos 7 dias e o que abre nos próximos 3, a mesma
    janela da prova chegando no funil. Só atividade com o que fazer, e cada uma
    uma vez só."""
    prazos = []
    for a in atividades:
        if not a.com_o_que_fazer:
            continue
        if a.situacao == "aberta" and a.fecha_em and agora < a.fecha_em <= agora + JANELA_DO_PRAZO:
            prazos.append((a.fecha_em, "fecha", a))
        elif a.situacao == "agendada" and a.abre_em and a.abre_em <= agora + ANTECEDENCIA_DA_PROVA:
            prazos.append((a.abre_em, "abre", a))
    prazos.sort(key=lambda p: (p[0], p[2].exam_id))
    return [
        {"exam_id": a.exam_id, "titulo": a.titulo, "turma_nome": a.turma_nome,
         "modo": a.modo, "tipo": tipo, "quando": quando.isoformat()}
        for quando, tipo, a in prazos
    ]
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: `14 passed`

Depois a suíte inteira: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q`
Esperado: `457 passed`

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/inicio_service.py backend/tests/test_inicio.py
```
```bash
/usr/bin/git commit -m "feat(inicio): regras do continuar, da proxima atividade e dos prazos"
```

---

### Task 8: Painel do Início, esquemas e rotas do aluno

**Arquivos:**
- Alterar: `backend/app/services/inicio_service.py` (bloco de imports do topo e funções novas no fim)
- Alterar: `backend/app/models/schemas.py` (classes novas no fim)
- Alterar: `backend/app/api/routes/student_activity.py` (imports e duas rotas no fim)
- Teste: `backend/tests/test_inicio.py` (bloco de imports do topo e classes no fim)

**Interfaces:**
- Consome: as regras puras da Task 7, `novidades_do_aluno` e `contar` (Task 3), `Novidade` (Task 1), `titulo_da_atividade` de `student_activity_service`, `situacao_da_atividade` de `app.services.calendario`, `ler_historico` de `historico_do_aluno`.
- Produz:
  - `painel(student: Student, db: Session, agora: datetime | None = None) -> dict` com `tem_turma`, `novidades`, `continuar`, `prazos`
  - `GET /aluno/inicio` (`InicioResponse`) e `GET /aluno/novidades/contagem` (`ContagemNovidadesResponse`, `{ "total": n }`), consumidas pelas Tasks 9 e 10

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/test_inicio.py`, trocar o bloco de imports do topo:

```python
from datetime import datetime, timedelta

from app.services.historico_do_aluno import ACERTO, ERRO, FALHA, LISTA, TRILHA, Envio
from app.services.inicio_service import (
    AtividadeDoPainel, ItemDisponivel, escolher_continuar, prazos_proximos, proxima_atividade,
)
```

por:

```python
from datetime import datetime, timedelta

import pytest

from app.auth.service import create_access_token
from app.auth.student_service import create_student_token
from app.models.orm import (
    Enrollment, Exam, Novidade, Question, QuestionCluster, Student, Submission,
)
from app.services.historico_do_aluno import ACERTO, ERRO, FALHA, LISTA, TRILHA, Envio
from app.services.inicio_service import (
    AtividadeDoPainel, ItemDisponivel, escolher_continuar, painel, prazos_proximos,
    proxima_atividade,
)
```

No fim do arquivo, acrescentar:

```python


@pytest.fixture()
def prova(db, exam_factory):
    exam = exam_factory(questions=[{"number": "1"}, {"number": "2"}], titulo="Lista 3")
    exam.fecha_em = AGORA + timedelta(days=2)
    db.commit()
    db.refresh(exam)
    return exam


def _matricular(db, email, turma_id):
    s = Student(email=email, nome=email.split("@")[0], senha_hash="x")
    db.add(s)
    db.flush()
    db.add(Enrollment(student_id=s.id, turma_id=turma_id))
    db.commit()
    db.refresh(s)
    return s


@pytest.fixture()
def aluno(db, prova):
    return _matricular(db, "ana@teste.com", prova.turma_id)


def _errou(db, prova, aluno, numero="1", quando=AGORA - timedelta(hours=1), cluster_id=None):
    questao = next(q for q in prova.questions if q.number == numero)
    db.add(Submission(
        question_id=questao.id, code="int main(){}", error_category="Saída Incorreta",
        all_tests_passed=False, student_id=aluno.id, attempt_number=1,
        cluster_id=cluster_id, submitted_at=quando,
    ))
    db.commit()
    return questao


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


class TestPainel:
    def test_questao_em_andamento_e_prazo_da_atividade(self, db, aluno, prova):
        _errou(db, prova, aluno)
        resultado = painel(aluno, db, agora=AGORA)
        assert resultado["tem_turma"] is True
        assert resultado["novidades"] == []
        assert resultado["continuar"] == {
            "origem": "lista", "situacao": "em_andamento", "titulo": "Questão 1 · Lista 3",
            "turma_nome": "Turma Teste", "tentativas": 1, "ultimo_erro": "Saída Incorreta",
            "exam_id": prova.id, "question_number": "1", "exercicio_id": None,
        }
        assert resultado["prazos"] == [{
            "exam_id": prova.id, "titulo": "Lista 3", "turma_nome": "Turma Teste",
            "modo": "prova", "tipo": "fecha",
            "quando": (AGORA + timedelta(days=2)).isoformat(),
        }]

    def test_so_atividades_publicadas_das_turmas_do_aluno(
        self, db, aluno, prova, exam_factory
    ):
        rascunho = Exam(filename="r.pdf", raw_text="", turma_id=prova.turma_id,
                        titulo="Rascunho", publicada=False,
                        fecha_em=AGORA + timedelta(days=1))
        db.add(rascunho)
        db.flush()
        db.add(Question(exam_id=rascunho.id, number="1", statement="x"))
        outra = exam_factory(questions=[{"number": "1"}], titulo="De outra turma")
        outra.fecha_em = AGORA + timedelta(days=1)
        db.commit()
        prazos = painel(aluno, db, agora=AGORA)["prazos"]
        assert [p["exam_id"] for p in prazos] == [prova.id]

    def test_tentativas_esgotadas_tiram_a_atividade_do_continuar_e_dos_prazos(
        self, db, aluno, prova
    ):
        prova.max_tentativas = 1
        db.commit()
        _errou(db, prova, aluno, "1")
        _errou(db, prova, aluno, "2")
        resultado = painel(aluno, db, agora=AGORA)
        assert resultado["continuar"] is None
        assert resultado["prazos"] == []

    def test_atividade_encerrada_nao_entra(self, db, aluno, prova):
        prova.fecha_em = AGORA - timedelta(hours=1)
        db.commit()
        _errou(db, prova, aluno, quando=AGORA - timedelta(hours=2))
        resultado = painel(aluno, db, agora=AGORA)
        assert resultado["continuar"] is None
        assert resultado["prazos"] == []

    def test_aluno_sem_turma(self, db):
        sozinho = Student(email="sem@teste.com", nome="Sem Turma", senha_hash="x")
        db.add(sozinho)
        db.commit()
        assert painel(sozinho, db, agora=AGORA) == {
            "tem_turma": False, "novidades": [], "continuar": None, "prazos": []}


class TestRotas:
    @pytest.mark.parametrize("caminho", ["/aluno/inicio", "/aluno/novidades/contagem"])
    def test_sem_token_da_401(self, client, caminho):
        assert client.get(caminho).status_code == 401

    @pytest.mark.parametrize("caminho", ["/aluno/inicio", "/aluno/novidades/contagem"])
    def test_token_de_professor_da_401(self, client, professor, caminho):
        resp = client.get(caminho, headers=_auth(create_access_token(professor.id)))
        assert resp.status_code == 401

    def test_cada_aluno_recebe_so_o_seu(self, client, db, aluno, prova):
        colega = _matricular(db, "bia@teste.com", prova.turma_id)
        questao = _errou(db, prova, aluno, cluster_id=0)
        db.add(QuestionCluster(
            question_id=questao.id, cluster_label=0, chave="cat:Saída Incorreta", size=1,
            dominant_error="Saída Incorreta", resposta_professor="Revejam a parada.",
            resposta_em=AGORA))
        db.add(Novidade(student_id=aluno.id, tipo="retorno", question_id=questao.id,
                        grupo_chave="cat:Saída Incorreta", chegou_em=AGORA))
        db.commit()

        meu = client.get("/aluno/inicio", headers=_auth(create_student_token(aluno.id))).json()
        dela = client.get("/aluno/inicio",
                          headers=_auth(create_student_token(colega.id))).json()
        assert [n["titulo"] for n in meu["novidades"]] == ["Questão 1 · Lista 3"]
        assert dela["novidades"] == []
        assert client.get("/aluno/novidades/contagem",
                          headers=_auth(create_student_token(aluno.id))).json() == {"total": 1}
        assert client.get("/aluno/novidades/contagem",
                          headers=_auth(create_student_token(colega.id))).json() == {"total": 0}
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_inicio.py -q`
Esperado: FALHA na coleta com `ImportError: cannot import name 'painel'`

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/inicio_service.py`, trocar o bloco de imports do topo:

```python
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.services.funil_regras import ANTECEDENCIA_DA_PROVA
from app.services.historico_do_aluno import ACERTO, FALHA, LISTA, Envio
```

por:

```python
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.orm import Exam, ExercicioGerado, Student, Submission
from app.services.calendario import situacao_da_atividade
from app.services.funil_regras import ANTECEDENCIA_DA_PROVA
from app.services.historico_do_aluno import ACERTO, FALHA, LISTA, TRILHA, Envio, ler_historico
from app.services.novidades_service import novidades_do_aluno
from app.services.student_activity_service import titulo_da_atividade
```

No fim do arquivo, acrescentar:

```python


def painel(student: Student, db: Session, agora: datetime | None = None) -> dict:
    """O Início do aluno. Sem matrícula, só avisa que ele não tem turma."""
    agora = agora or datetime.utcnow()
    turma_ids = [e.turma_id for e in student.enrollments]
    if not turma_ids:
        return {"tem_turma": False, "novidades": [], "continuar": None, "prazos": []}

    envios = ler_historico(student, db)
    atividades, disponiveis = _atividades_e_questoes(student, turma_ids, envios, agora, db)
    disponiveis.update(_exercicios_abertos(student, db))
    return {
        "tem_turma": True,
        "novidades": novidades_do_aluno(student, db),
        "continuar": escolher_continuar(envios, disponiveis, proxima_atividade(atividades)),
        "prazos": prazos_proximos(atividades, agora),
    }


def _atividades_e_questoes(student: Student, turma_ids: list[int], envios: list[Envio],
                           agora: datetime, db: Session):
    """As atividades publicadas das turmas do aluno e, das abertas, as questões
    sem acerto que ainda têm tentativa. O teto conta todos os envios da questão,
    como o `submeter` conta."""
    resolvidas = {e.item_id for e in envios if e.origem == LISTA and e.resultado == ACERTO}
    usadas = dict(
        db.query(Submission.question_id, func.count(Submission.id))
        .filter(Submission.student_id == student.id)
        .group_by(Submission.question_id)
        .all()
    )
    exams = (
        db.query(Exam)
        .filter(Exam.turma_id.in_(turma_ids), Exam.publicada.is_(True))
        .all()
    )
    atividades: list[AtividadeDoPainel] = []
    disponiveis: dict[tuple[str, int], ItemDisponivel] = {}
    for exam in exams:
        situacao = situacao_da_atividade(exam, agora)
        titulo = titulo_da_atividade(exam)
        turma_nome = exam.turma.nome if exam.turma else ""
        pendentes = [
            q for q in exam.questions
            if q.id not in resolvidas
            and (exam.max_tentativas is None or usadas.get(q.id, 0) < exam.max_tentativas)
        ]
        atividades.append(AtividadeDoPainel(
            exam_id=exam.id, titulo=titulo, turma_nome=turma_nome,
            modo=exam.modo or Exam.MODO_PROVA, situacao=situacao,
            abre_em=exam.abre_em, fecha_em=exam.fecha_em, criada_em=exam.created_at,
            com_o_que_fazer=bool(pendentes),
        ))
        if situacao == "aberta":
            for q in pendentes:
                disponiveis[(LISTA, q.id)] = ItemDisponivel(
                    origem=LISTA, item_id=q.id, titulo=f"Questão {q.number} · {titulo}",
                    turma_nome=turma_nome, exam_id=exam.id, question_number=q.number)
    return atividades, disponiveis


def _exercicios_abertos(student: Student, db: Session) -> dict[tuple[str, int], ItemDisponivel]:
    abertos = (
        db.query(ExercicioGerado)
        .filter(ExercicioGerado.student_id == student.id,
                ExercicioGerado.resolvido.is_(False),
                ExercicioGerado.reportado.is_(False))
        .all()
    )
    return {
        (TRILHA, e.id): ItemDisponivel(origem=TRILHA, item_id=e.id, titulo=e.titulo,
                                       exercicio_id=e.id)
        for e in abertos
    }
```

No fim de `backend/app/models/schemas.py`, acrescentar:

```python


# ── Início do aluno ──────────────────────────────────────────────────────────

class NovidadeItem(BaseModel):
    tipo: Literal["retorno", "exercicio"]
    titulo: str
    chegou_em: Optional[str] = None
    exam_id: Optional[int] = None
    question_number: Optional[str] = None
    exercicio_id: Optional[int] = None


class ContinuarItem(BaseModel):
    origem: Literal["lista", "trilha"]
    situacao: Literal["em_andamento", "proxima"]
    titulo: str
    turma_nome: str = ""
    tentativas: int = 0
    ultimo_erro: str = ""
    exam_id: Optional[int] = None
    question_number: Optional[str] = None
    exercicio_id: Optional[int] = None


class PrazoItem(BaseModel):
    exam_id: int
    titulo: str
    turma_nome: str
    modo: str
    tipo: Literal["fecha", "abre"]
    quando: str


class InicioResponse(BaseModel):
    tem_turma: bool
    novidades: List[NovidadeItem] = []
    continuar: Optional[ContinuarItem] = None
    prazos: List[PrazoItem] = []


class ContagemNovidadesResponse(BaseModel):
    total: int
```

Em `backend/app/api/routes/student_activity.py`, trocar:

```python
from app.models.schemas import (
    AlunoSubmissaoRequest, AlunoSubmissaoResponse, AtividadeDetalhe, AtividadeResumo,
    ErrosRecorrentesResponse, ExplicacaoResponse, HistoricoQuestaoResponse, ProgressoResponse,
)
```

por:

```python
from app.models.schemas import (
    AlunoSubmissaoRequest, AlunoSubmissaoResponse, AtividadeDetalhe, AtividadeResumo,
    ContagemNovidadesResponse, ErrosRecorrentesResponse, ExplicacaoResponse,
    HistoricoQuestaoResponse, InicioResponse, ProgressoResponse,
)
from app.services.inicio_service import painel
from app.services.novidades_service import contar
```

No fim de `backend/app/api/routes/student_activity.py`, acrescentar:

```python


@router.get("/inicio", response_model=InicioResponse)
def get_inicio(
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    return painel(current, db)


@router.get("/novidades/contagem", response_model=ContagemNovidadesResponse)
def get_contagem_de_novidades(
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    return {"total": contar(current, db)}
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: `24 passed`

Depois a suíte inteira: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q`
Esperado: `467 passed`

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/inicio_service.py backend/app/models/schemas.py backend/app/api/routes/student_activity.py backend/tests/test_inicio.py
```
```bash
/usr/bin/git commit -m "feat(inicio): painel do inicio e contagem de novidades nas rotas do aluno"
```

---

### Task 9: Página do Início

**Arquivos:**
- Criar: `frontend/src/components/EntrarNaTurma.jsx`
- Alterar: `frontend/src/pages/aluno/TurmasPage.jsx` (imports e remoção da função local `EntrarNaTurma`)
- Criar: `frontend/src/pages/aluno/InicioPage.jsx`
- Alterar: `frontend/src/api/aluno.js` (fim do arquivo)
- Alterar: `frontend/src/utils/datas.js` (fim do arquivo)
- Alterar: `frontend/src/App.jsx` (lazy import e rota `aluno`)

**Interfaces:**
- Consome: `GET /aluno/inicio` da Task 8, com `tem_turma`, `novidades` (`tipo`, `titulo`, `chegou_em`, `exam_id`, `question_number`, `exercicio_id`), `continuar` (`origem`, `situacao`, `titulo`, `turma_nome`, `tentativas`, `ultimo_erro`, `exam_id`, `question_number`, `exercicio_id`) e `prazos` (`exam_id`, `titulo`, `turma_nome`, `modo`, `tipo`, `quando`).
- Produz: `getInicio()` e `contarNovidades()` em `frontend/src/api/aluno.js` (a Task 10 usa `contarNovidades`), `prazoRelativo(iso, agora)` em `utils/datas.js`, componente `EntrarNaTurma` (`{ aoEntrar }`).

- [ ] **Passo 1: extrair o formulário de entrar na turma**

Criar `frontend/src/components/EntrarNaTurma.jsx`:

```jsx
import { useState } from 'react'
import { entrarNaTurma } from '../api/aluno'
import Spinner from './Spinner'

export default function EntrarNaTurma({ aoEntrar }) {
  const [codigo, setCodigo] = useState('')
  const [entrando, setEntrando] = useState(false)
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!codigo.trim()) return
    setErro('')
    setSucesso('')
    setEntrando(true)
    try {
      const { data } = await entrarNaTurma(codigo.trim(), 'codigo')
      setSucesso(`Você entrou em ${data.nome}.`)
      setCodigo('')
      await aoEntrar()
    } catch (err) {
      setErro(err.response?.data?.detail || 'Não foi possível entrar na turma.')
    } finally {
      setEntrando(false)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-sm font-semibold text-gray-900 mb-1">Entrar em uma turma</h2>
      <p className="text-xs text-gray-400 mb-4">Use o código de 6 caracteres que o professor passou.</p>
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
        <input
          type="text"
          value={codigo}
          onChange={e => setCodigo(e.target.value.toUpperCase())}
          placeholder="ABC234"
          maxLength={6}
          className="flex-1 text-sm font-mono tracking-widest uppercase rounded-lg border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
        <button
          type="submit"
          disabled={entrando || !codigo.trim()}
          className="inline-flex items-center justify-center gap-2 text-sm px-5 py-2.5 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {entrando && <Spinner className="w-4 h-4" />}
          Entrar
        </button>
      </form>
      {erro && <p className="mt-2 text-xs text-red-600">{erro}</p>}
      {sucesso && <p className="mt-2 text-xs text-green-600">{sucesso}</p>}
    </div>
  )
}
```

Em `frontend/src/pages/aluno/TurmasPage.jsx`, trocar:

```jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { entrarNaTurma, listarMinhasTurmas } from '../../api/aluno'
import Spinner from '../../components/Spinner'
```

por:

```jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listarMinhasTurmas } from '../../api/aluno'
import EntrarNaTurma from '../../components/EntrarNaTurma'
import Spinner from '../../components/Spinner'
```

e apagar a função local `function EntrarNaTurma({ aoEntrar }) { ... }` inteira (do `function EntrarNaTurma` até o `}` que fecha o componente, logo antes de `function TurmaCard`). O resto da `TurmasPage` não muda.

- [ ] **Passo 2: chamadas à API e prazo relativo**

No fim de `frontend/src/api/aluno.js`, acrescentar:

```js

// ── início ───────────────────────────────────────────────────────────────────

export const getInicio = () => alunoApi.get('/aluno/inicio')

export const contarNovidades = () => alunoApi.get('/aluno/novidades/contagem')
```

No fim de `frontend/src/utils/datas.js`, acrescentar:

```js

// "hoje", "amanhã" ou "em N dias", contando dias de calendário no fuso do aluno.
export function prazoRelativo(iso, agora = new Date()) {
  const alvo = paraData(iso)
  const dia = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  const dias = Math.round((dia(alvo) - dia(agora)) / 86400000)
  if (dias <= 0) return 'hoje'
  if (dias === 1) return 'amanhã'
  return `em ${dias} dias`
}
```

- [ ] **Passo 3: a página do Início**

Criar `frontend/src/pages/aluno/InicioPage.jsx`:

```jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getInicio } from '../../api/aluno'
import EntrarNaTurma from '../../components/EntrarNaTurma'
import Spinner from '../../components/Spinner'
import { modoLabel } from '../../utils/atividade'
import { prazoRelativo } from '../../utils/datas'
import { shortError } from '../../utils/errorLabels'

const TEXTO_DA_NOVIDADE = {
  retorno: 'Seu professor respondeu ao seu erro',
  exercicio: 'Exercício novo pronto na trilha',
}

function linkDaNovidade(n) {
  return n.tipo === 'retorno'
    ? `/aluno/atividades/${n.exam_id}/questoes/${n.question_number}`
    : `/aluno/treino/${n.exercicio_id}`
}

function linkDoContinuar(c) {
  if (c.origem === 'trilha') return `/aluno/treino/${c.exercicio_id}`
  if (c.situacao === 'proxima') return `/aluno/atividades/${c.exam_id}`
  return `/aluno/atividades/${c.exam_id}/questoes/${c.question_number}`
}

function Novidades({ itens }) {
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold text-gray-900">Novidades</h2>
      <div className="space-y-2">
        {itens.map(n => (
          <Link
            key={`${n.tipo}-${n.exam_id ?? ''}-${n.question_number ?? ''}-${n.exercicio_id ?? ''}`}
            to={linkDaNovidade(n)}
            className="flex items-center gap-3 bg-white rounded-xl border border-purple-200 p-4 hover:border-purple-400 transition-colors"
          >
            <span className="w-2 h-2 rounded-full bg-purple-600 shrink-0" aria-hidden="true" />
            <div className="min-w-0">
              <p className="text-sm font-medium text-gray-900">{TEXTO_DA_NOVIDADE[n.tipo]}</p>
              <p className="text-xs text-gray-500 truncate">{n.titulo}</p>
            </div>
          </Link>
        ))}
      </div>
    </section>
  )
}

function Continuar({ item }) {
  const emAndamento = item.situacao === 'em_andamento'
  const detalhes = [
    item.turma_nome,
    emAndamento && `${item.tentativas} tentativa${item.tentativas === 1 ? '' : 's'}`,
    emAndamento && item.ultimo_erro && `último erro: ${shortError(item.ultimo_erro)}`,
  ].filter(Boolean)

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col sm:flex-row sm:items-center gap-4">
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">
          {emAndamento ? 'Continuar de onde parou' : 'Próxima atividade'}
        </p>
        <p className="mt-1 text-sm font-medium text-gray-900 truncate">
          {item.origem === 'trilha' ? `Trilha · ${item.titulo}` : item.titulo}
        </p>
        {detalhes.length > 0 && (
          <p className="text-xs text-gray-400 mt-0.5">{detalhes.join(' · ')}</p>
        )}
      </div>
      <Link
        to={linkDoContinuar(item)}
        className="inline-flex items-center justify-center text-sm px-5 py-2.5 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-700 transition-colors"
      >
        {emAndamento ? 'Continuar' : 'Começar'}
      </Link>
    </section>
  )
}

function Prazos({ itens }) {
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold text-gray-900">Prazos próximos</h2>
      <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
        {itens.map(p => (
          <Link
            key={p.exam_id}
            to={`/aluno/atividades/${p.exam_id}`}
            className="flex items-center justify-between gap-3 px-5 py-3 hover:bg-gray-50 transition-colors"
          >
            <div className="min-w-0">
              <p className="text-sm text-gray-900 truncate">{p.titulo}</p>
              <p className="text-xs text-gray-400">{p.turma_nome}</p>
            </div>
            <p className={`text-xs font-medium shrink-0 ${p.tipo === 'fecha' ? 'text-yellow-700' : 'text-purple-600'}`}>
              {modoLabel(p.modo)} · {p.tipo} {prazoRelativo(p.quando)}
            </p>
          </Link>
        ))}
      </div>
    </section>
  )
}

export default function InicioPage() {
  const [inicio, setInicio] = useState(null)
  const [erro, setErro] = useState(false)

  const carregar = () => getInicio()
    .then(({ data }) => { setInicio(data); setErro(false) })
    .catch(() => setErro(true))

  useEffect(() => { carregar() }, [])

  if (erro) {
    return (
      <div className="bg-white rounded-xl border border-dashed border-gray-200 p-10 text-center">
        <p className="text-sm text-gray-500">Não foi possível carregar o início.</p>
      </div>
    )
  }

  if (!inicio) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="w-6 h-6 text-purple-600" />
      </div>
    )
  }

  // Conta nova cai aqui: uma tela só, com o que ela precisa fazer.
  if (!inicio.tem_turma) {
    return (
      <div className="max-w-md mx-auto py-10 space-y-4">
        <div className="text-center">
          <h1 className="text-xl font-semibold text-gray-900">Comece entrando na sua turma</h1>
          <p className="mt-1 text-sm text-gray-500">
            Suas atividades aparecem aqui assim que você entrar.
          </p>
        </div>
        <EntrarNaTurma aoEntrar={carregar} />
      </div>
    )
  }

  const { novidades, continuar, prazos } = inicio
  const tudoEmDia = novidades.length === 0 && !continuar && prazos.length === 0

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Início</h1>
        <p className="text-sm text-gray-400 mt-0.5">
          O que chegou para você, onde você parou e o que vence logo.
        </p>
      </div>

      {novidades.length > 0 && <Novidades itens={novidades} />}
      {continuar && <Continuar item={continuar} />}
      {prazos.length > 0 && <Prazos itens={prazos} />}

      {tudoEmDia && (
        <div className="bg-white rounded-xl border border-dashed border-gray-200 p-10 text-center">
          <p className="text-sm text-gray-500">Tudo em dia. Que tal treinar?</p>
          <Link
            to="/aluno/treino"
            className="mt-2 inline-block text-sm font-medium text-purple-600 hover:text-purple-700"
          >
            Ir para a trilha
          </Link>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Passo 4: a rota**

Em `frontend/src/App.jsx`, trocar:

```jsx
const TurmasPage = lazy(() => import('./pages/aluno/TurmasPage'))
```

por:

```jsx
const InicioPage = lazy(() => import('./pages/aluno/InicioPage'))
const TurmasPage = lazy(() => import('./pages/aluno/TurmasPage'))
```

e trocar:

```jsx
                  <Route path="aluno" element={<Navigate to="/aluno/turmas" replace />} />
```

por:

```jsx
                  <Route path="aluno" element={<InicioPage />} />
```

O `Navigate` continua importado, porque a rota `submit/*` usa.

- [ ] **Passo 5: lint e build**

Rodar: `cd frontend && rtk proxy ./node_modules/.bin/eslint .`
Esperado: os mesmos 4 erros antigos (`QuestionPage.jsx` e `TestCasesPage.jsx`), nenhum novo.

Rodar: `cd frontend && npm run build`
Esperado: build sem erro.

- [ ] **Passo 6: commitar**

```bash
/usr/bin/git add frontend/src/components/EntrarNaTurma.jsx frontend/src/pages/aluno/TurmasPage.jsx frontend/src/pages/aluno/InicioPage.jsx frontend/src/api/aluno.js frontend/src/utils/datas.js frontend/src/App.jsx
```
```bash
/usr/bin/git commit -m "feat(aluno): pagina inicio com novidades, continuar e prazos"
```

---

### Task 10: "Início" no menu com a bolinha de novidades

**Arquivos:**
- Alterar: `frontend/src/components/AlunoLayout.jsx`

**Interfaces:**
- Consome: `contarNovidades()` da Task 9, que devolve `{ total }`.
- Produz: nada para outras tarefas.

- [ ] **Passo 1: a bolinha no menu**

Em `frontend/src/components/AlunoLayout.jsx`, trocar:

```jsx
import { useEffect, useRef } from 'react'
import { Link, NavLink, Outlet, useNavigate, useSearchParams } from 'react-router-dom'
import { registrarAcesso } from '../api/aluno'
```

por:

```jsx
import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { contarNovidades, registrarAcesso } from '../api/aluno'
```

Logo depois da constante `linkClass`, acrescentar:

```jsx

function LinkInicio({ novidades }) {
  return (
    <NavLink to="/aluno" end className={linkClass}>
      <span className="inline-flex items-center gap-1.5">
        Início
        {novidades > 0 && (
          <span
            className="min-w-[1.125rem] h-[1.125rem] px-1 rounded-full bg-purple-600 text-white text-[10px] font-semibold leading-[1.125rem] text-center"
            aria-label={`${novidades} novidade${novidades === 1 ? '' : 's'}`}
          >
            {novidades > 9 ? '9+' : novidades}
          </span>
        )}
      </span>
    </NavLink>
  )
}
```

Dentro de `AlunoLayout`, trocar:

```jsx
  const via = searchParams.get('via')
  const registrou = useRef(false)
```

por:

```jsx
  const via = searchParams.get('via')
  const registrou = useRef(false)
  const { pathname } = useLocation()
  const [novidades, setNovidades] = useState(0)

  // RF20: a bolinha do Início, refeita a cada troca de página, porque abrir a
  // questão ou o exercício é o que marca a novidade como vista.
  useEffect(() => {
    let ativo = true
    contarNovidades()
      .then(({ data }) => { if (ativo) setNovidades(data.total) })
      .catch(() => { if (ativo) setNovidades(0) })
    return () => { ativo = false }
  }, [pathname])
```

No menu do computador, trocar:

```jsx
            <div className="hidden sm:flex items-center gap-1">
              <NavLink to="/aluno/turmas" className={linkClass}>Turmas</NavLink>
```

por:

```jsx
            <div className="hidden sm:flex items-center gap-1">
              <LinkInicio novidades={novidades} />
              <NavLink to="/aluno/turmas" className={linkClass}>Turmas</NavLink>
```

No menu do celular, trocar:

```jsx
        <div className="sm:hidden border-t border-gray-100 px-6 py-2 flex gap-1">
          <NavLink to="/aluno/turmas" className={linkClass}>Turmas</NavLink>
```

por:

```jsx
        <div className="sm:hidden border-t border-gray-100 px-6 py-2 flex gap-1">
          <LinkInicio novidades={novidades} />
          <NavLink to="/aluno/turmas" className={linkClass}>Turmas</NavLink>
```

- [ ] **Passo 2: lint e build**

Rodar: `cd frontend && rtk proxy ./node_modules/.bin/eslint .`
Esperado: os mesmos 4 erros antigos, nenhum novo.

Rodar: `cd frontend && npm run build`
Esperado: build sem erro.

- [ ] **Passo 3: commitar**

```bash
/usr/bin/git add frontend/src/components/AlunoLayout.jsx
```
```bash
/usr/bin/git commit -m "feat(aluno): inicio no menu com a bolinha de novidades"
```
