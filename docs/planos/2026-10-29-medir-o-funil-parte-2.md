# Medir o funil, parte 2: plano de implementação

> **Para quem executa:** usar a skill `sdd` (recomendado) ou a execução sem subagentes descrita nela. Passos com caixa de seleção (`- [ ]`).

**Objetivo:** registrar cada abertura do app do aluno com a origem, medir por ela a retenção, os sinais de hábito e o momento de sucesso, gravar a origem de cada matrícula com um convite que já leva o código da turma e fazer a trilha contar numa turma só a partir da matrícula.

**Arquitetura:** a migração 0018 cria a tabela `acessos` e a coluna `enrollments.origem`. Um serviço novo (`acesso_service`) grava o acesso com o descarte de 30 minutos, atrás da rota `POST /aluno/acessos`, chamada pelo `AlunoLayout`. As contas novas entram como funções puras em `funil_regras.py`, sobre registros simples, e o `funil_service.py` lê os acessos, as datas das provas e a origem, filtra pela matrícula e monta o funil. O convite é uma página nova do aluno (`/aluno/convite/:codigo`) e um botão novo na página da turma do professor.

**Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic v2, pytest, React 19, react-router 7, Tailwind v4.

**Spec:** `docs/specs/2026-10-29-medir-o-funil-parte-2.md`. O plano argumenta a partir dele, e quem executa lê os dois. A seção "Definições" do spec é a regra de cada conta. O spec da parte 1 (`docs/specs/2026-10-26-medir-o-funil.md`) continua valendo no que não muda.

## Restrições globais

- Migração `0018`, arquivo `backend/migrations/versions/0018_acessos_e_origem_da_matricula.py`, `revision = '0018'`, `down_revision = '0017'`. Tabela `acessos` com `id`, `student_id` (chave estrangeira simples para `students.id`), `momento` (`DateTime`, obrigatório) e `via` (`String(32)`, nula), mais o índice `ix_acessos_student_id_momento` em `(student_id, momento)`. Coluna `enrollments.origem`, `String(16)`, nula.
- Origens da matrícula: `"convite"` e `"codigo"` (`Enrollment.ORIGEM_CONVITE` e `Enrollment.ORIGEM_CODIGO`), nula nas matrículas de antes. A origem só é gravada quando a matrícula é criada.
- Origens de acesso aceitas: só `{"convite"}`. A `via` passa por `strip().lower()`. Vazia ou desconhecida vira nula.
- Descarte do acesso: recentes são os acessos do aluno com `momento > agora - 30 minutos`. Não grava quando o novo vem sem origem e há algum recente, ou quando vem com origem e há um recente com a mesma origem. Exatamente 30 minutos depois já grava.
- Filtro pela matrícula: numa turma, tentativas da trilha e acessos só contam com `momento >= entrada` da matrícula do aluno nela. Envios de lista não são filtrados.
- Prova que puxa: atividade publicada da turma, `modo` diferente de `"treino"`, com ao menos uma data. Intervalo fechado de `abre_em - 3 dias` (ou sem limite) até `fecha_em` (ou sem limite). Sem nenhuma data, não puxa.
- Sessão: eventos (matrícula, acessos, tentativas) seguidos com intervalo de até 30 minutos, incluído o limite.
- Taxas e médias com uma casa decimal, em porcentagem, nulas quando o denominador é zero. As taxas da retenção são sobre a `base`. A do momento de sucesso é sobre os matriculados.
- O total do script traz da retenção só `semana`, `base`, `voltaram`, `taxa`, `voltaram_por_envio` e `taxa_por_envio`.
- RNF04: nenhuma rota de professor devolve acesso por aluno, e o script não mostra nome de aluno. O acesso não guarda IP, navegador nem página. RN09: a saúde continua pelos envios.
- Textos exatos do aluno: `"Depois de entrar, você vai direto para a turma."`, `"Entrando na turma..."`, `"Este convite não vale mais. Peça o código ao professor."`, `"Ir para minhas turmas"`, `"Não foi possível entrar na turma agora."`, `"Tentar de novo"`.
- Textos exatos do professor: botão `"Copiar convite"` (e `"Copiado"`), ajuda `"Passe o código ou o convite com link, que já leva o código. N já entraram com conta."` (com `"entrou"` para um aluno), a mensagem do convite como está na Task 10, `"Momento de sucesso: ninguém corrigiu um erro ainda."`.
- Testes: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest <alvo> -q`. Nunca `rtk pytest`. Nunca duas suítes ao mesmo tempo.
- Git dentro do worktree: rodar `git` direto, sem `rtk` (o isolamento recusa `rtk git`), a partir da raiz do worktree `/home/otavio/produtos-digitais-cs1/.claude/worktrees/medir-o-funil-parte-2`. Commit sem `Co-Authored-By`.
- Não rodar `alembic upgrade` nem o script contra o banco de desenvolvimento. Isso fica para o smoke do `fechamento`.
- Lint do front: a base tem 4 erros antigos em `QuestionPage.jsx` e `TestCasesPage.jsx`. Só erro novo bloqueia. Ruff do projeto: regras `F`, `E9` e `B`.
- Datas como no resto do banco: UTC sem fuso, `datetime.utcnow()`.

## Estrutura de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `backend/migrations/versions/0018_acessos_e_origem_da_matricula.py` | Criar | Tabela `acessos` e coluna `enrollments.origem` |
| `backend/app/models/orm.py` | Alterar | Modelo `Acesso`, `Enrollment.origem` e constantes, `Student.acessos` |
| `backend/app/services/acesso_service.py` | Criar | Normalizar a origem e gravar o acesso com o descarte |
| `backend/app/models/schemas.py` | Alterar | `AcessoRequest`, `origem` na entrada, esquemas novos do funil |
| `backend/app/api/routes/student.py` | Alterar | Rota `POST /aluno/acessos` e repasse da origem na entrada |
| `backend/app/auth/student_service.py` | Alterar | `entrar_na_turma` grava a origem |
| `backend/app/services/funil_regras.py` | Alterar | Registros novos, prova que puxa, origem, retenção pelo acesso, sessão e momento de sucesso |
| `backend/app/services/funil_service.py` | Alterar | Ler origem, acessos e datas das provas, filtrar pela matrícula, total novo |
| `backend/scripts/funil.py` | Alterar | Linhas novas do relatório |
| `backend/tests/unit/test_student_model.py` | Alterar | Origem da matrícula e acesso no modelo |
| `backend/tests/test_acesso.py` | Criar | Serviço e rota de acesso |
| `backend/tests/test_student_auth.py` | Alterar | Origem na entrada da turma |
| `backend/tests/unit/test_funil_regras.py` | Alterar | Regras puras novas e chamadas atualizadas |
| `backend/tests/test_funil.py` | Alterar | Serviço com banco, filtro, total e rota |
| `backend/tests/test_script_funil.py` | Alterar | Linhas novas do script |
| `frontend/src/api/aluno.js` | Alterar | `registrarAcesso` e origem em `entrarNaTurma` |
| `frontend/src/utils/convitePendente.js` | Criar | Guardar, ler e apagar o código do convite no `sessionStorage` |
| `frontend/src/components/AlunoLayout.jsx` | Alterar | Registrar o acesso |
| `frontend/src/pages/aluno/ConvitePage.jsx` | Criar | Entrada pelo link do convite |
| `frontend/src/App.jsx` | Alterar | Rota `aluno/convite/:codigo` |
| `frontend/src/pages/aluno/AlunoRegisterPage.jsx` | Alterar | Aviso e volta ao convite depois do cadastro |
| `frontend/src/pages/aluno/AlunoLoginPage.jsx` | Alterar | Aviso e volta ao convite depois do login |
| `frontend/src/pages/aluno/TurmasPage.jsx` | Alterar | Entrada digitada com origem `codigo` |
| `frontend/src/pages/TurmaDetailPage.jsx` | Alterar | Botão "Copiar convite" e ajuda nova |
| `frontend/src/components/FunilDaTurma.jsx` | Alterar | Origem, momento de sucesso, retenção pelo acesso e sinais |

As regras puras continuam separadas do serviço para os testes delas não montarem nada no banco. O `funil_service` só lê, filtra e converte.

---

### Task 1: migração 0018 e modelos

**Arquivos:**
- Criar: `backend/migrations/versions/0018_acessos_e_origem_da_matricula.py`
- Alterar: `backend/app/models/orm.py` (import do SQLAlchemy, classes `Student` e `Enrollment`, classe nova `Acesso` logo depois de `Enrollment`)
- Teste: `backend/tests/unit/test_student_model.py`

**Interfaces:**
- Consome: nada de outras tarefas.
- Produz: modelo `Acesso` (`id`, `student_id`, `momento`, `via`, relação `student`). `Enrollment.origem: str | None`, `Enrollment.ORIGEM_CONVITE = "convite"`, `Enrollment.ORIGEM_CODIGO = "codigo"`. `Student.acessos`.

- [ ] **Passo 1: aplicar a coluna no banco de teste**

O `conftest.py` usa `create_all`, que cria a tabela nova mas não altera `enrollments`. Rodar a partir da raiz do worktree:

```bash
cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -c "
import os
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv('.env')
url = urlparse(os.environ['DATABASE_URL'])
teste = urlunparse(url._replace(path=url.path + '_test'))
with create_engine(teste).begin() as c:
    c.execute(text('ALTER TABLE enrollments ADD COLUMN IF NOT EXISTS origem VARCHAR(16)'))
print('coluna aplicada no banco de teste')
"
```

Esperado: `coluna aplicada no banco de teste`. Registrar no relatório da tarefa que o `ALTER` foi aplicado no banco de teste.

- [ ] **Passo 2: escrever os testes que falham**

Em `backend/tests/unit/test_student_model.py`, trocar o import do ORM por:

```python
from app.models.orm import Acesso, Enrollment, Student, Submission, Turma
```

e acrescentar no fim do arquivo:

```python
def test_matricula_guarda_a_origem(db, professor, student):
    turma = create_turma("Algoritmos", "COMP101", db, professor_id=professor.id)
    db.add(Enrollment(student_id=student.id, turma_id=turma.id,
                      origem=Enrollment.ORIGEM_CONVITE))
    db.commit()
    assert db.query(Enrollment).one().origem == "convite"
    assert Enrollment.ORIGEM_CODIGO == "codigo"


def test_matricula_sem_origem_fica_nula(db, professor, student):
    turma = create_turma("Algoritmos", "COMP101", db, professor_id=professor.id)
    db.add(Enrollment(student_id=student.id, turma_id=turma.id))
    db.commit()
    assert db.query(Enrollment).one().origem is None


def test_acesso_tem_momento_e_sai_junto_com_o_aluno(db, student):
    db.add(Acesso(student_id=student.id, via="convite"))
    db.commit()
    acesso = db.query(Acesso).one()
    assert acesso.momento is not None
    assert acesso.via == "convite"
    assert student.acessos == [acesso]

    db.delete(student)
    db.commit()
    assert db.query(Acesso).count() == 0
```

- [ ] **Passo 3: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_student_model.py -q`
Esperado: FALHA na coleta com `ImportError: cannot import name 'Acesso'`.

- [ ] **Passo 4: escrever o modelo**

Em `backend/app/models/orm.py`, trocar o import do SQLAlchemy por:

```python
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float, Index,
    UniqueConstraint,
)
```

Na classe `Student`, logo depois de `submissions = relationship(...)`, acrescentar:

```python
    acessos = relationship("Acesso", back_populates="student", cascade="all, delete-orphan")
```

Trocar a classe `Enrollment` inteira por:

```python
class Enrollment(Base):
    """Matrícula do aluno na turma (vínculo aluno↔turma). `origem` diz como ele
    entrou, pelo link do convite ou digitando o código. Nula nas de antes da 0018."""
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "turma_id", name="uq_enrollment_student_turma"),
    )

    ORIGEM_CONVITE = "convite"
    ORIGEM_CODIGO = "codigo"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    turma_id = Column(Integer, ForeignKey("turmas.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    origem = Column(String(16), nullable=True)

    student = relationship("Student", back_populates="enrollments")
    turma = relationship("Turma", back_populates="enrollments")


class Acesso(Base):
    """Abertura do app do aluno. `via` é a origem que veio no link (`?via=`), nula
    quando ele abriu por conta própria. Não guarda IP, navegador nem página."""
    __tablename__ = "acessos"
    __table_args__ = (
        Index("ix_acessos_student_id_momento", "student_id", "momento"),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    momento = Column(DateTime, nullable=False, default=datetime.utcnow)
    via = Column(String(32), nullable=True)

    student = relationship("Student", back_populates="acessos")
```

