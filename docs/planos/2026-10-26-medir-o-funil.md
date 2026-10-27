# Medir o funil, parte 1: plano de implementação

> **Para quem executa:** usar a skill `sdd` (recomendado) ou a execução sem subagentes descrita nela. Passos com caixa de seleção (`- [ ]`).

**Objetivo:** calcular na hora a North Star (erros corrigidos por semana), o funil de aquisição, ativação e retenção e a saúde dos alunos de cada turma, mostrar isso ao professor na página da turma e dar à equipe um script com o total de todas as turmas.

**Arquitetura:** um campo novo `turmas.alunos_previstos` (migração 0017). As contas ficam em funções puras em `app/services/funil_regras.py`, sobre registros simples (`Tentativa`, `Matricula`). A leitura do banco fica em `app/services/funil_service.py`, que monta esses registros e chama as regras. Uma rota fina `GET /turmas/{id}/funil` entrega o resultado ao componente `FunilDaTurma.jsx`, e o script `backend/scripts/funil.py` imprime o total.

**Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic v2, pytest, React 19, Tailwind v4.

**Spec:** `docs/specs/2026-10-26-medir-o-funil.md`. O plano argumenta a partir dele, e quem executa lê os dois. A seção "Definições" do spec é a regra de cada conta.

## Restrições globais

- Migração `0017`, arquivo `backend/migrations/versions/0017_alunos_previstos_da_turma.py`, `revision = '0017'`, `down_revision = '0016'`. Coluna `turmas.alunos_previstos`, `Integer`, nula permitida.
- `alunos_previstos` aceita de 1 a 1000 ou nulo. 0 e 1001 dão 422.
- O `PUT /turmas/{id}` só mexe em `alunos_previstos` quando o campo vem no corpo. `null` limpa.
- Acerto na lista: `error_category == "Correto"`. Acerto na trilha: `all_tests_passed` verdadeiro. Falha técnica: não é acerto e a categoria é `"Erro Desconhecido"` ou vazia. Erro: o resto.
- Falha técnica conta como envio (retenção, ativação por envio, dias sem envio) e nunca como erro nem como acerto.
- Semana de segunda a domingo pela data UTC, identificada pela segunda-feira em ISO. Sempre 8 semanas na resposta, a atual e as 7 anteriores.
- Janela da primeira semana e da ativação: 7 dias exatos (`timedelta(days=7)`), com o limite incluído.
- Saúde: vermelho com mais de 14 dias sem envio, ou mais de 7 dias com o último envio sendo erro de lista numa questão em aberto. Amarelo com 7 dias ou mais, ou 5 erros numa questão em aberto. Comparação pelo tempo exato, não por dias inteiros.
- Motivos, com o texto exato: `"Mais de 14 dias sem envio"`, `"Parou depois de errar"`, `"7 a 14 dias sem envio"`, `"5 erros seguidos na mesma questão"`.
- Metas: aquisição 80, ativação 60, retenção 50, vermelho abaixo de 15. Ficam no serviço e vão na resposta.
- Taxas e médias com uma casa decimal, em porcentagem, nulas quando o denominador é zero ou nulo.
- RN05: a North Star só aparece como número da turma. RNF04: nome de aluno só na rota do professor dono, e o script não mostra nome de aluno. A trilha nunca vira motivo de risco nem deixa aluno pendente.
- Textos do painel, exatos: `"Funil da turma"`, `"Informe quantos alunos a turma tem para ver a taxa de entrada."`, `"O funil aparece quando os alunos entrarem pelo código da turma."`, `"Não foi possível carregar o funil."`, `"Nenhum aluno em risco agora."`, `"Alunos na turma (opcional)"`. Texto do script: `"Nenhuma turma cadastrada."`.
- Testes: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest <alvo> -q`. Nunca `rtk pytest`. Nunca duas suítes ao mesmo tempo.
- Git dentro do worktree: rodar `git` direto, sem `rtk` (o isolamento do worktree recusa `rtk git`), a partir da raiz do worktree `/home/otavio/produtos-digitais-cs1/.claude/worktrees/medir-o-funil`. Commit sem `Co-Authored-By`.
- Não rodar `alembic upgrade` nem o script contra o banco de desenvolvimento. Isso fica para o smoke do `fechamento`.
- Lint do front: a base tem 4 erros antigos em `QuestionPage.jsx` e `TestCasesPage.jsx`. Só erro novo bloqueia. Ruff do projeto: regras `F`, `E9` e `B`.

## Estrutura de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `backend/migrations/versions/0017_alunos_previstos_da_turma.py` | Criar | Coluna `turmas.alunos_previstos` |
| `backend/app/models/orm.py` | Alterar | `Turma.alunos_previstos` |
| `backend/app/models/schemas.py` | Alterar | Campo novo nos esquemas da turma e os esquemas do funil |
| `backend/app/services/turma_service.py` | Alterar | Gravar e devolver `alunos_previstos` |
| `backend/app/api/routes/turma.py` | Alterar | Repassar o campo e a rota `GET /turmas/{id}/funil` |
| `backend/app/services/calendario.py` | Criar | `semana_iso` e `situacao_da_atividade`, tiradas de `student_activity_service` |
| `backend/app/services/student_activity_service.py` | Alterar | Passa a importar as duas funções de `calendario` |
| `backend/app/services/funil_regras.py` | Criar | Registros e regras puras do funil, sem banco |
| `backend/app/services/funil_service.py` | Criar | Leitura do banco, `funil_da_turma` e `funil_geral` |
| `backend/scripts/funil.py` | Criar | Relatório de todas as turmas no terminal |
| `backend/tests/test_turma_alunos_previstos.py` | Criar | Campo novo pela API |
| `backend/tests/unit/test_calendario.py` | Criar | As duas funções movidas |
| `backend/tests/unit/test_funil_regras.py` | Criar | Regras puras |
| `backend/tests/test_funil.py` | Criar | Serviço com banco e rota |
| `backend/tests/test_script_funil.py` | Criar | Script |
| `frontend/src/api/exam.js` | Alterar | `getTurmaFunil` e `alunos_previstos` em criar e editar |
| `frontend/src/pages/TurmaListPage.jsx` | Alterar | Campo "Alunos na turma (opcional)" |
| `frontend/src/components/FunilDaTurma.jsx` | Criar | Bloco do funil |
| `frontend/src/pages/TurmaDetailPage.jsx` | Alterar | Mostra o bloco e recarrega depois de excluir atividade |

A regra pura fica num arquivo separado do serviço para os testes dela não precisarem montar turma, atividade e envio no banco. O serviço só lê e converte.

---

### Task 1: campo `alunos_previstos` na turma

**Arquivos:**
- Criar: `backend/migrations/versions/0017_alunos_previstos_da_turma.py`
- Alterar: `backend/app/models/orm.py` (classe `Turma`, logo depois de `codigo_acesso`)
- Alterar: `backend/app/models/schemas.py` (import do Pydantic, `TurmaCreate`, `TurmaUpdate`, `TurmaResponse`, `TurmaDetailResponse`)
- Alterar: `backend/app/services/turma_service.py` (`create_turma`, `update_turma`, `list_turmas`, `get_turma_detail`)
- Alterar: `backend/app/api/routes/turma.py` (`post_turma`, `put_turma`)
- Teste: `backend/tests/test_turma_alunos_previstos.py`

**Interfaces:**
- Consome: nada de outras tarefas.
- Produz: `Turma.alunos_previstos: int | None`. `create_turma(nome, codigo, db, professor_id=None, alunos_previstos=None)`. `update_turma(turma, nome, codigo, db, alunos_previstos=_MANTER)`. `TurmaResponse.alunos_previstos` e `TurmaDetailResponse.alunos_previstos`.

- [ ] **Passo 1: aplicar a coluna no banco de teste**

O `conftest.py` usa `create_all`, que não altera tabela existente. Rodar a partir da raiz do worktree:

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
    c.execute(text('ALTER TABLE turmas ADD COLUMN IF NOT EXISTS alunos_previstos INTEGER'))
print('coluna aplicada no banco de teste')
"
```

Esperado: `coluna aplicada no banco de teste`. Registrar no relatório da tarefa que o `ALTER` foi aplicado no banco de teste.

- [ ] **Passo 2: escrever os testes que falham**

Criar `backend/tests/test_turma_alunos_previstos.py`:

```python
"""Tamanho da turma informado pelo professor, o denominador da aquisição no funil."""


def _criar(client, **extra):
    return client.post("/turmas", json={"nome": "CS1 A", "codigo": "CS1", **extra})


class TestCriar:
    def test_cria_com_o_tamanho_e_devolve(self, client):
        resp = _criar(client, alunos_previstos=60)
        assert resp.status_code == 200
        assert resp.json()["alunos_previstos"] == 60
        assert client.get("/turmas").json()[0]["alunos_previstos"] == 60
        assert client.get(f"/turmas/{resp.json()['id']}").json()["alunos_previstos"] == 60

    def test_sem_o_campo_fica_nulo(self, client):
        assert _criar(client).json()["alunos_previstos"] is None

    def test_zero_e_recusado(self, client):
        assert _criar(client, alunos_previstos=0).status_code == 422

    def test_acima_de_mil_e_recusado(self, client):
        assert _criar(client, alunos_previstos=1001).status_code == 422


class TestEditar:
    def test_put_sem_o_campo_mantem_o_valor(self, client):
        turma_id = _criar(client, alunos_previstos=60).json()["id"]
        resp = client.put(f"/turmas/{turma_id}", json={"nome": "CS1 B", "codigo": "CS1"})
        assert resp.status_code == 200
        assert resp.json()["nome"] == "CS1 B"
        assert resp.json()["alunos_previstos"] == 60

    def test_put_com_null_limpa(self, client):
        turma_id = _criar(client, alunos_previstos=60).json()["id"]
        resp = client.put(f"/turmas/{turma_id}",
                          json={"nome": "CS1", "codigo": "CS1", "alunos_previstos": None})
        assert resp.json()["alunos_previstos"] is None

    def test_put_com_valor_troca(self, client):
        turma_id = _criar(client, alunos_previstos=60).json()["id"]
        resp = client.put(f"/turmas/{turma_id}",
                          json={"nome": "CS1", "codigo": "CS1", "alunos_previstos": 45})
        assert resp.json()["alunos_previstos"] == 45

    def test_put_com_zero_e_recusado(self, client):
        turma_id = _criar(client).json()["id"]
        resp = client.put(f"/turmas/{turma_id}",
                          json={"nome": "CS1", "codigo": "CS1", "alunos_previstos": 0})
        assert resp.status_code == 422
```

- [ ] **Passo 3: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_turma_alunos_previstos.py -q`
Esperado: FALHA com `KeyError: 'alunos_previstos'` nas respostas e status 200 onde se espera 422.

- [ ] **Passo 4: criar a migração**

Criar `backend/migrations/versions/0017_alunos_previstos_da_turma.py`:

```python
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
```

- [ ] **Passo 5: ORM**

Em `backend/app/models/orm.py`, na classe `Turma`, logo depois da linha `codigo_acesso = Column(...)`:

```python
    # Tamanho da turma informado pelo professor. É o denominador da aquisição no
    # funil, porque o sistema só conhece quem entrou, não quem deveria entrar.
    alunos_previstos = Column(Integer, nullable=True)
```

- [ ] **Passo 6: esquemas**

Em `backend/app/models/schemas.py`, trocar `from pydantic import BaseModel, EmailStr` por:

```python
from pydantic import BaseModel, EmailStr, Field
```

Trocar `TurmaCreate` e `TurmaUpdate` por:

```python
class TurmaCreate(BaseModel):
    nome: str
    codigo: str
    alunos_previstos: Optional[int] = Field(None, ge=1, le=1000)


class TurmaUpdate(BaseModel):
    nome: str
    codigo: str
    alunos_previstos: Optional[int] = Field(None, ge=1, le=1000)
