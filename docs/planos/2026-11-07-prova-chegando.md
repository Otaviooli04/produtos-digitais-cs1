# Prova chegando: plano de implementação

> **Para quem executa:** usar a skill `sdd` (recomendado) ou a execução sem subagentes descrita nela. Passos com caixa de seleção (`- [ ]`).

**Objetivo:** nos três dias antes de uma prova abrir, o Início do aluno oferece um cartão com até 3 erros dele para treinar, e a volta guarda os dados do experimento 5.

**Arquitetura:** regra em funções puras num módulo novo, `app/services/prova_chegando.py`. O `painel` do `inicio_service` monta o cartão a partir do histórico que ele já lê, sem tabela nem migração. O front ganha um componente na `InicioPage`, e Treinar reaproveita `POST /aluno/treino/gerar`.

**Stack:** FastAPI, SQLAlchemy, pytest, React, Tailwind.

**Spec:** `docs/specs/2026-11-07-prova-chegando.md`

## Restrições globais

- Sem migração, tabela ou coluna nova.
- Janela: `abre_em - 3 dias <= agora < abre_em`, com `ANTECEDENCIA_DA_PROVA` de `app/services/funil_regras.py`.
- Só atividade com `modo == "prova"`, `situacao == "agendada"` e `com_o_que_fazer`. Sem `abre_em`, nunca.
- No máximo 3 erros no cartão: `MAXIMO_DE_ERROS = 3`.
- Acerto que marca feito: `origem == TRILHA`, `resultado == ACERTO`, `categoria != alvo`, `momento >= abre_em - 3 dias`.
- Valor da via: `prova_chegando`.
- Texto do cartão: `Um treino curto com o que mais trava você. Nada aqui vale nota.`
- A pré-geração do cartão não cria novidade: `registrar_novidade=False`.
- Nenhum teste pode chamar o Gemini nem abrir `SessionLocal` em thread: nos testes do painel, `preparar_proximo` é sempre simulado.
- RN01, RN04, RN06 e RN09: sem sorteio, sem push, individual, sem cobrança a quem não tem erro.
- Textos em PT-BR, sem ponto e vírgula na prosa, comentário só onde o porquê não é óbvio, commit sem `Co-Authored-By`.
- Dentro do worktree: `/usr/bin/git`, um comando por chamada, a partir da raiz do worktree. Os testes rodam de `backend/`, com o Python em `/home/otavio/produtos-digitais-cs1/backend/venv/bin/python`.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| Criar `backend/app/services/prova_chegando.py` | Regras puras: qual prova, quais erros, o dicionário do cartão e o primeiro pendente |
| Criar `backend/tests/test_prova_chegando.py` | Testes das regras puras |
| Alterar `backend/app/services/treino_service.py` | `preparar_proximo` ganha `registrar_novidade` |
| Alterar `backend/tests/test_treino.py` | Testes do parâmetro novo |
| Alterar `backend/app/services/acesso_service.py` | Via `prova_chegando` aceita |
| Alterar `backend/tests/test_acesso.py` e `backend/tests/test_funil.py` | Testes da via e do "sem aviso" |
| Alterar `backend/app/services/inicio_service.py` | O `painel` monta o cartão, tira a prova dos prazos e prepara o exercício |
| Alterar `backend/app/models/schemas.py` | `ProvaChegandoItem` e o campo em `InicioResponse` |
| Alterar `backend/tests/test_inicio.py` | Testes do painel e da rota |
| Alterar `frontend/src/pages/aluno/InicioPage.jsx` | Componente `ProvaChegando` |

## Lotes

- Lote A, Tasks 1 a 4: regras puras, preparo sem novidade e via (backend, sem rota)
- Lote B, Task 5: painel, esquema e rota (backend)
- Lote C, Task 6: cartão na tela (frontend)

## Varredura

### Pares que dividem arquivo ou interface

| Par | O que uma produz x o que a outra consome | Situação |
|---|---|---|
| T1 → T2 | T1 cria o módulo e `MAXIMO_DE_ERROS`, T2 acrescenta funções no mesmo arquivo com imports já no topo | bate |
| T1 → T5 | `prova_na_janela(atividades, agora)` usada pelo painel | bate |
| T2 → T5 | `montar_cartao(atividade, erros, envios)` e `primeiro_pendente(cartao)` usadas pelo painel | bate |
| T3 → T5 | `preparar_proximo(student_id, categoria, registrar_novidade=True)` chamada com `False`. O simulado da T5 aceita o mesmo parâmetro | bate |
| T4 → T6 | a via `prova_chegando` aceita pelo backend é a que a T6 põe na URL | bate |
| T5 → T6 | campos `exam_id`, `titulo`, `abre_em` e `erros[].error_category`, `erros[].feito` lidos pela tela | bate |
| T3 x `pre_geracoes` em `test_treino.py` | o simulado de lá recebe `(student_id, categoria)`, e os chamadores de lá continuam sem o parâmetro novo | sem conflito |
| T1 x `inicio_service` | `prova_chegando` só importa `AtividadeDoPainel` sob `TYPE_CHECKING`, porque o `inicio_service` importa `prova_chegando` | sem ciclo |

### O teste de cada tarefa bate com o código dela?