- [ ] **Passo 5: escrever a migração**

Criar `backend/migrations/versions/0018_acessos_e_origem_da_matricula.py`:

```python
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
```

- [ ] **Passo 6: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_student_model.py -q`
Esperado: PASSA.

Conferir que a migração carrega com o número certo:

```bash
cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -c "
import importlib.util
spec = importlib.util.spec_from_file_location('m', 'migrations/versions/0018_acessos_e_origem_da_matricula.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print(m.revision, m.down_revision)
"
```

Esperado: `0018 0017`.

- [ ] **Passo 7: rodar a suíte inteira**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q 2>&1 | tail -3`
Esperado: tudo passando, 304 testes (301 da base mais 3).

- [ ] **Passo 8: commitar**

```bash
git add backend/migrations/versions/0018_acessos_e_origem_da_matricula.py backend/app/models/orm.py backend/tests/unit/test_student_model.py
git commit -m "feat(funil): migracao 0018 com a tabela de acessos e a origem da matricula"
```

---

### Task 2: serviço e rota de acesso

**Arquivos:**
- Criar: `backend/app/services/acesso_service.py`
- Alterar: `backend/app/models/schemas.py` (classe nova `AcessoRequest`, logo depois de `TurmaEntrarRequest`)
- Alterar: `backend/app/api/routes/student.py` (imports e rota nova no fim do arquivo, antes de `_to_response`)
- Teste: `backend/tests/test_acesso.py`

**Interfaces:**
- Consome: modelo `Acesso` da Task 1.
- Produz: `VIAS_ACEITAS`, `JANELA_DO_ACESSO`, `normalizar_via(via: str | None) -> str | None`, `registrar_acesso(student_id: int, via: str | None, db: Session, agora: datetime | None = None) -> bool`. Rota `POST /aluno/acessos` com corpo `{"via": str | null}` e resposta 204.

- [ ] **Passo 1: escrever os testes que falham**

Criar `backend/tests/test_acesso.py`:

```python
"""Registro de acesso do aluno (RF14): descarte em 30 minutos e origem aceita."""
from datetime import datetime, timedelta

import pytest

from app.auth.service import create_access_token
from app.auth.student_service import create_student_token
from app.models.orm import Acesso, Student
from app.services.acesso_service import registrar_acesso

AGORA = datetime(2026, 10, 28, 12, 0)


@pytest.fixture()
def aluno(db):
    s = Student(email="ana@teste.com", nome="Ana", senha_hash="x")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _vias(db, aluno):
    return [a.via for a in
            db.query(Acesso).filter_by(student_id=aluno.id).order_by(Acesso.momento).all()]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


class TestRegistrarAcesso:
    def test_grava_o_primeiro_acesso(self, db, aluno):
        assert registrar_acesso(aluno.id, None, db, agora=AGORA) is True
        acesso = db.query(Acesso).one()
        assert acesso.momento == AGORA
        assert acesso.via is None

    def test_sem_origem_descarta_antes_de_30_minutos_e_grava_com_30(self, db, aluno):
        registrar_acesso(aluno.id, None, db, agora=AGORA)
        assert registrar_acesso(aluno.id, None, db, agora=AGORA + timedelta(minutes=29)) is False
        assert registrar_acesso(aluno.id, None, db, agora=AGORA + timedelta(minutes=30)) is True
        assert _vias(db, aluno) == [None, None]

    def test_sem_origem_logo_depois_do_convite_e_descartado(self, db, aluno):
        registrar_acesso(aluno.id, "convite", db, agora=AGORA)
        assert registrar_acesso(aluno.id, None, db, agora=AGORA + timedelta(minutes=5)) is False
        assert _vias(db, aluno) == ["convite"]

    def test_convite_logo_depois_de_abrir_grava_e_o_segundo_nao(self, db, aluno):
        registrar_acesso(aluno.id, None, db, agora=AGORA)
        assert registrar_acesso(aluno.id, "convite", db, agora=AGORA + timedelta(minutes=5)) is True
        assert registrar_acesso(aluno.id, "convite", db, agora=AGORA + timedelta(minutes=6)) is False
        assert _vias(db, aluno) == [None, "convite"]

    @pytest.mark.parametrize("recebida, gravada", [
        (" Convite ", "convite"),
        ("", None),
        ("whatsapp", None),
    ])
    def test_origem_normalizada(self, db, aluno, recebida, gravada):
        registrar_acesso(aluno.id, recebida, db, agora=AGORA)
        assert _vias(db, aluno) == [gravada]

    def test_acesso_de_outro_aluno_nao_interfere(self, db, aluno):
        outro = Student(email="bia@teste.com", nome="Bia", senha_hash="x")
        db.add(outro)
        db.commit()
        registrar_acesso(outro.id, None, db, agora=AGORA)
        assert registrar_acesso(aluno.id, None, db, agora=AGORA + timedelta(minutes=1)) is True


class TestRota:
    def test_aluno_registra_e_recebe_204(self, client, db, aluno):
        resp = client.post("/aluno/acessos", json={"via": "convite"},
                           headers=_auth(create_student_token(aluno.id)))
        assert resp.status_code == 204
        assert _vias(db, aluno) == ["convite"]

    def test_corpo_vazio_grava_sem_origem(self, client, db, aluno):
        resp = client.post("/aluno/acessos", json={},
                           headers=_auth(create_student_token(aluno.id)))
        assert resp.status_code == 204
        assert _vias(db, aluno) == [None]

    def test_sem_token_da_401(self, client):
        assert client.post("/aluno/acessos", json={}).status_code == 401

    def test_token_de_professor_da_401(self, client, professor):
        resp = client.post("/aluno/acessos", json={},
                           headers=_auth(create_access_token(professor.id)))
        assert resp.status_code == 401

    def test_via_com_33_caracteres_da_422(self, client, aluno):
        resp = client.post("/aluno/acessos", json={"via": "x" * 33},
                           headers=_auth(create_student_token(aluno.id)))
        assert resp.status_code == 422
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_acesso.py -q`
Esperado: FALHA na coleta com `ModuleNotFoundError: No module named 'app.services.acesso_service'`.

- [ ] **Passo 3: escrever o serviço**

Criar `backend/app/services/acesso_service.py`:

```python
"""Registro da abertura do app do aluno (RF14), no máximo um por janela."""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.orm import Acesso

# Só origens conhecidas entram no banco, para não guardar texto livre da URL.
# Os tipos de aviso chegam nas fases 3 e 4.
VIAS_ACEITAS = {"convite"}
JANELA_DO_ACESSO = timedelta(minutes=30)


def normalizar_via(via: str | None) -> str | None:
    via = (via or "").strip().lower()
    return via if via in VIAS_ACEITAS else None


def registrar_acesso(student_id: int, via: str | None, db: Session,
                     agora: datetime | None = None) -> bool:
    """Reabrir o app sem origem perto de qualquer acesso não conta, para quem
    entrou pelo convite e voltou à aba não ganhar uma abertura sem aviso. Com
    origem, só não conta se a mesma origem já entrou na janela."""
    agora = agora or datetime.utcnow()
    via = normalizar_via(via)
    recentes = {
        v for (v,) in db.query(Acesso.via).filter(
            Acesso.student_id == student_id,
            Acesso.momento > agora - JANELA_DO_ACESSO,
        ).all()
    }
    if recentes and (via is None or via in recentes):
        return False
    db.add(Acesso(student_id=student_id, momento=agora, via=via))
    db.commit()
    return True
```

- [ ] **Passo 4: escrever o esquema e a rota**

Em `backend/app/models/schemas.py`, logo depois da classe `TurmaEntrarRequest`, acrescentar:

```python
class AcessoRequest(BaseModel):
    via: Optional[str] = Field(None, max_length=32)
```

Em `backend/app/api/routes/student.py`, trocar o import dos esquemas por:

```python
from app.models.schemas import (
    AcessoRequest, PasswordChange, StudentCreate, StudentLogin, StudentResponse,
    StudentTokenResponse, StudentUpdate, TurmaDoAlunoResponse, TurmaEntrarRequest,
)
from app.services.acesso_service import registrar_acesso
```

e acrescentar a rota logo depois de `minhas_turmas`, antes de `_to_response`:

```python
@router.post("/acessos", status_code=204)
def registrar(
    body: AcessoRequest,
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    registrar_acesso(current.id, body.via, db)
```

- [ ] **Passo 5: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_acesso.py -q`
Esperado: PASSA, 13 testes.

- [ ] **Passo 6: commitar**

```bash
git add backend/app/services/acesso_service.py backend/app/models/schemas.py backend/app/api/routes/student.py backend/tests/test_acesso.py
git commit -m "feat(acesso): registro da abertura do app do aluno com descarte em 30 minutos"
```

---

### Task 3: origem na entrada da turma

**Arquivos:**
- Alterar: `backend/app/models/schemas.py` (classe `TurmaEntrarRequest`)
- Alterar: `backend/app/auth/student_service.py` (`entrar_na_turma`)
- Alterar: `backend/app/api/routes/student.py` (`entrar`)
- Teste: `backend/tests/test_student_auth.py` (classe `TestEntrarNaTurma`)

**Interfaces:**
- Consome: `Enrollment.origem`, `Enrollment.ORIGEM_CODIGO` da Task 1.
- Produz: `TurmaEntrarRequest.origem: Literal["convite", "codigo"] = "codigo"`. `entrar_na_turma(student, codigo_acesso, db, origem=Enrollment.ORIGEM_CODIGO) -> Turma`. A Task 9 manda `origem` no corpo de `POST /aluno/turmas/entrar`.

- [ ] **Passo 1: escrever os testes que falham**

Em `backend/tests/test_student_auth.py`, dentro da classe `TestEntrarNaTurma`, logo depois de `test_entrar_duas_vezes_nao_duplica`, acrescentar:

```python
    def test_convite_grava_a_origem(self, client, db, turma_com_codigo):
        turma, _ = turma_com_codigo
        token = _registrar(client).json()["access_token"]
        resp = client.post("/aluno/turmas/entrar",
                           json={"codigo_acesso": "ABC234", "origem": "convite"},
                           headers=_auth(token))
        assert resp.status_code == 200
        assert db.query(Enrollment).filter_by(turma_id=turma.id).one().origem == "convite"

    def test_sem_origem_grava_codigo(self, client, db, turma_com_codigo):
        turma, _ = turma_com_codigo
        token = _registrar(client).json()["access_token"]
        client.post("/aluno/turmas/entrar", json={"codigo_acesso": "ABC234"}, headers=_auth(token))
        assert db.query(Enrollment).filter_by(turma_id=turma.id).one().origem == "codigo"

    def test_entrar_de_novo_nao_muda_a_origem(self, client, db, turma_com_codigo):
        turma, _ = turma_com_codigo
        token = _registrar(client).json()["access_token"]
        client.post("/aluno/turmas/entrar", json={"codigo_acesso": "ABC234"}, headers=_auth(token))
        resp = client.post("/aluno/turmas/entrar",
                           json={"codigo_acesso": "ABC234", "origem": "convite"},
                           headers=_auth(token))
        assert resp.status_code == 200
        assert db.query(Enrollment).filter_by(turma_id=turma.id).one().origem == "codigo"

    def test_origem_fora_da_lista_da_422(self, client, turma_com_codigo):
        token = _registrar(client).json()["access_token"]
        resp = client.post("/aluno/turmas/entrar",
                           json={"codigo_acesso": "ABC234", "origem": "whatsapp"},
                           headers=_auth(token))
        assert resp.status_code == 422

    def test_convite_com_codigo_inexistente_da_404_sem_matricula(self, client, db, turma_com_codigo):
        token = _registrar(client).json()["access_token"]
        resp = client.post("/aluno/turmas/entrar",
                           json={"codigo_acesso": "ZZZZZZ", "origem": "convite"},
                           headers=_auth(token))
        assert resp.status_code == 404
        assert db.query(Enrollment).count() == 0
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_student_auth.py -q`
Esperado: FALHA em `test_convite_grava_a_origem` (origem `None` em vez de `"convite"`), `test_sem_origem_grava_codigo`, `test_entrar_de_novo_nao_muda_a_origem` e `test_origem_fora_da_lista_da_422` (200 em vez de 422).

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/models/schemas.py`, trocar a classe `TurmaEntrarRequest` por:

```python
class TurmaEntrarRequest(BaseModel):
    codigo_acesso: str
    origem: Literal["convite", "codigo"] = "codigo"
```

Em `backend/app/auth/student_service.py`, trocar `entrar_na_turma` por:

```python
def entrar_na_turma(student: Student, codigo_acesso: str, db: Session,
                    origem: str = Enrollment.ORIGEM_CODIGO) -> Turma:
    """Vincula o aluno à turma pelo código de acesso. Idempotente: entrar de novo
    na mesma turma devolve o vínculo existente em vez de duplicar, e a origem
    continua a da primeira entrada."""
    codigo = (codigo_acesso or "").strip().upper()
    turma = db.query(Turma).filter(Turma.codigo_acesso == codigo).first()
    if not turma:
        raise ValueError("Código de turma inválido.")

    ja_vinculado = db.query(Enrollment).filter(
        Enrollment.student_id == student.id,
        Enrollment.turma_id == turma.id,
    ).first()
    if not ja_vinculado:
        db.add(Enrollment(student_id=student.id, turma_id=turma.id, origem=origem))
        db.commit()
        vincular_submissoes_anteriores(student, db)
    return turma
```

Em `backend/app/api/routes/student.py`, na rota `entrar`, trocar a chamada por:

```python
        turma = entrar_na_turma(current, body.codigo_acesso, db, body.origem)
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_student_auth.py -q`
Esperado: PASSA.

- [ ] **Passo 5: commitar**

```bash
git add backend/app/models/schemas.py backend/app/auth/student_service.py backend/app/api/routes/student.py backend/tests/test_student_auth.py
git commit -m "feat(turma): matricula grava se o aluno entrou pelo convite ou pelo codigo"
```

---

### Task 4: regras puras, registros novos, prova que puxa e aquisição por origem

**Arquivos:**
- Alterar: `backend/app/services/funil_regras.py`
- Teste: `backend/tests/unit/test_funil_regras.py`

**Interfaces:**
- Consome: `Enrollment.ORIGEM_CONVITE` e `Enrollment.ORIGEM_CODIGO` da Task 1.
- Produz: `ANTECEDENCIA_DA_PROVA = timedelta(days=3)`. `Matricula(aluno, nome, entrada, origem=None)`. Registro congelado `Acesso(aluno: int, momento: datetime, via: str | None = None)`. Registro congelado `JanelaDeProva(inicio: datetime | None, fim: datetime | None)`. `janela_da_prova(abre_em, fecha_em) -> JanelaDeProva | None`. `com_prova_marcada(momento, janelas) -> bool`. `por_origem(matriculas) -> {"convite": int, "codigo": int, "sem_origem": int}`. `aquisicao(...)` passa a devolver também `por_origem`.

- [ ] **Passo 1: escrever os testes que falham**

Em `backend/tests/unit/test_funil_regras.py`, trocar o import por:

```python
from app.services.funil_regras import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, Matricula, Tentativa, aquisicao, ativacao,
    com_prova_marcada, erros_corrigidos, janela_da_prova, montar_funil, north_star,
    por_origem, protecao, resultado_da_lista, resultado_da_trilha, retencao,
    retencao_da_semana, saude, ultimas_semanas,
)
```

trocar o helper `mat` por:

```python
def mat(aluno, entrada, nome="Aluno", origem=None):
    return Matricula(aluno=aluno, nome=nome, entrada=entrada, origem=origem)
```

e acrescentar, logo depois da classe `TestAquisicao`:

```python
class TestPorOrigem:
    def test_conta_as_tres_origens(self):
        matriculas = [mat(1, DIA0, origem="convite"), mat(2, DIA0, origem="convite"),
                      mat(3, DIA0, origem="codigo"), mat(4, DIA0)]
        esperado = {"convite": 2, "codigo": 1, "sem_origem": 1}
        assert por_origem(matriculas) == esperado
        assert aquisicao(matriculas, None)["por_origem"] == esperado

    def test_turma_vazia(self):
        assert por_origem([]) == {"convite": 0, "codigo": 0, "sem_origem": 0}


ABRE = datetime(2026, 10, 20, 8, 0)
FECHA = datetime(2026, 10, 20, 10, 0)


class TestProvaQuePuxa:
    def test_com_as_duas_datas_puxa_de_tres_dias_antes_ate_o_fechamento(self):
        janelas = [janela_da_prova(ABRE, FECHA)]
        assert com_prova_marcada(ABRE - timedelta(days=3), janelas)
        assert com_prova_marcada(FECHA, janelas)
        assert not com_prova_marcada(ABRE - timedelta(days=3, seconds=1), janelas)
        assert not com_prova_marcada(FECHA + timedelta(seconds=1), janelas)

    def test_so_com_abertura_puxa_dali_em_diante(self):
        janelas = [janela_da_prova(ABRE, None)]
        assert not com_prova_marcada(ABRE - timedelta(days=4), janelas)
        assert com_prova_marcada(ABRE + timedelta(days=60), janelas)

    def test_so_com_fechamento_puxa_ate_ele(self):
        janelas = [janela_da_prova(None, FECHA)]
        assert com_prova_marcada(FECHA - timedelta(days=60), janelas)
        assert not com_prova_marcada(FECHA + timedelta(seconds=1), janelas)

    def test_sem_datas_nao_tem_janela(self):
        assert janela_da_prova(None, None) is None
        assert not com_prova_marcada(ABRE, [])

    def test_basta_uma_prova_puxar(self):
        outra = janela_da_prova(datetime(2026, 11, 10), datetime(2026, 11, 10, 2))
        janelas = [janela_da_prova(ABRE, FECHA), outra]
        assert com_prova_marcada(datetime(2026, 11, 8), janelas)
        assert not com_prova_marcada(datetime(2026, 11, 1), janelas)
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_funil_regras.py -q`
Esperado: FALHA na coleta com `ImportError: cannot import name 'com_prova_marcada'`.

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/funil_regras.py`:

Acrescentar aos imports:

```python
from app.models.orm import Enrollment
```

Logo depois de `JANELA = timedelta(days=7)`, acrescentar:

```python
# A prova puxa o aluno desde 3 dias antes de abrir, a janela do aviso "Prova chegando".
ANTECEDENCIA_DA_PROVA = timedelta(days=3)
```

Trocar a classe `Matricula` por:

```python
@dataclass(frozen=True)
class Matricula:
    aluno: int
    nome: str
    entrada: datetime
    origem: str | None = None


@dataclass(frozen=True)
class Acesso:
    """Uma abertura do app do aluno. `via` nula é abertura por conta própria."""
    aluno: int
    momento: datetime
    via: str | None = None


@dataclass(frozen=True)
class JanelaDeProva:
    """Intervalo fechado em que uma prova puxa o aluno. Lado nulo é sem limite."""
    inicio: datetime | None
    fim: datetime | None
```

Logo antes de `def aquisicao`, acrescentar:

```python
def por_origem(matriculas: list[Matricula]) -> dict:
    contagem = Counter(m.origem for m in matriculas)
    convite = contagem[Enrollment.ORIGEM_CONVITE]
    codigo = contagem[Enrollment.ORIGEM_CODIGO]
    return {"convite": convite, "codigo": codigo, "sem_origem": len(matriculas) - convite - codigo}
```

No `return` de `aquisicao`, acrescentar a chave `"por_origem": por_origem(matriculas),` logo antes de `"meta": META_AQUISICAO,`.

Logo antes de `def retencao_da_semana`, acrescentar:

```python
def janela_da_prova(abre_em: datetime | None, fecha_em: datetime | None) -> JanelaDeProva | None:
    """Prova sem data não puxa ninguém."""
    if abre_em is None and fecha_em is None:
        return None
    inicio = abre_em - ANTECEDENCIA_DA_PROVA if abre_em else None
    return JanelaDeProva(inicio=inicio, fim=fecha_em)


def com_prova_marcada(momento: datetime, janelas: list[JanelaDeProva]) -> bool:
    return any(
        (j.inicio is None or j.inicio <= momento) and (j.fim is None or momento <= j.fim)
        for j in janelas
    )
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_funil_regras.py tests/test_funil.py -q`
Esperado: PASSA. O `test_funil.py` continua verde porque a chave nova da aquisição não muda nada que ele confere.

- [ ] **Passo 5: commitar**

```bash
git add backend/app/services/funil_regras.py backend/tests/unit/test_funil_regras.py
git commit -m "feat(funil): prova que puxa o aluno e matriculas por origem"
```

---

### Task 5: regras puras, retenção pelo acesso e sinais de hábito

**Arquivos:**
- Alterar: `backend/app/services/funil_regras.py` (imports, `DadosDaTurma` novo, `retencao_da_semana`, `retencao`, `montar_funil`)
- Alterar: `backend/app/services/funil_service.py` (sai `_DadosDaTurma`, entra `DadosDaTurma`, chamadas novas)
- Teste: `backend/tests/unit/test_funil_regras.py` (classes `TestRetencao` e `TestMontarFunil`)
- Teste: `backend/tests/test_funil.py` (`test_tamanho_da_turma_e_atividade_de_treino`)

**Interfaces:**
- Consome: `Acesso`, `JanelaDeProva` e `com_prova_marcada` da Task 4.
- Produz: registro `DadosDaTurma(matriculas, tentativas, questoes_abertas, acessos=[], janelas=[])`. `retencao_da_semana(semana, matriculas, tentativas, acessos, janelas) -> dict` com as chaves `semana`, `base`, `voltaram`, `taxa`, `sem_prova_marcada`, `taxa_sem_prova_marcada`, `sem_aviso`, `taxa_sem_aviso`, `voltaram_por_envio`, `taxa_por_envio`, `por_conta_propria`, `taxa_por_conta_propria`. `retencao(matriculas, tentativas, acessos, janelas, agora) -> dict`. `montar_funil(dados: DadosDaTurma, alunos_previstos, agora) -> dict`.

- [ ] **Passo 1: escrever os testes que falham**

Em `backend/tests/unit/test_funil_regras.py`, trocar o import por:

```python
from app.services.funil_regras import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, Acesso, DadosDaTurma, Matricula, Tentativa,
    aquisicao, ativacao, com_prova_marcada, erros_corrigidos, janela_da_prova,
    montar_funil, north_star, por_origem, protecao, resultado_da_lista,
    resultado_da_trilha, retencao, retencao_da_semana, saude, ultimas_semanas,
)
```

Trocar a classe `TestRetencao` inteira por:

```python
SEMANA = "2026-10-19"
ANTES = datetime(2026, 10, 14, 10)
NA_SEMANA = datetime(2026, 10, 21, 10)