```

Em `TurmaResponse` e em `TurmaDetailResponse`, logo depois de `codigo_acesso: Optional[str] = None`, acrescentar:

```python
    alunos_previstos: Optional[int] = None
```

- [ ] **Passo 7: serviço da turma**

Em `backend/app/services/turma_service.py`, logo acima de `def create_turma`, acrescentar:

```python
# Padrão de `update_turma` para "o campo não veio no corpo", que é diferente de
# None: None limpa o campo, _MANTER deixa como está.
_MANTER = object()
```

Trocar `create_turma` e `update_turma` por:

```python
def create_turma(nome: str, codigo: str, db: Session, professor_id: int | None = None,
                 alunos_previstos: int | None = None) -> Turma:
    turma = Turma(
        nome=nome,
        codigo=codigo,
        codigo_acesso=gerar_codigo_acesso(db),
        created_at=datetime.utcnow(),
        professor_id=professor_id,
        alunos_previstos=alunos_previstos,
    )
    db.add(turma)
    db.commit()
    db.refresh(turma)
    return turma


def update_turma(turma: Turma, nome: str, codigo: str, db: Session,
                 alunos_previstos=_MANTER) -> Turma:
    turma.nome = nome
    turma.codigo = codigo
    if alunos_previstos is not _MANTER:
        turma.alunos_previstos = alunos_previstos
    db.commit()
    db.refresh(turma)
    return turma
```

Em `list_turmas`, no dicionário de cada turma, logo depois de `"codigo_acesso": t.codigo_acesso,`, acrescentar `"alunos_previstos": t.alunos_previstos,`. Em `get_turma_detail`, logo depois de `"codigo_acesso": turma.codigo_acesso,`, acrescentar `"alunos_previstos": turma.alunos_previstos,`.

- [ ] **Passo 8: rotas**

Em `backend/app/api/routes/turma.py`, em `post_turma`, trocar a chamada por:

```python
    turma = create_turma(body.nome, body.codigo, db, professor_id=professor.id,
                         alunos_previstos=body.alunos_previstos)
```

Em `put_turma`, trocar `update_turma(turma, body.nome, body.codigo, db)` por:

```python
    opcionais = body.model_dump(include={"alunos_previstos"}, exclude_unset=True)
    update_turma(turma, body.nome, body.codigo, db, **opcionais)
```

- [ ] **Passo 9: rodar e ver passar**

Rodar: o mesmo comando do passo 3
Esperado: PASSA, 8 testes.

- [ ] **Passo 10: suíte inteira**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q 2>&1 | tail -3`
Esperado: tudo passa (a base tinha 228). `tests/unit/test_crud_cascade.py` chama `update_turma(turma, nome, codigo, db)` e continua passando.

- [ ] **Passo 11: commitar**

```bash
git add backend/migrations/versions/0017_alunos_previstos_da_turma.py backend/app/models/orm.py backend/app/models/schemas.py backend/app/services/turma_service.py backend/app/api/routes/turma.py backend/tests/test_turma_alunos_previstos.py
git commit -m "feat(turma): tamanho da turma informado pelo professor"
```

---

### Task 2: módulo `calendario` com a semana e a situação da atividade

As duas funções hoje são privadas de `student_activity_service` (`_semana` e `_situacao`). O funil também precisa delas, e nenhum módulo do projeto importa nome com sublinhado de outro. Elas mudam para um módulo próprio com nome público.

**Arquivos:**
- Criar: `backend/app/services/calendario.py`
- Alterar: `backend/app/services/student_activity_service.py` (linhas 37 a 43, 134, 193, 448, 452 e 464 a 466, contadas no arquivo antes de qualquer mudança)
- Teste: `backend/tests/unit/test_calendario.py`

**Interfaces:**
- Consome: nada de outras tarefas.
- Produz: `semana_iso(momento: datetime) -> str` e `situacao_da_atividade(exam: Exam, agora: datetime | None = None) -> str`, que devolve `"agendada"`, `"encerrada"` ou `"aberta"`.

- [ ] **Passo 1: escrever o teste que falha**

Criar `backend/tests/unit/test_calendario.py`:

```python
from datetime import datetime

from app.models.orm import Exam
from app.services.calendario import semana_iso, situacao_da_atividade


def test_semana_vai_de_segunda_a_domingo():
    assert semana_iso(datetime(2026, 10, 26, 0, 0)) == "2026-10-26"
    assert semana_iso(datetime(2026, 11, 1, 23, 59)) == "2026-10-26"
    assert semana_iso(datetime(2026, 11, 2, 0, 0)) == "2026-11-02"


def test_situacao_da_atividade():
    agora = datetime(2026, 10, 26, 12, 0)
    assert situacao_da_atividade(Exam(), agora) == "aberta"
    assert situacao_da_atividade(Exam(abre_em=datetime(2026, 10, 27)), agora) == "agendada"
    assert situacao_da_atividade(Exam(fecha_em=datetime(2026, 10, 25)), agora) == "encerrada"
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_calendario.py -q`
Esperado: FALHA com `ModuleNotFoundError: No module named 'app.services.calendario'`

- [ ] **Passo 3: criar o módulo**

Criar `backend/app/services/calendario.py`:

```python
"""Recortes de tempo usados por mais de um serviço: a semana de um envio e a
situação de uma atividade num instante."""
from datetime import datetime, timedelta

from app.models.orm import Exam


def semana_iso(momento: datetime) -> str:
    """Segunda-feira da semana do momento, em ISO. É o que identifica a semana."""
    dia = momento.date()
    return (dia - timedelta(days=dia.weekday())).isoformat()


def situacao_da_atividade(exam: Exam, agora: datetime | None = None) -> str:
    agora = agora or datetime.utcnow()
    if exam.abre_em and agora < exam.abre_em:
        return "agendada"
    if exam.fecha_em and agora > exam.fecha_em:
        return "encerrada"
    return "aberta"
```

- [ ] **Passo 4: trocar o uso em `student_activity_service`**

Em `backend/app/services/student_activity_service.py`:
- Apagar a função `_situacao` inteira (linhas 37 a 43) e a função `_semana` inteira (linhas 464 a 466).
- Logo depois de `from app.models.orm import Exam, Question, Student, Submission`, acrescentar `from app.services.calendario import semana_iso, situacao_da_atividade`.
- Nas linhas 134 e 193, trocar `situacao = _situacao(exam)` por `situacao = situacao_da_atividade(exam)`.
- Na linha 448, trocar `_semana(sub.submitted_at)` por `semana_iso(sub.submitted_at)`. Na linha 452, trocar `_semana(primeira_correta.submitted_at)` por `semana_iso(primeira_correta.submitted_at)`.
- O `timedelta` do import continua sendo usado nas linhas 429 e 435. Não remover.

Conferir que não sobrou nada: `grep -n -E "_semana\(|_situacao\(" backend/app/services/student_activity_service.py` não deve imprimir nada.

- [ ] **Passo 5: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: PASSA, 2 testes.

- [ ] **Passo 6: suíte inteira**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q 2>&1 | tail -3`
Esperado: tudo passa. Os testes de `tests/test_student_activity.py` (situação agendada na lista, evolução por semana) provam que o comportamento não mudou.

- [ ] **Passo 7: commitar**

```bash
git add backend/app/services/calendario.py backend/app/services/student_activity_service.py backend/tests/unit/test_calendario.py
git commit -m "refactor(calendario): semana e situacao da atividade num modulo comum"
```

---

### Task 3: regras puras, registros, North Star e proteção

**Arquivos:**
- Criar: `backend/app/services/funil_regras.py`
- Teste: `backend/tests/unit/test_funil_regras.py`

**Interfaces:**
- Consome: `semana_iso` de `app.services.calendario` (Task 2).
- Produz, em `app.services.funil_regras`:
  - constantes `ACERTO = "acerto"`, `ERRO = "erro"`, `FALHA = "falha"`, `LISTA = "lista"`, `TRILHA = "trilha"`, `SEMANAS = 8`, `JANELA = timedelta(days=7)`, `META_AQUISICAO = 80.0`, `META_ATIVACAO = 60.0`, `META_RETENCAO = 50.0`, `META_VERMELHO = 15.0`, `CATEGORIA_FALHA_TECNICA = "Erro Desconhecido"`
  - `@dataclass(frozen=True) Tentativa(aluno: int, origem: str, item_id: int, momento: datetime, ordem: int, resultado: str, por_conta_propria: bool = False)`, com a propriedade `item -> tuple[int, str, int]`
  - `@dataclass(frozen=True) Matricula(aluno: int, nome: str, entrada: datetime)`
  - `resultado_da_lista(error_category: str | None) -> str`
  - `resultado_da_trilha(all_tests_passed: bool | None, error_category: str | None) -> str`
  - `taxa(parte: int, todo: int | None) -> float | None`
  - `ultimas_semanas(agora: datetime) -> list[str]`
  - `erros_corrigidos(tentativas: list[Tentativa]) -> list[tuple[int, datetime]]`
  - `north_star(corrigidos: list[tuple[int, datetime]], agora: datetime) -> dict`
  - `protecao(tentativas: list[Tentativa]) -> dict`
  - os auxiliares privados `_em_ordem(tentativas)` e `_por_item(tentativas)`, que as Tasks 4 e 5 usam no mesmo arquivo

- [ ] **Passo 1: escrever os testes que falham**

Criar `backend/tests/unit/test_funil_regras.py`:

```python
"""Regras do funil sobre registros montados à mão, sem banco."""
import itertools
from datetime import datetime, timedelta

from app.services.funil_regras import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, Tentativa, erros_corrigidos, north_star, protecao,
    resultado_da_lista, resultado_da_trilha, ultimas_semanas,
)

# Quarta-feira. A semana atual começa em 2026-10-26.
AGORA = datetime(2026, 10, 28, 12, 0)
_ids = itertools.count(1)


def tent(resultado, momento, aluno=1, item=10, origem=LISTA, por_conta_propria=False):
    return Tentativa(aluno=aluno, origem=origem, item_id=item, momento=momento,
                     ordem=next(_ids), resultado=resultado, por_conta_propria=por_conta_propria)


def _por_semana(ns):
    return {s["semana"]: s["erros_corrigidos"] for s in ns["semanas"]}


class TestResultado:
    def test_lista(self):
        assert resultado_da_lista("Correto") == ACERTO
        assert resultado_da_lista("Erro Desconhecido") == FALHA
        assert resultado_da_lista("") == FALHA
        assert resultado_da_lista(None) == FALHA
        assert resultado_da_lista("Violação de Estrutura") == ERRO

    def test_trilha(self):
        assert resultado_da_trilha(True, "") == ACERTO
        assert resultado_da_trilha(False, "Erro Desconhecido") == FALHA
        assert resultado_da_trilha(None, "") == FALHA
        assert resultado_da_trilha(False, "Violação de Estrutura") == ERRO


class TestSemanas:
    def test_oito_semanas_terminando_na_atual(self):
        semanas = ultimas_semanas(AGORA)
        assert len(semanas) == 8
        assert semanas[0] == "2026-09-07"
        assert semanas[-1] == "2026-10-26"

    def test_sem_correcao_as_oito_semanas_vem_com_zero(self):
        ns = north_star([], AGORA)
        assert len(ns["semanas"]) == 8
        assert all(s["erros_corrigidos"] == 0 for s in ns["semanas"])
        assert ns["semana_atual"] == 0
        assert ns["total"] == 0