| Tarefa | Conferência | Situação |
|---|---|---|
| T1 | 10 testes. `a.abre_em - 3 dias <= agora < a.abre_em` dá entra em `+3d` e `+1s`, fora em `+3d1s` e em `abre_em == AGORA`. 566 + 10 = 576 | bate |
| T2 | 13 testes, 9 de `erros_do_treino`, 2 de `montar_cartao` e 2 de `primeiro_pendente`. As ordens esperadas saem de `erros_do_aluno` (total decrescente, depois nome). 576 + 13 = 589 | bate |
| T3 | 2 testes com `gemini_ok` e `sem_thread`, os dois simulam Gemini e Docker também na fase vermelha. 589 + 2 = 591 | bate |
| T4 | 1 caso novo na parametrização, 1 teste de acesso e 1 do funil. O do funil já passa na fase vermelha, porque só fixa o comportamento atual (`a.via is None`), e isso está dito no passo. 591 + 3 = 594 | bate |
| T5 | 9 testes novos, com `preparos` simulando `preparar_proximo`, e o teste do aluno sem turma atualizado. Janela do `AGORA`: `abre_em = AGORA + 2d` começa em `AGORA - 1d`, e `_errou` e o acerto caem nela. 594 + 9 = 603 | bate |
| T6 | Sem suíte de front. Lint e build na tarefa, e a tela no smoke do `fechamento` | bate |

Âncoras conferidas no arquivo de hoje: `VIAS_ACEITAS = {"convite"}`, `def preparar_proximo(student_id: int, categoria: str) -> None:`, `registrar_exercicio(exercicio, db)` (uma só em `preparar_proximo`), `class InicioResponse(BaseModel):`, `def test_matriculas_por_origem(self, db, professor):`, `("whatsapp", None),`.

---

### Task 1: qual prova entra no cartão

**Arquivos:**
- Criar: `backend/app/services/prova_chegando.py`
- Teste: `backend/tests/test_prova_chegando.py`

**Interfaces:**
- Consome: `AtividadeDoPainel` de `app.services.inicio_service` (`exam_id`, `titulo`, `turma_nome`, `modo`, `situacao`, `abre_em`, `fecha_em`, `criada_em`, `com_o_que_fazer`).
- Produz: `prova_na_janela(atividades: list[AtividadeDoPainel], agora: datetime) -> AtividadeDoPainel | None` e `MAXIMO_DE_ERROS = 3`.

- [ ] **Passo 1: escrever o teste que falha**

Criar `backend/tests/test_prova_chegando.py`:

```python
"""Prova chegando (experimento 5): qual prova entra no cartão e quais erros ele mostra."""
from datetime import datetime, timedelta

from app.services.inicio_service import AtividadeDoPainel
from app.services.prova_chegando import prova_na_janela

AGORA = datetime(2026, 11, 4, 12, 0)


def _atividade(exam_id=1, abre_em=AGORA + timedelta(days=2), modo="prova", situacao="agendada",
               com_o_que_fazer=True):
    return AtividadeDoPainel(
        exam_id=exam_id, titulo=f"Prova {exam_id}", turma_nome="Turma A", modo=modo,
        situacao=situacao, abre_em=abre_em, fecha_em=None, criada_em=AGORA,
        com_o_que_fazer=com_o_que_fazer)


class TestProvaNaJanela:
    def test_exatamente_3_dias_antes_entra(self):
        prova = _atividade(abre_em=AGORA + timedelta(days=3))
        assert prova_na_janela([prova], AGORA) is prova

    def test_um_segundo_antes_de_a_janela_comecar_nao_entra(self):
        prova = _atividade(abre_em=AGORA + timedelta(days=3, seconds=1))
        assert prova_na_janela([prova], AGORA) is None

    def test_um_segundo_antes_de_abrir_entra(self):
        prova = _atividade(abre_em=AGORA + timedelta(seconds=1))
        assert prova_na_janela([prova], AGORA) is prova

    def test_no_instante_de_abrir_nao_entra(self):
        assert prova_na_janela([_atividade(abre_em=AGORA, situacao="aberta")], AGORA) is None

    def test_sem_abre_em_nao_entra(self):
        assert prova_na_janela([_atividade(abre_em=None, situacao="aberta")], AGORA) is None

    def test_lista_nao_entra(self):
        assert prova_na_janela([_atividade(modo="treino")], AGORA) is None

    def test_sem_o_que_fazer_nao_entra(self):
        assert prova_na_janela([_atividade(com_o_que_fazer=False)], AGORA) is None

    def test_encerrada_nao_entra(self):
        assert prova_na_janela([_atividade(situacao="encerrada")], AGORA) is None

    def test_duas_na_janela_vale_a_que_abre_primeiro(self):
        depois = _atividade(exam_id=1, abre_em=AGORA + timedelta(days=2))
        antes = _atividade(exam_id=2, abre_em=AGORA + timedelta(days=1))
        assert prova_na_janela([depois, antes], AGORA) is antes

    def test_empate_vale_o_menor_id(self):
        maior = _atividade(exam_id=9)
        menor = _atividade(exam_id=3)
        assert prova_na_janela([maior, menor], AGORA) is menor
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_prova_chegando.py -q`
Esperado: FALHA com `ModuleNotFoundError: No module named 'app.services.prova_chegando'`

- [ ] **Passo 3: escrever o mínimo para passar**

Criar `backend/app/services/prova_chegando.py`:

```python
"""Prova chegando (experimento 5): o treino curto que o Início oferece nos três
dias antes de uma prova abrir. Funções puras sobre registros simples, testadas
sem banco. O cartão é calculado na hora, sem tabela própria."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.models.orm import Exam
from app.services.funil_regras import ANTECEDENCIA_DA_PROVA

if TYPE_CHECKING:
    from app.services.inicio_service import AtividadeDoPainel

MAXIMO_DE_ERROS = 3


def prova_na_janela(atividades: list[AtividadeDoPainel], agora: datetime) -> AtividadeDoPainel | None:
    """A prova agendada que abre nos próximos 3 dias e ainda tem o que fazer. Com
    mais de uma, a que abre primeiro, e no empate a de menor id."""
    na_janela = [
        a for a in atividades
        if a.modo == Exam.MODO_PROVA and a.situacao == "agendada" and a.com_o_que_fazer
        and a.abre_em and a.abre_em - ANTECEDENCIA_DA_PROVA <= agora < a.abre_em
    ]
    return min(na_janela, key=lambda a: (a.abre_em, a.exam_id), default=None)
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do Passo 2
Esperado: 10 passam

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/prova_chegando.py backend/tests/test_prova_chegando.py
/usr/bin/git commit -m "feat(prova-chegando): qual prova entra no cartao"
```

---

### Task 2: quais erros o cartão mostra

**Arquivos:**
- Alterar: `backend/app/services/prova_chegando.py`
- Teste: `backend/tests/test_prova_chegando.py`

**Interfaces:**
- Consome: `Envio`, `Erro`, `ACERTO`, `TRILHA` e `erros_do_aluno` de `app.services.historico_do_aluno`. `ler_historico` devolve os envios em ordem de tempo.
- Produz: `erros_do_treino(erros: list[Erro], envios: list[Envio], inicio_da_janela: datetime) -> list[dict]`, com itens `{"error_category": str, "feito": bool}`. `montar_cartao(atividade, erros, envios) -> dict | None`, com as chaves `exam_id`, `titulo`, `turma_nome`, `abre_em`, `erros`. `primeiro_pendente(cartao: dict) -> str | None`.

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/test_prova_chegando.py`, trocar o bloco de imports por:

```python
from datetime import datetime, timedelta

from app.services.historico_do_aluno import ACERTO, ERRO, LISTA, TRILHA, Envio, erros_do_aluno
from app.services.inicio_service import AtividadeDoPainel
from app.services.prova_chegando import (
    erros_do_treino, montar_cartao, primeiro_pendente, prova_na_janela,
)
```

E acrescentar no fim do arquivo:

```python
INICIO = AGORA - timedelta(days=1)


def _errou(categoria, minuto):
    return Envio(origem=LISTA, item_id=1, momento=INICIO + timedelta(minutes=minuto),
                 categoria=categoria, resultado=ERRO, o_que_fazer="Revise.")


def _acertou(alvo, minuto, categoria="Correto"):
    return Envio(origem=TRILHA, item_id=9, momento=INICIO + timedelta(minutes=minuto),
                 categoria=categoria, resultado=ACERTO, alvo=alvo)


def _lista(envios):
    return erros_do_treino(erros_do_aluno(envios), envios, INICIO)


class TestErrosDoTreino:
    def test_so_ativos_por_frequencia_cortados_em_3(self):
        envios = [_errou("A", -40), _errou("A", -39), _errou("A", -38),
                  _errou("B", -37), _errou("B", -36), _errou("C", -35), _errou("D", -34)]
        assert _lista(envios) == [
            {"error_category": "A", "feito": False},
            {"error_category": "B", "feito": False},
            {"error_category": "C", "feito": False},
        ]

    def test_acerto_na_janela_vira_feito_e_vem_primeiro(self):
        envios = [_errou("A", -40), _errou("A", -39), _errou("A", -38), _errou("B", -37),
                  _acertou("B", 5)]
        assert _lista(envios) == [
            {"error_category": "B", "feito": True},
            {"error_category": "A", "feito": False},
        ]

    def test_acerto_antes_da_janela_nao_conta(self):
        envios = [_errou("A", -300), _acertou("A", -200), _errou("B", -100)]
        assert _lista(envios) == [{"error_category": "B", "feito": False}]

    def test_acerto_com_a_categoria_do_alvo_nao_conta(self):
        envios = [_errou("A", -40), _acertou("A", 5, categoria="A")]
        assert _lista(envios) == [{"error_category": "A", "feito": False}]

    def test_erro_feito_que_reaparece_continua_feito(self):
        envios = [_errou("A", -40), _acertou("A", 5), _errou("A", 6)]
        assert _lista(envios) == [{"error_category": "A", "feito": True}]

    def test_sem_erros_a_lista_fica_vazia(self):
        assert _lista([]) == []

    def test_acerto_para_outra_categoria_nao_marca_esta(self):
        envios = [_errou("A", -40), _errou("B", -39), _acertou("B", 5)]
        assert _lista(envios) == [
            {"error_category": "B", "feito": True},
            {"error_category": "A", "feito": False},
        ]

    def test_acerto_de_alvo_que_o_aluno_nunca_errou_nao_entra(self):
        envios = [_errou("A", -40), _acertou("Z", 5)]
        assert _lista(envios) == [{"error_category": "A", "feito": False}]

    def test_superado_antes_da_janela_entra_se_treinar_de_novo(self):
        envios = [_errou("A", -300), _acertou("A", -200), _acertou("A", 5)]
        assert _lista(envios) == [{"error_category": "A", "feito": True}]