def ac(aluno, momento, via=None):
    return Acesso(aluno=aluno, momento=momento, via=via)


class TestRetencao:
    def test_pelo_envio_e_por_conta_propria_na_semana(self):
        matriculas = [mat(1, DIA0), mat(2, DIA0), mat(3, DIA0), mat(4, datetime(2026, 10, 27))]
        tentativas = [
            tent(ERRO, datetime(2026, 10, 14), aluno=1),
            tent(ERRO, datetime(2026, 10, 20), aluno=1),
            tent(ERRO, datetime(2026, 10, 21), aluno=2),
            tent(ERRO, datetime(2026, 10, 10), aluno=3),
            tent(ERRO, datetime(2026, 10, 22), aluno=3, por_conta_propria=True),
            tent(ERRO, datetime(2026, 10, 10), aluno=4),
            tent(ERRO, datetime(2026, 10, 22), aluno=4),
        ]
        s = retencao_da_semana(SEMANA, matriculas, tentativas, [], [])
        assert s["base"] == 3
        assert s["voltaram_por_envio"] == 2
        assert s["por_conta_propria"] == 1
        assert s["taxa_por_envio"] == 66.7
        assert s["taxa_por_conta_propria"] == 33.3
        assert s["voltaram"] == 0

    def test_por_conta_propria_tambem_pede_envio_antes(self):
        tentativas = [tent(ERRO, datetime(2026, 10, 20), por_conta_propria=True)]
        s = retencao_da_semana(SEMANA, [mat(1, DIA0)], tentativas, [], [])
        assert s["voltaram_por_envio"] == 0
        assert s["por_conta_propria"] == 0

    def test_voltou_pelo_acesso_com_acesso_antes(self):
        s = retencao_da_semana(SEMANA, [mat(1, DIA0)], [], [ac(1, ANTES), ac(1, NA_SEMANA)], [])
        assert s["voltaram"] == 1
        assert s["taxa"] == 100.0
        assert s["voltaram_por_envio"] == 0

    def test_voltou_pelo_acesso_com_so_envio_antes(self):
        s = retencao_da_semana(SEMANA, [mat(1, DIA0)], [tent(ERRO, ANTES)], [ac(1, NA_SEMANA)], [])
        assert s["voltaram"] == 1

    def test_acesso_sem_atividade_antes_nao_conta(self):
        s = retencao_da_semana(SEMANA, [mat(1, DIA0)], [], [ac(1, NA_SEMANA)], [])
        assert s["voltaram"] == 0

    def test_envio_sem_acesso_conta_so_pelo_envio(self):
        tentativas = [tent(ERRO, ANTES), tent(ERRO, NA_SEMANA)]
        s = retencao_da_semana(SEMANA, [mat(1, DIA0)], tentativas, [], [])
        assert s["voltaram"] == 0
        assert s["voltaram_por_envio"] == 1

    def test_sem_prova_marcada_so_com_acesso_fora_das_janelas(self):
        janelas = [janela_da_prova(datetime(2026, 10, 23, 8), datetime(2026, 10, 23, 10))]
        acessos = [
            # aluno 1 só abriu dentro da janela da prova
            ac(1, ANTES), ac(1, datetime(2026, 10, 21, 10)),
            # aluno 2 abriu uma vez antes de a prova começar a puxar
            ac(2, ANTES), ac(2, datetime(2026, 10, 19, 9)), ac(2, datetime(2026, 10, 22, 9)),
        ]
        s = retencao_da_semana(SEMANA, [mat(1, DIA0), mat(2, DIA0)], [], acessos, janelas)
        assert s["voltaram"] == 2
        assert s["sem_prova_marcada"] == 1
        assert s["taxa_sem_prova_marcada"] == 50.0

    def test_sem_aviso_so_com_acesso_sem_origem(self):
        acessos = [ac(1, ANTES), ac(1, NA_SEMANA), ac(2, ANTES), ac(2, NA_SEMANA, via="convite")]
        s = retencao_da_semana(SEMANA, [mat(1, DIA0), mat(2, DIA0)], [], acessos, [])
        assert s["voltaram"] == 2
        assert s["sem_aviso"] == 1
        assert s["taxa_sem_aviso"] == 50.0

    def test_base_zero_deixa_todas_as_taxas_nulas(self):
        s = retencao_da_semana(SEMANA, [], [], [], [])
        for chave in ("taxa", "taxa_sem_prova_marcada", "taxa_sem_aviso",
                      "taxa_por_envio", "taxa_por_conta_propria"):
            assert s[chave] is None

    def test_cartao_usa_a_ultima_semana_completa(self):
        r = retencao([mat(1, DIA0)], [], [], [], AGORA)
        assert len(r["semanas"]) == 8
        assert r["semanas"][-1]["semana"] == "2026-10-26"
        assert r["ultima_completa"]["semana"] == SEMANA
        assert r["meta"] == 50.0