class TestErrosCorrigidos:
    def test_errou_e_acertou_conta_um_na_semana_do_acerto(self):
        tentativas = [tent(ERRO, datetime(2026, 10, 16)), tent(ACERTO, datetime(2026, 10, 27))]
        ns = north_star(erros_corrigidos(tentativas), AGORA)
        assert ns["semana_atual"] == 1
        assert ns["total"] == 1
        assert _por_semana(ns)["2026-10-12"] == 0

    def test_acertou_de_primeira_nao_conta(self):
        assert erros_corrigidos([tent(ACERTO, datetime(2026, 10, 27))]) == []

    def test_errou_acertou_errou_e_acertou_de_novo_conta_um(self):
        tentativas = [
            tent(ERRO, datetime(2026, 10, 20)), tent(ACERTO, datetime(2026, 10, 21)),
            tent(ERRO, datetime(2026, 10, 26)), tent(ACERTO, datetime(2026, 10, 27)),
        ]
        corrigidos = erros_corrigidos(tentativas)
        assert corrigidos == [(1, datetime(2026, 10, 21))]

    def test_so_errou_nao_conta(self):
        tentativas = [tent(ERRO, datetime(2026, 10, 26)), tent(ERRO, datetime(2026, 10, 27))]
        assert erros_corrigidos(tentativas) == []

    def test_falha_tecnica_antes_do_acerto_nao_conta(self):
        tentativas = [tent(FALHA, datetime(2026, 10, 26)), tent(ACERTO, datetime(2026, 10, 27))]
        assert erros_corrigidos(tentativas) == []

    def test_falha_tecnica_entre_o_erro_e_o_acerto_nao_atrapalha(self):
        tentativas = [tent(ERRO, datetime(2026, 10, 26)), tent(FALHA, datetime(2026, 10, 26, 1)),
                      tent(ACERTO, datetime(2026, 10, 27))]
        assert len(erros_corrigidos(tentativas)) == 1

    def test_trilha_conta(self):
        tentativas = [tent(ERRO, datetime(2026, 10, 26), origem=TRILHA),
                      tent(ACERTO, datetime(2026, 10, 27), origem=TRILHA)]
        assert len(erros_corrigidos(tentativas)) == 1

    def test_mesmo_id_na_lista_e_na_trilha_sao_itens_diferentes(self):
        tentativas = [
            tent(ERRO, datetime(2026, 10, 26), origem=LISTA), tent(ACERTO, datetime(2026, 10, 27), origem=LISTA),
            tent(ERRO, datetime(2026, 10, 26), origem=TRILHA), tent(ACERTO, datetime(2026, 10, 27), origem=TRILHA),
        ]
        assert len(erros_corrigidos(tentativas)) == 2

    def test_a_ordem_vem_do_momento_e_nao_da_lista(self):
        tentativas = [tent(ACERTO, datetime(2026, 10, 27)), tent(ERRO, datetime(2026, 10, 26))]
        assert len(erros_corrigidos(tentativas)) == 1