class TestCartao:
    def test_monta_o_cartao(self):
        prova = _atividade(exam_id=7, abre_em=AGORA + timedelta(days=2))
        envios = [_errou("A", -40)]
        assert montar_cartao(prova, erros_do_aluno(envios), envios) == {
            "exam_id": 7, "titulo": "Prova 7", "turma_nome": "Turma A",
            "abre_em": (AGORA + timedelta(days=2)).isoformat(),
            "erros": [{"error_category": "A", "feito": False}],
        }

    def test_sem_erro_para_mostrar_nao_ha_cartao(self):
        assert montar_cartao(_atividade(), [], []) is None

    def test_primeiro_pendente_pula_os_feitos(self):
        cartao = {"erros": [{"error_category": "B", "feito": True},
                            {"error_category": "A", "feito": False}]}
        assert primeiro_pendente(cartao) == "A"

    def test_sem_pendente_devolve_vazio(self):
        assert primeiro_pendente({"erros": [{"error_category": "B", "feito": True}]}) is None
```

Conferência das contas: em `test_monta_o_cartao`, `abre_em = AGORA + 2d`, então o início da janela é `AGORA - 1d`, igual a `INICIO`. Em `test_acerto_antes_da_janela_nao_conta`, o acerto de "A" a -200 min vem depois do erro a -300, então "A" está superado e sem acerto na janela, e por isso sai.

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_prova_chegando.py -q`
Esperado: FALHA com `ImportError` em `erros_do_treino`

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/prova_chegando.py`, trocar `from app.services.funil_regras import ANTECEDENCIA_DA_PROVA` por:

```python
from app.services.funil_regras import ANTECEDENCIA_DA_PROVA
from app.services.historico_do_aluno import ACERTO, TRILHA, Envio, Erro
```

E acrescentar no fim do arquivo:

```python
def erros_do_treino(erros: list[Erro], envios: list[Envio], inicio_da_janela: datetime) -> list[dict]:
    """Os feitos primeiro, em ordem do acerto, depois os ativos na ordem de
    `erros_do_aluno`, até o máximo. Um erro feito não volta atrás dentro da
    janela. O acerto com a própria categoria do alvo não conta, como em
    `erros_do_aluno`: violação de estrutura e aviso saem antes dos testes, então
    o exercício passa com o erro ainda ali."""
    conhecidos = {erro.categoria for erro in erros}
    feitos: list[str] = []
    for envio in envios:
        if (envio.origem == TRILHA and envio.resultado == ACERTO
                and envio.categoria != envio.alvo and envio.momento >= inicio_da_janela
                and envio.alvo in conhecidos and envio.alvo not in feitos):
            feitos.append(envio.alvo)
    pendentes = [erro.categoria for erro in erros if erro.ativo and erro.categoria not in feitos]
    itens = ([{"error_category": c, "feito": True} for c in feitos]
             + [{"error_category": c, "feito": False} for c in pendentes])
    return itens[:MAXIMO_DE_ERROS]


def montar_cartao(atividade: AtividadeDoPainel, erros: list[Erro], envios: list[Envio]) -> dict | None:
    """O cartão da prova, ou nada quando o aluno não tem erro para treinar."""
    itens = erros_do_treino(erros, envios, atividade.abre_em - ANTECEDENCIA_DA_PROVA)
    if not itens:
        return None
    return {
        "exam_id": atividade.exam_id,
        "titulo": atividade.titulo,
        "turma_nome": atividade.turma_nome,
        "abre_em": atividade.abre_em.isoformat(),
        "erros": itens,
    }


def primeiro_pendente(cartao: dict) -> str | None:
    """A categoria do primeiro erro da lista que ainda não está feito."""
    return next((e["error_category"] for e in cartao["erros"] if not e["feito"]), None)
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do Passo 2
Esperado: 23 passam

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/prova_chegando.py backend/tests/test_prova_chegando.py
/usr/bin/git commit -m "feat(prova-chegando): erros do treino curto e dicionario do cartao"
```

---

### Task 3: preparar o exercício sem criar novidade

**Arquivos:**
- Alterar: `backend/app/services/treino_service.py`
- Teste: `backend/tests/test_treino.py`

**Interfaces:**
- Produz: `preparar_proximo(student_id: int, categoria: str, registrar_novidade: bool = True) -> None`. Sem o parâmetro, o comportamento continua igual.

- [ ] **Passo 1: escrever o teste que falha**

Acrescentar no fim de `backend/tests/test_treino.py`:

```python
class TestPreparoSemNovidade:
    """O cartão da prova chegando prepara o exercício sem acender a bolinha."""

    def test_sem_novidade_gera_mas_nao_registra(
        self, db, aluno, erros_do_aluno, gemini_ok, sem_thread
    ):
        from app.models.orm import Novidade
        from app.services.novidades_service import contar
        from app.services.treino_service import preparar_proximo

        preparar_proximo(aluno.id, "Tudo no Main", registrar_novidade=False)
        db.expire_all()
        assert db.query(ExercicioGerado).filter_by(
            student_id=aluno.id, error_category="Tudo no Main").count() == 1
        assert db.query(Novidade).filter_by(student_id=aluno.id).count() == 0
        assert contar(aluno, db) == 0

    def test_por_padrao_continua_registrando(
        self, db, aluno, erros_do_aluno, gemini_ok, sem_thread
    ):
        from app.models.orm import Novidade
        from app.services.treino_service import preparar_proximo

        preparar_proximo(aluno.id, "Tudo no Main")
        db.expire_all()
        assert db.query(Novidade).filter_by(student_id=aluno.id).count() == 1
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_treino.py::TestPreparoSemNovidade -q`
Esperado: `test_sem_novidade_gera_mas_nao_registra` FALHA com `TypeError` em `registrar_novidade`, e `test_por_padrao_continua_registrando` PASSA, porque só fixa o comportamento atual.

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/treino_service.py`, trocar:

```python
def preparar_proximo(student_id: int, categoria: str) -> None:
    """Deixa o próximo exercício da categoria pronto antes de o aluno pedir.

    É isto que tira a geração do caminho dele: com um exercício esperando, abrir
    a trilha custa uma consulta ao banco em vez dos nove segundos do Gemini mais
    os dois do Docker. Não faz nada quando já existe um pendente, quando o teto
    do dia acabou ou quando já há geração em voo para a mesma chave."""
```

por:

```python
def preparar_proximo(student_id: int, categoria: str, registrar_novidade: bool = True) -> None:
    """Deixa o próximo exercício da categoria pronto antes de o aluno pedir.

    É isto que tira a geração do caminho dele: com um exercício esperando, abrir
    a trilha custa uma consulta ao banco em vez dos nove segundos do Gemini mais
    os dois do Docker. Não faz nada quando já existe um pendente, quando o teto
    do dia acabou ou quando já há geração em voo para a mesma chave.

    `registrar_novidade=False` é do cartão da prova chegando: ali o aluno já está
    vendo o treino, e a novidade acenderia a bolinha só por abrir o Início."""
```

E trocar:

```python
            exercicio = _gerar_e_salvar(student, categoria, diagnostico, db)
            registrar_exercicio(exercicio, db)
```

por:

```python
            exercicio = _gerar_e_salvar(student, categoria, diagnostico, db)
            if registrar_novidade:
                registrar_exercicio(exercicio, db)
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_treino.py -q`
Esperado: todos passam

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/treino_service.py backend/tests/test_treino.py
/usr/bin/git commit -m "feat(treino): preparar exercicio sem registrar novidade"
```

---

### Task 4: via do cartão

**Arquivos:**
- Alterar: `backend/app/services/acesso_service.py`
- Teste: `backend/tests/test_acesso.py` e `backend/tests/test_funil.py`

**Interfaces:**
- Produz: `prova_chegando` em `VIAS_ACEITAS`, que a Task 6 usa em `?via=prova_chegando`.

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/test_acesso.py`, trocar:

```python
        ("whatsapp", None),
    ])
```

por:

```python
        ("whatsapp", None),
        ("prova_chegando", "prova_chegando"),
    ])
```

E, logo depois de `test_convite_logo_depois_de_abrir_grava_e_o_segundo_nao`, acrescentar:

```python
    def test_cartao_da_prova_logo_depois_de_abrir_grava(self, db, aluno):
        registrar_acesso(aluno.id, None, db, agora=AGORA)
        assert registrar_acesso(aluno.id, "prova_chegando", db,
                                agora=AGORA + timedelta(minutes=5)) is True
        assert _vias(db, aluno) == [None, "prova_chegando"]
```

Em `backend/tests/test_funil.py`, logo antes de `def test_matriculas_por_origem(self, db, professor):`, acrescentar:

```python
    def test_via_do_cartao_nao_apaga_o_sem_aviso(self, db, professor):
        turma = _turma(db, professor)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma])
        _acesso(db, ana, datetime(2026, 10, 14, 10))
        _acesso(db, ana, datetime(2026, 10, 21, 10))
        _acesso(db, ana, datetime(2026, 10, 21, 10, 5), via="prova_chegando")

        ultima = funil_da_turma(turma, db, agora=AGORA)["retencao"]["ultima_completa"]

        assert ultima["voltaram"] == 1
        assert ultima["sem_aviso"] == 1

```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_acesso.py tests/test_funil.py -q -k "prova_chegando or cartao"`
Esperado: os dois de `test_acesso.py` FALHAM, porque a via vira `None`. O de `test_funil.py` PASSA, porque só fixa o comportamento atual (`a.via is None`).

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/acesso_service.py`, trocar:

```python
# Os tipos de aviso chegam nas fases 3 e 4.
VIAS_ACEITAS = {"convite"}
```

por:

```python
# Os tipos de aviso chegam na fase 4.
VIAS_ACEITAS = {"convite", "prova_chegando"}
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_acesso.py tests/test_funil.py -q`
Esperado: todos passam

- [ ] **Passo 5: commitar e conferir o lote**

```bash
/usr/bin/git add backend/app/services/acesso_service.py backend/tests/test_acesso.py backend/tests/test_funil.py
/usr/bin/git commit -m "feat(acesso): via do cartao da prova chegando"
```

Rodar a suíte inteira: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q 2>&1 | tail -2`
Esperado: 594 passam

---

### Task 5: cartão no painel e na rota

**Arquivos:**
- Alterar: `backend/app/services/inicio_service.py`
- Alterar: `backend/app/models/schemas.py`
- Teste: `backend/tests/test_inicio.py`

**Interfaces:**
- Consome: `prova_na_janela`, `montar_cartao` e `primeiro_pendente` (Tasks 1 e 2), `preparar_proximo(..., registrar_novidade=False)` (Task 3) e `erros_do_aluno` de `historico_do_aluno`.
- Produz: `painel(...)["prova_chegando"]`, `dict | None`, e `GET /aluno/inicio` com `prova_chegando`: `exam_id`, `titulo`, `turma_nome`, `abre_em`, `erros[{error_category, feito}]`.

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/test_inicio.py`, trocar:

```python
from app.auth.student_service import create_student_token
from app.models.orm import (
    Enrollment, Exam, ExercicioGerado, Novidade, Question, QuestionCluster, Student, Submission,
)
```

por:

```python
from app.auth.student_service import create_student_token
from app.core.tempo import agora_utc
from app.models.orm import (
    Enrollment, Exam, ExercicioGerado, Novidade, Question, QuestionCluster, Student, Submission,
    TentativaDeTreino,
)
```

Trocar:

```python
        assert painel(sozinho, db, agora=AGORA) == {
            "tem_turma": False, "novidades": [], "continuar": None, "prazos": []}
```

por:

```python
        assert painel(sozinho, db, agora=AGORA) == {
            "tem_turma": False, "novidades": [], "prova_chegando": None, "continuar": None,
            "prazos": []}
```

E acrescentar no fim do arquivo:

```python
@pytest.fixture()
def preparos(monkeypatch):
    """Anota os preparos pedidos pelo painel. Sem isto, o painel abriria uma
    thread com a sessão real e chamaria o Gemini."""
    pedidos = []
    monkeypatch.setattr(
        "app.services.inicio_service.preparar_proximo",
        lambda student_id, categoria, registrar_novidade=True: pedidos.append(
            (student_id, categoria, registrar_novidade)),
    )
    return pedidos


def _prova_agendada(db, exam_factory, turma_id, titulo="Prova 1", abre_em=AGORA + timedelta(days=2)):
    exam = exam_factory(questions=[{"number": "1"}], titulo=titulo)
    exam.turma_id = turma_id
    exam.abre_em = abre_em
    db.commit()
    db.refresh(exam)
    return exam


def _acertou_na_trilha(db, aluno, categoria, quando=AGORA - timedelta(minutes=30)):
    exercicio = ExercicioGerado(student_id=aluno.id, error_category=categoria, titulo="Soma",
                                enunciado="Some os pares.")
    db.add(exercicio)
    db.flush()
    db.add(TentativaDeTreino(
        exercicio_id=exercicio.id, student_id=aluno.id, code="int main(){}",
        all_tests_passed=True, error_category="Correto", attempt_number=1, submitted_at=quando))
    db.commit()


class TestProvaChegando:
    def test_cartao_vem_e_a_prova_sai_dos_prazos(self, db, aluno, prova, exam_factory, preparos):
        _errou(db, prova, aluno)
        agendada = _prova_agendada(db, exam_factory, prova.turma_id)
        resultado = painel(aluno, db, agora=AGORA)
        assert resultado["prova_chegando"] == {
            "exam_id": agendada.id, "titulo": "Prova 1", "turma_nome": "Turma Teste",
            "abre_em": (AGORA + timedelta(days=2)).isoformat(),
            "erros": [{"error_category": "Saída Incorreta", "feito": False}],
        }
        assert [p["exam_id"] for p in resultado["prazos"]] == [prova.id]

    def test_segunda_prova_da_janela_fica_nos_prazos(self, db, aluno, prova, exam_factory, preparos):
        _errou(db, prova, aluno)
        primeira = _prova_agendada(db, exam_factory, prova.turma_id,
                                   abre_em=AGORA + timedelta(days=1))
        segunda = _prova_agendada(db, exam_factory, prova.turma_id, titulo="Prova 2")
        resultado = painel(aluno, db, agora=AGORA)
        assert resultado["prova_chegando"]["exam_id"] == primeira.id
        assert {p["exam_id"] for p in resultado["prazos"]} == {prova.id, segunda.id}

    def test_sem_erro_nao_ha_cartao_e_a_prova_fica_nos_prazos(
        self, db, aluno, prova, exam_factory, preparos
    ):
        agendada = _prova_agendada(db, exam_factory, prova.turma_id)
        resultado = painel(aluno, db, agora=AGORA)
        assert resultado["prova_chegando"] is None
        assert agendada.id in {p["exam_id"] for p in resultado["prazos"]}
        assert preparos == []

    def test_prova_de_outra_turma_nao_aparece(self, db, aluno, prova, exam_factory, preparos):
        _errou(db, prova, aluno)
        outra = exam_factory(questions=[{"number": "1"}], titulo="De outra turma")
        outra.abre_em = AGORA + timedelta(days=2)
        db.commit()
        assert painel(aluno, db, agora=AGORA)["prova_chegando"] is None

    def test_erros_de_outro_aluno_nao_entram(self, db, aluno, prova, exam_factory, preparos):
        colega = _matricular(db, "bia@teste.com", prova.turma_id)
        _errou(db, prova, colega)
        _prova_agendada(db, exam_factory, prova.turma_id)
        assert painel(aluno, db, agora=AGORA)["prova_chegando"] is None
        assert painel(colega, db, agora=AGORA)["prova_chegando"]["erros"] == [
            {"error_category": "Saída Incorreta", "feito": False}]

    def test_prepara_o_primeiro_nao_feito_sem_novidade(
        self, db, aluno, prova, exam_factory, preparos
    ):
        _errou(db, prova, aluno, "1")
        _errou(db, prova, aluno, "2")
        questao = next(q for q in prova.questions if q.number == "1")
        db.add(Submission(question_id=questao.id, code="int main(){}", error_category="Tudo no Main",
                          all_tests_passed=False, student_id=aluno.id, attempt_number=2,
                          submitted_at=AGORA - timedelta(minutes=50)))
        db.commit()
        _acertou_na_trilha(db, aluno, "Saída Incorreta")
        _prova_agendada(db, exam_factory, prova.turma_id)
        erros = painel(aluno, db, agora=AGORA)["prova_chegando"]["erros"]
        assert erros == [{"error_category": "Saída Incorreta", "feito": True},
                         {"error_category": "Tudo no Main", "feito": False}]
        assert preparos == [(aluno.id, "Tudo no Main", False)]

    def test_tudo_feito_nao_prepara(self, db, aluno, prova, exam_factory, preparos):
        _errou(db, prova, aluno)
        _acertou_na_trilha(db, aluno, "Saída Incorreta")
        _prova_agendada(db, exam_factory, prova.turma_id)
        erros = painel(aluno, db, agora=AGORA)["prova_chegando"]["erros"]
        assert erros == [{"error_category": "Saída Incorreta", "feito": True}]
        assert preparos == []

    def test_sem_prova_na_janela_nao_prepara(self, db, aluno, prova, preparos):
        _errou(db, prova, aluno)
        assert painel(aluno, db, agora=AGORA)["prova_chegando"] is None
        assert preparos == []

    def test_rota_devolve_o_cartao(self, client, db, aluno, prova, exam_factory, preparos):
        agora = agora_utc()
        _errou(db, prova, aluno, quando=agora - timedelta(hours=1))
        agendada = _prova_agendada(db, exam_factory, prova.turma_id,
                                   abre_em=agora + timedelta(days=2))
        corpo = client.get("/aluno/inicio",
                           headers=_auth(create_student_token(aluno.id))).json()
        assert corpo["prova_chegando"]["exam_id"] == agendada.id
        assert corpo["prova_chegando"]["erros"] == [
            {"error_category": "Saída Incorreta", "feito": False}]
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_inicio.py -q`
Esperado: os 9 de `TestProvaChegando` dão ERROR ou FALHA, porque `inicio_service` ainda não tem `preparar_proximo`, e `test_aluno_sem_turma` FALHA pela chave nova. Nenhum chama o Gemini, porque o painel antigo não prepara nada.

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/models/schemas.py`, trocar:

```python
class InicioResponse(BaseModel):
    tem_turma: bool
    novidades: List[NovidadeItem] = []
    continuar: Optional[ContinuarItem] = None