```

Trocar a classe `TestMontarFunil` por:

```python
class TestMontarFunil:
    def test_traz_os_seis_blocos(self):
        dados = DadosDaTurma(matriculas=[mat(1, _dias(30))], tentativas=[], questoes_abertas=ABERTAS)
        funil = montar_funil(dados, 40, AGORA)
        assert set(funil) == {"north_star", "aquisicao", "ativacao", "retencao", "saude", "protecao"}
        assert funil["aquisicao"]["alunos_previstos"] == 40
```

Em `backend/tests/test_funil.py`, no fim de `test_tamanho_da_turma_e_atividade_de_treino`, trocar `assert ultima["voltaram"] == 1` por:

```python
        assert ultima["voltaram_por_envio"] == 1
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_funil_regras.py tests/test_funil.py -q`
Esperado: FALHA na coleta com `ImportError: cannot import name 'DadosDaTurma'`.

- [ ] **Passo 3: escrever as regras**

Em `backend/app/services/funil_regras.py`:

Trocar `from dataclasses import dataclass` por:

```python
from dataclasses import dataclass, field
```

Logo depois da classe `JanelaDeProva`, acrescentar:

```python
@dataclass
class DadosDaTurma:
    """O que o serviço leu de uma turma, com a trilha e os acessos já filtrados
    pela matrícula."""
    matriculas: list[Matricula]
    tentativas: list[Tentativa]
    questoes_abertas: dict[int, int | None]
    acessos: list[Acesso] = field(default_factory=list)
    janelas: list[JanelaDeProva] = field(default_factory=list)
```

Trocar `retencao_da_semana` e `retencao` por:

```python
def retencao_da_semana(semana: str, matriculas: list[Matricula], tentativas: list[Tentativa],
                       acessos: list[Acesso], janelas: list[JanelaDeProva]) -> dict:
    """Voltou quem abriu o app na semana e já tinha feito algo antes dela, acesso
    ou envio. O envio antes conta para as semanas de antes da tabela de acessos
    não aparecerem zeradas. Os sinais de hábito são recortes de quem voltou. Pelo
    envio é a conta da parte 1."""
    inicio = datetime.combine(date.fromisoformat(semana), time.min)
    fim = inicio + timedelta(weeks=1)
    base = {m.aluno for m in matriculas if m.entrada < fim}

    enviaram_antes = {t.aluno for t in tentativas if t.momento < inicio}
    envios_na_semana = [t for t in tentativas if inicio <= t.momento < fim]
    por_envio = {t.aluno for t in envios_na_semana} & enviaram_antes & base
    proprios = {t.aluno for t in envios_na_semana if t.por_conta_propria} & enviaram_antes & base

    ativos_antes = enviaram_antes | {a.aluno for a in acessos if a.momento < inicio}
    acessos_na_semana = [a for a in acessos if inicio <= a.momento < fim]
    voltaram = {a.aluno for a in acessos_na_semana} & ativos_antes & base
    sem_prova = {a.aluno for a in acessos_na_semana
                 if not com_prova_marcada(a.momento, janelas)} & voltaram
    sem_aviso = {a.aluno for a in acessos_na_semana if a.via is None} & voltaram
    return {
        "semana": semana,
        "base": len(base),
        "voltaram": len(voltaram),
        "taxa": taxa(len(voltaram), len(base)),
        "sem_prova_marcada": len(sem_prova),
        "taxa_sem_prova_marcada": taxa(len(sem_prova), len(base)),
        "sem_aviso": len(sem_aviso),
        "taxa_sem_aviso": taxa(len(sem_aviso), len(base)),
        "voltaram_por_envio": len(por_envio),
        "taxa_por_envio": taxa(len(por_envio), len(base)),
        "por_conta_propria": len(proprios),
        "taxa_por_conta_propria": taxa(len(proprios), len(base)),
    }


def retencao(matriculas: list[Matricula], tentativas: list[Tentativa], acessos: list[Acesso],
             janelas: list[JanelaDeProva], agora: datetime) -> dict:
    """O cartão usa a última semana completa: a atual começa toda segunda perto
    de zero e pareceria queda."""
    semanas = [retencao_da_semana(s, matriculas, tentativas, acessos, janelas)
               for s in ultimas_semanas(agora)]
    return {"semanas": semanas, "ultima_completa": semanas[-2], "meta": META_RETENCAO}
```

Trocar `montar_funil` por:

```python
def montar_funil(dados: DadosDaTurma, alunos_previstos: int | None, agora: datetime) -> dict:
    corrigidos = erros_corrigidos(dados.tentativas)
    return {
        "north_star": north_star(corrigidos, agora),
        "aquisicao": aquisicao(dados.matriculas, alunos_previstos),
        "ativacao": ativacao(dados.matriculas, dados.tentativas, corrigidos),
        "retencao": retencao(dados.matriculas, dados.tentativas, dados.acessos, dados.janelas, agora),
        "saude": saude(dados.matriculas, dados.tentativas, dados.questoes_abertas, agora),
        "protecao": protecao(dados.tentativas),
    }
```

- [ ] **Passo 4: adaptar o serviço**

Em `backend/app/services/funil_service.py`:

Apagar a linha `from dataclasses import dataclass` e a classe `_DadosDaTurma` inteira.

Trocar o import das regras por:

```python
from app.services.funil_regras import (
    LISTA, TRILHA, DadosDaTurma, Matricula, Tentativa, alunos_ativados, erros_corrigidos,
    montar_funil, north_star, resultado_da_lista, resultado_da_trilha, retencao_da_semana,
    taxa, ultimas_semanas,
)
```

Trocar `_dados_da_turma` por:

```python
def _dados_da_turma(turma: Turma, db: Session, agora: datetime) -> DadosDaTurma:
    matriculas = _matriculas(turma.id, db)
    alunos = [m.aluno for m in matriculas]
    tentativas: list[Tentativa] = []
    if alunos:
        tentativas = _tentativas_de_lista(turma.id, alunos, db) + _tentativas_de_trilha(alunos, db)
    return DadosDaTurma(matriculas=matriculas, tentativas=tentativas,
                        questoes_abertas=_questoes_abertas(turma.id, db, agora))
```

Em `funil_da_turma`, trocar a chamada de `montar_funil` por:

```python
        **montar_funil(dados, turma.alunos_previstos, agora),
```

Em `funil_geral`, trocar a linha `funil = montar_funil(...)` (que ocupa duas linhas) por:

```python
        funil = montar_funil(dados, turma.alunos_previstos, agora)
```

e trocar a chave `"retencao_ultima_semana"` do `return` por:

```python
            "retencao_ultima_semana": retencao_da_semana(
                ultimas_semanas(agora)[-2], matriculas, tentativas, [], []),
```

- [ ] **Passo 5: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_funil_regras.py tests/test_funil.py tests/test_script_funil.py -q`
Esperado: PASSA.

- [ ] **Passo 6: commitar**

```bash
git add backend/app/services/funil_regras.py backend/app/services/funil_service.py backend/tests/unit/test_funil_regras.py backend/tests/test_funil.py
git commit -m "feat(funil): retencao pelo acesso com os sinais sem prova marcada e sem aviso"
```

---

### Task 6: regras puras, sessão e momento de sucesso

**Arquivos:**
- Alterar: `backend/app/services/funil_regras.py` (imports, constante, `fim_da_sessao`, `sucesso`, `montar_funil`)
- Teste: `backend/tests/unit/test_funil_regras.py`

**Interfaces:**
- Consome: `Acesso`, `DadosDaTurma` e `montar_funil(dados, alunos_previstos, agora)` da Task 5.
- Produz: `JANELA_DA_SESSAO = timedelta(minutes=30)`. `fim_da_sessao(entrada: datetime, momentos: list[datetime]) -> datetime`. `sucesso(matriculas, tentativas, acessos, corrigidos) -> dict` com `chegaram`, `ainda_nao_chegaram`, `mediana_minutos`, `na_sessao_da_matricula`, `taxa_na_sessao_da_matricula`. `montar_funil` passa a devolver também o bloco `"sucesso"`.

- [ ] **Passo 1: escrever os testes que falham**

Em `backend/tests/unit/test_funil_regras.py`, trocar o import por:

```python
from app.services.funil_regras import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, Acesso, DadosDaTurma, Matricula, Tentativa,
    aquisicao, ativacao, com_prova_marcada, erros_corrigidos, fim_da_sessao,
    janela_da_prova, montar_funil, north_star, por_origem, protecao, resultado_da_lista,
    resultado_da_trilha, retencao, retencao_da_semana, saude, sucesso, ultimas_semanas,
)
```

Acrescentar, logo antes da classe `TestMontarFunil`:

```python
class TestSessao:
    def test_eventos_a_cada_30_minutos_continuam_a_sessao(self):
        momentos = [DIA0 + timedelta(minutes=30), DIA0 + timedelta(minutes=60)]
        assert fim_da_sessao(DIA0, momentos) == DIA0 + timedelta(minutes=60)

    def test_intervalo_maior_que_30_minutos_encerra(self):
        momentos = [DIA0 + timedelta(minutes=10), DIA0 + timedelta(minutes=40, seconds=1)]
        assert fim_da_sessao(DIA0, momentos) == DIA0 + timedelta(minutes=10)

    def test_sem_evento_termina_na_matricula(self):
        assert fim_da_sessao(DIA0, []) == DIA0

    def test_evento_de_antes_da_matricula_nao_entra(self):
        assert fim_da_sessao(DIA0, [DIA0 - timedelta(minutes=5)]) == DIA0


def _corrigiu(aluno, minutos):
    """Erro um minuto depois da matrícula e acerto `minutos` depois dela."""
    return [tent(ERRO, DIA0 + timedelta(minutes=1), aluno=aluno),
            tent(ACERTO, DIA0 + timedelta(minutes=minutos), aluno=aluno)]


class TestSucesso:
    def test_na_sessao_da_matricula_em_outra_sessao_e_sem_chegar(self):
        matriculas = [mat(1, DIA0), mat(2, DIA0), mat(3, DIA0)]
        tentativas = _corrigiu(1, 20) + _corrigiu(2, 1440) + [tent(ERRO, DIA0 + timedelta(minutes=10), aluno=3)]
        s = sucesso(matriculas, tentativas, [], erros_corrigidos(tentativas))
        assert s["chegaram"] == 2
        assert s["ainda_nao_chegaram"] == 1
        assert s["na_sessao_da_matricula"] == 1
        assert s["taxa_na_sessao_da_matricula"] == 33.3
        assert s["mediana_minutos"] == 730.0

    def test_mediana_com_quantidade_impar(self):
        matriculas = [mat(1, DIA0), mat(2, DIA0), mat(3, DIA0)]
        tentativas = _corrigiu(1, 10) + _corrigiu(2, 20) + _corrigiu(3, 90)
        s = sucesso(matriculas, tentativas, [], erros_corrigidos(tentativas))
        assert s["mediana_minutos"] == 20.0

    def test_acesso_mantem_a_sessao_viva(self):
        tentativas = [tent(ERRO, DIA0 + timedelta(minutes=5)), tent(ACERTO, DIA0 + timedelta(minutes=50))]
        corrigidos = erros_corrigidos(tentativas)
        sem_acesso = sucesso([mat(1, DIA0)], tentativas, [], corrigidos)
        com_acesso = sucesso([mat(1, DIA0)], tentativas,
                             [Acesso(aluno=1, momento=DIA0 + timedelta(minutes=30))], corrigidos)
        assert sem_acesso["na_sessao_da_matricula"] == 0
        assert com_acesso["na_sessao_da_matricula"] == 1

    def test_ninguem_chegou(self):
        s = sucesso([mat(1, DIA0)], [], [], [])
        assert s["chegaram"] == 0
        assert s["ainda_nao_chegaram"] == 1
        assert s["mediana_minutos"] is None
        assert s["taxa_na_sessao_da_matricula"] == 0.0

    def test_turma_vazia_tem_taxa_nula(self):
        assert sucesso([], [], [], [])["taxa_na_sessao_da_matricula"] is None

    def test_correcao_antes_da_matricula_nao_conta(self):
        tentativas = [tent(ERRO, DIA0 - timedelta(days=2)), tent(ACERTO, DIA0 - timedelta(days=1))]
        s = sucesso([mat(1, DIA0)], tentativas, [], erros_corrigidos(tentativas))
        assert s["chegaram"] == 0
        assert s["ainda_nao_chegaram"] == 1
```

Trocar a classe `TestMontarFunil` por:

```python
class TestMontarFunil:
    def test_traz_os_sete_blocos(self):
        dados = DadosDaTurma(matriculas=[mat(1, _dias(30))], tentativas=[], questoes_abertas=ABERTAS)
        funil = montar_funil(dados, 40, AGORA)
        assert set(funil) == {"north_star", "aquisicao", "ativacao", "retencao", "saude",
                              "protecao", "sucesso"}
        assert funil["aquisicao"]["alunos_previstos"] == 40
        assert funil["sucesso"]["ainda_nao_chegaram"] == 1
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_funil_regras.py -q`
Esperado: FALHA na coleta com `ImportError: cannot import name 'fim_da_sessao'`.

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/funil_regras.py`:

Acrescentar aos imports:

```python
from statistics import median
```

Logo depois de `ANTECEDENCIA_DA_PROVA`, acrescentar:

```python
# A mesma janela do registro de acesso: 30 minutos sem evento encerram a sessão.
JANELA_DA_SESSAO = timedelta(minutes=30)
```

Logo antes de `def montar_funil`, acrescentar:

```python
def fim_da_sessao(entrada: datetime, momentos: list[datetime]) -> datetime:
    """Último instante da sessão que começa na matrícula. Ela segue enquanto cada
    evento vem até JANELA_DA_SESSAO depois do anterior."""
    fim = entrada
    for momento in sorted(m for m in momentos if m >= entrada):
        if momento - fim > JANELA_DA_SESSAO:
            break
        fim = momento
    return fim


def sucesso(matriculas: list[Matricula], tentativas: list[Tentativa], acessos: list[Acesso],
            corrigidos: list[tuple[int, datetime]]) -> dict:
    """RF16: o primeiro erro corrigido depois da matrícula, quanto tempo levou e se
    veio ainda na sessão em que o aluno entrou na turma."""
    entrada = {m.aluno: m.entrada for m in matriculas}
    primeiro: dict[int, datetime] = {}
    for aluno, momento in corrigidos:
        if aluno in entrada and momento >= entrada[aluno]:
            if aluno not in primeiro or momento < primeiro[aluno]:
                primeiro[aluno] = momento

    eventos: dict[int, list[datetime]] = defaultdict(list)
    for t in tentativas:
        eventos[t.aluno].append(t.momento)
    for a in acessos:
        eventos[a.aluno].append(a.momento)

    minutos = []
    na_sessao = 0
    for aluno, momento in primeiro.items():
        minutos.append((momento - entrada[aluno]).total_seconds() / 60)
        if momento <= fim_da_sessao(entrada[aluno], eventos[aluno]):
            na_sessao += 1
    return {
        "chegaram": len(primeiro),
        "ainda_nao_chegaram": len(matriculas) - len(primeiro),
        "mediana_minutos": round(median(minutos), 1) if minutos else None,
        "na_sessao_da_matricula": na_sessao,
        "taxa_na_sessao_da_matricula": taxa(na_sessao, len(matriculas)),
    }
```

No `return` de `montar_funil`, acrescentar a última chave:

```python
        "sucesso": sucesso(dados.matriculas, dados.tentativas, dados.acessos, corrigidos),
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_funil_regras.py tests/test_funil.py -q`
Esperado: PASSA.

- [ ] **Passo 5: commitar**

```bash
git add backend/app/services/funil_regras.py backend/tests/unit/test_funil_regras.py
git commit -m "feat(funil): momento de sucesso com a mediana e a sessao da matricula"
```

---

### Task 7: serviço do funil, leitura nova, filtro pela matrícula e resposta

**Arquivos:**
- Alterar: `backend/app/services/funil_service.py`
- Alterar: `backend/app/services/funil_regras.py` (só o comentário dentro de `saude`)
- Alterar: `backend/app/models/schemas.py` (`AquisicaoFunil`, `SemanaRetencao`, `FunilTurmaResponse`, classes novas `OrigemDasMatriculas` e `SucessoFunil`)
- Teste: `backend/tests/test_funil.py`

O spec chama a leitura das datas de `_datas_das_provas`. Aqui ela já devolve as janelas prontas, por isso o nome é `_janelas_das_provas`.

**Interfaces:**
- Consome: modelo `Acesso` e `Enrollment.origem` da Task 1. `Acesso`, `JanelaDeProva`, `janela_da_prova` da Task 4. `DadosDaTurma`, `retencao_da_semana(semana, matriculas, tentativas, acessos, janelas)` e `montar_funil(dados, alunos_previstos, agora)` da Task 5. O bloco `"sucesso"` da Task 6.
- Produz: `GET /turmas/{id}/funil` com `aquisicao.por_origem`, a semana nova da retenção e o bloco `sucesso`. `funil_geral` com `total.retencao_ultima_semana` só com `semana`, `base`, `voltaram`, `taxa`, `voltaram_por_envio` e `taxa_por_envio`, e cada linha de `por_turma` com as chaves novas `por_origem`, `taxa_retencao_envio` e `taxa_sucesso_na_sessao` (`taxa_retencao` passa a ser pelo acesso). A Task 8 usa esse `funil_geral`. A Task 10 usa a resposta da rota.

- [ ] **Passo 1: escrever os testes que falham**

Em `backend/tests/test_funil.py`:

Trocar o import do ORM por:

```python
from app.models.orm import (
    Acesso, Enrollment, ExercicioGerado, Exam, Professor, Question, Student, Submission,
    TentativaDeTreino, Turma,
)
```

Trocar o helper `_aluno` por:

```python
def _aluno(db, email, nome, turmas, entrada=AGORA - timedelta(days=20), origem=None):
    aluno = Student(email=email, nome=nome, senha_hash="x")
    db.add(aluno)
    db.flush()
    for turma in turmas:
        db.add(Enrollment(student_id=aluno.id, turma_id=turma.id, created_at=entrada,
                          origem=origem))
    db.commit()
    db.refresh(aluno)
    return aluno
```

Logo depois do helper `_treino`, acrescentar:

```python
def _acesso(db, aluno, momento, via=None):
    db.add(Acesso(student_id=aluno.id, momento=momento, via=via))
    db.commit()
```

Logo antes da classe `TestFunilGeral`, acrescentar:

```python
class TestFiltroPelaMatricula:
    def test_trilha_de_antes_da_matricula_fica_fora_da_turma(self, db, professor):
        turma = _turma(db, professor)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma], entrada=AGORA - timedelta(days=2))
        exercicio = _treino(db, ana, False, AGORA - timedelta(days=5))
        _treino(db, ana, True, AGORA - timedelta(days=4), exercicio=exercicio)

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["north_star"]["total"] == 0
        assert funil["ativacao"]["com_primeiro_envio"] == 0

    def test_trilha_entre_duas_matriculas_conta_so_na_turma_em_que_ja_estava(self, db, professor):
        a = _turma(db, professor, "CS1 A")
        b = _turma(db, professor, "CS1 B")
        ana = _aluno(db, "ana@teste.com", "Ana", [a], entrada=AGORA - timedelta(days=10))
        db.add(Enrollment(student_id=ana.id, turma_id=b.id, created_at=AGORA - timedelta(days=2)))
        db.commit()
        exercicio = _treino(db, ana, False, AGORA - timedelta(days=5))
        _treino(db, ana, True, AGORA - timedelta(days=4), exercicio=exercicio)

        assert funil_da_turma(a, db, agora=AGORA)["north_star"]["total"] == 1
        assert funil_da_turma(b, db, agora=AGORA)["north_star"]["total"] == 0
        assert funil_geral(db, agora=AGORA)["total"]["north_star"]["total"] == 1

    def test_lista_religada_de_antes_da_matricula_conta_na_north_star_e_nao_no_sucesso(
            self, db, professor):
        turma = _turma(db, professor)
        questao = _atividade(db, turma)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma], entrada=AGORA - timedelta(days=2))
        _envio(db, ana, questao, ERRO_COMUM, AGORA - timedelta(days=5))
        _envio(db, ana, questao, "Correto", AGORA - timedelta(days=4))

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["north_star"]["total"] == 1
        assert funil["sucesso"]["chegaram"] == 0

    def test_acesso_de_antes_da_matricula_nao_conta_na_retencao(self, db, professor):
        turma = _turma(db, professor)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma], entrada=datetime(2026, 10, 21))
        _acesso(db, ana, datetime(2026, 10, 15, 10))
        _acesso(db, ana, datetime(2026, 10, 22, 10))

        ultima = funil_da_turma(turma, db, agora=AGORA)["retencao"]["ultima_completa"]

        assert ultima["base"] == 1
        assert ultima["voltaram"] == 0