class TestProtecao:
    def test_media_ate_acertar_e_acerto_de_primeira(self):
        tentativas = [
            tent(ERRO, datetime(2026, 10, 20), item=1), tent(ERRO, datetime(2026, 10, 21), item=1),
            tent(ACERTO, datetime(2026, 10, 22), item=1),
            tent(ACERTO, datetime(2026, 10, 20), item=2),
            tent(ERRO, datetime(2026, 10, 20), item=3),
        ]
        p = protecao(tentativas)
        assert p["media_tentativas_ate_acertar"] == 2.0
        assert p["acerto_de_primeira"] == 33.3
        assert p["itens_com_acerto"] == 2

    def test_falha_tecnica_nao_entra_na_conta(self):
        p = protecao([tent(FALHA, datetime(2026, 10, 20)), tent(ACERTO, datetime(2026, 10, 21))])
        assert p["media_tentativas_ate_acertar"] == 1.0
        assert p["acerto_de_primeira"] == 100.0

    def test_so_falha_tecnica_deixa_tudo_nulo(self):
        p = protecao([tent(FALHA, datetime(2026, 10, 20))])
        assert p == {"media_tentativas_ate_acertar": None, "acerto_de_primeira": None,
                     "itens_com_acerto": 0}
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_funil_regras.py -q`
Esperado: FALHA com `ModuleNotFoundError: No module named 'app.services.funil_regras'`

- [ ] **Passo 3: escrever o mínimo para passar**

Criar `backend/app/services/funil_regras.py`:

```python
"""Regras do funil da turma, sobre registros simples e sem banco.

A leitura fica em `funil_service`. Aqui só entra o que já foi lido, por isso
cada conta se testa com listas montadas à mão."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.services.calendario import semana_iso
from app.services.student_activity_service import CATEGORIA_CORRETA

# O que as heurísticas devolvem quando a execução falha por fora do código do
# aluno, como o Docker fora do ar. Não é erro dele.
CATEGORIA_FALHA_TECNICA = "Erro Desconhecido"

ACERTO = "acerto"
ERRO = "erro"
FALHA = "falha"

LISTA = "lista"
TRILHA = "trilha"

SEMANAS = 8
JANELA = timedelta(days=7)

META_AQUISICAO = 80.0
META_ATIVACAO = 60.0
META_RETENCAO = 50.0
META_VERMELHO = 15.0


@dataclass(frozen=True)
class Tentativa:
    """Um envio do aluno, de lista ou de trilha, já classificado."""
    aluno: int
    origem: str
    item_id: int
    momento: datetime
    ordem: int
    resultado: str
    por_conta_propria: bool = False

    @property
    def item(self) -> tuple[int, str, int]:
        return (self.aluno, self.origem, self.item_id)


@dataclass(frozen=True)
class Matricula:
    aluno: int
    nome: str
    entrada: datetime


def resultado_da_lista(error_category: str | None) -> str:
    if error_category == CATEGORIA_CORRETA:
        return ACERTO
    if not error_category or error_category == CATEGORIA_FALHA_TECNICA:
        return FALHA
    return ERRO


def resultado_da_trilha(all_tests_passed: bool | None, error_category: str | None) -> str:
    if all_tests_passed:
        return ACERTO
    if not error_category or error_category == CATEGORIA_FALHA_TECNICA:
        return FALHA
    return ERRO


def taxa(parte: int, todo: int | None) -> float | None:
    return round(parte / todo * 100, 1) if todo else None


def ultimas_semanas(agora: datetime) -> list[str]:
    """As SEMANAS semanas que terminam na atual, da mais antiga para a atual."""
    atual = date.fromisoformat(semana_iso(agora))
    return [(atual - timedelta(weeks=i)).isoformat() for i in range(SEMANAS - 1, -1, -1)]


def _em_ordem(tentativas: list[Tentativa]) -> list[Tentativa]:
    return sorted(tentativas, key=lambda t: (t.momento, t.ordem))


def _por_item(tentativas: list[Tentativa]) -> dict[tuple[int, str, int], list[Tentativa]]:
    series: dict[tuple[int, str, int], list[Tentativa]] = defaultdict(list)
    for t in _em_ordem(tentativas):
        series[t.item].append(t)
    return series


def erros_corrigidos(tentativas: list[Tentativa]) -> list[tuple[int, datetime]]:
    """Aluno e momento do primeiro acerto de cada item que teve erro antes dele.
    Um por item: errar de novo depois de acertar não abre outra correção."""
    corrigidos = []
    for serie in _por_item(tentativas).values():
        errou = False
        for t in serie:
            if t.resultado == ERRO:
                errou = True
            elif t.resultado == ACERTO:
                if errou:
                    corrigidos.append((t.aluno, t.momento))
                break
    return corrigidos


def north_star(corrigidos: list[tuple[int, datetime]], agora: datetime) -> dict:
    semanas = ultimas_semanas(agora)
    por_semana = Counter(semana_iso(momento) for _, momento in corrigidos)
    return {
        "semana_atual": por_semana[semanas[-1]],
        "total": len(corrigidos),
        "semanas": [{"semana": s, "erros_corrigidos": por_semana[s]} for s in semanas],
    }


def protecao(tentativas: list[Tentativa]) -> dict:
    """Acompanha a North Star para ela não crescer pelo motivo errado, como o
    aluno tentando às cegas até passar."""
    ate_acertar = []
    de_primeira = []
    for serie in _por_item(tentativas).values():
        validas = [t for t in serie if t.resultado != FALHA]
        if not validas:
            continue
        de_primeira.append(validas[0].resultado == ACERTO)
        posicao = next((i for i, t in enumerate(validas) if t.resultado == ACERTO), None)
        if posicao is not None:
            ate_acertar.append(posicao + 1)
    media = round(sum(ate_acertar) / len(ate_acertar), 1) if ate_acertar else None
    return {
        "media_tentativas_ate_acertar": media,
        "acerto_de_primeira": taxa(sum(de_primeira), len(de_primeira)),
        "itens_com_acerto": len(ate_acertar),
    }
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: PASSA, 16 testes.

- [ ] **Passo 5: commitar**

```bash
git add backend/app/services/funil_regras.py backend/tests/unit/test_funil_regras.py
git commit -m "feat(funil): erros corrigidos por semana e metricas de protecao"
```

---

### Task 4: regras puras, aquisição, ativação e retenção

**Arquivos:**
- Alterar: `backend/app/services/funil_regras.py` (acrescentar no fim)
- Alterar: `backend/tests/unit/test_funil_regras.py` (acrescentar imports e classes no fim)

**Interfaces:**
- Consome: `Tentativa`, `Matricula`, `taxa`, `ultimas_semanas`, `JANELA`, `META_AQUISICAO`, `META_ATIVACAO`, `META_RETENCAO` da Task 3.
- Produz, em `app.services.funil_regras`:
  - `aquisicao(matriculas: list[Matricula], alunos_previstos: int | None) -> dict`
  - `alunos_ativados(matriculas: list[Matricula], corrigidos: list[tuple[int, datetime]]) -> set[int]`
  - `ativacao(matriculas: list[Matricula], tentativas: list[Tentativa], corrigidos: list[tuple[int, datetime]]) -> dict`
  - `retencao_da_semana(semana: str, matriculas: list[Matricula], tentativas: list[Tentativa]) -> dict`
  - `retencao(matriculas: list[Matricula], tentativas: list[Tentativa], agora: datetime) -> dict`

- [ ] **Passo 1: escrever os testes que falham**

Em `backend/tests/unit/test_funil_regras.py`, trocar o bloco de import de `app.services.funil_regras` por:

```python
from app.services.funil_regras import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, Matricula, Tentativa, aquisicao, ativacao,
    erros_corrigidos, north_star, protecao, resultado_da_lista, resultado_da_trilha,
    retencao, retencao_da_semana, ultimas_semanas,
)
```

Logo depois da função `tent`, acrescentar:

```python
def mat(aluno, entrada, nome="Aluno"):
    return Matricula(aluno=aluno, nome=nome, entrada=entrada)
```

No fim do arquivo, acrescentar:

```python
DIA0 = datetime(2026, 10, 1, 10, 0)


class TestAquisicao:
    def test_sem_o_tamanho_da_turma_as_taxas_ficam_nulas(self):
        a = aquisicao([mat(1, DIA0), mat(2, DIA0)], None)
        assert a["matriculados"] == 2
        assert a["alunos_previstos"] is None
        assert a["taxa_matriculados"] is None
        assert a["taxa_primeira_semana"] is None
        assert a["meta"] == 80.0

    def test_primeira_semana_conta_ate_sete_dias_da_primeira_matricula(self):
        matriculas = [mat(1, DIA0), mat(2, DIA0 + timedelta(days=7)), mat(3, DIA0 + timedelta(days=8))]
        a = aquisicao(matriculas, 4)
        assert a["primeira_semana"] == 2
        assert a["taxa_primeira_semana"] == 50.0
        assert a["taxa_matriculados"] == 75.0

    def test_turma_vazia(self):
        a = aquisicao([], 10)
        assert a["matriculados"] == 0
        assert a["primeira_semana"] == 0
        assert a["taxa_matriculados"] == 0.0


class TestAtivacao:
    def test_ativa_quem_corrige_ate_sete_dias_depois_de_entrar(self):
        matriculas = [mat(1, DIA0), mat(2, DIA0), mat(3, DIA0)]
        tentativas = [
            tent(ERRO, DIA0 + timedelta(days=1), aluno=1),
            tent(ACERTO, DIA0 + timedelta(days=7), aluno=1),
            tent(ERRO, DIA0 + timedelta(days=1), aluno=2),
            tent(ACERTO, DIA0 + timedelta(days=8), aluno=2),
            tent(ACERTO, DIA0 + timedelta(days=1), aluno=3),
        ]
        a = ativacao(matriculas, tentativas, erros_corrigidos(tentativas))
        assert a["matriculados"] == 3
        assert a["com_primeiro_envio"] == 3
        assert a["ativados"] == 1
        assert a["taxa"] == 33.3
        assert a["meta"] == 60.0

    def test_correcao_antes_da_matricula_nao_ativa(self):
        tentativas = [tent(ERRO, DIA0, origem=TRILHA), tent(ACERTO, DIA0 + timedelta(days=1), origem=TRILHA)]
        a = ativacao([mat(1, DIA0 + timedelta(days=5))], tentativas, erros_corrigidos(tentativas))
        assert a["ativados"] == 0

    def test_envio_de_quem_nao_esta_matriculado_nao_conta(self):
        a = ativacao([mat(1, DIA0)], [tent(ERRO, DIA0, aluno=99)], [])
        assert a["com_primeiro_envio"] == 0

    def test_falha_tecnica_conta_como_envio(self):
        a = ativacao([mat(1, DIA0)], [tent(FALHA, DIA0 + timedelta(days=1))], [])
        assert a["com_primeiro_envio"] == 1


class TestRetencao:
    def test_voltou_e_por_conta_propria_na_semana(self):
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
        s = retencao_da_semana("2026-10-19", matriculas, tentativas)
        assert s["base"] == 3
        assert s["voltaram"] == 2
        assert s["por_conta_propria"] == 1
        assert s["taxa"] == 66.7
        assert s["taxa_por_conta_propria"] == 33.3

    def test_por_conta_propria_tambem_pede_envio_antes(self):
        tentativas = [tent(ERRO, datetime(2026, 10, 20), por_conta_propria=True)]
        s = retencao_da_semana("2026-10-19", [mat(1, DIA0)], tentativas)
        assert s["voltaram"] == 0
        assert s["por_conta_propria"] == 0

    def test_base_zero_da_taxa_nula(self):
        s = retencao_da_semana("2026-10-19", [], [])
        assert s["taxa"] is None
        assert s["taxa_por_conta_propria"] is None

    def test_cartao_usa_a_ultima_semana_completa(self):
        r = retencao([mat(1, DIA0)], [], AGORA)
        assert len(r["semanas"]) == 8
        assert r["semanas"][-1]["semana"] == "2026-10-26"
        assert r["ultima_completa"]["semana"] == "2026-10-19"
        assert r["meta"] == 50.0
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_funil_regras.py -q`
Esperado: FALHA com `ImportError: cannot import name 'aquisicao'`

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/funil_regras.py`, trocar `from datetime import date, datetime, timedelta` por `from datetime import date, datetime, time, timedelta` e acrescentar no fim do arquivo:

```python
def aquisicao(matriculas: list[Matricula], alunos_previstos: int | None) -> dict:
    """A primeira matrícula da turma marca a divulgação do código, e a primeira
    semana conta a partir dela."""
    primeira_semana = 0
    if matriculas:
        divulgacao = min(m.entrada for m in matriculas)
        primeira_semana = sum(1 for m in matriculas if m.entrada <= divulgacao + JANELA)
    return {
        "matriculados": len(matriculas),
        "alunos_previstos": alunos_previstos,
        "taxa_matriculados": taxa(len(matriculas), alunos_previstos),
        "primeira_semana": primeira_semana,
        "taxa_primeira_semana": taxa(primeira_semana, alunos_previstos),
        "meta": META_AQUISICAO,
    }


def alunos_ativados(matriculas: list[Matricula],
                    corrigidos: list[tuple[int, datetime]]) -> set[int]:
    """Quem corrigiu um erro entre a própria matrícula e JANELA depois dela."""
    entrada = {m.aluno: m.entrada for m in matriculas}
    return {
        aluno for aluno, momento in corrigidos
        if aluno in entrada and entrada[aluno] <= momento <= entrada[aluno] + JANELA
    }


def ativacao(matriculas: list[Matricula], tentativas: list[Tentativa],
             corrigidos: list[tuple[int, datetime]]) -> dict:
    matriculados = {m.aluno for m in matriculas}
    ativados = alunos_ativados(matriculas, corrigidos)
    return {
        "matriculados": len(matriculados),
        "com_primeiro_envio": len({t.aluno for t in tentativas} & matriculados),
        "ativados": len(ativados),
        "taxa": taxa(len(ativados), len(matriculados)),
        "meta": META_ATIVACAO,
    }


def retencao_da_semana(semana: str, matriculas: list[Matricula],
                       tentativas: list[Tentativa]) -> dict:
    """Quem enviou na semana e já tinha enviado antes dela. Por conta própria é
    o mesmo, com o envio da semana em atividade de treino ou na trilha."""
    inicio = datetime.combine(date.fromisoformat(semana), time.min)
    fim = inicio + timedelta(weeks=1)
    base = {m.aluno for m in matriculas if m.entrada < fim}
    antes = {t.aluno for t in tentativas if t.momento < inicio}
    na_semana = [t for t in tentativas if inicio <= t.momento < fim]
    voltaram = {t.aluno for t in na_semana} & antes & base
    proprios = {t.aluno for t in na_semana if t.por_conta_propria} & antes & base
    return {
        "semana": semana,
        "base": len(base),
        "voltaram": len(voltaram),
        "por_conta_propria": len(proprios),
        "taxa": taxa(len(voltaram), len(base)),
        "taxa_por_conta_propria": taxa(len(proprios), len(base)),
    }


def retencao(matriculas: list[Matricula], tentativas: list[Tentativa], agora: datetime) -> dict:
    """O cartão usa a última semana completa: a atual começa toda segunda perto
    de zero e pareceria queda."""
    semanas = [retencao_da_semana(s, matriculas, tentativas) for s in ultimas_semanas(agora)]
    return {"semanas": semanas, "ultima_completa": semanas[-2], "meta": META_RETENCAO}
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: PASSA, 27 testes.

- [ ] **Passo 5: commitar**

```bash
git add backend/app/services/funil_regras.py backend/tests/unit/test_funil_regras.py
git commit -m "feat(funil): aquisicao, ativacao e retencao semanal"
```

---

### Task 5: regras puras, saúde do aluno e montagem do funil

**Arquivos:**
- Alterar: `backend/app/services/funil_regras.py` (acrescentar no fim)
- Alterar: `backend/tests/unit/test_funil_regras.py` (acrescentar imports e classes no fim)

**Interfaces:**
- Consome: `Tentativa`, `Matricula`, `taxa`, `_em_ordem`, `erros_corrigidos`, `north_star`, `protecao`, `META_VERMELHO`, `LISTA`, `ACERTO`, `ERRO` da Task 3 e `aquisicao`, `ativacao`, `retencao` da Task 4.
- Produz, em `app.services.funil_regras`:
  - constantes `VERMELHO = "vermelho"`, `AMARELO = "amarelo"`, `LIMITE_VERMELHO = timedelta(days=14)`, `LIMITE_AMARELO = timedelta(days=7)`, `ERROS_SEGUIDOS = 5`, `MOTIVO_SEM_ENVIO_LONGO`, `MOTIVO_PAROU_DEPOIS_DE_ERRAR`, `MOTIVO_SEM_ENVIO`, `MOTIVO_ERROS_SEGUIDOS`
  - `saude(matriculas: list[Matricula], tentativas: list[Tentativa], questoes_abertas: dict[int, int | None], agora: datetime) -> dict`, em que `questoes_abertas` vai do `question_id` ao `max_tentativas` da atividade, só para atividades publicadas e abertas da turma
  - `montar_funil(matriculas: list[Matricula], tentativas: list[Tentativa], questoes_abertas: dict[int, int | None], alunos_previstos: int | None, agora: datetime) -> dict`, com as chaves `north_star`, `aquisicao`, `ativacao`, `retencao`, `saude` e `protecao`

- [ ] **Passo 1: escrever os testes que falham**

Em `backend/tests/unit/test_funil_regras.py`, trocar o bloco de import de `app.services.funil_regras` por:

```python
from app.services.funil_regras import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, Matricula, Tentativa, aquisicao, ativacao,
    erros_corrigidos, montar_funil, north_star, protecao, resultado_da_lista,
    resultado_da_trilha, retencao, retencao_da_semana, saude, ultimas_semanas,
)
```

No fim do arquivo, acrescentar:

```python
# Questões 10 e 11 abertas e sem teto de tentativas.
ABERTAS = {10: None, 11: None}


def _dias(n, **extra):
    return AGORA - timedelta(days=n, **extra)


def _saude(tentativas, matriculas=None, abertas=None):
    matriculas = matriculas if matriculas is not None else [mat(1, _dias(30), nome="Ana")]
    return saude(matriculas, tentativas, ABERTAS if abertas is None else abertas, AGORA)


def _cores(s):
    return ([(a["nome"], a["motivo"]) for a in s["vermelho"]],
            [(a["nome"], a["motivo"]) for a in s["amarelo"]])


class TestSaude:
    def test_mais_de_14_dias_sem_envio_e_vermelho(self):
        s = _saude([tent(ACERTO, _dias(15), item=11)])
        assert _cores(s) == ([("Ana", "Mais de 14 dias sem envio")], [])
        assert s["vermelho"][0]["dias_sem_envio"] == 15
        assert s["vermelho"][0]["ultimo_envio"] == _dias(15).isoformat()

    def test_exatamente_14_dias_ainda_e_amarelo(self):
        s = _saude([tent(ACERTO, _dias(14), item=11)])
        assert _cores(s) == ([], [("Ana", "7 a 14 dias sem envio")])

    def test_exatamente_7_dias_ja_e_amarelo(self):
        s = _saude([tent(ACERTO, _dias(7), item=11)])
        assert _cores(s) == ([], [("Ana", "7 a 14 dias sem envio")])

    def test_mais_de_7_dias_depois_de_errar_numa_questao_em_aberto_e_vermelho(self):
        s = _saude([tent(ERRO, _dias(8), item=10)])
        assert _cores(s) == ([("Ana", "Parou depois de errar")], [])

    def test_exatamente_7_dias_depois_de_errar_e_amarelo(self):
        s = _saude([tent(ERRO, _dias(7), item=10)])
        assert _cores(s) == ([], [("Ana", "7 a 14 dias sem envio")])

    def test_8_dias_depois_de_acertar_e_amarelo(self):
        s = _saude([tent(ACERTO, _dias(8), item=11)])
        assert _cores(s) == ([], [("Ana", "7 a 14 dias sem envio")])

    def test_falha_tecnica_no_fim_nao_e_parar_depois_de_errar(self):
        s = _saude([tent(FALHA, _dias(8), item=10)])
        assert _cores(s) == ([], [("Ana", "7 a 14 dias sem envio")])

    def test_cinco_erros_numa_questao_em_aberto_e_amarelo(self):
        s = _saude([tent(ERRO, _dias(3, minutes=i), item=10) for i in range(5)])
        assert _cores(s) == ([], [("Ana", "5 erros seguidos na mesma questão")])

    def test_quatro_erros_e_6_dias_fica_fora(self):
        s = _saude([tent(ERRO, _dias(6, minutes=i), item=10) for i in range(4)])
        assert _cores(s) == ([], [])

    def test_quem_nunca_enviou_conta_desde_a_matricula(self):
        s = _saude([], matriculas=[mat(1, _dias(15), nome="Ana"), mat(2, _dias(8), nome="Bia")])
        assert _cores(s) == ([("Ana", "Mais de 14 dias sem envio")], [("Bia", "7 a 14 dias sem envio")])
        assert s["vermelho"][0]["ultimo_envio"] is None

    def test_quem_resolveu_tudo_o_que_esta_aberto_fica_fora(self):
        s = _saude([tent(ACERTO, _dias(30), item=10), tent(ACERTO, _dias(30), item=11)])
        assert _cores(s) == ([], [])

    def test_sem_questao_aberta_ninguem_fica_pendente(self):
        s = _saude([], abertas={})
        assert _cores(s) == ([], [])

    def test_teto_de_tentativas_gasto_tira_a_questao(self):
        tentativas = [tent(ERRO, _dias(20), item=10), tent(ERRO, _dias(20, minutes=-1), item=10)]
        assert _cores(_saude(tentativas, abertas={10: 2})) == ([], [])
        assert _cores(_saude(tentativas, abertas={10: 3}))[0] == [("Ana", "Mais de 14 dias sem envio")]

    def test_trilha_conta_como_envio_mas_nao_vira_motivo(self):
        tentativas = [tent(ERRO, _dias(20), item=10)]
        tentativas += [tent(ERRO, _dias(1, minutes=i), item=7, origem=TRILHA) for i in range(5)]
        assert _cores(_saude(tentativas)) == ([], [])

    def test_ordem_por_dias_sem_envio_e_depois_por_nome(self):
        matriculas = [mat(1, _dias(16), nome="Caio"), mat(2, _dias(20), nome="Bia"),
                      mat(3, _dias(16), nome="Ana")]
        s = _saude([], matriculas=matriculas)
        assert [a["nome"] for a in s["vermelho"]] == ["Bia", "Ana", "Caio"]

    def test_taxa_de_vermelho_sobre_os_matriculados(self):
        matriculas = [mat(1, _dias(20), nome="Ana")] + [mat(i, _dias(1), nome=f"A{i}") for i in range(2, 5)]
        s = _saude([], matriculas=matriculas)
        assert s["taxa_vermelho"] == 25.0
        assert s["meta"] == 15.0


class TestMontarFunil:
    def test_traz_os_seis_blocos(self):
        funil = montar_funil([mat(1, _dias(30))], [], ABERTAS, 40, AGORA)
        assert set(funil) == {"north_star", "aquisicao", "ativacao", "retencao", "saude", "protecao"}
        assert funil["aquisicao"]["alunos_previstos"] == 40
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_funil_regras.py -q`
Esperado: FALHA com `ImportError: cannot import name 'montar_funil'`

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/funil_regras.py`, logo depois de `META_VERMELHO = 15.0`, acrescentar:

```python

VERMELHO = "vermelho"
AMARELO = "amarelo"
LIMITE_VERMELHO = timedelta(days=14)
LIMITE_AMARELO = timedelta(days=7)
ERROS_SEGUIDOS = 5

MOTIVO_SEM_ENVIO_LONGO = "Mais de 14 dias sem envio"
MOTIVO_PAROU_DEPOIS_DE_ERRAR = "Parou depois de errar"
MOTIVO_SEM_ENVIO = "7 a 14 dias sem envio"
MOTIVO_ERROS_SEGUIDOS = "5 erros seguidos na mesma questão"
```

No fim do arquivo, acrescentar:

```python
def _questoes_em_aberto(serie: list[Tentativa],
                        questoes_abertas: dict[int, int | None]) -> dict[int, int]:
    """Questão aberta sem acerto em que o aluno ainda pode enviar, com quantos
    erros ele já tem nela. Quem gastou o teto não tem mais o que fazer ali."""
    por_questao: dict[int, list[Tentativa]] = defaultdict(list)
    for t in serie:
        if t.origem == LISTA:
            por_questao[t.item_id].append(t)
    em_aberto = {}
    for questao_id, teto in questoes_abertas.items():
        feitas = por_questao.get(questao_id, [])
        if any(t.resultado == ACERTO for t in feitas):
            continue
        if teto is not None and len(feitas) >= teto:
            continue
        em_aberto[questao_id] = sum(1 for t in feitas if t.resultado == ERRO)
    return em_aberto


def _cor(parado: timedelta, ultimo: Tentativa | None,
         em_aberto: dict[int, int]) -> tuple[str | None, str | None]:
    if parado > LIMITE_VERMELHO:
        return VERMELHO, MOTIVO_SEM_ENVIO_LONGO
    parou_no_erro = (
        ultimo is not None and ultimo.origem == LISTA
        and ultimo.resultado == ERRO and ultimo.item_id in em_aberto
    )
    if parado > LIMITE_AMARELO and parou_no_erro:
        return VERMELHO, MOTIVO_PAROU_DEPOIS_DE_ERRAR
    if parado >= LIMITE_AMARELO:
        return AMARELO, MOTIVO_SEM_ENVIO
    if any(erros >= ERROS_SEGUIDOS for erros in em_aberto.values()):
        return AMARELO, MOTIVO_ERROS_SEGUIDOS
    return None, None


def saude(matriculas: list[Matricula], tentativas: list[Tentativa],
          questoes_abertas: dict[int, int | None], agora: datetime) -> dict:
    """Só entra em risco quem ainda tem questão aberta para resolver (RN09). A
    trilha conta como envio, mas nunca vira motivo: o professor não vê a trilha."""
    por_aluno: dict[int, list[Tentativa]] = defaultdict(list)
    for t in _em_ordem(tentativas):
        por_aluno[t.aluno].append(t)

    listas: dict[str, list[dict]] = {VERMELHO: [], AMARELO: []}
    for m in matriculas:
        serie = por_aluno.get(m.aluno, [])
        em_aberto = _questoes_em_aberto(serie, questoes_abertas)
        if not em_aberto:
            continue
        ultimo = serie[-1] if serie else None
        parado = agora - (ultimo.momento if ultimo else m.entrada)
        cor, motivo = _cor(parado, ultimo, em_aberto)
        if cor is None:
            continue
        listas[cor].append({
            "student_id": m.aluno,
            "nome": m.nome,
            "motivo": motivo,
            "dias_sem_envio": parado.days,
            "ultimo_envio": ultimo.momento.isoformat() if ultimo else None,
        })
    for alunos in listas.values():
        alunos.sort(key=lambda a: (-a["dias_sem_envio"], a["nome"]))
    return {
        "vermelho": listas[VERMELHO],
        "amarelo": listas[AMARELO],
        "taxa_vermelho": taxa(len(listas[VERMELHO]), len(matriculas)),
        "meta": META_VERMELHO,
    }


def montar_funil(matriculas: list[Matricula], tentativas: list[Tentativa],
                 questoes_abertas: dict[int, int | None], alunos_previstos: int | None,
                 agora: datetime) -> dict:
    corrigidos = erros_corrigidos(tentativas)
    return {
        "north_star": north_star(corrigidos, agora),
        "aquisicao": aquisicao(matriculas, alunos_previstos),
        "ativacao": ativacao(matriculas, tentativas, corrigidos),
        "retencao": retencao(matriculas, tentativas, agora),
        "saude": saude(matriculas, tentativas, questoes_abertas, agora),
        "protecao": protecao(tentativas),
    }
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: PASSA, 44 testes.

- [ ] **Passo 5: commitar**

```bash
git add backend/app/services/funil_regras.py backend/tests/unit/test_funil_regras.py
git commit -m "feat(funil): saude do aluno em vermelho e amarelo"
```

---

### Task 6: serviço que lê o banco, `funil_da_turma` e `funil_geral`

**Arquivos:**
- Criar: `backend/app/services/funil_service.py`
- Teste: `backend/tests/test_funil.py`

**Interfaces:**
- Consome: `Turma.alunos_previstos` (Task 1), `situacao_da_atividade` (Task 2), e de `app.services.funil_regras` (Tasks 3 a 5): `LISTA`, `TRILHA`, `Matricula`, `Tentativa`, `alunos_ativados`, `erros_corrigidos`, `montar_funil`, `north_star`, `resultado_da_lista`, `resultado_da_trilha`, `retencao_da_semana`, `taxa`, `ultimas_semanas`.
- Produz, em `app.services.funil_service`:
  - `funil_da_turma(turma: Turma, db: Session, agora: datetime | None = None) -> dict`, com `turma_id`, `gerado_em` (ISO de `agora`) e as seis chaves de `montar_funil`
  - `funil_geral(db: Session, agora: datetime | None = None) -> dict`, com `gerado_em`, `total` (`north_star`, `professores_com_turma`, `turmas_com_matricula`, `matriculados`, `ativados`, `taxa_ativacao`, `retencao_ultima_semana`) e `por_turma` (lista com `turma_id`, `nome`, `professor`, `matriculados`, `alunos_previstos`, `taxa_ativacao`, `taxa_retencao`, `north_star_semana`, `north_star_total`, `vermelhos`), em ordem de `Turma.id`

- [ ] **Passo 1: escrever os testes que falham**

Criar `backend/tests/test_funil.py`:

```python
"""Funil da turma lido do banco: o que entra na conta e o que fica de fora."""
from datetime import datetime, timedelta

import pytest

from app.models.orm import (
    Enrollment, ExercicioGerado, Exam, Question, Student, Submission, TentativaDeTreino, Turma,
)
from app.services.funil_service import funil_da_turma, funil_geral

# Quarta-feira. A semana atual começa em 2026-10-26 e a última completa em 2026-10-19.
AGORA = datetime(2026, 10, 28, 12, 0)
ERRO_COMUM = "Violação de Estrutura"


def _turma(db, professor, nome="CS1 A", alunos_previstos=None):
    turma = Turma(nome=nome, codigo="CS1", professor_id=professor.id,
                  alunos_previstos=alunos_previstos)
    db.add(turma)
    db.commit()
    db.refresh(turma)
    return turma


def _atividade(db, turma, publicada=True, modo="prova", abre_em=None, fecha_em=None,
               max_tentativas=None):
    exam = Exam(filename="lista.pdf", raw_text="", turma_id=turma.id, publicada=publicada,
                modo=modo, abre_em=abre_em, fecha_em=fecha_em, max_tentativas=max_tentativas)
    db.add(exam)
    db.flush()
    questao = Question(exam_id=exam.id, number="1", statement="Enunciado")
    db.add(questao)
    db.commit()
    db.refresh(questao)
    return questao


def _aluno(db, email, nome, turmas, entrada=AGORA - timedelta(days=20)):
    aluno = Student(email=email, nome=nome, senha_hash="x")
    db.add(aluno)
    db.flush()
    for turma in turmas:
        db.add(Enrollment(student_id=aluno.id, turma_id=turma.id, created_at=entrada))
    db.commit()
    db.refresh(aluno)
    return aluno


def _envio(db, aluno, questao, categoria, momento):
    db.add(Submission(question_id=questao.id, student_id=aluno.id if aluno else None,
                      matricula=None if aluno else "2026001", code="int main(){return 0;}",
                      error_category=categoria, submitted_at=momento))
    db.commit()


def _treino(db, aluno, passou, momento, exercicio=None):
    if exercicio is None:
        exercicio = ExercicioGerado(student_id=aluno.id, error_category=ERRO_COMUM,
                                    titulo="Treino", enunciado="Enunciado", casos_teste=[])
        db.add(exercicio)
        db.flush()
    db.add(TentativaDeTreino(exercicio_id=exercicio.id, student_id=aluno.id,
                             code="int main(){return 0;}", all_tests_passed=passou,
                             error_category="" if passou else ERRO_COMUM, submitted_at=momento))
    db.commit()
    return exercicio


def _nomes(saude):
    return [a["nome"] for a in saude["vermelho"]], [a["nome"] for a in saude["amarelo"]]


class TestFunilDaTurma:
    def test_conta_erro_corrigido_da_lista_e_da_trilha(self, db, professor):
        turma = _turma(db, professor)
        questao = _atividade(db, turma)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma])
        _envio(db, ana, questao, ERRO_COMUM, AGORA - timedelta(days=1))
        _envio(db, ana, questao, "Correto", AGORA - timedelta(hours=2))
        exercicio = _treino(db, ana, False, AGORA - timedelta(days=1))
        _treino(db, ana, True, AGORA - timedelta(hours=1), exercicio=exercicio)

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["turma_id"] == turma.id
        assert funil["gerado_em"] == AGORA.isoformat()
        assert funil["north_star"]["total"] == 2
        assert funil["north_star"]["semana_atual"] == 2

    def test_envio_sem_conta_fica_fora(self, db, professor):
        turma = _turma(db, professor)
        questao = _atividade(db, turma)
        _aluno(db, "ana@teste.com", "Ana", [turma])
        _envio(db, None, questao, ERRO_COMUM, AGORA - timedelta(days=1))
        _envio(db, None, questao, "Correto", AGORA - timedelta(hours=2))

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["north_star"]["total"] == 0
        assert funil["ativacao"]["com_primeiro_envio"] == 0

    def test_atividade_nao_publicada_fica_fora(self, db, professor):
        turma = _turma(db, professor)
        rascunho = _atividade(db, turma, publicada=False)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma])
        _envio(db, ana, rascunho, ERRO_COMUM, AGORA - timedelta(days=1))
        _envio(db, ana, rascunho, "Correto", AGORA - timedelta(hours=2))

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["north_star"]["total"] == 0
        assert _nomes(funil["saude"]) == ([], [])

    def test_atividade_encerrada_ou_agendada_nao_deixa_pendente(self, db, professor):
        turma = _turma(db, professor)
        _atividade(db, turma, fecha_em=AGORA - timedelta(days=1))
        _atividade(db, turma, abre_em=AGORA + timedelta(days=1))
        _aluno(db, "ana@teste.com", "Ana", [turma])

        assert _nomes(funil_da_turma(turma, db, agora=AGORA)["saude"]) == ([], [])

        _atividade(db, turma)
        assert _nomes(funil_da_turma(turma, db, agora=AGORA)["saude"]) == (["Ana"], [])

    @pytest.mark.parametrize("teto, vermelhos", [(2, []), (3, ["Ana"])])
    def test_teto_de_tentativas_gasto_tira_a_questao(self, db, professor, teto, vermelhos):
        turma = _turma(db, professor)
        questao = _atividade(db, turma, max_tentativas=teto)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma], entrada=AGORA - timedelta(days=30))
        _envio(db, ana, questao, ERRO_COMUM, AGORA - timedelta(days=20))
        _envio(db, ana, questao, ERRO_COMUM, AGORA - timedelta(days=20, minutes=-1))

        assert _nomes(funil_da_turma(turma, db, agora=AGORA)["saude"])[0] == vermelhos

    def test_tamanho_da_turma_e_atividade_de_treino(self, db, professor):
        turma = _turma(db, professor, alunos_previstos=4)
        questao = _atividade(db, turma, modo="treino")
        ana = _aluno(db, "ana@teste.com", "Ana", [turma], entrada=AGORA - timedelta(days=30))
        _envio(db, ana, questao, ERRO_COMUM, datetime(2026, 10, 14, 10))
        _envio(db, ana, questao, ERRO_COMUM, datetime(2026, 10, 20, 10))

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["aquisicao"]["alunos_previstos"] == 4
        assert funil["aquisicao"]["taxa_matriculados"] == 25.0
        ultima = funil["retencao"]["ultima_completa"]
        assert ultima["semana"] == "2026-10-19"
        assert ultima["voltaram"] == 1
        assert ultima["por_conta_propria"] == 1


class TestFunilGeral:
    def test_treino_de_aluno_em_duas_turmas_conta_uma_vez_no_total(self, db, professor):
        a = _turma(db, professor, "CS1 A")
        b = _turma(db, professor, "CS1 B")
        ana = _aluno(db, "ana@teste.com", "Ana", [a, b])
        exercicio = _treino(db, ana, False, AGORA - timedelta(days=1))
        _treino(db, ana, True, AGORA - timedelta(hours=1), exercicio=exercicio)

        assert funil_da_turma(a, db, agora=AGORA)["north_star"]["total"] == 1
        assert funil_da_turma(b, db, agora=AGORA)["north_star"]["total"] == 1
        geral = funil_geral(db, agora=AGORA)
        assert geral["total"]["north_star"]["total"] == 1
        assert geral["total"]["matriculados"] == 1
        assert [t["north_star_total"] for t in geral["por_turma"]] == [1, 1]

    def test_professores_e_turmas_com_matricula(self, db, professor):
        a = _turma(db, professor, "CS1 A", alunos_previstos=30)
        _turma(db, professor, "CS1 B")
        _aluno(db, "ana@teste.com", "Ana", [a])

        geral = funil_geral(db, agora=AGORA)

        assert geral["total"]["professores_com_turma"] == 1
        assert geral["total"]["turmas_com_matricula"] == 1
        assert [t["nome"] for t in geral["por_turma"]] == ["CS1 A", "CS1 B"]
        assert geral["por_turma"][0]["professor"] == "Professor Teste"
        assert geral["por_turma"][0]["alunos_previstos"] == 30
        assert geral["total"]["retencao_ultima_semana"]["semana"] == "2026-10-19"

    def test_base_vazia(self, db):
        geral = funil_geral(db, agora=AGORA)
        assert geral["por_turma"] == []
        assert geral["total"]["matriculados"] == 0
        assert geral["total"]["taxa_ativacao"] is None
        assert geral["total"]["north_star"]["total"] == 0
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_funil.py -q`
Esperado: FALHA com `ModuleNotFoundError: No module named 'app.services.funil_service'`

- [ ] **Passo 3: escrever o mínimo para passar**

Criar `backend/app/services/funil_service.py`:

```python
"""Funil da turma calculado na hora, com o que o banco já guarda.