```

por:

```python
class ErroDoTreinoCurto(BaseModel):
    error_category: str
    feito: bool


class ProvaChegandoItem(BaseModel):
    exam_id: int
    titulo: str
    turma_nome: str
    abre_em: str
    erros: List[ErroDoTreinoCurto] = []


class InicioResponse(BaseModel):
    tem_turma: bool
    novidades: List[NovidadeItem] = []
    prova_chegando: Optional[ProvaChegandoItem] = None
    continuar: Optional[ContinuarItem] = None
```

Em `backend/app/services/inicio_service.py`, trocar:

```python
"""Início do aluno: o que chegou para ele, onde ele parou e o que vence logo.

Monta o painel e não grava nada. As novidades vêm do `novidades_service`, e o
resto sai do histórico unificado (`ler_historico`), o mesmo do progresso e da
trilha, para os três concordarem sobre o que está resolvido. A regra mora em
funções puras sobre registros simples, testadas sem banco."""
```

por:

```python
"""Início do aluno: o que chegou para ele, onde ele parou e o que vence logo.

Monta o painel e não grava nada na sessão dele. A única escrita que ele dispara
é o exercício da prova chegando, preparado em thread própria. As novidades vêm
do `novidades_service`, e o resto sai do histórico unificado (`ler_historico`),
o mesmo do progresso e da trilha, para os três concordarem sobre o que está
resolvido. A regra mora em funções puras sobre registros simples, testadas sem
banco."""
```

Trocar:

```python
from app.services.historico_do_aluno import ACERTO, FALHA, LISTA, TRILHA, Envio, ler_historico
from app.services.novidades_service import novidades_do_aluno
from app.services.student_activity_service import titulo_da_atividade
```

por:

```python
from app.services.historico_do_aluno import (
    ACERTO, FALHA, LISTA, TRILHA, Envio, erros_do_aluno, ler_historico,
)
from app.services.novidades_service import novidades_do_aluno
from app.services.prova_chegando import montar_cartao, primeiro_pendente, prova_na_janela
from app.services.student_activity_service import titulo_da_atividade
from app.services.treino_service import preparar_proximo
```

Trocar:

```python
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
```

por:

```python
        return {"tem_turma": False, "novidades": [], "prova_chegando": None, "continuar": None,
                "prazos": []}

    envios = ler_historico(student, db)
    atividades, disponiveis = _atividades_e_questoes(student, turma_ids, envios, agora, db)
    disponiveis.update(_exercicios_abertos(student, db))
    prazos = prazos_proximos(atividades, agora)
    cartao = _prova_chegando(student, atividades, envios, agora)
    if cartao:
        prazos = [p for p in prazos if p["exam_id"] != cartao["exam_id"]]
    return {
        "tem_turma": True,
        "novidades": novidades_do_aluno(student, db),
        "prova_chegando": cartao,
        "continuar": escolher_continuar(envios, disponiveis, proxima_atividade(atividades)),
        "prazos": prazos,
    }