class TestRetencaoPeloAcesso:
    def test_voltou_pelo_acesso_com_os_sinais(self, db, professor):
        turma = _turma(db, professor)
        # A prova puxa de 2026-10-20 08:00 até 2026-10-23 10:00.
        prova = _atividade(db, turma, abre_em=datetime(2026, 10, 23, 8),
                           fecha_em=datetime(2026, 10, 23, 10))
        # Treino e rascunho com data cobririam 2026-10-19, mas não puxam.
        _atividade(db, turma, modo="treino", abre_em=datetime(2026, 10, 19),
                   fecha_em=datetime(2026, 10, 25))
        _atividade(db, turma, publicada=False, abre_em=datetime(2026, 10, 19, 12),
                   fecha_em=datetime(2026, 10, 25))
        ana = _aluno(db, "ana@teste.com", "Ana", [turma])
        bia = _aluno(db, "bia@teste.com", "Bia", [turma])
        caio = _aluno(db, "caio@teste.com", "Caio", [turma])
        _acesso(db, ana, datetime(2026, 10, 14, 10))
        _acesso(db, ana, datetime(2026, 10, 21, 10))
        _acesso(db, bia, datetime(2026, 10, 14, 10))
        _acesso(db, bia, datetime(2026, 10, 19, 9), via="convite")
        _envio(db, caio, prova, ERRO_COMUM, datetime(2026, 10, 14, 10))
        _envio(db, caio, prova, ERRO_COMUM, datetime(2026, 10, 20, 10))

        ultima = funil_da_turma(turma, db, agora=AGORA)["retencao"]["ultima_completa"]

        assert ultima["semana"] == "2026-10-19"
        assert ultima["base"] == 3
        assert ultima["voltaram"] == 2
        assert ultima["taxa"] == 66.7
        assert ultima["sem_prova_marcada"] == 1
        assert ultima["sem_aviso"] == 1
        assert ultima["voltaram_por_envio"] == 1
        assert ultima["taxa_por_envio"] == 33.3

    def test_matriculas_por_origem(self, db, professor):
        turma = _turma(db, professor)
        _aluno(db, "ana@teste.com", "Ana", [turma], origem="convite")
        _aluno(db, "bia@teste.com", "Bia", [turma], origem="codigo")
        _aluno(db, "caio@teste.com", "Caio", [turma])

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["aquisicao"]["por_origem"] == {"convite": 1, "codigo": 1, "sem_origem": 1}
```

Dentro da classe `TestFunilGeral`, acrescentar:

```python
    def test_total_e_linhas_trazem_os_campos_novos(self, db, professor):
        turma = _turma(db, professor)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma], origem="convite")
        _acesso(db, ana, datetime(2026, 10, 14, 10))
        _acesso(db, ana, datetime(2026, 10, 21, 10))

        geral = funil_geral(db, agora=AGORA)

        semana = geral["total"]["retencao_ultima_semana"]
        assert set(semana) == {"semana", "base", "voltaram", "taxa", "voltaram_por_envio",
                               "taxa_por_envio"}
        assert semana["voltaram"] == 1
        linha = geral["por_turma"][0]
        assert linha["taxa_retencao"] == 100.0
        assert linha["taxa_retencao_envio"] == 0.0
        assert linha["por_origem"] == {"convite": 1, "codigo": 0, "sem_origem": 0}
        assert linha["taxa_sucesso_na_sessao"] == 0.0
```

Na classe `TestRota`, no fim de `test_dono_recebe_o_funil`, acrescentar:

```python
        assert corpo["aquisicao"]["por_origem"] == {"convite": 0, "codigo": 0, "sem_origem": 1}
        assert {"sem_prova_marcada", "taxa_sem_aviso", "voltaram_por_envio",
                "taxa_por_envio"} <= set(corpo["retencao"]["ultima_completa"])
        assert corpo["sucesso"]["ainda_nao_chegaram"] == 1
        assert corpo["sucesso"]["mediana_minutos"] is None
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_funil.py -q`
Esperado: FALHA em `test_trilha_de_antes_da_matricula_fica_fora_da_turma`, `test_trilha_entre_duas_matriculas_conta_so_na_turma_em_que_ja_estava`, `test_voltou_pelo_acesso_com_os_sinais`, `test_matriculas_por_origem`, `test_total_e_linhas_trazem_os_campos_novos` e `test_dono_recebe_o_funil`. Os outros dois já passam: `test_lista_religada_de_antes_da_matricula_conta_na_north_star_e_nao_no_sucesso` porque a regra do sucesso da Task 6 já ignora o que veio antes da matrícula, e `test_acesso_de_antes_da_matricula_nao_conta_na_retencao` porque os acessos ainda não são lidos. Eles ficam para proteger o filtro depois desta tarefa.

- [ ] **Passo 3: escrever os esquemas**

Em `backend/app/models/schemas.py`, logo antes de `class AquisicaoFunil`, acrescentar:

```python
class OrigemDasMatriculas(BaseModel):
    convite: int
    codigo: int
    sem_origem: int
```

Na classe `AquisicaoFunil`, acrescentar o campo `por_origem: OrigemDasMatriculas` logo antes de `meta: float`.

Trocar a classe `SemanaRetencao` por:

```python
class SemanaRetencao(BaseModel):
    semana: str
    base: int
    voltaram: int
    taxa: Optional[float] = None
    sem_prova_marcada: int
    taxa_sem_prova_marcada: Optional[float] = None
    sem_aviso: int
    taxa_sem_aviso: Optional[float] = None
    voltaram_por_envio: int
    taxa_por_envio: Optional[float] = None
    por_conta_propria: int
    taxa_por_conta_propria: Optional[float] = None
```

Logo antes de `class FunilTurmaResponse`, acrescentar:

```python
class SucessoFunil(BaseModel):
    chegaram: int
    ainda_nao_chegaram: int
    mediana_minutos: Optional[float] = None
    na_sessao_da_matricula: int
    taxa_na_sessao_da_matricula: Optional[float] = None
```

e na classe `FunilTurmaResponse`, acrescentar o último campo `sucesso: SucessoFunil`.

- [ ] **Passo 4: escrever a leitura e o filtro**

Trocar o conteúdo de `backend/app/services/funil_service.py` por:

```python
"""Funil da turma calculado na hora, com o que o banco já guarda.

Este módulo só lê e converte em registros. As contas estão em `funil_regras`."""
from datetime import datetime

from sqlalchemy.orm import Session, load_only

from app.models.orm import (
    Acesso as AcessoDoBanco, Enrollment, Exam, Professor, Question, Student, Submission,
    TentativaDeTreino, Turma,
)
from app.services.calendario import situacao_da_atividade
from app.services.funil_regras import (
    LISTA, TRILHA, Acesso, DadosDaTurma, JanelaDeProva, Matricula, Tentativa,
    alunos_ativados, erros_corrigidos, janela_da_prova, montar_funil, north_star,
    resultado_da_lista, resultado_da_trilha, retencao_da_semana, taxa, ultimas_semanas,
)

# Os sinais de hábito ficam fora do total: a prova é de uma turma e o total junta
# alunos de turmas diferentes.
_RETENCAO_NO_TOTAL = ("semana", "base", "voltaram", "taxa", "voltaram_por_envio", "taxa_por_envio")


def _matriculas(turma_id: int, db: Session) -> list[Matricula]:
    linhas = (
        db.query(Enrollment.student_id, Student.nome, Enrollment.created_at, Enrollment.origem)
        .join(Student, Student.id == Enrollment.student_id)
        .filter(Enrollment.turma_id == turma_id)
        .all()
    )
    return [Matricula(aluno=aluno, nome=nome, entrada=entrada, origem=origem)
            for aluno, nome, entrada, origem in linhas]


def _tentativas_de_lista(turma_id: int, alunos: list[int], db: Session) -> list[Tentativa]:
    """Envios com conta, em atividade publicada da turma. Os do TCC, importados
    só com matrícula, ficam de fora."""
    linhas = (
        db.query(Submission.id, Submission.student_id, Submission.question_id,
                 Submission.submitted_at, Submission.error_category, Exam.modo)
        .join(Question, Question.id == Submission.question_id)
        .join(Exam, Exam.id == Question.exam_id)
        .filter(
            Exam.turma_id == turma_id,
            Exam.publicada.is_(True),
            Submission.student_id.in_(alunos),
            Submission.submitted_at.isnot(None),
        )
        .all()
    )
    return [
        Tentativa(aluno=aluno, origem=LISTA, item_id=questao, momento=momento, ordem=sid,
                  resultado=resultado_da_lista(categoria),
                  por_conta_propria=modo == Exam.MODO_TREINO)
        for sid, aluno, questao, momento, categoria, modo in linhas
    ]


def _tentativas_de_trilha(alunos: list[int], db: Session) -> list[Tentativa]:
    """A trilha não tem turma, então o treino do aluno entra em todas as turmas
    dele, cada uma a partir da matrícula."""
    linhas = (
        db.query(TentativaDeTreino.id, TentativaDeTreino.student_id,
                 TentativaDeTreino.exercicio_id, TentativaDeTreino.submitted_at,
                 TentativaDeTreino.all_tests_passed, TentativaDeTreino.error_category)
        .filter(TentativaDeTreino.student_id.in_(alunos),
                TentativaDeTreino.submitted_at.isnot(None))
        .all()
    )
    return [
        Tentativa(aluno=aluno, origem=TRILHA, item_id=exercicio, momento=momento, ordem=tid,
                  resultado=resultado_da_trilha(passou, categoria), por_conta_propria=True)
        for tid, aluno, exercicio, momento, passou, categoria in linhas
    ]


def _acessos(alunos: list[int], db: Session) -> list[Acesso]:
    linhas = (
        db.query(AcessoDoBanco.student_id, AcessoDoBanco.momento, AcessoDoBanco.via)
        .filter(AcessoDoBanco.student_id.in_(alunos))
        .all()
    )
    return [Acesso(aluno=aluno, momento=momento, via=via) for aluno, momento, via in linhas]


def _janelas_das_provas(turma_id: int, db: Session) -> list[JanelaDeProva]:
    """Provas publicadas da turma com data. Atividade de treino não puxa ninguém."""
    linhas = (
        db.query(Exam.abre_em, Exam.fecha_em)
        .filter(Exam.turma_id == turma_id, Exam.publicada.is_(True),
                Exam.modo != Exam.MODO_TREINO)
        .all()
    )
    janelas = (janela_da_prova(abre_em, fecha_em) for abre_em, fecha_em in linhas)
    return [j for j in janelas if j is not None]


def _questoes_abertas(turma_id: int, db: Session, agora: datetime) -> dict[int, int | None]:
    linhas = (
        db.query(Question.id, Exam)
        .join(Exam, Exam.id == Question.exam_id)
        .options(load_only(Exam.abre_em, Exam.fecha_em, Exam.max_tentativas))
        .filter(Exam.turma_id == turma_id, Exam.publicada.is_(True))
        .all()
    )
    return {
        questao: exam.max_tentativas for questao, exam in linhas
        if situacao_da_atividade(exam, agora) == "aberta"
    }


def _desde_a_matricula(registros: list, entrada: dict[int, datetime]) -> list:
    """Trilha e acesso não têm turma. Numa turma, só vale o que veio depois de o
    aluno entrar nela."""
    return [r for r in registros if r.momento >= entrada[r.aluno]]


def _dados_da_turma(turma: Turma, db: Session, agora: datetime) -> DadosDaTurma:
    matriculas = _matriculas(turma.id, db)
    entrada = {m.aluno: m.entrada for m in matriculas}
    alunos = list(entrada)
    tentativas: list[Tentativa] = []
    acessos: list[Acesso] = []
    if alunos:
        trilha = _desde_a_matricula(_tentativas_de_trilha(alunos, db), entrada)
        tentativas = _tentativas_de_lista(turma.id, alunos, db) + trilha
        acessos = _desde_a_matricula(_acessos(alunos, db), entrada)
    return DadosDaTurma(
        matriculas=matriculas,
        tentativas=tentativas,
        questoes_abertas=_questoes_abertas(turma.id, db, agora),
        acessos=acessos,
        janelas=_janelas_das_provas(turma.id, db),
    )


def funil_da_turma(turma: Turma, db: Session, agora: datetime | None = None) -> dict:
    agora = agora or datetime.utcnow()
    dados = _dados_da_turma(turma, db, agora)
    return {
        "turma_id": turma.id,
        "gerado_em": agora.isoformat(),
        **montar_funil(dados, turma.alunos_previstos, agora),
    }