Este módulo só lê e converte em registros. As contas estão em `funil_regras`."""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.orm import (
    Enrollment, Exam, Professor, Question, Student, Submission, TentativaDeTreino, Turma,
)
from app.services.calendario import situacao_da_atividade
from app.services.funil_regras import (
    LISTA, TRILHA, Matricula, Tentativa, alunos_ativados, erros_corrigidos, montar_funil,
    north_star, resultado_da_lista, resultado_da_trilha, retencao_da_semana, taxa,
    ultimas_semanas,
)


@dataclass
class _DadosDaTurma:
    matriculas: list[Matricula]
    tentativas: list[Tentativa]
    questoes_abertas: dict[int, int | None]


def _matriculas(turma_id: int, db: Session) -> list[Matricula]:
    linhas = (
        db.query(Enrollment.student_id, Student.nome, Enrollment.created_at)
        .join(Student, Student.id == Enrollment.student_id)
        .filter(Enrollment.turma_id == turma_id)
        .all()
    )
    return [Matricula(aluno=aluno, nome=nome, entrada=entrada) for aluno, nome, entrada in linhas]


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
    """A trilha não tem turma, então o treino do aluno entra em todas as turmas dele."""
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


def _questoes_abertas(turma_id: int, db: Session, agora: datetime) -> dict[int, int | None]:
    linhas = (
        db.query(Question.id, Exam)
        .join(Exam, Exam.id == Question.exam_id)
        .filter(Exam.turma_id == turma_id, Exam.publicada.is_(True))
        .all()
    )
    return {
        questao: exam.max_tentativas for questao, exam in linhas
        if situacao_da_atividade(exam, agora) == "aberta"
    }


def _dados_da_turma(turma: Turma, db: Session, agora: datetime) -> _DadosDaTurma:
    matriculas = _matriculas(turma.id, db)
    alunos = [m.aluno for m in matriculas]
    tentativas: list[Tentativa] = []
    if alunos:
        tentativas = _tentativas_de_lista(turma.id, alunos, db) + _tentativas_de_trilha(alunos, db)
    return _DadosDaTurma(matriculas, tentativas, _questoes_abertas(turma.id, db, agora))


def funil_da_turma(turma: Turma, db: Session, agora: datetime | None = None) -> dict:
    agora = agora or datetime.utcnow()
    dados = _dados_da_turma(turma, db, agora)
    return {
        "turma_id": turma.id,
        "gerado_em": agora.isoformat(),
        **montar_funil(dados.matriculas, dados.tentativas, dados.questoes_abertas,
                       turma.alunos_previstos, agora),
    }


def funil_geral(db: Session, agora: datetime | None = None) -> dict:
    """Todas as turmas, para o script da equipe. O total conta cada item e cada
    aluno uma vez, então não é a soma das turmas: o treino de quem está em duas
    turmas aparece nas duas."""
    agora = agora or datetime.utcnow()
    turmas = db.query(Turma).order_by(Turma.id).all()
    professores = dict(db.query(Professor.id, Professor.nome).all())

    por_turma = []
    todas: set[Tentativa] = set()
    primeira_entrada: dict[int, Matricula] = {}
    ativados: set[int] = set()
    for turma in turmas:
        dados = _dados_da_turma(turma, db, agora)
        funil = montar_funil(dados.matriculas, dados.tentativas, dados.questoes_abertas,
                             turma.alunos_previstos, agora)
        todas.update(dados.tentativas)
        ativados |= alunos_ativados(dados.matriculas, erros_corrigidos(dados.tentativas))
        for m in dados.matriculas:
            atual = primeira_entrada.get(m.aluno)
            if atual is None or m.entrada < atual.entrada:
                primeira_entrada[m.aluno] = m
        por_turma.append({
            "turma_id": turma.id,
            "nome": turma.nome,
            "professor": professores.get(turma.professor_id),
            "matriculados": funil["aquisicao"]["matriculados"],
            "alunos_previstos": turma.alunos_previstos,
            "taxa_ativacao": funil["ativacao"]["taxa"],
            "taxa_retencao": funil["retencao"]["ultima_completa"]["taxa"],
            "north_star_semana": funil["north_star"]["semana_atual"],
            "north_star_total": funil["north_star"]["total"],
            "vermelhos": len(funil["saude"]["vermelho"]),
        })

    matriculas = list(primeira_entrada.values())
    tentativas = list(todas)
    return {
        "gerado_em": agora.isoformat(),
        "total": {
            "north_star": north_star(erros_corrigidos(tentativas), agora),
            "professores_com_turma": len({t.professor_id for t in turmas if t.professor_id is not None}),
            "turmas_com_matricula": sum(1 for t in por_turma if t["matriculados"]),
            "matriculados": len(matriculas),
            "ativados": len(ativados),
            "taxa_ativacao": taxa(len(ativados), len(matriculas)),
            "retencao_ultima_semana": retencao_da_semana(
                ultimas_semanas(agora)[-2], matriculas, tentativas),
        },
        "por_turma": por_turma,
    }
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: PASSA, 10 testes.

- [ ] **Passo 5: suíte inteira**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q 2>&1 | tail -3`
Esperado: tudo passa.

- [ ] **Passo 6: commitar**

```bash
git add backend/app/services/funil_service.py backend/tests/test_funil.py
git commit -m "feat(funil): leitura do banco por turma e total de todas as turmas"
```

---

### Task 7: esquemas da resposta e rota `GET /turmas/{id}/funil`

**Arquivos:**
- Alterar: `backend/app/models/schemas.py` (logo depois da classe `TurmaAnalyticsResponse`)
- Alterar: `backend/app/api/routes/turma.py` (imports e rota nova no fim)
- Alterar: `backend/tests/test_funil.py` (imports, fixture `anonimo` e classe nova no fim)

**Interfaces:**
- Consome: `funil_da_turma(turma, db, agora=None)` da Task 6 e `_get_turma_or_404(turma_id, db, professor_id)`, que já existe em `routes/turma.py`.
- Produz: `FunilTurmaResponse` e submodelos em `app.models.schemas`. Rota `GET /turmas/{turma_id}/funil`, que o front chama na Task 10.

- [ ] **Passo 1: escrever os testes que falham**

Em `backend/tests/test_funil.py`, trocar os imports do topo por:

```python
"""Funil da turma lido do banco: o que entra na conta e o que fica de fora."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.auth.student_service import create_student_token
from app.main import app as fastapi_app
from app.models.database import get_db
from app.models.orm import (
    Enrollment, ExercicioGerado, Exam, Professor, Question, Student, Submission,
    TentativaDeTreino, Turma,
)
from app.services.funil_service import funil_da_turma, funil_geral
```

No fim do arquivo, acrescentar:

```python
@pytest.fixture()
def anonimo(db):
    """Cliente sem professor injetado: quem decide é a autenticação de verdade."""
    def override_get_db():
        yield db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