def _prova_chegando(student: Student, atividades: list[AtividadeDoPainel], envios: list[Envio],
                    agora: datetime) -> dict | None:
    """O cartão da prova chegando, com o exercício do primeiro erro pendente já a
    caminho, sem novidade, porque o aluno está vendo o treino no próprio cartão."""
    atividade = prova_na_janela(atividades, agora)
    if not atividade:
        return None
    cartao = montar_cartao(atividade, erros_do_aluno(envios), envios)
    if cartao:
        pendente = primeiro_pendente(cartao)
        if pendente:
            preparar_proximo(student.id, pendente, registrar_novidade=False)
    return cartao
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_inicio.py -q`
Esperado: todos passam

Depois a suíte inteira: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q 2>&1 | tail -2`
Esperado: 603 passam

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/inicio_service.py backend/app/models/schemas.py backend/tests/test_inicio.py
/usr/bin/git commit -m "feat(inicio): cartao da prova chegando no painel"
```

---

### Task 6: cartão na tela

**Arquivos:**
- Alterar: `frontend/src/pages/aluno/InicioPage.jsx`

**Interfaces:**
- Consome: `inicio.prova_chegando` da Task 5, `gerarExercicio(categoria)` de `api/aluno.js`, que devolve `{ data: { id } }`, `prazoRelativo` de `utils/datas` e `shortError` de `utils/errorLabels`. `AlunoLayout` já registra `?via=` e tira da URL.

- [ ] **Passo 1: importar o que o cartão usa**

Em `frontend/src/pages/aluno/InicioPage.jsx`, trocar:

```jsx
import { Link } from 'react-router-dom'
import { getInicio } from '../../api/aluno'
```

por:

```jsx
import { Link, useNavigate } from 'react-router-dom'
import { gerarExercicio, getInicio } from '../../api/aluno'
```

- [ ] **Passo 2: escrever o componente**

Logo antes de `function Continuar({ item }) {`, acrescentar:

```jsx
function ProvaChegando({ prova }) {
  const navigate = useNavigate()
  const [gerando, setGerando] = useState(null)
  const [erro, setErro] = useState('')
  const feitos = prova.erros.filter(e => e.feito).length
  const tudoFeito = feitos === prova.erros.length

  const treinar = async (categoria) => {
    setErro('')
    setGerando(categoria)
    try {
      const { data } = await gerarExercicio(categoria)
      navigate(`/aluno/treino/${data.id}?via=prova_chegando`)
    } catch (e) {
      setErro(e.response?.data?.detail || 'Não foi possível abrir o treino agora.')
      setGerando(null)
    }
  }

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
      <div className="min-w-0">
        <h2 className="text-sm font-semibold text-gray-900 break-words">
          {prova.titulo} abre {prazoRelativo(prova.abre_em)}
        </h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Um treino curto com o que mais trava você. Nada aqui vale nota.
        </p>
      </div>

      <ul className="divide-y divide-gray-100">
        {prova.erros.map(e => (
          <li key={e.error_category} className="flex items-center justify-between gap-3 py-2">
            <span className="text-sm text-gray-700 min-w-0 break-words">{shortError(e.error_category)}</span>
            {e.feito ? (
              <span className="text-xs font-medium text-green-700 shrink-0">✓ feito</span>
            ) : (
              <button
                type="button"
                onClick={() => treinar(e.error_category)}
                disabled={gerando !== null}
                className="inline-flex items-center justify-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
              >
                {gerando === e.error_category && <Spinner className="w-4 h-4" />}
                Treinar
              </button>
            )}
          </li>
        ))}
      </ul>

      {gerando && (
        <p className="text-xs text-gray-500">Montando o exercício. Pode levar alguns segundos.</p>
      )}
      {erro && <p className="text-xs text-red-600">{erro}</p>}

      <p className="text-xs text-gray-400">
        {tudoFeito ? 'Treino feito' : `${feitos} de ${prova.erros.length} feitos`}
      </p>
    </section>
  )
}

```

- [ ] **Passo 3: mostrar o cartão na página**

Trocar:

```jsx
  const { novidades, continuar, prazos } = inicio
  const tudoEmDia = novidades.length === 0 && !continuar && prazos.length === 0
```

por:

```jsx
  const { novidades, prova_chegando: provaChegando, continuar, prazos } = inicio
  const tudoEmDia = novidades.length === 0 && !provaChegando && !continuar && prazos.length === 0
```

E trocar:

```jsx
      {novidades.length > 0 && <Novidades itens={novidades} />}
      {continuar && <Continuar item={continuar} />}
```

por:

```jsx
      {novidades.length > 0 && <Novidades itens={novidades} />}
      {provaChegando && <ProvaChegando prova={provaChegando} />}
      {continuar && <Continuar item={continuar} />}
```

- [ ] **Passo 4: lint e build**

Rodar, de `frontend/`: `rtk proxy ./node_modules/.bin/eslint . 2>&1 | tail -3`
Esperado: nenhum erro

Rodar, de `frontend/`: `npm run build 2>&1 | tail -1`
Esperado: `built in`

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add frontend/src/pages/aluno/InicioPage.jsx
/usr/bin/git commit -m "feat(frontend): cartao da prova chegando no inicio"
```