def funil_geral(db: Session, agora: datetime | None = None) -> dict:
    """Todas as turmas, para o script da equipe. O total conta cada item e cada
    aluno uma vez, então não é a soma das turmas: o treino de quem está em duas
    turmas aparece nas duas. Juntar o que cada turma leu faz cada aluno contar a
    partir da primeira matrícula."""
    agora = agora or datetime.utcnow()
    turmas = db.query(Turma).order_by(Turma.id).all()
    professores = dict(db.query(Professor.id, Professor.nome).all())

    por_turma = []
    todas: set[Tentativa] = set()
    todos_os_acessos: set[Acesso] = set()
    primeira_entrada: dict[int, Matricula] = {}
    ativados: set[int] = set()
    for turma in turmas:
        dados = _dados_da_turma(turma, db, agora)
        funil = montar_funil(dados, turma.alunos_previstos, agora)
        todas.update(dados.tentativas)
        todos_os_acessos.update(dados.acessos)
        ativados |= alunos_ativados(dados.matriculas, erros_corrigidos(dados.tentativas))
        for m in dados.matriculas:
            atual = primeira_entrada.get(m.aluno)
            if atual is None or m.entrada < atual.entrada:
                primeira_entrada[m.aluno] = m
        semana_da_turma = funil["retencao"]["ultima_completa"]
        por_turma.append({
            "turma_id": turma.id,
            "nome": turma.nome,
            "professor": professores.get(turma.professor_id),
            "matriculados": funil["aquisicao"]["matriculados"],
            "alunos_previstos": turma.alunos_previstos,
            "por_origem": funil["aquisicao"]["por_origem"],
            "taxa_ativacao": funil["ativacao"]["taxa"],
            "taxa_retencao": semana_da_turma["taxa"],
            "taxa_retencao_envio": semana_da_turma["taxa_por_envio"],
            "taxa_sucesso_na_sessao": funil["sucesso"]["taxa_na_sessao_da_matricula"],
            "north_star_semana": funil["north_star"]["semana_atual"],
            "north_star_total": funil["north_star"]["total"],
            "vermelhos": len(funil["saude"]["vermelho"]),
        })

    matriculas = list(primeira_entrada.values())
    tentativas = list(todas)
    semana = retencao_da_semana(ultimas_semanas(agora)[-2], matriculas, tentativas,
                                list(todos_os_acessos), [])
    return {
        "gerado_em": agora.isoformat(),
        "total": {
            "north_star": north_star(erros_corrigidos(tentativas), agora),
            "professores_com_turma": len({t.professor_id for t in turmas if t.professor_id is not None}),
            "turmas_com_matricula": sum(1 for t in por_turma if t["matriculados"]),
            "matriculados": len(matriculas),
            "ativados": len(ativados),
            "taxa_ativacao": taxa(len(ativados), len(matriculas)),
            "retencao_ultima_semana": {chave: semana[chave] for chave in _RETENCAO_NO_TOTAL},
        },
        "por_turma": por_turma,
    }
```

Em `backend/app/services/funil_regras.py`, dentro de `saude`, trocar o comentário

```python
        # A trilha não tem turma, então o último envio pode ser de antes da
        # matrícula. Nesse caso o relógio começa na entrada.
```

por:

```python
        # Um envio de lista religado pela matrícula institucional pode ser de
        # antes da matrícula. Nesse caso o relógio começa na entrada.
```

- [ ] **Passo 5: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_funil.py tests/unit/test_funil_regras.py -q`
Esperado: PASSA.

- [ ] **Passo 6: rodar a suíte inteira**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q 2>&1 | tail -3`
Esperado: tudo passando. O `test_script_funil.py` continua verde porque o script ainda lê `voltaram`, `base`, `taxa` e `taxa_retencao`, que continuam existindo.

- [ ] **Passo 7: commitar**

```bash
git add backend/app/services/funil_service.py backend/app/services/funil_regras.py backend/app/models/schemas.py backend/tests/test_funil.py
git commit -m "feat(funil): acessos, provas e origem no funil, com a trilha contada a partir da matricula"
```

---

### Task 8: script `funil.py` com as linhas novas

**Arquivos:**
- Alterar: `backend/scripts/funil.py` (`relatorio`)
- Teste: `backend/tests/test_script_funil.py`

**Interfaces:**
- Consome: `funil_geral` da Task 7, com `total.retencao_ultima_semana` (`semana`, `base`, `voltaram`, `taxa`, `voltaram_por_envio`, `taxa_por_envio`) e as chaves de `por_turma` (`por_origem`, `taxa_retencao`, `taxa_retencao_envio`, `taxa_sucesso_na_sessao`).
- Produz: o texto do relatório. Nenhuma tarefa depende dele.

- [ ] **Passo 1: escrever os testes que falham**

Em `backend/tests/test_script_funil.py`, no fim de `test_base_vazia_roda_sem_erro`, acrescentar:

```python
    assert "0 de 0 pelo acesso (sem dado), 0 pelo envio (sem dado)" in texto
```

No fim de `test_turma_aparece_sem_nome_de_aluno`, acrescentar:

```python
    assert "0 pelo convite, 0 pelo código e 1 sem origem" in texto
    assert "retenção 0.0% pelo acesso e 0.0% pelo envio" in texto
    assert "0.0% chegaram ao momento de sucesso na mesma sessão" in texto
    assert "Retenção na semana de 2026-10-19: 0 de 1 pelo acesso (0.0%), 0 pelo envio (0.0%)" in texto
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_script_funil.py -q`
Esperado: FALHA nos dois testes, com `AssertionError` nas linhas novas.

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/scripts/funil.py`, dentro de `relatorio`, trocar as duas linhas da retenção do total

```python
        f"  Retenção na semana de {semana['semana']}: {semana['voltaram']} de {semana['base']} "
        f"({_pct(semana['taxa'])})",
```

por:

```python
        f"  Retenção na semana de {semana['semana']}: {semana['voltaram']} de {semana['base']} "
        f"pelo acesso ({_pct(semana['taxa'])}), {semana['voltaram_por_envio']} pelo envio "
        f"({_pct(semana['taxa_por_envio'])})",
```

e trocar o laço `for t in funil["por_turma"]:` inteiro por:

```python
    for t in funil["por_turma"]:
        previstos = f" de {t['alunos_previstos']} previstos" if t["alunos_previstos"] else ""
        origem = t["por_origem"]
        linhas.append(
            f"  {t['nome']} ({t['professor'] or 'sem professor'}): "
            f"{t['matriculados']} matriculados{previstos} "
            f"({origem['convite']} pelo convite, {origem['codigo']} pelo código e "
            f"{origem['sem_origem']} sem origem), "
            f"ativação {_pct(t['taxa_ativacao'])}, "
            f"retenção {_pct(t['taxa_retencao'])} pelo acesso e "
            f"{_pct(t['taxa_retencao_envio'])} pelo envio, "
            f"{_pct(t['taxa_sucesso_na_sessao'])} chegaram ao momento de sucesso na mesma sessão, "
            f"erros corrigidos {t['north_star_semana']} na semana e {t['north_star_total']} no total, "
            f"{t['vermelhos']} em vermelho"
        )
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_script_funil.py -q`
Esperado: PASSA.

- [ ] **Passo 5: commitar**

```bash
git add backend/scripts/funil.py backend/tests/test_script_funil.py
git commit -m "feat(funil): script mostra a retencao pelo acesso, a origem e o momento de sucesso"
```

---

### Task 9: front do aluno, registro de acesso e convite

**Arquivos:**
- Alterar: `frontend/src/api/aluno.js`
- Criar: `frontend/src/utils/convitePendente.js`
- Alterar: `frontend/src/components/AlunoLayout.jsx`
- Criar: `frontend/src/pages/aluno/ConvitePage.jsx`
- Alterar: `frontend/src/App.jsx`
- Alterar: `frontend/src/pages/aluno/AlunoRegisterPage.jsx`
- Alterar: `frontend/src/pages/aluno/AlunoLoginPage.jsx`
- Alterar: `frontend/src/pages/aluno/TurmasPage.jsx`

**Interfaces:**
- Consome: `POST /aluno/acessos` com `{ via }` da Task 2. `POST /aluno/turmas/entrar` com `{ codigo_acesso, origem }` da Task 3, que devolve `{ id, nome, ... }` e dá 404 com código inválido.
- Produz: `registrarAcesso(via = null)`, `entrarNaTurma(codigoAcesso, origem = 'codigo')`, `guardarConvite(codigo)`, `lerConvite()`, `apagarConvite()`. Rota `/aluno/convite/:codigo`. A Task 10 monta o link `${window.location.origin}/aluno/convite/${codigo}` que cai nesta página.

O front não tem suíte de testes. A conferência é o lint, o build e o smoke do `fechamento`.

- [ ] **Passo 1: chamadas da API**

Em `frontend/src/api/aluno.js`, trocar `entrarNaTurma` por:

```js
export const entrarNaTurma = (codigoAcesso, origem = 'codigo') =>
  alunoApi.post('/aluno/turmas/entrar', { codigo_acesso: codigoAcesso, origem })
```

e acrescentar, logo depois de `listarMinhasTurmas`:

```js
export const registrarAcesso = (via = null) =>
  alunoApi.post('/aluno/acessos', { via })
```

- [ ] **Passo 2: código do convite guardado na aba**

Criar `frontend/src/utils/convitePendente.js`:

```js
// O código do convite atravessa o cadastro ou o login guardado na aba. Sem
// sessionStorage (aba privada, bloqueio do navegador), o aluno só perde o atalho.
const CHAVE = 'convite_pendente'

export function guardarConvite(codigo) {
  try {
    sessionStorage.setItem(CHAVE, codigo)
  } catch {
    // sem armazenamento, segue sem o atalho
  }
}

export function lerConvite() {
  try {
    return sessionStorage.getItem(CHAVE)
  } catch {
    return null
  }
}

export function apagarConvite() {
  try {
    sessionStorage.removeItem(CHAVE)
  } catch {
    // sem armazenamento, não há o que apagar
  }
}
```

- [ ] **Passo 3: registro do acesso no layout do aluno**

Em `frontend/src/components/AlunoLayout.jsx`, trocar as três primeiras linhas de import por:

```jsx
import { useEffect, useRef } from 'react'
import { Link, NavLink, Outlet, useNavigate, useSearchParams } from 'react-router-dom'
import { registrarAcesso } from '../api/aluno'
import { useAlunoAuth } from '../context/AlunoAuthContext'
import Logo from './Logo'
```

Dentro de `AlunoLayout`, logo depois de `const navigate = useNavigate()`, acrescentar:

```jsx
  const [searchParams, setSearchParams] = useSearchParams()
  const via = searchParams.get('via')
  const registrou = useRef(false)

  // RF14: cada abertura do app vira um acesso. O servidor descarta o que vier
  // perto demais de outro, então aqui não há controle de tempo. Tirar o `via`
  // da URL não conta como abertura nova.
  useEffect(() => {
    if (registrou.current && !via) return
    registrou.current = true
    registrarAcesso(via)
      .catch(() => {})
      .finally(() => {
        if (via) {
          setSearchParams(params => { params.delete('via'); return params }, { replace: true })
        }
      })
  }, [via, setSearchParams])

  useEffect(() => {
    const aoVoltar = () => {
      if (document.visibilityState === 'visible') registrarAcesso().catch(() => {})
    }
    document.addEventListener('visibilitychange', aoVoltar)
    return () => document.removeEventListener('visibilitychange', aoVoltar)
  }, [])
```

- [ ] **Passo 4: página do convite**

Criar `frontend/src/pages/aluno/ConvitePage.jsx`:

```jsx
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { entrarNaTurma } from '../../api/aluno'
import { useAlunoAuth } from '../../context/AlunoAuthContext'
import { apagarConvite, guardarConvite } from '../../utils/convitePendente'
import Logo from '../../components/Logo'
import Spinner from '../../components/Spinner'

export default function ConvitePage() {
  const { codigo } = useParams()
  const { isAuthenticated, loading } = useAlunoAuth()
  const navigate = useNavigate()
  const [situacao, setSituacao] = useState('entrando')
  const [tentativa, setTentativa] = useState(0)

  // Guarda antes de tudo: com o token vencido, o cliente do aluno manda direto
  // para o login, e o código precisa sobreviver até a volta.
  useEffect(() => {
    guardarConvite(codigo)
  }, [codigo])

  useEffect(() => {
    if (loading) return
    if (!isAuthenticated) {
      navigate('/aluno/cadastro', { replace: true })
      return
    }
    let ativo = true
    entrarNaTurma(codigo, 'convite')
      .then(({ data }) => {
        if (!ativo) return
        apagarConvite()
        navigate(`/aluno/turmas/${data.id}?via=convite`, { replace: true })
      })
      .catch((err) => {
        if (!ativo) return
        if (err.response?.status === 404) {
          apagarConvite()
          setSituacao('invalido')
        } else {
          setSituacao('falhou')
        }
      })
    return () => { ativo = false }
  }, [codigo, isAuthenticated, loading, navigate, tentativa])

  const tentarDeNovo = () => {
    setSituacao('entrando')
    setTentativa(t => t + 1)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <Logo className="w-8 h-8" />
          <span className="font-semibold text-gray-900">Analytics CS1</span>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center">
          {situacao === 'entrando' && (
            <div className="flex flex-col items-center gap-3">
              <Spinner className="w-6 h-6 text-purple-600" />
              <p className="text-sm text-gray-500">Entrando na turma...</p>
            </div>
          )}
          {situacao === 'invalido' && (
            <>
              <p className="text-sm text-gray-700 mb-4">
                Este convite não vale mais. Peça o código ao professor.
              </p>
              <Link to="/aluno/turmas" className="text-sm text-purple-600 hover:underline font-medium">
                Ir para minhas turmas
              </Link>
            </>
          )}
          {situacao === 'falhou' && (
            <>
              <p className="text-sm text-gray-700 mb-4">Não foi possível entrar na turma agora.</p>
              <button
                onClick={tentarDeNovo}
                className="text-sm px-4 py-2 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-700 transition-colors"
              >
                Tentar de novo
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Passo 5: rota do convite**

Em `frontend/src/App.jsx`, logo depois de `const AlunoRegisterPage = lazy(...)`, acrescentar:

```jsx
const ConvitePage = lazy(() => import('./pages/aluno/ConvitePage'))
```

e logo depois de `<Route path="aluno/cadastro" element={<AlunoRegisterPage />} />`, fora do `AlunoProtectedRoute`, acrescentar:

```jsx
              <Route path="aluno/convite/:codigo" element={<ConvitePage />} />
```

- [ ] **Passo 6: cadastro e login voltam ao convite**

Em `frontend/src/pages/aluno/AlunoRegisterPage.jsx`:

Acrescentar o import:

```jsx
import { lerConvite } from '../../utils/convitePendente'
```

Logo depois de `const [loading, setLoading] = useState(false)`, acrescentar:

```jsx
  const [convite] = useState(lerConvite)
```

Dentro de `handleSubmit`, trocar `navigate('/aluno', { replace: true })` por:

```jsx
      navigate(convite ? `/aluno/convite/${encodeURIComponent(convite)}` : '/aluno', { replace: true })
```

Logo antes de `<form onSubmit={handleSubmit} className="space-y-4">`, acrescentar:

```jsx
          {convite && (
            <div className="rounded-lg bg-purple-50 border border-purple-100 px-4 py-2.5 text-sm text-purple-700 mb-4">
              Depois de entrar, você vai direto para a turma.
            </div>
          )}
```

Fazer as mesmas quatro mudanças em `frontend/src/pages/aluno/AlunoLoginPage.jsx`: o mesmo import de `lerConvite`, a mesma linha `const [convite] = useState(lerConvite)` logo depois de `const [loading, setLoading] = useState(false)`, a mesma troca do `navigate('/aluno', { replace: true })` dentro de `handleSubmit` e o mesmo bloco do aviso logo antes de `<form onSubmit={handleSubmit} className="space-y-4">`.

- [ ] **Passo 7: entrada digitada com origem**

Em `frontend/src/pages/aluno/TurmasPage.jsx`, dentro de `handleSubmit` de `EntrarNaTurma`, trocar `await entrarNaTurma(codigo.trim())` por:

```jsx
      const { data } = await entrarNaTurma(codigo.trim(), 'codigo')
```

(a linha original já começa com `const { data } =`, só a chamada muda).

- [ ] **Passo 8: lint e build**

Rodar a partir da raiz do worktree: `cd frontend && npm run lint 2>&1 | tail -3`
Esperado: `✖ 4 problems (4 errors, 0 warnings)`, os mesmos 4 erros antigos.

Rodar: `cd frontend && npm run build 2>&1 | tail -5`
Esperado: build sem erro, com `ConvitePage` num pedaço próprio.

- [ ] **Passo 9: commitar**

```bash
git add frontend/src/api/aluno.js frontend/src/utils/convitePendente.js frontend/src/components/AlunoLayout.jsx frontend/src/pages/aluno/ConvitePage.jsx frontend/src/App.jsx frontend/src/pages/aluno/AlunoRegisterPage.jsx frontend/src/pages/aluno/AlunoLoginPage.jsx frontend/src/pages/aluno/TurmasPage.jsx
git commit -m "feat(aluno): registro de acesso e entrada na turma pelo link do convite"
```

---

### Task 10: front do professor, convite copiado e painel do funil

**Arquivos:**
- Alterar: `frontend/src/pages/TurmaDetailPage.jsx`
- Alterar: `frontend/src/components/FunilDaTurma.jsx`

**Interfaces:**
- Consome: a rota `/aluno/convite/:codigo` da Task 9. A resposta de `GET /turmas/{id}/funil` da Task 7: `aquisicao.por_origem.{convite, codigo, sem_origem}`, `retencao.ultima_completa.{voltaram, base, taxa, taxa_por_envio, taxa_sem_prova_marcada, taxa_sem_aviso, taxa_por_conta_propria}` e `sucesso.{chegaram, mediana_minutos, taxa_na_sessao_da_matricula}`.
- Produz: nada que outra tarefa use.

- [ ] **Passo 1: botão "Copiar convite"**

Em `frontend/src/pages/TurmaDetailPage.jsx`, logo depois de `const [copiado, setCopiado] = useState(false)`, acrescentar:

```jsx
  const [conviteCopiado, setConviteCopiado] = useState(false)
```

Logo depois da função `copiarCodigo`, acrescentar:

```jsx
  // RF06: mensagem pronta com o link que já leva o código da turma.
  const copiarConvite = async () => {
    if (!turma?.codigo_acesso) return
    const link = `${window.location.origin}/aluno/convite/${turma.codigo_acesso}`
    const mensagem =
      `Nossa turma de ${turma.nome} vai usar o Analytics CS1 nas listas e no treino. ` +
      `Para entrar, abra ${link} e crie sua conta. ` +
      `Se preferir, use o código ${turma.codigo_acesso} na área do aluno.`
    try {
      await navigator.clipboard.writeText(mensagem)
      setConviteCopiado(true)
      setTimeout(() => setConviteCopiado(false), 2000)
    } catch {
      setError('Não foi possível copiar o convite.')
    }
  }
```

No bloco "Entrada dos alunos na turma", trocar o parágrafo de ajuda

```jsx
            Passe este código aos alunos. {turma.aluno_count ?? 0} já {(turma.aluno_count ?? 0) === 1 ? 'entrou' : 'entraram'} com conta.
```

por:

```jsx
            Passe o código ou o convite com link, que já leva o código. {turma.aluno_count ?? 0} já {(turma.aluno_count ?? 0) === 1 ? 'entrou' : 'entraram'} com conta.
```

e, logo depois do botão `Copiar código` (o `</button>` que fecha o `{copiado ? 'Copiado' : 'Copiar código'}`), acrescentar:

```jsx
          <button
            onClick={copiarConvite}
            disabled={!turma.codigo_acesso}
            className="text-sm px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition-colors"
          >
            {conviteCopiado ? 'Copiado' : 'Copiar convite'}
          </button>
```

- [ ] **Passo 2: duração e textos novos no painel**

Em `frontend/src/components/FunilDaTurma.jsx`, logo depois da função `formatarData`, acrescentar:

```jsx
// Mediana do momento de sucesso em texto curto: "45 min", "2 h 15 min", "3 dias".
const formatarDuracao = (minutos) => {
  const total = Math.floor(minutos)
  if (total < 60) return `${total} min`
  if (total < 24 * 60) {
    const horas = Math.floor(total / 60)
    const resto = total % 60
    return resto ? `${horas} h ${resto} min` : `${horas} h`
  }
  const dias = Math.floor(total / (24 * 60))
  return `${dias} ${dias === 1 ? 'dia' : 'dias'}`
}

const textoSucesso = (sucesso) => (sucesso.chegaram === 0
  ? 'Momento de sucesso: ninguém corrigiu um erro ainda.'
  : `Momento de sucesso: mediana de ${formatarDuracao(sucesso.mediana_minutos)} depois da matrícula. ${pct(sucesso.taxa_na_sessao_da_matricula)} chegaram na mesma sessão.`)
```

Trocar a função `EtapaCard` por:

```jsx
function EtapaCard({ titulo, valor, detalhe, extra, meta, atingida }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-1">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{titulo}</p>
        {meta && <Meta atingida={atingida}>{meta}</Meta>}
      </div>
      <p className="text-2xl font-bold text-gray-900">{valor}</p>
      {detalhe && <p className="text-xs text-gray-500">{detalhe}</p>}
      {extra && <p className="text-xs text-gray-500">{extra}</p>}
    </div>
  )
}
```

- [ ] **Passo 3: cartões de aquisição, ativação e retenção, e a linha de hábito**

Em `Painel`, trocar as três primeiras linhas do corpo por:

```jsx
  const { north_star: ns, aquisicao, ativacao, retencao, saude, protecao, sucesso } = funil
  const semana = retencao.ultima_completa
  const media = protecao.media_tentativas_ate_acertar
  const origem = aquisicao.por_origem
  const textoOrigem = origem.convite + origem.codigo > 0
    ? `${origem.convite} pelo convite, ${origem.codigo} pelo código.`
    : null
```

Trocar o bloco `<div className="grid gap-4 sm:grid-cols-3">` inteiro (os três `EtapaCard`) por:

```jsx
      <div className="grid gap-4 sm:grid-cols-3">
        <EtapaCard
          titulo="Aquisição"
          valor={aquisicao.alunos_previstos
            ? `${aquisicao.matriculados} de ${aquisicao.alunos_previstos}`
            : aquisicao.matriculados}
          detalhe={aquisicao.alunos_previstos
            ? `${pct(aquisicao.taxa_primeira_semana)} entraram na primeira semana.`
            : 'Informe quantos alunos a turma tem para ver a taxa de entrada.'}
          extra={textoOrigem}
          meta={aquisicao.alunos_previstos ? `Meta ${aquisicao.meta}%` : null}
          atingida={aquisicao.taxa_primeira_semana != null && aquisicao.taxa_primeira_semana >= aquisicao.meta}
        />
        <EtapaCard
          titulo="Ativação"
          valor={pct(ativacao.taxa)}
          detalhe={`${ativacao.ativados} de ${ativacao.matriculados} corrigiram o primeiro erro na primeira semana. ${ativacao.com_primeiro_envio} já enviaram algo.`}
          extra={textoSucesso(sucesso)}
          meta={`Meta ${ativacao.meta}%`}
          atingida={ativacao.taxa != null && ativacao.taxa >= ativacao.meta}
        />
        <EtapaCard
          titulo="Retenção"
          valor={pct(semana.taxa)}
          detalhe={`${semana.voltaram} de ${semana.base} abriram o app na semana de ${rotuloSemana(semana.semana)}. Pelo envio, ${pct(semana.taxa_por_envio)}.`}
          meta={`Meta ${retencao.meta}%`}
          atingida={semana.taxa != null && semana.taxa >= retencao.meta}
        />
      </div>

      <p className="text-xs text-gray-500">
        Hábito na semana de {rotuloSemana(semana.semana)}: {pct(semana.taxa_sem_prova_marcada)} voltaram sem prova marcada, {pct(semana.taxa_sem_aviso)} abriram sem aviso e {pct(semana.taxa_por_conta_propria)} enviaram no treino.
      </p>
```

- [ ] **Passo 4: lint e build**

Rodar a partir da raiz do worktree: `cd frontend && npm run lint 2>&1 | tail -3`
Esperado: `✖ 4 problems (4 errors, 0 warnings)`, os mesmos 4 erros antigos.

Rodar: `cd frontend && npm run build 2>&1 | tail -5`
Esperado: build sem erro.

- [ ] **Passo 5: commitar**

```bash
git add frontend/src/pages/TurmaDetailPage.jsx frontend/src/components/FunilDaTurma.jsx
git commit -m "feat(funil): convite copiado pelo professor e painel com acesso, habito e momento de sucesso"
```