class TestRota:
    def test_dono_recebe_o_funil(self, client, db, professor):
        turma = _turma(db, professor)
        _atividade(db, turma)
        _aluno(db, "ana@teste.com", "Ana Lima", [turma],
               entrada=datetime.utcnow() - timedelta(days=20))

        resp = client.get(f"/turmas/{turma.id}/funil")

        assert resp.status_code == 200
        corpo = resp.json()
        assert corpo["turma_id"] == turma.id
        assert len(corpo["north_star"]["semanas"]) == 8
        assert len(corpo["retencao"]["semanas"]) == 8
        assert corpo["aquisicao"]["meta"] == 80.0
        assert corpo["saude"]["vermelho"][0]["nome"] == "Ana Lima"
        assert corpo["saude"]["vermelho"][0]["ultimo_envio"] is None
        assert corpo["protecao"]["itens_com_acerto"] == 0

    def test_turma_de_outro_professor_da_404(self, client, db):
        outro = Professor(email="outro@teste.com", nome="Outro Professor", senha_hash="x")
        db.add(outro)
        db.commit()
        turma = _turma(db, outro)
        assert client.get(f"/turmas/{turma.id}/funil").status_code == 404

    def test_token_de_aluno_da_401(self, anonimo, db, professor):
        turma = _turma(db, professor)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma])
        token = create_student_token(ana.id)
        resp = anonimo.get(f"/turmas/{turma.id}/funil",
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_sem_token_da_401(self, anonimo, db, professor):
        turma = _turma(db, professor)
        assert anonimo.get(f"/turmas/{turma.id}/funil").status_code == 401
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_funil.py -q`
Esperado: FALHA em `TestRota` com status 404 onde se espera 200 e 401, porque a rota não existe.

- [ ] **Passo 3: esquemas**

Em `backend/app/models/schemas.py`, logo depois da classe `TurmaAnalyticsResponse` (antes do comentário `# ── Aluno: atividades, tentativas e progresso`), acrescentar:

```python
# ── Funil da turma ───────────────────────────────────────────────────────────

class SemanaNorthStar(BaseModel):
    semana: str
    erros_corrigidos: int


class NorthStarFunil(BaseModel):
    semana_atual: int
    total: int
    semanas: List[SemanaNorthStar]


class AquisicaoFunil(BaseModel):
    matriculados: int
    alunos_previstos: Optional[int] = None
    taxa_matriculados: Optional[float] = None
    primeira_semana: int
    taxa_primeira_semana: Optional[float] = None
    meta: float


class AtivacaoFunil(BaseModel):
    matriculados: int
    com_primeiro_envio: int
    ativados: int
    taxa: Optional[float] = None
    meta: float


class SemanaRetencao(BaseModel):
    semana: str
    base: int
    voltaram: int
    por_conta_propria: int
    taxa: Optional[float] = None
    taxa_por_conta_propria: Optional[float] = None


class RetencaoFunil(BaseModel):
    semanas: List[SemanaRetencao]
    ultima_completa: SemanaRetencao
    meta: float


class AlunoEmRisco(BaseModel):
    student_id: int
    nome: str
    motivo: str
    dias_sem_envio: int
    ultimo_envio: Optional[str] = None


class SaudeFunil(BaseModel):
    vermelho: List[AlunoEmRisco]
    amarelo: List[AlunoEmRisco]
    taxa_vermelho: Optional[float] = None
    meta: float


class ProtecaoFunil(BaseModel):
    media_tentativas_ate_acertar: Optional[float] = None
    acerto_de_primeira: Optional[float] = None
    itens_com_acerto: int


class FunilTurmaResponse(BaseModel):
    turma_id: int
    gerado_em: str
    north_star: NorthStarFunil
    aquisicao: AquisicaoFunil
    ativacao: AtivacaoFunil
    retencao: RetencaoFunil
    saude: SaudeFunil
    protecao: ProtecaoFunil

```

- [ ] **Passo 4: rota**

Em `backend/app/api/routes/turma.py`, trocar o import de `app.models.schemas` por:

```python
from app.models.schemas import (
    FunilTurmaResponse, TurmaAnalyticsResponse, TurmaCreate, TurmaDetailResponse, TurmaResponse,
    TurmaUpdate,
)
```

Logo depois do import de `app.services.turma_service`, acrescentar:

```python
from app.services.funil_service import funil_da_turma
```

No fim do arquivo, acrescentar:

```python
@router.get("/{turma_id}/funil", response_model=FunilTurmaResponse)
def get_funil(
    turma_id: int,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    turma = _get_turma_or_404(turma_id, db, professor.id)
    return funil_da_turma(turma, db)
```

- [ ] **Passo 5: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: PASSA, 14 testes.

- [ ] **Passo 6: suíte inteira**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q 2>&1 | tail -3`
Esperado: tudo passa.

- [ ] **Passo 7: commitar**

```bash
git add backend/app/models/schemas.py backend/app/api/routes/turma.py backend/tests/test_funil.py
git commit -m "feat(funil): rota do funil da turma para o professor dono"
```

---

### Task 8: script `funil.py` com o total de todas as turmas

**Arquivos:**
- Criar: `backend/scripts/funil.py`
- Teste: `backend/tests/test_script_funil.py`

**Interfaces:**
- Consome: `funil_geral(db, agora=None)` da Task 6, com as chaves descritas lá.
- Produz: `relatorio(db: Session, agora: datetime | None = None) -> str` em `scripts.funil`.

- [ ] **Passo 1: escrever os testes que falham**

Criar `backend/tests/test_script_funil.py`:

```python
"""Relatório do funil para a equipe: só números, nenhum nome de aluno."""
from datetime import datetime, timedelta

from app.models.orm import Enrollment, Exam, Question, Student, Turma
from scripts.funil import relatorio

AGORA = datetime(2026, 10, 28, 12, 0)


def test_base_vazia_roda_sem_erro(db):
    texto = relatorio(db, agora=AGORA)
    assert "Nenhuma turma cadastrada." in texto
    assert "Matriculados: 0" in texto
    assert "Total desde o início: 0" in texto


def test_turma_aparece_sem_nome_de_aluno(db, professor):
    turma = Turma(nome="CS1 Noite", codigo="CS1", professor_id=professor.id, alunos_previstos=40)
    db.add(turma)
    db.flush()
    exam = Exam(filename="lista.pdf", raw_text="", turma_id=turma.id, publicada=True)
    db.add(exam)
    db.flush()
    db.add(Question(exam_id=exam.id, number="1", statement="Enunciado"))
    aluna = Student(email="beatriz@teste.com", nome="Beatriz Souza", senha_hash="x")
    db.add(aluna)
    db.flush()
    db.add(Enrollment(student_id=aluna.id, turma_id=turma.id, created_at=AGORA - timedelta(days=20)))
    db.commit()

    texto = relatorio(db, agora=AGORA)

    assert "CS1 Noite (Professor Teste)" in texto
    assert "1 matriculados de 40 previstos" in texto
    assert "1 em vermelho" in texto
    assert "Beatriz" not in texto
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_script_funil.py -q`
Esperado: FALHA com `ModuleNotFoundError: No module named 'scripts.funil'`

- [ ] **Passo 3: escrever o mínimo para passar**

Criar `backend/scripts/funil.py`:

```python
"""
Funil de todas as turmas, para a equipe acompanhar a North Star sem criar papel
de administrador. Mostra só números: nenhum nome de aluno sai daqui.

Uso:
    cd backend
    venv/bin/python scripts/funil.py
"""
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import SessionLocal
from app.services.funil_service import funil_geral


def _pct(valor: float | None) -> str:
    return "sem dado" if valor is None else f"{valor}%"


def relatorio(db: Session, agora: datetime | None = None) -> str:
    funil = funil_geral(db, agora)
    total = funil["total"]
    ns = total["north_star"]
    semana = total["retencao_ultima_semana"]
    linhas = [
        f"Funil de todas as turmas, gerado em {funil['gerado_em'][:16].replace('T', ' ')} UTC",
        "",
        "North Star, erros corrigidos por semana",
        *(f"  {s['semana']}  {s['erros_corrigidos']}" for s in ns["semanas"]),
        f"  Total desde o início: {ns['total']}",
        "",
        "Total",
        f"  Professores com turma: {total['professores_com_turma']}",
        f"  Turmas com matrícula: {total['turmas_com_matricula']}",
        f"  Matriculados: {total['matriculados']}",
        f"  Ativados: {total['ativados']} ({_pct(total['taxa_ativacao'])})",
        f"  Retenção na semana de {semana['semana']}: {semana['voltaram']} de {semana['base']} "
        f"({_pct(semana['taxa'])})",
        "",
        "Por turma",
    ]
    if not funil["por_turma"]:
        linhas.append("  Nenhuma turma cadastrada.")
    for t in funil["por_turma"]:
        previstos = f" de {t['alunos_previstos']} previstos" if t["alunos_previstos"] else ""
        linhas.append(
            f"  {t['nome']} ({t['professor'] or 'sem professor'}): "
            f"{t['matriculados']} matriculados{previstos}, "
            f"ativação {_pct(t['taxa_ativacao'])}, retenção {_pct(t['taxa_retencao'])}, "
            f"erros corrigidos {t['north_star_semana']} na semana e {t['north_star_total']} no total, "
            f"{t['vermelhos']} em vermelho"
        )
    return "\n".join(linhas)


def main() -> None:
    db = SessionLocal()
    try:
        print(relatorio(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: PASSA, 2 testes. Não rodar o script contra o banco de desenvolvimento, que ainda não tem a coluna da 0017.

- [ ] **Passo 5: suíte inteira**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q 2>&1 | tail -3`
Esperado: tudo passa.

- [ ] **Passo 6: commitar**

```bash
git add backend/scripts/funil.py backend/tests/test_script_funil.py
git commit -m "feat(funil): script com o funil de todas as turmas para a equipe"
```

---

### Task 9: front, chamadas da API e campo "Alunos na turma"

**Arquivos:**
- Alterar: `frontend/src/api/exam.js` (`createTurma`, `updateTurma` e uma chamada nova depois de `getTurmaAnalytics`)
- Alterar: `frontend/src/pages/TurmaListPage.jsx`

**Interfaces:**
- Consome: `alunos_previstos` em `POST /turmas`, `PUT /turmas/{id}` e `GET /turmas` (Task 1). `GET /turmas/{id}/funil` (Task 7).
- Produz: `getTurmaFunil(id)`, `createTurma(nome, codigo, alunosPrevistos = null)` e `updateTurma(id, nome, codigo, alunosPrevistos = null)` em `frontend/src/api/exam.js`.

- [ ] **Passo 1: chamadas da API**

Em `frontend/src/api/exam.js`, trocar `createTurma` e `updateTurma` por:

```js
export const createTurma = (nome, codigo, alunosPrevistos = null) =>
  api.post('/turmas', { nome, codigo, alunos_previstos: alunosPrevistos })

export const updateTurma = (id, nome, codigo, alunosPrevistos = null) =>
  api.put(`/turmas/${id}`, { nome, codigo, alunos_previstos: alunosPrevistos })
```

Logo depois de `export const getTurmaAnalytics = ...`, acrescentar:

```js

export const getTurmaFunil = (id) => api.get(`/turmas/${id}/funil`)
```

- [ ] **Passo 2: estado e conversão em `TurmaListPage`**

Em `frontend/src/pages/TurmaListPage.jsx`, logo depois da constante `SORT_OPTIONS`, acrescentar:

```jsx
// Campo vazio é "não informado", que o backend guarda como nulo.
const paraAlunos = (valor) => (valor === '' ? null : Number(valor))
```

Logo depois de `const [codigo, setCodigo] = useState('')`, acrescentar `const [alunosPrevistos, setAlunosPrevistos] = useState('')`. Logo depois de `const [editCodigo, setEditCodigo] = useState('')`, acrescentar `const [editAlunos, setEditAlunos] = useState('')`.

Trocar `openEdit` por:

```jsx
  const openEdit = (t) => {
    setEditTurma(t)
    setEditNome(t.nome)
    setEditCodigo(t.codigo)
    setEditAlunos(t.alunos_previstos ?? '')
  }
```

Em `saveEdit`, trocar o `await updateTurma(...)` e o `setTurmas(...)` por:

```jsx
      await updateTurma(editTurma.id, editNome.trim(), editCodigo.trim(), paraAlunos(editAlunos))
      setTurmas(prev => prev.map(t => t.id === editTurma.id
        ? { ...t, nome: editNome.trim(), codigo: editCodigo.trim(), alunos_previstos: paraAlunos(editAlunos) }
        : t))
```

Em `handleCreate`, trocar `const { data } = await createTurma(nome.trim(), codigo.trim())` por `const { data } = await createTurma(nome.trim(), codigo.trim(), paraAlunos(alunosPrevistos))` e, logo depois de `setCodigo('')`, acrescentar `setAlunosPrevistos('')`.

- [ ] **Passo 3: campos nos formulários**

No formulário de criação, logo depois do `<input>` com `placeholder="Código (ex: CS1-2026-1)"`, acrescentar:

```jsx
            <input
              type="number"
              min={1}
              max={1000}
              value={alunosPrevistos}
              onChange={e => setAlunosPrevistos(e.target.value)}
              placeholder="Alunos na turma (opcional)"
              className="sm:w-56 text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
```

No modal "Editar turma", logo depois do `<input>` com `placeholder="Código"`, acrescentar:

```jsx
          <input
            type="number" min={1} max={1000} value={editAlunos} onChange={e => setEditAlunos(e.target.value)}
            placeholder="Alunos na turma (opcional)"
            className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
```

- [ ] **Passo 4: lint e build**

Rodar: `cd frontend && npm run lint 2>&1 | tail -3`
Esperado: os mesmos 4 erros antigos, nenhum em `TurmaListPage.jsx` nem em `exam.js`.

Rodar: `cd frontend && npm run build 2>&1 | tail -3`
Esperado: build sem erro.

- [ ] **Passo 5: commitar**

```bash
git add frontend/src/api/exam.js frontend/src/pages/TurmaListPage.jsx
git commit -m "feat(frontend): campo de alunos na turma ao criar e editar"
```

---

### Task 10: front, bloco "Funil da turma"

**Arquivos:**
- Criar: `frontend/src/components/FunilDaTurma.jsx`
- Alterar: `frontend/src/pages/TurmaDetailPage.jsx`

**Interfaces:**
- Consome: `getTurmaFunil(id)` da Task 9, a resposta `FunilTurmaResponse` da Task 7, e os componentes `Badge` (cores `red` e `yellow`), `BarList` (`items: [{ label, value, title }]`) e `Spinner`, que já existem.
- Produz: `<FunilDaTurma turmaId={...} recarga={...} />`.

- [ ] **Passo 1: componente**

Criar `frontend/src/components/FunilDaTurma.jsx`. O carregamento só chama `setEstado` dentro do `.then` e do `.catch`, nunca direto no corpo do efeito, para não cair na regra do ESLint que já acusa `QuestionPage.jsx`.

```jsx
import { useEffect, useState } from 'react'
import { getTurmaFunil } from '../api/exam'
import Badge from './Badge'
import BarList from './BarList'
import Spinner from './Spinner'

const pct = (valor) => (valor == null ? 'sem dado' : `${valor}%`)

// A semana chega como a segunda-feira em ISO (AAAA-MM-DD).
const rotuloSemana = (iso) => {
  const [, mes, dia] = iso.split('-')
  return `${dia}/${mes}`
}

const formatarData = (iso) =>
  new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })

function Meta({ atingida, children }) {
  return (
    <span className={`text-xs font-medium ${atingida ? 'text-emerald-600' : 'text-gray-400'}`}>
      {children}
    </span>
  )
}

function EtapaCard({ titulo, valor, detalhe, meta, atingida }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-1">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{titulo}</p>
        <Meta atingida={atingida}>{meta}</Meta>
      </div>
      <p className="text-2xl font-bold text-gray-900">{valor}</p>
      {detalhe && <p className="text-xs text-gray-500">{detalhe}</p>}
    </div>
  )
}

function AlunosEmRisco({ saude }) {
  const alunos = [
    ...saude.vermelho.map(a => ({ ...a, cor: 'red', rotulo: 'Vermelho' })),
    ...saude.amarelo.map(a => ({ ...a, cor: 'yellow', rotulo: 'Amarelo' })),
  ]
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-baseline justify-between gap-2 mb-3">
        <h3 className="text-sm font-semibold text-gray-700">Alunos em risco</h3>
        <Meta atingida={saude.taxa_vermelho != null && saude.taxa_vermelho < saude.meta}>
          {pct(saude.taxa_vermelho)} em vermelho · meta abaixo de {saude.meta}%
        </Meta>
      </div>
      {alunos.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum aluno em risco agora.</p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {alunos.map(a => (
            <li key={a.student_id} className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2 text-sm">
              <Badge color={a.cor}>{a.rotulo}</Badge>
              <span className="flex-1 min-w-0 truncate text-gray-900">{a.nome}</span>
              <span className="text-gray-500">{a.motivo}</span>
              <span className="text-xs text-gray-400">
                {a.ultimo_envio ? `último envio em ${formatarData(a.ultimo_envio)}` : 'nunca enviou'}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function Painel({ funil }) {
  const { north_star: ns, aquisicao, ativacao, retencao, saude, protecao } = funil
  const semana = retencao.ultima_completa
  const media = protecao.media_tentativas_ate_acertar
  return (
    <>
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-1">
          <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Erros corrigidos</p>
          <p className="text-2xl font-bold text-gray-900">{ns.semana_atual}</p>
          <p className="text-xs text-gray-500">nesta semana · {ns.total} desde o início</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5 lg:col-span-2">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Erros corrigidos por semana</h3>
          <BarList
            items={ns.semanas.map(s => ({
              label: rotuloSemana(s.semana),
              value: s.erros_corrigidos,
              title: `Semana de ${rotuloSemana(s.semana)}`,
            }))}
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <EtapaCard
          titulo="Aquisição"
          valor={aquisicao.alunos_previstos
            ? `${aquisicao.matriculados} de ${aquisicao.alunos_previstos}`
            : aquisicao.matriculados}
          detalhe={aquisicao.alunos_previstos
            ? `${pct(aquisicao.taxa_primeira_semana)} entraram na primeira semana`
            : 'Informe quantos alunos a turma tem para ver a taxa de entrada.'}
          meta={`Meta ${aquisicao.meta}%`}
          atingida={aquisicao.taxa_primeira_semana != null && aquisicao.taxa_primeira_semana >= aquisicao.meta}
        />
        <EtapaCard
          titulo="Ativação"
          valor={pct(ativacao.taxa)}
          detalhe={`${ativacao.ativados} de ${ativacao.matriculados} corrigiram o primeiro erro na primeira semana. ${ativacao.com_primeiro_envio} já enviaram algo.`}
          meta={`Meta ${ativacao.meta}%`}
          atingida={ativacao.taxa != null && ativacao.taxa >= ativacao.meta}
        />
        <EtapaCard
          titulo="Retenção"
          valor={pct(semana.taxa)}
          detalhe={`${semana.voltaram} de ${semana.base} voltaram na semana de ${rotuloSemana(semana.semana)}. Por conta própria, ${pct(semana.taxa_por_conta_propria)}.`}
          meta={`Meta ${retencao.meta}%`}
          atingida={semana.taxa != null && semana.taxa >= retencao.meta}
        />
      </div>

      <AlunosEmRisco saude={saude} />

      <p className="text-xs text-gray-500">
        {media == null
          ? 'Proteção: ainda não há questão resolvida para medir.'
          : `Proteção: ${media} tentativas até acertar, em média, e ${pct(protecao.acerto_de_primeira)} de acerto de primeira.`}
      </p>
    </>
  )
}

export default function FunilDaTurma({ turmaId, recarga = 0 }) {
  const [estado, setEstado] = useState({ carregando: true, funil: null, erro: false })

  useEffect(() => {
    let ativo = true
    getTurmaFunil(turmaId)
      .then(({ data }) => { if (ativo) setEstado({ carregando: false, funil: data, erro: false }) })
      .catch(() => { if (ativo) setEstado({ carregando: false, funil: null, erro: true }) })
    return () => { ativo = false }
  }, [turmaId, recarga])

  return (
    <section className="space-y-4">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Funil da turma</h2>
      {estado.carregando ? (
        <div className="flex justify-center py-8"><Spinner className="w-5 h-5 text-purple-600" /></div>
      ) : estado.erro ? (
        <p className="text-sm text-red-600">Não foi possível carregar o funil.</p>
      ) : estado.funil.aquisicao.matriculados === 0 ? (
        <p className="text-sm text-gray-500">O funil aparece quando os alunos entrarem pelo código da turma.</p>
      ) : (
        <Painel funil={estado.funil} />
      )}
    </section>
  )
}
```

- [ ] **Passo 2: página da turma**

Em `frontend/src/pages/TurmaDetailPage.jsx`:
- Logo depois de `import TrajetoriaDeErros from '../components/TrajetoriaDeErros'`, acrescentar `import FunilDaTurma from '../components/FunilDaTurma'`.
- Logo depois de `const [copiado, setCopiado] = useState(false)`, acrescentar `const [recargaFunil, setRecargaFunil] = useState(0)`.
- Em `confirmDeleteExam`, logo depois da linha `getTurmaAnalytics(turmaId).then(({ data: a }) => setAnalytics(a)).catch(() => {})`, acrescentar `setRecargaFunil(n => n + 1)`.
- Logo depois do bloco `{/* KPIs */}` (o `{analytics && (<div className="grid grid-cols-2 sm:grid-cols-4 gap-4">...</div>)}`) e antes do comentário `{/* Charts`, acrescentar:

```jsx
      <FunilDaTurma turmaId={turmaId} recarga={recargaFunil} />
```

- [ ] **Passo 3: lint e build**

Rodar: `cd frontend && npm run lint 2>&1 | tail -3`
Esperado: os mesmos 4 erros antigos, nenhum em `FunilDaTurma.jsx` nem em `TurmaDetailPage.jsx`.

Rodar: `cd frontend && npm run build 2>&1 | tail -3`
Esperado: build sem erro.

- [ ] **Passo 4: commitar**

```bash
git add frontend/src/components/FunilDaTurma.jsx frontend/src/pages/TurmaDetailPage.jsx
git commit -m "feat(frontend): bloco do funil na pagina da turma"
```

A conferência no navegador (bloco com dados, turma vazia, campo novo na criação e na edição) é o smoke do `fechamento`, depois do `alembic upgrade head` com aviso.
