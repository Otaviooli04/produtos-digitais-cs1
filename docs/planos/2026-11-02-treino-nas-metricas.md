# Treino nas métricas do aluno: plano de implementação

> **Para quem executa:** usar a skill `sdd` (recomendado) ou a execução sem subagentes descrita nela. Passos com caixa de seleção (`- [ ]`).

**Objetivo:** o progresso, os erros recorrentes e a trilha do aluno passam a ler também as tentativas da trilha, com o erro superado fora do topo e a falha técnica fora das contas de erro.

**Arquitetura:** um módulo novo, `app/services/historico_do_aluno.py`, lê os envios das listas e as tentativas da trilha numa lista só (`ler_historico`) e guarda as regras puras sobre ela (erros ativos e superados, tendência, contas do progresso). `student_activity_service` e `treino_service` passam a montar as respostas a partir dele. O front só ganha textos e as seções de superados.

**Stack:** FastAPI, SQLAlchemy, pytest, React 19, Tailwind v4.

**Spec:** `docs/specs/2026-11-02-treino-nas-metricas.md`

## Restrições globais

- Nenhuma migração e nenhuma tabela ou coluna nova.
- Classificação de um envio (a mesma do funil): lista com `error_category == "Correto"` é `acerto`. Trilha com `all_tests_passed` verdadeiro é `acerto`. Categoria vazia, nula ou `"Erro Desconhecido"` (sem acerto) é `falha`. O resto é `erro`.
- Erro superado: depois do último envio de resultado `erro` e categoria X, existe envio da trilha com `alvo == X` e resultado `acerto`. `superado_em` é o momento do primeiro desses acertos. Exercício reportado não conta.
- Envio sem `submitted_at` fica fora do histórico.
- Ativos ordenados por total decrescente e depois pelo nome da categoria. Superados por `superado_em` decrescente.
- Tendência sobre as 10 últimas tentativas válidas (`JANELA_RECENTE = 10`), com os limites 0,8 e 1,2 de hoje.
- No máximo 5 rótulos por erro (`ROTULOS_POR_ERRO = 5`). Rótulo da trilha: `"Trilha · <título do exercício>"`.
- Campos novos nas respostas, todos com valor padrão: `ErroRecorrente.no_treino`, `ErrosRecorrentesResponse.superados`, `TrilhaResponse.superados`, `ProgressoResponse.tentativas_no_treino` e `ProgressoResponse.exercicios_resolvidos`. `ErroSuperado` tem `error_category`, `total` e `superado_em` (ISO).
- Mensagem de `TreinoIndisponivel` sem erro ativo: `"Você superou todos os erros que repetia. Resolva uma questão da sua turma e volte aqui."`
- Textos do aluno exatamente como em Comportamento do spec. Sem aviso novo na hora do acerto (o 2.4 vem antes de qualquer recompensa nova).
- Rotas e papéis não mudam: tudo continua com `get_current_student` e lido pelo `student_id` do aluno logado.
- O módulo `historico_do_aluno.py` só importa `app.models.orm` e `app.services.calendario`, para não criar import circular.
- Dentro do worktree, git pelo caminho completo `/usr/bin/git`, um comando por chamada. O gancho do rtk transforma `git` em `rtk git`, e a trava do worktree recusa.
- Testes: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest <alvo> -q`. Nunca `rtk pytest`. Base: 353 testes passando.

---

## Estrutura de arquivos

| Arquivo | O que muda |
|---|---|
| `backend/app/services/historico_do_aluno.py` (novo) | Classificação do envio, registros `Envio`, `Erro`, `Tendencia` e `Resolucao`, regras puras e a leitura `ler_historico` |
| `backend/app/services/funil_regras.py` | Passa a importar `ACERTO`, `ERRO`, `FALHA` e `LISTA` do módulo novo. Saem as constantes e as duas funções de resultado |
| `backend/app/services/funil_service.py` | Importa `LISTA`, `TRILHA` e as funções de resultado do módulo novo |
| `backend/app/services/student_activity_service.py` | `erros_recorrentes` e `progresso` reescritos sobre o histórico. Saem `JANELA_RECENTE`, `_tendencia`, `_dias_seguidos` e `_evolucao` |
| `backend/app/services/treino_service.py` | `categorias_para_treinar`, `trilha`, `gerar_para_categoria`, `preparar_proximo` e `treinar` sobre o histórico |
| `backend/app/models/schemas.py` | `ErroSuperado` novo e os campos novos |
| `backend/tests/unit/test_historico_do_aluno.py` (novo) | Regras puras com listas montadas à mão |
| `backend/tests/test_leitura_do_historico.py` (novo) | `ler_historico` contra o banco de teste |
| `backend/tests/unit/test_funil_regras.py` | Import novo. `TestResultado` vai para o arquivo novo |
| `backend/tests/test_student_activity.py` | Testes de erros recorrentes e progresso com treino |
| `backend/tests/test_treino.py` | Testes de superados, geração e pré-geração |
| `frontend/src/utils/datas.js` (novo) | `dataCurta(iso)`, a data "28/10" |
| `frontend/src/pages/aluno/ProgressoPage.jsx` | Textos novos e a seção "Erros que você superou" |
| `frontend/src/pages/aluno/TreinoPage.jsx` | Seção dos superados com "Treinar de novo" e a mensagem de tudo superado |

## Lotes

- Lote A, Tasks 1 a 4: o módulo do histórico (classificação, regras dos erros, regras do progresso e leitura)
- Lote B, Tasks 5 a 7: serviços e respostas (erros recorrentes, progresso e trilha)
- Lote C, Tasks 8 e 9: front do progresso e da trilha

## Varredura

### Pares que dividem arquivo ou interface

| Par | O que uma produz x o que a outra consome | Situação |
|---|---|---|
| T1 → T2, T4 | `ACERTO`, `ERRO`, `FALHA`, `LISTA`, `TRILHA`, `resultado_da_lista` e `resultado_da_trilha` usados nas regras e na leitura | bate |
| T1 x T2 x T3 x T4 | as quatro mexem no topo de `historico_do_aluno.py`. Cada uma traz o bloco de imports inteiro do seu estado e acrescenta uma seção no fim | sem conflito, na ordem |
| T2 → T5, T7 | `Erro` (`categoria`, `ativo`, `total`, `no_treino`, `ultima_ocorrencia`, `o_que_fazer`, `superado_em`), `erros_do_aluno`, `superados`, `rotulos`, `tendencias` e `Tendencia` (`recentes`, `anteriores`, `sentido`) | bate |
| T3 → T6 | `Resolucao` (`item`, `momento`, `tentativas`), `resolucoes`, `dias_seguidos(envios, hoje)` e `evolucao(envios, resolvidas)` | bate |
| T4 → T5, T6, T7 | `ler_historico(student, db) -> list[Envio]` já ordenada | bate |
| T1 x T5 x T6 | as três mexem nos imports de `student_activity_service.py`. T1 traz `CATEGORIA_CORRETA`, T5 acrescenta os nomes dos erros e T6 os do progresso e tira `timedelta` e `semana_iso` | sem conflito, na ordem |
| T5 x T6 | as duas reescrevem funções diferentes de `student_activity_service.py` e classes diferentes de `schemas.py` | sem conflito |
| T5 → T6 | helper `_treino(db, aluno_id, alvo, tentativas, ...)` em `tests/test_student_activity.py` | bate |
| T5 → T7 | `ErroSuperado` criado em T5 antes de `ErrosRecorrentesResponse`, usado por `TrilhaResponse` em T7, que vem depois no arquivo | bate |
| T1 x T7 | T1 troca a constante de `treino_service.py` por import, T7 tira o import porque deixa de usar | bate |
| T5, T6, T7 → T8, T9 | campos `superados[].error_category`, `superados[].total`, `superados[].superado_em`, `erros[].no_treino`, `tentativas_no_treino` | bate |
| T8 → T9 | `dataCurta` em `frontend/src/utils/datas.js` | bate |

### O teste de cada tarefa bate com o código dela?

| Tarefa | Conferência | Situação |
|---|---|---|
| T1 | Os 2 testes de `TestResultado` saem de `test_funil_regras.py` e entram iguais no arquivo novo. 353 + 0 = 353 | bate |
| T2 | 14 testes. Contas conferidas à mão: ordem `["C", "A", "B", "E", "D"]` (C tem 3, A e B têm 2 e empatam pelo nome, E superado às 12:10 e D às 12:08), rótulos `[Trilha, Q1, Q6, Q5, Q4]` (o item 99 não tem rótulo e o Q1 repetido sai), tendência de `Laço` melhorando (0 de 10 contra 4 de 4) e de `OFF` piorando (10 de 10 contra 0 de 4), falha fora da janela deixa `Laço` estável com 10 recentes. 353 + 14 = 367 | bate |
| T3 | 8 testes. Tentativas até acertar = 2 (erro, falha ignorada, acerto), falha antes do acerto = 1, semanas 2026-10-12 e 2026-10-26 (28/10/2026 é quarta). 367 + 8 = 375 | bate |
| T4 | 5 testes contra o banco. Ordem lista 0, trilha 10, lista 20, empate lista antes da trilha, reportado fora, sem momento fora, outro aluno fora. 375 + 5 = 380 | bate |
| T5 | 5 testes novos. `Laço` com total 2 e `no_treino` 1, rótulos `["Trilha · Soma dos pares", "prova.pdf · Q1"]` (`exam_factory` cria `prova.pdf` sem título), superado com total 2, falha fora dos totais. Os 3 testes antigos de erros recorrentes continuam valendo (5 válidas e 4 erros no primeiro). 380 + 5 = 385 | bate |
| T6 | 3 testes novos e 2 asserções novas em `test_sem_submissao`. Média (1 + 3) / 2 = 2.0, 4 tentativas, 3 no treino. Os testes antigos continuam (1.5 em `test_contadores`). 385 + 3 = 388 | bate |
| T7 | 7 testes em `TestSuperados`, 2 em `TestRotaDaTrilha`, 1 novo em `TestPreGeracao` e `test_resolver_prepara_o_proximo` reescrito com outro nome (o erro resolvido vira superado, então o próximo é `Tudo no Main`). 388 + 10 = 398 | bate |
| T8 | front sem suíte: lint sem erro novo e build | bate |
| T9 | front sem suíte: lint sem erro novo e build | bate |

---

### Task 1: classificação do envio num módulo do histórico

**Arquivos:**
- Criar: `backend/app/services/historico_do_aluno.py`
- Criar: `backend/tests/unit/test_historico_do_aluno.py`
- Alterar: `backend/app/services/funil_regras.py`, `backend/app/services/funil_service.py`, `backend/tests/unit/test_funil_regras.py`, `backend/app/services/student_activity_service.py`, `backend/app/services/treino_service.py`

**Interfaces:**
- Consome: nada
- Produz: em `app.services.historico_do_aluno`, `CATEGORIA_CORRETA = "Correto"`, `CATEGORIA_FALHA_TECNICA = "Erro Desconhecido"`, `ACERTO = "acerto"`, `ERRO = "erro"`, `FALHA = "falha"`, `LISTA = "lista"`, `TRILHA = "trilha"`, `resultado_da_lista(error_category: str | None) -> str` e `resultado_da_trilha(all_tests_passed: bool | None, error_category: str | None) -> str`

- [ ] **Passo 1: escrever o teste que falha**

Criar `backend/tests/unit/test_historico_do_aluno.py`:

```python
"""Regras do histórico do aluno sobre registros montados à mão, sem banco."""
from app.services.historico_do_aluno import (
    ACERTO, ERRO, FALHA, resultado_da_lista, resultado_da_trilha,
)


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
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_historico_do_aluno.py -q`
Esperado: FALHA com `ModuleNotFoundError: No module named 'app.services.historico_do_aluno'`

- [ ] **Passo 3: criar o módulo e trocar os imports**

Criar `backend/app/services/historico_do_aluno.py`:

```python
"""Histórico do aluno: os envios das listas e as tentativas da trilha numa
lista só, em ordem de tempo.

O progresso, os erros recorrentes e a trilha leem daqui, então os três sempre
concordam sobre o que o aluno errou e o que ele já superou. A classificação de
cada envio também mora aqui, e o funil da turma usa a mesma."""

CATEGORIA_CORRETA = "Correto"
# O que as heurísticas devolvem quando a execução falha por fora do código do
# aluno, como o Docker fora do ar. Não é erro dele.
CATEGORIA_FALHA_TECNICA = "Erro Desconhecido"

ACERTO = "acerto"
ERRO = "erro"
FALHA = "falha"

LISTA = "lista"
TRILHA = "trilha"


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
```

Em `backend/app/services/funil_regras.py`, trocar este trecho do topo:

```python
from app.services.student_activity_service import CATEGORIA_CORRETA

# O que as heurísticas devolvem quando a execução falha por fora do código do
# aluno, como o Docker fora do ar. Não é erro dele.
CATEGORIA_FALHA_TECNICA = "Erro Desconhecido"

ACERTO = "acerto"
ERRO = "erro"
FALHA = "falha"

LISTA = "lista"
TRILHA = "trilha"
```

por:

```python
from app.services.historico_do_aluno import ACERTO, ERRO, FALHA, LISTA
```

E apagar de `funil_regras.py` as duas funções `resultado_da_lista` e `resultado_da_trilha` (o bloco que começa em `def resultado_da_lista(error_category: str | None) -> str:` e termina no `return ERRO` de `resultado_da_trilha`, logo antes de `def taxa(`), com as linhas em branco delas.

Em `backend/app/services/funil_service.py`, trocar:

```python
from app.services.funil_regras import (
    LISTA, TRILHA, Acesso, DadosDaTurma, JanelaDeProva, Matricula, Tentativa,
    alunos_ativados, erros_corrigidos, janela_da_prova, montar_funil, north_star,
    resultado_da_lista, resultado_da_trilha, retencao_da_semana, taxa, ultimas_semanas,
)
```

por:

```python
from app.services.funil_regras import (
    Acesso, DadosDaTurma, JanelaDeProva, Matricula, Tentativa,
    alunos_ativados, erros_corrigidos, janela_da_prova, montar_funil, north_star,
    retencao_da_semana, taxa, ultimas_semanas,
)
from app.services.historico_do_aluno import (
    LISTA, TRILHA, resultado_da_lista, resultado_da_trilha,
)
```

Em `backend/tests/unit/test_funil_regras.py`, trocar:

```python
from app.services.funil_regras import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, Acesso, DadosDaTurma, Matricula, Tentativa,
    aquisicao, ativacao, com_prova_marcada, erros_corrigidos, fim_da_sessao,
    janela_da_prova, montar_funil, north_star, por_origem, protecao, resultado_da_lista,
    resultado_da_trilha, retencao, retencao_da_semana, saude, sucesso, ultimas_semanas,
)
```

por:

```python
from app.services.funil_regras import (
    Acesso, DadosDaTurma, Matricula, Tentativa,
    aquisicao, ativacao, com_prova_marcada, erros_corrigidos, fim_da_sessao,
    janela_da_prova, montar_funil, north_star, por_origem, protecao,
    retencao, retencao_da_semana, saude, sucesso, ultimas_semanas,
)
from app.services.historico_do_aluno import ACERTO, ERRO, FALHA, LISTA, TRILHA
```

E apagar de `test_funil_regras.py` a classe `TestResultado` inteira (de `class TestResultado:` até a linha antes de `class TestSemanas:`), que foi para o arquivo novo.

Em `backend/app/services/student_activity_service.py`, apagar a linha `CATEGORIA_CORRETA = "Correto"` e, logo abaixo de `from app.services.calendario import semana_iso, situacao_da_atividade`, acrescentar:

```python
from app.services.historico_do_aluno import CATEGORIA_CORRETA
```

Em `backend/app/services/treino_service.py`, apagar a linha `CATEGORIA_CORRETA = "Correto"` e a linha em branco que vem depois dela e, logo abaixo de `from app.models.orm import ExercicioGerado, Student, Submission, TentativaDeTreino`, acrescentar:

```python
from app.services.historico_do_aluno import CATEGORIA_CORRETA
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_historico_do_aluno.py tests/unit/test_funil_regras.py tests/test_funil.py tests/test_treino.py tests/test_student_activity.py -q`
Esperado: PASSA

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/historico_do_aluno.py backend/tests/unit/test_historico_do_aluno.py backend/app/services/funil_regras.py backend/app/services/funil_service.py backend/tests/unit/test_funil_regras.py backend/app/services/student_activity_service.py backend/app/services/treino_service.py
/usr/bin/git commit -m "refactor(historico): classificacao do envio num modulo do historico do aluno"
```

### Task 2: erros ativos, superados e tendência

**Arquivos:**
- Alterar: `backend/app/services/historico_do_aluno.py`
- Teste: `backend/tests/unit/test_historico_do_aluno.py`

**Interfaces:**
- Consome: `ACERTO`, `ERRO`, `FALHA`, `TRILHA` de T1
- Produz:
  - `Envio(origem: str, item_id: int, momento: datetime, categoria: str, resultado: str, o_que_fazer: str = "", alvo: str = "", titulo: str = "")`, dataclass congelada, com a propriedade `item -> tuple[str, int]`
  - `Erro(categoria: str, ocorrencias: tuple[Envio, ...], superado_em: datetime | None = None)`, dataclass congelada, com as propriedades `ativo`, `total`, `no_treino`, `ultima_ocorrencia` e `o_que_fazer`
  - `Tendencia(recentes: int, anteriores: int, sentido: str)`, dataclass congelada
  - `erros_do_aluno(envios: list[Envio]) -> list[Erro]`, ativos e depois superados, já ordenados
  - `superados(erros: list[Erro]) -> list[dict]` com `error_category`, `total` e `superado_em` (ISO)
  - `rotulos(erro: Erro, rotulo_da_questao: dict[int, str]) -> list[str]`
  - `tendencias(envios: list[Envio]) -> dict[str, Tendencia]`
  - `JANELA_RECENTE = 10` e `ROTULOS_POR_ERRO = 5`

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/unit/test_historico_do_aluno.py`, trocar o import do topo por:

```python
from datetime import datetime, timedelta

from app.services.historico_do_aluno import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, Envio, Tendencia, erros_do_aluno,
    resultado_da_lista, resultado_da_trilha, rotulos, superados, tendencias,
)

# Quarta-feira, 28/10/2026, ao meio-dia.
T0 = datetime(2026, 10, 28, 12, 0)
OFF = "Acesso Fora dos Limites: Off-by-One"
LACO = "Laço Infinito"


def lista(minutos, resultado=ERRO, categoria=OFF, item=1, o_que_fazer="faça assim"):
    return Envio(origem=LISTA, item_id=item, momento=T0 + timedelta(minutes=minutos),
                 categoria="Correto" if resultado == ACERTO else categoria,
                 resultado=resultado, o_que_fazer=o_que_fazer)


def trilha(minutos, resultado=ACERTO, alvo=OFF, categoria=None, item=100,
           titulo="Soma dos pares", o_que_fazer=""):
    if categoria is None:
        categoria = "Correto" if resultado == ACERTO else alvo
    return Envio(origem=TRILHA, item_id=item, momento=T0 + timedelta(minutes=minutos),
                 categoria=categoria, resultado=resultado, o_que_fazer=o_que_fazer,
                 alvo=alvo, titulo=titulo)
```

E acrescentar no fim do arquivo:

```python
class TestErros:
    def test_acerto_no_treino_do_mesmo_erro_supera(self):
        (erro,) = erros_do_aluno([lista(0), trilha(10)])
        assert not erro.ativo
        assert erro.superado_em == T0 + timedelta(minutes=10)

    def test_acerto_antes_da_ultima_ocorrencia_nao_supera(self):
        (erro,) = erros_do_aluno([lista(0), trilha(10), lista(20)])
        assert erro.ativo
        assert erro.superado_em is None

    def test_erro_que_volta_precisa_de_novo_acerto(self):
        (erro,) = erros_do_aluno([lista(0), trilha(10), lista(20), trilha(30, item=101)])
        assert erro.superado_em == T0 + timedelta(minutes=30)

    def test_acerto_em_exercicio_de_outro_erro_nao_supera(self):
        (erro,) = erros_do_aluno([lista(0), trilha(10, alvo=LACO)])
        assert erro.ativo

    def test_superado_em_e_o_primeiro_acerto_depois_da_ultima_ocorrencia(self):
        (erro,) = erros_do_aluno([lista(0), trilha(10), trilha(20)])
        assert erro.superado_em == T0 + timedelta(minutes=10)

    def test_erro_cometido_no_treino_vira_erro_ativo(self):
        erros = erros_do_aluno([lista(0), trilha(10, resultado=ERRO, categoria=LACO)])
        laco = next(e for e in erros if e.categoria == LACO)
        assert laco.ativo
        assert laco.total == 1
        assert laco.no_treino == 1

    def test_falha_tecnica_nao_vira_erro(self):
        assert erros_do_aluno([lista(0, FALHA, categoria="Erro Desconhecido")]) == []

    def test_contas_do_erro(self):
        (erro,) = erros_do_aluno([
            lista(0, o_que_fazer="primeiro"),
            trilha(10, resultado=ERRO),
            lista(20, item=2, o_que_fazer="último"),
        ])
        assert erro.total == 3
        assert erro.no_treino == 1
        assert erro.o_que_fazer == "último"
        assert erro.ultima_ocorrencia == T0 + timedelta(minutes=20)

    def test_ordem_ativos_pelo_total_e_nome_superados_do_mais_recente(self):
        envios = [
            lista(0, categoria="B"), lista(1, categoria="B"),
            lista(2, categoria="A"), lista(3, categoria="A"),
            lista(4, categoria="C"), lista(5, categoria="C"), lista(6, categoria="C"),
            lista(7, categoria="D"), trilha(8, alvo="D"),
            lista(9, categoria="E"), trilha(10, alvo="E", item=101),
        ]
        assert [e.categoria for e in erros_do_aluno(envios)] == ["C", "A", "B", "E", "D"]

    def test_superados_no_formato_da_tela(self):
        erros = erros_do_aluno([lista(0), lista(1), trilha(10), lista(20, categoria=LACO)])
        assert superados(erros) == [
            {"error_category": OFF, "total": 2, "superado_em": "2026-10-28T12:10:00"},
        ]

    def test_rotulos_do_mais_recente_sem_repetir_no_maximo_cinco(self):
        envios = [lista(i, item=i) for i in range(1, 7)] + [
            lista(7, item=1), trilha(8, resultado=ERRO), lista(9, item=99),
        ]
        (erro,) = erros_do_aluno(envios)
        rotulo_da_questao = {i: f"Lista 1 · Q{i}" for i in range(1, 7)}
        assert rotulos(erro, rotulo_da_questao) == [
            "Trilha · Soma dos pares", "Lista 1 · Q1", "Lista 1 · Q6", "Lista 1 · Q5",
            "Lista 1 · Q4",
        ]


class TestTendencia:
    def test_erro_que_parou_esta_melhorando_e_o_novo_piorando(self):
        envios = [lista(i, categoria=LACO) for i in range(4)] + [
            lista(10 + i, item=2) for i in range(10)
        ]
        t = tendencias(envios)
        assert t[LACO] == Tendencia(recentes=0, anteriores=4, sentido="melhorando")
        assert t[OFF] == Tendencia(recentes=10, anteriores=0, sentido="piorando")

    def test_sem_tentativa_fora_da_janela_e_estavel(self):
        t = tendencias([lista(0), lista(1, ACERTO, item=2)])
        assert t[OFF] == Tendencia(recentes=1, anteriores=0, sentido="estavel")

    def test_falha_tecnica_nao_ocupa_a_janela(self):
        antigos = [lista(i, categoria=LACO) for i in range(10)]
        falhas = [lista(20 + i, FALHA, categoria="Erro Desconhecido") for i in range(10)]
        t = tendencias(antigos + falhas)
        assert t[LACO] == Tendencia(recentes=10, anteriores=0, sentido="estavel")
        assert "Erro Desconhecido" not in t
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_historico_do_aluno.py -q`
Esperado: FALHA com `ImportError: cannot import name 'Envio'`

- [ ] **Passo 3: escrever as regras**

Em `backend/app/services/historico_do_aluno.py`, trocar o trecho do docstring até `TRILHA = "trilha"` por:

```python
"""Histórico do aluno: os envios das listas e as tentativas da trilha numa
lista só, em ordem de tempo.

O progresso, os erros recorrentes e a trilha leem daqui, então os três sempre
concordam sobre o que o aluno errou e o que ele já superou. As regras trabalham
sobre registros simples e se testam com listas montadas à mão. A classificação
de cada envio também mora aqui, e o funil da turma usa a mesma."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime

CATEGORIA_CORRETA = "Correto"
# O que as heurísticas devolvem quando a execução falha por fora do código do
# aluno, como o Docker fora do ar. Não é erro dele.
CATEGORIA_FALHA_TECNICA = "Erro Desconhecido"

ACERTO = "acerto"
ERRO = "erro"
FALHA = "falha"

LISTA = "lista"
TRILHA = "trilha"

# Quantas tentativas válidas contam como "recentes" ao medir a tendência de um erro.
JANELA_RECENTE = 10
# Quantos lugares o painel mostra em "Aconteceu em".
ROTULOS_POR_ERRO = 5
```

E acrescentar no fim do arquivo:

```python
# ── registros ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Envio:
    """Um envio do aluno, de lista ou de trilha, já classificado.

    `alvo` e `titulo` só existem na trilha: o erro para o qual o exercício foi
    feito e o nome dele."""
    origem: str
    item_id: int
    momento: datetime
    categoria: str
    resultado: str
    o_que_fazer: str = ""
    alvo: str = ""
    titulo: str = ""

    @property
    def item(self) -> tuple[str, int]:
        return (self.origem, self.item_id)


@dataclass(frozen=True)
class Erro:
    """Uma categoria que o aluno já errou, com as ocorrências em ordem de tempo."""
    categoria: str
    ocorrencias: tuple[Envio, ...]
    superado_em: datetime | None = None

    @property
    def ativo(self) -> bool:
        return self.superado_em is None

    @property
    def total(self) -> int:
        return len(self.ocorrencias)

    @property
    def no_treino(self) -> int:
        return sum(1 for e in self.ocorrencias if e.origem == TRILHA)

    @property
    def ultima_ocorrencia(self) -> datetime:
        return self.ocorrencias[-1].momento

    @property
    def o_que_fazer(self) -> str:
        return self.ocorrencias[-1].o_que_fazer


@dataclass(frozen=True)
class Tendencia:
    recentes: int
    anteriores: int
    sentido: str  # 'melhorando' | 'piorando' | 'estavel'


# ── erros ────────────────────────────────────────────────────────────────────

def erros_do_aluno(envios: list[Envio]) -> list[Erro]:
    """Cada categoria que o aluno errou: os ativos primeiro, pelo total e depois
    pelo nome, e os superados depois, do mais recente para o mais antigo.

    Superado é o erro em que, depois da última vez que ele apareceu, o aluno
    acertou um exercício da trilha feito para ele. Se o erro aparece de novo,
    volta a ser ativo até o próximo acerto. Falha técnica nunca vira erro."""
    por_categoria: dict[str, list[Envio]] = defaultdict(list)
    for e in envios:
        if e.resultado == ERRO:
            por_categoria[e.categoria].append(e)

    erros = []
    for categoria, ocorrencias in por_categoria.items():
        ultima = ocorrencias[-1].momento
        superado_em = next(
            (e.momento for e in envios
             if e.origem == TRILHA and e.alvo == categoria
             and e.resultado == ACERTO and e.momento > ultima),
            None,
        )
        erros.append(Erro(categoria, tuple(ocorrencias), superado_em))

    ativos = sorted((e for e in erros if e.ativo), key=lambda e: (-e.total, e.categoria))
    ja_superados = sorted(
        (e for e in erros if not e.ativo), key=lambda e: e.superado_em, reverse=True)
    return ativos + ja_superados


def superados(erros: list[Erro]) -> list[dict]:
    """Os erros superados no formato que o painel e a trilha mostram."""
    return [
        {"error_category": e.categoria, "total": e.total,
         "superado_em": e.superado_em.isoformat()}
        for e in erros if not e.ativo
    ]


def rotulos(erro: Erro, rotulo_da_questao: dict[int, str]) -> list[str]:
    """Onde o erro aconteceu, do mais recente para o mais antigo, sem repetir.
    A questão sem rótulo, de atividade que o aluno não vê, fica de fora."""
    vistos: list[str] = []
    for e in reversed(erro.ocorrencias):
        rotulo = (f"Trilha · {e.titulo}" if e.origem == TRILHA
                  else rotulo_da_questao.get(e.item_id))
        if rotulo and rotulo not in vistos:
            vistos.append(rotulo)
    return vistos[:ROTULOS_POR_ERRO]


def tendencias(envios: list[Envio]) -> dict[str, Tendencia]:
    """Para cada categoria errada, a frequência dela nas JANELA_RECENTE últimas
    tentativas válidas contra a do resto do histórico. A falha técnica não
    ocupa lugar em nenhuma das duas janelas."""
    validas = [e for e in envios if e.resultado != FALHA]
    janela = validas[-JANELA_RECENTE:]
    janela_anterior = len(validas) - len(janela)
    total = Counter(e.categoria for e in validas if e.resultado == ERRO)
    recentes = Counter(e.categoria for e in janela if e.resultado == ERRO)
    return {
        categoria: Tendencia(
            recentes[categoria],
            n - recentes[categoria],
            _sentido(recentes[categoria], n - recentes[categoria], len(janela), janela_anterior),
        )
        for categoria, n in total.items()
    }


def _sentido(recentes: int, anteriores: int, janela_recente: int, janela_anterior: int) -> str:
    """Sem histórico anterior suficiente não há tendência."""
    if janela_anterior == 0 or janela_recente == 0:
        return "estavel"
    taxa_recente = recentes / janela_recente
    taxa_anterior = anteriores / janela_anterior
    if taxa_recente <= taxa_anterior * 0.8:
        return "melhorando"
    if taxa_recente >= taxa_anterior * 1.2:
        return "piorando"
    return "estavel"
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: PASSA, 16 testes

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/historico_do_aluno.py backend/tests/unit/test_historico_do_aluno.py
/usr/bin/git commit -m "feat(historico): erros ativos, superados e tendencia sobre listas e trilha"
```

### Task 3: contas do progresso

**Arquivos:**
- Alterar: `backend/app/services/historico_do_aluno.py`
- Teste: `backend/tests/unit/test_historico_do_aluno.py`

**Interfaces:**
- Consome: `Envio`, `ACERTO`, `FALHA` de T1 e T2
- Produz:
  - `Resolucao(item: tuple[str, int], momento: datetime, tentativas: int)`, dataclass congelada
  - `resolucoes(envios: list[Envio]) -> list[Resolucao]`
  - `dias_seguidos(envios: list[Envio], hoje: date) -> int`
  - `evolucao(envios: list[Envio], resolvidas: list[Resolucao]) -> list[dict]` com `periodo`, `tentativas` e `resolvidas`

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/unit/test_historico_do_aluno.py`, trocar a linha `from datetime import datetime, timedelta` e o bloco `from app.services.historico_do_aluno import (...)` logo abaixo dela por:

```python
from datetime import date, datetime, timedelta

from app.services.historico_do_aluno import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, Envio, Tendencia, dias_seguidos, erros_do_aluno,
    evolucao, resolucoes, resultado_da_lista, resultado_da_trilha, rotulos, superados,
    tendencias,
)
```

E acrescentar no fim do arquivo:

```python
HOJE = date(2026, 10, 28)


def no_dia(dia):
    return Envio(origem=LISTA, item_id=1, momento=datetime(2026, 10, dia, 10, 0),
                 categoria=OFF, resultado=ERRO)


class TestResolucoes:
    def test_conta_so_as_tentativas_validas_ate_o_primeiro_acerto(self):
        envios = [
            lista(0), lista(1, FALHA, categoria="Erro Desconhecido"),
            lista(2, ACERTO), lista(3), lista(4, ACERTO),
        ]
        (r,) = resolucoes(envios)
        assert r.item == (LISTA, 1)
        assert r.tentativas == 2
        assert r.momento == T0 + timedelta(minutes=2)

    def test_falha_antes_do_acerto_ainda_e_acerto_de_primeira(self):
        (r,) = resolucoes([lista(0, FALHA, categoria="Erro Desconhecido"), lista(1, ACERTO)])
        assert r.tentativas == 1

    def test_item_sem_acerto_nao_esta_resolvido(self):
        assert resolucoes([lista(0), trilha(1, resultado=ERRO)]) == []

    def test_questao_e_exercicio_com_o_mesmo_id_sao_itens_diferentes(self):
        rs = resolucoes([lista(0, ACERTO, item=5), trilha(1, item=5)])
        assert sorted(r.item for r in rs) == [(LISTA, 5), (TRILHA, 5)]


class TestDiasSeguidos:
    def test_sequencia_terminando_hoje(self):
        assert dias_seguidos([no_dia(26), no_dia(27), no_dia(28)], HOJE) == 3

    def test_quem_enviou_ontem_mantem_a_sequencia(self):
        assert dias_seguidos([no_dia(26), no_dia(27)], HOJE) == 2

    def test_buraco_zera(self):
        assert dias_seguidos([no_dia(25)], HOJE) == 0
        assert dias_seguidos([], HOJE) == 0


class TestEvolucao:
    def test_tentativas_e_primeiros_acertos_por_semana(self):
        envios = [
            Envio(origem=LISTA, item_id=1, momento=datetime(2026, 10, 14, 10),
                  categoria=OFF, resultado=ERRO),
            Envio(origem=TRILHA, item_id=100, momento=datetime(2026, 10, 27, 10),
                  categoria="Correto", resultado=ACERTO, alvo=OFF),
            Envio(origem=LISTA, item_id=1, momento=datetime(2026, 10, 28, 10),
                  categoria="Correto", resultado=ACERTO),
        ]
        assert evolucao(envios, resolucoes(envios)) == [
            {"periodo": "2026-10-12", "tentativas": 1, "resolvidas": 0},
            {"periodo": "2026-10-26", "tentativas": 2, "resolvidas": 2},
        ]
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_historico_do_aluno.py -q`
Esperado: FALHA com `ImportError: cannot import name 'dias_seguidos'`

- [ ] **Passo 3: escrever as contas**

Em `backend/app/services/historico_do_aluno.py`, trocar:

```python
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
```

por:

```python
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.services.calendario import semana_iso
```

E acrescentar no fim do arquivo:

```python
# ── progresso ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Resolucao:
    """O primeiro acerto de um item e quantas tentativas válidas ele levou,
    contando o próprio acerto."""
    item: tuple[str, int]
    momento: datetime
    tentativas: int


def resolucoes(envios: list[Envio]) -> list[Resolucao]:
    """Um registro por item resolvido. A falha técnica não conta como tentativa,
    e o que vem depois do primeiro acerto não muda nada."""
    validas: Counter[tuple[str, int]] = Counter()
    resolvidos: dict[tuple[str, int], Resolucao] = {}
    for e in envios:
        if e.item in resolvidos or e.resultado == FALHA:
            continue
        validas[e.item] += 1
        if e.resultado == ACERTO:
            resolvidos[e.item] = Resolucao(e.item, e.momento, validas[e.item])
    return list(resolvidos.values())


def dias_seguidos(envios: list[Envio], hoje: date) -> int:
    """Sequência de dias consecutivos com pelo menos um envio, terminando hoje ou
    ontem (quem enviou ontem ainda não perdeu a sequência)."""
    dias = {e.momento.date() for e in envios}
    referencia = hoje if hoje in dias else hoje - timedelta(days=1)
    sequencia = 0
    while referencia in dias:
        sequencia += 1
        referencia -= timedelta(days=1)
    return sequencia


def evolucao(envios: list[Envio], resolvidas: list[Resolucao]) -> list[dict]:
    """Série semanal de tentativas e de itens resolvidos pela primeira vez. Só
    aparecem as semanas com alguma tentativa."""
    tentativas = Counter(semana_iso(e.momento) for e in envios)
    primeiras = Counter(semana_iso(r.momento) for r in resolvidas)
    return [
        {"periodo": semana, "tentativas": tentativas[semana], "resolvidas": primeiras[semana]}
        for semana in sorted(tentativas)
    ]
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: PASSA, 24 testes

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/historico_do_aluno.py backend/tests/unit/test_historico_do_aluno.py
/usr/bin/git commit -m "feat(historico): contas do progresso com lista e trilha"
```

### Task 4: leitura do histórico

**Arquivos:**
- Alterar: `backend/app/services/historico_do_aluno.py`
- Criar: `backend/tests/test_leitura_do_historico.py`

**Interfaces:**
- Consome: `Envio`, `resultado_da_lista`, `resultado_da_trilha`, `LISTA`, `TRILHA` de T1 e T2
- Produz: `ler_historico(student: Student, db: Session) -> list[Envio]`, em ordem de momento, com a lista antes da trilha no empate e depois o id do registro

- [ ] **Passo 1: escrever o teste que falha**

Criar `backend/tests/test_leitura_do_historico.py`:

```python
"""Leitura do histórico do aluno: listas e trilha numa lista só, em ordem."""
from datetime import datetime, timedelta

import pytest

from app.models.orm import ExercicioGerado, Student, Submission, TentativaDeTreino
from app.services.historico_do_aluno import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, ler_historico,
)

T0 = datetime(2026, 10, 28, 12, 0)
OFF = "Acesso Fora dos Limites: Off-by-One"


@pytest.fixture()
def aluno(db):
    s = Student(email="historico@aluno.com", nome="Aluno Histórico", senha_hash="x")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@pytest.fixture()
def questao(exam_factory):
    return exam_factory(questions=[{"number": "1"}]).questions[0]


def _envio(db, aluno, questao, minutos, categoria):
    sub = Submission(
        question_id=questao.id, code="int main(){}", error_category=categoria,
        all_tests_passed=categoria == "Correto", actionable_feedback="faça assim",
        student_id=aluno.id, submitted_at=T0 + timedelta(minutes=minutos),
    )
    db.add(sub)
    return sub


def _exercicio(db, aluno, reportado=False):
    e = ExercicioGerado(student_id=aluno.id, error_category=OFF, titulo="Soma dos pares",
                        enunciado="Some os pares.", casos_teste=[], reportado=reportado)
    db.add(e)
    db.flush()
    return e


def _tentativa(db, aluno, exercicio, minutos, passou, categoria):
    db.add(TentativaDeTreino(
        exercicio_id=exercicio.id, student_id=aluno.id, code="int main(){}",
        all_tests_passed=passou, error_category=categoria,
        submitted_at=T0 + timedelta(minutes=minutos),
    ))


def test_junta_listas_e_trilha_em_ordem_de_tempo(db, aluno, questao):
    exercicio = _exercicio(db, aluno)
    _envio(db, aluno, questao, 20, "Correto")
    _tentativa(db, aluno, exercicio, 10, True, "Correto")
    _envio(db, aluno, questao, 0, OFF)
    db.commit()

    envios = ler_historico(aluno, db)
    assert [(e.origem, e.resultado) for e in envios] == [
        (LISTA, ERRO), (TRILHA, ACERTO), (LISTA, ACERTO)]
    assert envios[0].item_id == questao.id
    assert envios[0].o_que_fazer == "faça assim"
    assert envios[1].item_id == exercicio.id
    assert envios[1].alvo == OFF
    assert envios[1].titulo == "Soma dos pares"


def test_no_empate_a_lista_vem_antes_da_trilha(db, aluno, questao):
    exercicio = _exercicio(db, aluno)
    _tentativa(db, aluno, exercicio, 0, False, OFF)
    _envio(db, aluno, questao, 0, OFF)
    db.commit()

    assert [e.origem for e in ler_historico(aluno, db)] == [LISTA, TRILHA]


def test_tentativa_de_exercicio_reportado_fica_de_fora(db, aluno):
    exercicio = _exercicio(db, aluno, reportado=True)
    _tentativa(db, aluno, exercicio, 0, True, "Correto")
    db.commit()

    assert ler_historico(aluno, db) == []


def test_envio_sem_momento_fica_de_fora_e_falha_e_classificada(db, aluno, questao):
    _envio(db, aluno, questao, 0, "Erro Desconhecido")
    sem_momento = _envio(db, aluno, questao, 1, OFF)
    db.commit()
    sem_momento.submitted_at = None
    db.commit()

    (envio,) = ler_historico(aluno, db)
    assert envio.resultado == FALHA


def test_envio_de_outro_aluno_nao_entra(db, aluno, questao):
    outro = Student(email="outro@aluno.com", nome="Outro", senha_hash="x")
    db.add(outro)
    db.flush()
    exercicio = _exercicio(db, outro)
    _envio(db, outro, questao, 0, OFF)
    _tentativa(db, outro, exercicio, 1, False, OFF)
    db.commit()

    assert ler_historico(aluno, db) == []
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_leitura_do_historico.py -q`
Esperado: FALHA com `ImportError: cannot import name 'ler_historico'`

- [ ] **Passo 3: escrever a leitura**

Em `backend/app/services/historico_do_aluno.py`, trocar:

```python
from datetime import date, datetime, timedelta

from app.services.calendario import semana_iso
```

por:

```python
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.orm import ExercicioGerado, Student, Submission, TentativaDeTreino
from app.services.calendario import semana_iso
```

E acrescentar no fim do arquivo:

```python
# ── leitura ──────────────────────────────────────────────────────────────────

def ler_historico(student: Student, db: Session) -> list[Envio]:
    """Os envios das listas e as tentativas da trilha do aluno, em ordem de
    tempo. No empate, a lista vem antes da trilha e depois vale o id.

    Tentativa de exercício reportado fica de fora: o aluno disse que o
    exercício estava errado, e ele deixa de contar. Envio sem momento também,
    como no funil."""
    linhas: list[tuple[datetime, int, int, Envio]] = []

    envios_da_lista = (
        db.query(Submission.id, Submission.question_id, Submission.submitted_at,
                 Submission.error_category, Submission.actionable_feedback)
        .filter(Submission.student_id == student.id, Submission.submitted_at.isnot(None))
        .all()
    )
    for id_, questao_id, momento, categoria, o_que_fazer in envios_da_lista:
        linhas.append((momento, 0, id_, Envio(
            origem=LISTA, item_id=questao_id, momento=momento,
            categoria=categoria or "", resultado=resultado_da_lista(categoria),
            o_que_fazer=o_que_fazer or "",
        )))

    tentativas_da_trilha = (
        db.query(TentativaDeTreino.id, TentativaDeTreino.submitted_at,
                 TentativaDeTreino.all_tests_passed, TentativaDeTreino.error_category,
                 TentativaDeTreino.actionable_feedback,
                 ExercicioGerado.id.label("exercicio_id"),
                 ExercicioGerado.error_category.label("alvo"),
                 ExercicioGerado.titulo)
        .join(ExercicioGerado, ExercicioGerado.id == TentativaDeTreino.exercicio_id)
        .filter(TentativaDeTreino.student_id == student.id,
                TentativaDeTreino.submitted_at.isnot(None),
                ExercicioGerado.reportado.is_(False))
        .all()
    )
    for (id_, momento, passou, categoria, o_que_fazer,
         exercicio_id, alvo, titulo) in tentativas_da_trilha:
        linhas.append((momento, 1, id_, Envio(
            origem=TRILHA, item_id=exercicio_id, momento=momento,
            categoria=categoria or "", resultado=resultado_da_trilha(passou, categoria),
            o_que_fazer=o_que_fazer or "", alvo=alvo, titulo=titulo,
        )))

    linhas.sort(key=lambda linha: linha[:3])
    return [linha[3] for linha in linhas]
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2
Esperado: PASSA, 5 testes

- [ ] **Passo 5: rodar a suíte inteira e commitar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q 2>&1 | tail -3`
Esperado: 380 passando

```bash
/usr/bin/git add backend/app/services/historico_do_aluno.py backend/tests/test_leitura_do_historico.py
/usr/bin/git commit -m "feat(historico): leitura das listas e da trilha numa lista so"
```

### Task 5: erros recorrentes com o treino e os superados

**Arquivos:**
- Alterar: `backend/app/services/student_activity_service.py`, `backend/app/models/schemas.py`
- Teste: `backend/tests/test_student_activity.py`

**Interfaces:**
- Consome: `ler_historico` (T4), `erros_do_aluno`, `superados`, `rotulos`, `tendencias`, `Tendencia` (T2), `ERRO`, `FALHA` (T1)
- Produz:
  - em `schemas.py`, `ErroSuperado(error_category: str, total: int, superado_em: str)`, `ErroRecorrente.no_treino: int = 0` e `ErrosRecorrentesResponse.superados: List[ErroSuperado] = []`
  - em `tests/test_student_activity.py`, o helper `_treino(db, aluno_id, alvo, tentativas, quando=None, titulo="Soma dos pares", reportado=False)`, em que `tentativas` é uma lista de `(passou, categoria)`

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/test_student_activity.py`, logo depois da função `_aluno_id`, acrescentar:

```python
def _treino(db, aluno_id, alvo, tentativas, quando=None, titulo="Soma dos pares",
            reportado=False):
    """Um exercício da trilha feito para `alvo`, com as tentativas dadas como
    (passou, categoria), um segundo uma da outra a partir de `quando`."""
    from app.models.orm import ExercicioGerado, TentativaDeTreino

    quando = quando or datetime.utcnow()
    exercicio = ExercicioGerado(student_id=aluno_id, error_category=alvo, titulo=titulo,
                                enunciado="Some os pares.", casos_teste=[],
                                reportado=reportado)
    db.add(exercicio)
    db.flush()
    for i, (passou, categoria) in enumerate(tentativas):
        db.add(TentativaDeTreino(
            exercicio_id=exercicio.id, student_id=aluno_id, code="int main(){}",
            all_tests_passed=passou, error_category=categoria,
            actionable_feedback="treine assim", attempt_number=i + 1,
            submitted_at=quando + timedelta(seconds=i),
        ))
    db.commit()
    return exercicio
```

E acrescentar no fim da classe `TestErrosRecorrentes`, depois de `test_erro_antigo_que_parou_de_acontecer_esta_melhorando`:

```python
    def test_treino_soma_e_aparece_no_rotulo(self, client, db, token, prova, tentativa_factory):
        aluno_id = _aluno_id(client, token)
        tentativa_factory(aluno_id, "1", "Laço Infinito",
                          quando=datetime.utcnow() - timedelta(hours=1))
        _treino(db, aluno_id, "Saída Incorreta", [(False, "Laço Infinito")])

        data = client.get("/aluno/erros-recorrentes", headers=_auth(token)).json()
        (laco,) = data["erros"]
        assert laco["error_category"] == "Laço Infinito"
        assert laco["total"] == 2
        assert laco["no_treino"] == 1
        assert laco["questoes"] == ["Trilha · Soma dos pares", "prova.pdf · Q1"]
        assert laco["o_que_fazer"] == "treine assim"
        assert data["total_submissoes"] == 2
        assert data["total_com_erro"] == 2

    def test_erro_superado_sai_dos_ativos(self, client, db, token, prova, tentativa_factory):
        aluno_id = _aluno_id(client, token)
        antes = datetime.utcnow() - timedelta(hours=1)
        tentativa_factory(aluno_id, "1", "Laço Infinito", quando=antes)
        tentativa_factory(aluno_id, "2", "Saída Incorreta", quando=antes)
        _treino(db, aluno_id, "Laço Infinito", [(False, "Laço Infinito"), (True, "Correto")])

        data = client.get("/aluno/erros-recorrentes", headers=_auth(token)).json()
        assert [e["error_category"] for e in data["erros"]] == ["Saída Incorreta"]
        (superado,) = data["superados"]
        assert superado["error_category"] == "Laço Infinito"
        assert superado["total"] == 2
        assert superado["superado_em"]

    def test_falha_tecnica_fica_fora_das_contas(self, client, token, prova, tentativa_factory):
        aluno_id = _aluno_id(client, token)
        tentativa_factory(aluno_id, "1", "Erro Desconhecido")
        tentativa_factory(aluno_id, "1", "Laço Infinito")

        data = client.get("/aluno/erros-recorrentes", headers=_auth(token)).json()
        assert [e["error_category"] for e in data["erros"]] == ["Laço Infinito"]
        assert data["total_submissoes"] == 1
        assert data["total_com_erro"] == 1

    def test_treino_de_outro_aluno_nao_entra(self, client, db, token, prova):
        from app.models.orm import Student

        outro = Student(email="outro@aluno.com", nome="Outro", senha_hash="x")
        db.add(outro)
        db.commit()
        _treino(db, outro.id, "Laço Infinito", [(False, "Laço Infinito")])

        data = client.get("/aluno/erros-recorrentes", headers=_auth(token)).json()
        assert data["erros"] == []
        assert data["total_submissoes"] == 0

    def test_tentativa_de_exercicio_reportado_nao_conta(self, client, db, token, prova):
        aluno_id = _aluno_id(client, token)
        _treino(db, aluno_id, "Laço Infinito", [(False, "Laço Infinito")], reportado=True)

        data = client.get("/aluno/erros-recorrentes", headers=_auth(token)).json()
        assert data["erros"] == []
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_student_activity.py -k ErrosRecorrentes -q`
Esperado: FALHA em `test_treino_soma_e_aparece_no_rotulo`, `test_erro_superado_sai_dos_ativos` e `test_falha_tecnica_fica_fora_das_contas` (o serviço ainda não lê a trilha nem separa a falha)

- [ ] **Passo 3: reescrever os erros recorrentes**

Em `backend/app/models/schemas.py`, trocar:

```python
class ErroRecorrente(BaseModel):
    error_category: str
    total: int
    recentes: int
    anteriores: int
    tendencia: str  # 'melhorando' | 'piorando' | 'estavel'
    questoes: List[str] = []
    ultima_ocorrencia: str
    o_que_fazer: str = ""


class ErrosRecorrentesResponse(BaseModel):
    total_submissoes: int
    total_com_erro: int
    erros: List[ErroRecorrente] = []
```

por:

```python
class ErroRecorrente(BaseModel):
    error_category: str
    total: int
    recentes: int
    anteriores: int
    tendencia: str  # 'melhorando' | 'piorando' | 'estavel'
    questoes: List[str] = []
    ultima_ocorrencia: str
    o_que_fazer: str = ""
    no_treino: int = 0


class ErroSuperado(BaseModel):
    error_category: str
    total: int
    superado_em: str  # ISO, como ultima_ocorrencia


class ErrosRecorrentesResponse(BaseModel):
    total_submissoes: int
    total_com_erro: int
    erros: List[ErroRecorrente] = []
    superados: List[ErroSuperado] = []
```

Em `backend/app/services/student_activity_service.py`, trocar:

```python
from app.services.historico_do_aluno import CATEGORIA_CORRETA
```

por:

```python
from app.services.historico_do_aluno import (
    CATEGORIA_CORRETA, ERRO, FALHA, erros_do_aluno, ler_historico, rotulos, superados,
    tendencias,
)
```

Apagar as duas linhas:

```python
# Quantas submissões contam como "recentes" ao medir a tendência de um erro.
JANELA_RECENTE = 10
```

E trocar tudo de `# ── erros recorrentes ──` até o fim do arquivo (a função `erros_recorrentes` e a `_tendencia`) por:

```python
# ── erros recorrentes ────────────────────────────────────────────────────────

def erros_recorrentes(student: Student, db: Session) -> dict:
    """O padrão que o aluno repete, que é justamente o que ele não enxerga sozinho.
    Junta as listas e a trilha, e separa o que ele já superou treinando.
    Determinístico: sai das categorias das heurísticas, sem chamada de LLM."""
    turma_ids = _turma_ids(student)
    exams = db.query(Exam).filter(
        Exam.turma_id.in_(turma_ids), Exam.publicada.is_(True)
    ).all() if turma_ids else []
    rotulo_questao = {
        q.id: f"{titulo_da_atividade(e)} · Q{q.number}"
        for e in exams for q in e.questions
    }

    envios = ler_historico(student, db)
    erros = erros_do_aluno(envios)
    tendencia = tendencias(envios)

    return {
        "total_submissoes": sum(1 for e in envios if e.resultado != FALHA),
        "total_com_erro": sum(1 for e in envios if e.resultado == ERRO),
        "erros": [
            {
                "error_category": erro.categoria,
                "total": erro.total,
                "no_treino": erro.no_treino,
                "recentes": tendencia[erro.categoria].recentes,
                "anteriores": tendencia[erro.categoria].anteriores,
                "tendencia": tendencia[erro.categoria].sentido,
                "questoes": rotulos(erro, rotulo_questao),
                "ultima_ocorrencia": _iso(erro.ultima_ocorrencia) or "",
                "o_que_fazer": erro.o_que_fazer,
            }
            for erro in erros if erro.ativo
        ],
        "superados": superados(erros),
    }
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_student_activity.py -q`
Esperado: PASSA

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/student_activity_service.py backend/app/models/schemas.py backend/tests/test_student_activity.py
/usr/bin/git commit -m "feat(aluno): erros recorrentes com o treino e os erros superados"
```

### Task 6: progresso com o treino e só com atividade publicada

**Arquivos:**
- Alterar: `backend/app/services/student_activity_service.py`, `backend/app/models/schemas.py`
- Teste: `backend/tests/test_student_activity.py`

**Interfaces:**
- Consome: `ler_historico` (T4), `resolucoes`, `dias_seguidos`, `evolucao` (T3), `LISTA`, `TRILHA` (T1), o helper `_treino` de T5
- Produz: `ProgressoResponse.tentativas_no_treino: int = 0` e `ProgressoResponse.exercicios_resolvidos: int = 0`

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/test_student_activity.py`, na classe `TestProgresso`, trocar:

```python
    def test_sem_submissao(self, client, token):
        data = client.get("/aluno/progresso", headers=_auth(token)).json()
        assert data["total_tentativas"] == 0
        assert data["tentativas_por_questao_resolvida"] is None
        assert data["dias_seguidos"] == 0
```

por:

```python
    def test_sem_submissao(self, client, token):
        data = client.get("/aluno/progresso", headers=_auth(token)).json()
        assert data["total_tentativas"] == 0
        assert data["tentativas_por_questao_resolvida"] is None
        assert data["dias_seguidos"] == 0
        assert data["tentativas_no_treino"] == 0
        assert data["exercicios_resolvidos"] == 0

    def test_atividade_nao_publicada_fica_fora_do_total(self, client, db, token, prova):
        prova.publicada = False
        db.commit()

        data = client.get("/aluno/progresso", headers=_auth(token)).json()
        assert data["total_atividades"] == 0
        assert data["total_questoes"] == 0

    def test_treino_entra_no_esforco_e_nao_nas_questoes(
        self, client, db, token, prova, tentativa_factory,
    ):
        aluno_id = _aluno_id(client, token)
        tentativa_factory(aluno_id, "1", "Correto",
                          quando=datetime.utcnow() - timedelta(seconds=30))
        _treino(db, aluno_id, "Laço Infinito",
                [(False, "Laço Infinito"), (False, "Laço Infinito"), (True, "Correto")])

        data = client.get("/aluno/progresso", headers=_auth(token)).json()
        assert data["questoes_resolvidas"] == 1
        assert data["total_questoes"] == 2
        assert data["total_tentativas"] == 4
        assert data["tentativas_no_treino"] == 3
        assert data["exercicios_resolvidos"] == 1
        # Q1 de primeira e o treino na 3ª → média 2,0.
        assert data["tentativas_por_questao_resolvida"] == 2.0
        assert data["acertos_de_primeira"] == 1
        assert data["dias_seguidos"] == 1
        assert sum(p["tentativas"] for p in data["evolucao"]) == 4
        assert sum(p["resolvidas"] for p in data["evolucao"]) == 2

    def test_falha_tecnica_nao_conta_como_tentativa_ate_acertar(
        self, client, token, prova, tentativa_factory,
    ):
        aluno_id = _aluno_id(client, token)
        tentativa_factory(aluno_id, "1", "Erro Desconhecido")
        tentativa_factory(aluno_id, "1", "Correto")

        data = client.get("/aluno/progresso", headers=_auth(token)).json()
        assert data["total_tentativas"] == 2
        assert data["tentativas_por_questao_resolvida"] == 1.0
        assert data["acertos_de_primeira"] == 1
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_student_activity.py -k Progresso -q`
Esperado: FALHA em `test_sem_submissao` (`KeyError: 'tentativas_no_treino'`), `test_atividade_nao_publicada_fica_fora_do_total`, `test_treino_entra_no_esforco_e_nao_nas_questoes` e `test_falha_tecnica_nao_conta_como_tentativa_ate_acertar`

- [ ] **Passo 3: reescrever o progresso**

Em `backend/app/models/schemas.py`, trocar:

```python
    total_tentativas: int
    tentativas_por_questao_resolvida: Optional[float] = None
```

por:

```python
    total_tentativas: int
    tentativas_no_treino: int = 0
    exercicios_resolvidos: int = 0
    tentativas_por_questao_resolvida: Optional[float] = None
```

Em `backend/app/services/student_activity_service.py`, trocar os imports:

```python
from datetime import datetime, timedelta
```

por:

```python
from datetime import datetime
```

```python
from app.services.calendario import semana_iso, situacao_da_atividade
from app.services.historico_do_aluno import (
    CATEGORIA_CORRETA, ERRO, FALHA, erros_do_aluno, ler_historico, rotulos, superados,
    tendencias,
)
```

por:

```python
from app.services.calendario import situacao_da_atividade
from app.services.historico_do_aluno import (
    CATEGORIA_CORRETA, ERRO, FALHA, LISTA, TRILHA, dias_seguidos, erros_do_aluno, evolucao,
    ler_historico, resolucoes, rotulos, superados, tendencias,
)
```

E trocar tudo de `# ── progresso ──` até a linha antes de `# ── erros recorrentes ──` (as funções `progresso`, `_dias_seguidos` e `_evolucao`) por:

```python
# ── progresso ────────────────────────────────────────────────────────────────

def progresso(student: Student, db: Session) -> dict:
    """Os números do aluno contra a turma, com o treino somado no esforço.

    Questões resolvidas e atividades concluídas são só da turma, porque o total
    é o da turma. Tentativas, acertos de primeira, dias seguidos e a evolução
    juntam as questões e os exercícios da trilha."""
    turma_ids = _turma_ids(student)
    exams = db.query(Exam).filter(
        Exam.turma_id.in_(turma_ids), Exam.publicada.is_(True)
    ).all() if turma_ids else []
    questoes = [q for e in exams for q in e.questions]
    ids_das_questoes = {q.id for q in questoes}

    envios = [
        e for e in ler_historico(student, db)
        if e.origem == TRILHA or e.item_id in ids_das_questoes
    ]
    resolvidas = resolucoes(envios)
    questoes_resolvidas = {r.item[1] for r in resolvidas if r.item[0] == LISTA}
    concluidas = sum(
        1 for e in exams
        if e.questions and all(q.id in questoes_resolvidas for q in e.questions)
    )

    return {
        "total_atividades": len(exams),
        "atividades_concluidas": concluidas,
        "total_questoes": len(questoes),
        "questoes_resolvidas": len(questoes_resolvidas),
        "total_tentativas": len(envios),
        "tentativas_no_treino": sum(1 for e in envios if e.origem == TRILHA),
        "exercicios_resolvidos": sum(1 for r in resolvidas if r.item[0] == TRILHA),
        "tentativas_por_questao_resolvida": (
            round(sum(r.tentativas for r in resolvidas) / len(resolvidas), 1)
            if resolvidas else None
        ),
        "acertos_de_primeira": sum(1 for r in resolvidas if r.tentativas == 1),
        "dias_seguidos": dias_seguidos(envios, datetime.utcnow().date()),
        "ultima_submissao": _iso(envios[-1].momento) if envios else None,
        "evolucao": evolucao(envios, resolvidas),
    }


```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_student_activity.py -q`
Esperado: PASSA

Rodar também: `/home/otavio/produtos-digitais-cs1/backend/venv/bin/ruff check --select F,E9,B --ignore B008,B904 backend/app/services/student_activity_service.py`
Esperado: nenhum import sem uso

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/student_activity_service.py backend/app/models/schemas.py backend/tests/test_student_activity.py
/usr/bin/git commit -m "feat(aluno): progresso com o treino e so com atividade publicada"
```

### Task 7: trilha só com erros ativos, superados e pré-geração do próximo

**Arquivos:**
- Alterar: `backend/app/services/treino_service.py`, `backend/app/models/schemas.py`
- Teste: `backend/tests/test_treino.py`

**Interfaces:**
- Consome: `ler_historico` (T4), `Erro`, `erros_do_aluno`, `superados` (T2), `ErroSuperado` (T5)
- Produz: `TrilhaResponse.superados: List[ErroSuperado] = []`. `categorias_para_treinar(student, db)` com o mesmo formato de hoje, só com os ativos

- [ ] **Passo 1: escrever o teste que falha**

Em `backend/tests/test_treino.py`, logo depois da fixture `sem_thread`, acrescentar:

```python
@pytest.fixture()
def pre_geracoes(monkeypatch):
    """Anota as pré-gerações pedidas em vez de dispará-las."""
    pedidas = []
    monkeypatch.setattr("app.services.treino_service.preparar_proximo",
                        lambda student_id, categoria: pedidas.append(categoria))
    return pedidas


def _treinou(db, aluno, categoria, passou=True, reportado=False):
    """Um exercício da trilha para `categoria` com uma tentativa, gravada agora."""
    exercicio = ExercicioGerado(
        student_id=aluno.id, error_category=categoria, titulo="Soma",
        enunciado="Some os n primeiros inteiros.",
        casos_teste=[{"input": "3", "expected_output": "6"}],
        resolvido=passou, reportado=reportado, created_at=datetime.utcnow())
    db.add(exercicio)
    db.flush()
    db.add(TentativaDeTreino(
        exercicio_id=exercicio.id, student_id=aluno.id, code="int main(){}",
        all_tests_passed=passou, error_category="Correto" if passou else categoria,
        submitted_at=datetime.utcnow()))
    db.commit()
    return exercicio


def _token(client):
    resp = client.post("/aluno/login",
                       json={"email": CADASTRO["email"], "senha": CADASTRO["senha"]})
    return resp.json()["access_token"]
```

Depois da classe `TestOQueEntraNaTrilha`, acrescentar:

```python
class TestSuperados:
    def test_erro_superado_sai_das_categorias_e_vai_para_superados(
        self, db, aluno, erros_do_aluno, pre_geracoes
    ):
        from app.services.treino_service import trilha

        _treinou(db, aluno, "Acesso Fora dos Limites: Off-by-One")

        t = trilha(aluno, db)
        assert [c["error_category"] for c in t["categorias"]] == ["Tudo no Main"]
        assert [s["error_category"] for s in t["superados"]] == [
            "Acesso Fora dos Limites: Off-by-One"]
        assert t["superados"][0]["total"] == 3

    def test_sem_erro_ativo_gerar_sem_categoria_avisa_que_superou(
        self, db, aluno, erros_do_aluno, pre_geracoes
    ):
        from app.services.treino_service import TreinoIndisponivel, gerar_para_categoria

        _treinou(db, aluno, "Acesso Fora dos Limites: Off-by-One")
        _treinou(db, aluno, "Tudo no Main")

        with pytest.raises(TreinoIndisponivel) as e:
            gerar_para_categoria(aluno, None, db)
        assert str(e.value) == ("Você superou todos os erros que repetia. "
                                "Resolva uma questão da sua turma e volte aqui.")

    def test_treinar_de_novo_um_erro_superado(
        self, db, aluno, erros_do_aluno, gemini_ok, pre_geracoes
    ):
        from app.services.treino_service import gerar_para_categoria

        _treinou(db, aluno, "Acesso Fora dos Limites: Off-by-One")

        exercicio = gerar_para_categoria(aluno, "Acesso Fora dos Limites: Off-by-One", db)
        assert exercicio["error_category"] == "Acesso Fora dos Limites: Off-by-One"
        assert gemini_ok[0][1] == "troque <= por <"

    def test_categoria_que_o_aluno_nunca_errou(self, db, aluno, erros_do_aluno):
        from app.services.treino_service import TreinoIndisponivel, gerar_para_categoria

        with pytest.raises(TreinoIndisponivel) as e:
            gerar_para_categoria(aluno, "Laço Infinito", db)
        assert str(e.value) == "Você não tem erros nessa categoria."

    def test_acerto_em_exercicio_reportado_nao_supera(self, db, aluno, erros_do_aluno):
        from app.services.treino_service import categorias_para_treinar

        _treinou(db, aluno, "Acesso Fora dos Limites: Off-by-One", reportado=True)
        assert [c["error_category"] for c in categorias_para_treinar(aluno, db)] == [
            "Acesso Fora dos Limites: Off-by-One", "Tudo no Main"]

    def test_erro_do_treino_soma_nas_ocorrencias(self, db, aluno, erros_do_aluno):
        from app.services.treino_service import categorias_para_treinar

        for _ in range(3):
            _treinou(db, aluno, "Tudo no Main", passou=False)

        categorias = categorias_para_treinar(aluno, db)
        assert [(c["error_category"], c["ocorrencias"]) for c in categorias] == [
            ("Tudo no Main", 4), ("Acesso Fora dos Limites: Off-by-One", 3)]

    def test_falha_tecnica_nao_vira_categoria(self, db, aluno, exam_factory):
        from app.services.treino_service import categorias_para_treinar

        exam = exam_factory(questions=[{"number": "1"}])
        db.add(Submission(
            question_id=exam.questions[0].id, code="int main(){}",
            error_category="Erro Desconhecido", all_tests_passed=False,
            student_id=aluno.id, submitted_at=datetime.utcnow(),
        ))
        db.commit()
        assert categorias_para_treinar(aluno, db) == []


class TestRotaDaTrilha:
    def test_get_devolve_os_superados(self, client, db, aluno, erros_do_aluno, pre_geracoes):
        _treinou(db, aluno, "Acesso Fora dos Limites: Off-by-One")

        data = client.get("/aluno/treino", headers=_auth(_token(client))).json()
        assert [c["error_category"] for c in data["categorias"]] == ["Tudo no Main"]
        assert data["superados"][0]["error_category"] == "Acesso Fora dos Limites: Off-by-One"
        assert data["superados"][0]["superado_em"]

    def test_gerar_com_tudo_superado_da_409(self, client, db, aluno, erros_do_aluno, pre_geracoes):
        _treinou(db, aluno, "Acesso Fora dos Limites: Off-by-One")
        _treinou(db, aluno, "Tudo no Main")

        resp = client.post("/aluno/treino/gerar", json={}, headers=_auth(_token(client)))
        assert resp.status_code == 409
        assert resp.json()["detail"].startswith("Você superou todos os erros")
```

Na classe `TestPreGeracao`, trocar o teste `test_resolver_prepara_o_proximo` inteiro (do `def test_resolver_prepara_o_proximo(` até o `assert pendentes == 1, "o proximo tinha que estar pronto"`) por:

```python
    def test_resolver_prepara_o_proximo_erro_ativo(
        self, db, aluno, erros_do_aluno, gemini_ok, pre_geracoes
    ):
        """O erro do exercício resolvido vira superado, então o próximo a ficar
        pronto é o do erro que continua ativo, e não outro do mesmo."""
        from app.services import treino_service

        exercicio = treino_service.gerar_para_categoria(aluno, None, db)
        assert exercicio["error_category"] == "Acesso Fora dos Limites: Off-by-One"

        # O envio acerta: o evaluate_code do treino é o mesmo mock da referência.
        treino_service.treinar(aluno, exercicio["id"], "int main(){}", db)
        assert pre_geracoes == ["Tudo no Main"]

    def test_resolver_o_ultimo_erro_ativo_nao_prepara_nada(
        self, db, aluno, exam_factory, pre_geracoes, monkeypatch
    ):
        from app.services import treino_service

        exam = exam_factory(questions=[{"number": "1"}])
        db.add(Submission(
            question_id=exam.questions[0].id, code="int main(){}",
            error_category="Tudo no Main", all_tests_passed=False,
            student_id=aluno.id, submitted_at=datetime.utcnow(),
        ))
        exercicio = ExercicioGerado(
            student_id=aluno.id, error_category="Tudo no Main", titulo="Soma",
            enunciado="Some os n primeiros inteiros.",
            casos_teste=[{"input": "3", "expected_output": "6"}],
            created_at=datetime.utcnow())
        db.add(exercicio)
        db.commit()
        monkeypatch.setattr(treino_service, "evaluate_code",
                            lambda *a, **k: _resultado_referencia([True]))

        treino_service.treinar(aluno, exercicio.id, "int main(){}", db)
        assert pre_geracoes == []
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_treino.py -q`
Esperado: FALHA nos testes de `TestSuperados` (menos `test_categoria_que_o_aluno_nunca_errou`), de `TestRotaDaTrilha` e em `test_resolver_prepara_o_proximo_erro_ativo` (`pre_geracoes == ["Acesso Fora dos Limites: Off-by-One"]`)

- [ ] **Passo 3: reescrever a trilha**

Em `backend/app/models/schemas.py`, trocar:

```python
class TrilhaResponse(BaseModel):
    categorias: List[CategoriaParaTreinar] = []
    exercicios: List[ExercicioResumo] = []
    geracoes_restantes_hoje: int = 0
```

por:

```python
class TrilhaResponse(BaseModel):
    categorias: List[CategoriaParaTreinar] = []
    superados: List[ErroSuperado] = []
    exercicios: List[ExercicioResumo] = []
    geracoes_restantes_hoje: int = 0
```

Em `backend/app/services/treino_service.py`, trocar:

```python
from app.models.orm import ExercicioGerado, Student, Submission, TentativaDeTreino
from app.services.historico_do_aluno import CATEGORIA_CORRETA
```

por:

```python
from app.models.orm import ExercicioGerado, Student, TentativaDeTreino
from app.services.historico_do_aluno import Erro, erros_do_aluno, ler_historico, superados
```

Trocar a função `categorias_para_treinar` e a função `trilha` inteiras (de `def categorias_para_treinar(` até o `}` do `return` de `trilha`) por:

```python
def _erros(student: Student, db: Session) -> list[Erro]:
    """Os erros do aluno, ativos e superados, do mesmo histórico do painel de
    erros recorrentes: listas e trilha juntas. Sem chamada de LLM."""
    return erros_do_aluno(ler_historico(student, db))


def categorias_para_treinar(student: Student, db: Session) -> list[dict]:
    """Os erros ativos do aluno, do mais frequente para o menos. O que ele já
    superou treinando sai daqui e vai para os superados da trilha."""
    return _categorias([e for e in _erros(student, db) if e.ativo], student, db)


def _categorias(erros: list[Erro], student: Student, db: Session) -> list[dict]:
    gerados = (
        db.query(ExercicioGerado)
        .filter(ExercicioGerado.student_id == student.id,
                ExercicioGerado.reportado.is_(False))
        .all()
    )
    por_cat_gerados: dict[str, list[ExercicioGerado]] = defaultdict(list)
    for e in gerados:
        por_cat_gerados[e.error_category].append(e)

    categorias = []
    for erro in erros:
        exercicios = por_cat_gerados.get(erro.categoria, [])
        categorias.append({
            "error_category": erro.categoria,
            "ocorrencias": erro.total,
            "o_que_fazer": erro.o_que_fazer,
            "exercicios_gerados": len(exercicios),
            "exercicios_resolvidos": sum(1 for e in exercicios if e.resolvido),
            "tem_pendente": any(not e.resolvido for e in exercicios),
        })
    return categorias


def trilha(student: Student, db: Session) -> dict:
    erros = _erros(student, db)
    categorias = _categorias([e for e in erros if e.ativo], student, db)
    # Aquece a categoria que ele mais erra, que é a que o botão grande oferece.
    # Sem exercício pendente ali, o primeiro clique esperaria o Gemini.
    if categorias and not categorias[0]["tem_pendente"]:
        preparar_proximo(student.id, categorias[0]["error_category"])

    exercicios = (
        db.query(ExercicioGerado)
        .filter(ExercicioGerado.student_id == student.id,
                ExercicioGerado.reportado.is_(False))
        .order_by(ExercicioGerado.created_at.desc())
        .all()
    )
    return {
        "categorias": categorias,
        "superados": superados(erros),
        "exercicios": [_exercicio_resumo(e) for e in exercicios],
        "geracoes_restantes_hoje": _restantes_hoje(student, db),
    }
```

Em `gerar_para_categoria`, trocar:

```python
    categorias = categorias_para_treinar(student, db)
    if not categorias:
        raise TreinoIndisponivel(
            "Você ainda não tem erros suficientes para a trilha. "
            "Resolva alguma questão da sua turma e volte aqui.")

    if categoria:
        alvo = next((c for c in categorias if c["error_category"] == categoria), None)
        if not alvo:
            raise TreinoIndisponivel("Você não tem erros nessa categoria.")
    else:
        # Sem categoria pedida, vale o que já está pronto: a lista vem ordenada
        # pelo que ele mais erra, e entregar na hora um exercício da categoria
        # certa vale mais do que fazer o aluno esperar uma geração de outra.
        # A regra era a inversa antes de existir pré-geração, e nesse arranjo
        # ela passava por cima do exercício que já estava esperando.
        alvo = next((c for c in categorias if c["tem_pendente"]), categorias[0])

    pendente = (
        db.query(ExercicioGerado)
        .filter(ExercicioGerado.student_id == student.id,
                ExercicioGerado.error_category == alvo["error_category"],
```

por:

```python
    erros = _erros(student, db)
    if not erros:
        raise TreinoIndisponivel(
            "Você ainda não tem erros suficientes para a trilha. "
            "Resolva alguma questão da sua turma e volte aqui.")

    if categoria:
        # Pode ser um erro já superado: é o "Treinar de novo" da trilha.
        alvo = next((e for e in erros if e.categoria == categoria), None)
        if not alvo:
            raise TreinoIndisponivel("Você não tem erros nessa categoria.")
    else:
        ativos = [e for e in erros if e.ativo]
        if not ativos:
            raise TreinoIndisponivel(
                "Você superou todos os erros que repetia. "
                "Resolva uma questão da sua turma e volte aqui.")
        # Sem categoria pedida, vale o que já está pronto: a lista vem ordenada
        # pelo que ele mais erra, e entregar na hora um exercício da categoria
        # certa vale mais do que fazer o aluno esperar uma geração de outra.
        # A regra era a inversa antes de existir pré-geração, e nesse arranjo
        # ela passava por cima do exercício que já estava esperando.
        categorias = _categorias(ativos, student, db)
        pronta = next((c for c in categorias if c["tem_pendente"]), categorias[0])
        alvo = next(e for e in ativos if e.categoria == pronta["error_category"])

    pendente = (
        db.query(ExercicioGerado)
        .filter(ExercicioGerado.student_id == student.id,
                ExercicioGerado.error_category == alvo.categoria,
```

E, ainda em `gerar_para_categoria`, trocar:

```python
        exercicio = _gerar_e_salvar(student, alvo["error_category"], alvo["o_que_fazer"], db)
```

por:

```python
        exercicio = _gerar_e_salvar(student, alvo.categoria, alvo.o_que_fazer, db)
```

Em `preparar_proximo`, trocar:

```python
            diagnostico = next(
                (c["o_que_fazer"] for c in categorias_para_treinar(student, db)
                 if c["error_category"] == categoria), "")
```

por:

```python
            diagnostico = next(
                (e.o_que_fazer for e in _erros(student, db) if e.categoria == categoria), "")
```

Em `treinar`, trocar:

```python
    # Acabou de resolver: o próximo daquela categoria já começa a ser preparado,
    # então quando ele voltar à trilha não há espera.
    if acertou:
        preparar_proximo(student.id, exercicio.error_category)
```

por:

```python
    # Acabou de resolver: o erro do exercício passa a superado, então o próximo
    # a ficar pronto é o do primeiro erro que continua ativo. Assim, quando ele
    # voltar à trilha, não há espera.
    if acertou:
        proximo = next((e.categoria for e in _erros(student, db) if e.ativo), None)
        if proximo:
            preparar_proximo(student.id, proximo)
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_treino.py -q`
Esperado: PASSA

Rodar também: `/home/otavio/produtos-digitais-cs1/backend/venv/bin/ruff check --select F,E9,B --ignore B008,B904 backend/app/services/treino_service.py backend/app/services/student_activity_service.py backend/app/services/historico_do_aluno.py backend/app/services/funil_regras.py backend/app/services/funil_service.py`
Esperado: nada novo

- [ ] **Passo 5: rodar a suíte inteira e commitar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q 2>&1 | tail -3`
Esperado: 398 passando

```bash
/usr/bin/git add backend/app/services/treino_service.py backend/app/models/schemas.py backend/tests/test_treino.py
/usr/bin/git commit -m "feat(treino): trilha so com erros ativos, superados e pre-geracao do proximo"
```

### Task 8: treino e erros superados no progresso do aluno

**Arquivos:**
- Criar: `frontend/src/utils/datas.js`
- Alterar: `frontend/src/pages/aluno/ProgressoPage.jsx`

**Interfaces:**
- Consome: `GET /aluno/progresso` com `tentativas_no_treino`, e `GET /aluno/erros-recorrentes` com `erros[].no_treino` e `superados[]` (`error_category`, `total`, `superado_em`), de T5 e T6
- Produz: `dataCurta(iso: string) -> string` em `frontend/src/utils/datas.js`

- [ ] **Passo 1: criar o utilitário de data**

Criar `frontend/src/utils/datas.js`:

```js
// O backend manda o momento em ISO, e na tela só interessam o dia e o mês.
export function dataCurta(iso) {
  return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}
```

- [ ] **Passo 2: reescrever a página**

Trocar o conteúdo de `frontend/src/pages/aluno/ProgressoPage.jsx` por:

```jsx
import { useEffect, useState } from 'react'
import { getErrosRecorrentes, getProgresso } from '../../api/aluno'
import Badge from '../../components/Badge'
import BarList from '../../components/BarList'
import Spinner from '../../components/Spinner'
import { dataCurta } from '../../utils/datas'
import { shortError } from '../../utils/errorLabels'

const TENDENCIA = {
  melhorando: { label: 'melhorando', color: 'green' },
  piorando: { label: 'em alta', color: 'red' },
  estavel: { label: 'estável', color: 'gray' },
}

function Kpi({ label, value, sub }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value ?? '—'}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

function semanaLabel(iso) {
  const d = new Date(`${iso}T00:00:00`)
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}

export default function ProgressoPage() {
  const [progresso, setProgresso] = useState(null)
  const [erros, setErros] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getProgresso(), getErrosRecorrentes()])
      .then(([p, e]) => { setProgresso(p.data); setErros(e.data) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="w-6 h-6 text-purple-600" />
      </div>
    )
  }

  const semSubmissao = progresso.total_tentativas === 0
  const superados = erros.superados ?? []
  const noTreino = progresso.tentativas_no_treino > 0
    ? `, ${progresso.tentativas_no_treino} no treino`
    : ''

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Meu progresso</h1>
        <p className="text-sm text-gray-400 mt-0.5">
          O que suas tentativas mostram sobre o que você já domina e o que ainda trava.
        </p>
      </div>

      {semSubmissao ? (
        <div className="bg-white rounded-xl border border-dashed border-gray-200 p-10 text-center">
          <p className="text-sm text-gray-500">Você ainda não enviou nenhuma tentativa.</p>
          <p className="text-xs text-gray-400 mt-1">Resolva uma questão e o acompanhamento começa aqui.</p>
        </div>
      ) : (
        <>
          <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
            <Kpi
              label="Questões resolvidas"
              value={`${progresso.questoes_resolvidas}/${progresso.total_questoes}`}
              sub={`${progresso.atividades_concluidas} de ${progresso.total_atividades} atividades concluídas`}
            />
            <Kpi
              label="Tentativas até acertar"
              value={progresso.tentativas_por_questao_resolvida ?? '—'}
              sub="média nas questões e treinos que você resolveu"
            />
            <Kpi
              label="Acertos de primeira"
              value={progresso.acertos_de_primeira}
              sub="questões e treinos resolvidos no primeiro envio"
            />
            <Kpi
              label="Dias seguidos"
              value={progresso.dias_seguidos}
              sub={`${progresso.total_tentativas} tentativas no total${noTreino}`}
            />
          </div>

          {progresso.evolucao.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-1">Semana a semana</h2>
              <p className="text-xs text-gray-400 mb-4">
                Tentativas enviadas e o que você resolveu pela primeira vez, nas listas e no treino.
              </p>
              <BarList
                items={progresso.evolucao.map(p => ({
                  label: semanaLabel(p.periodo),
                  value: p.tentativas,
                  display: `${p.tentativas} · ${p.resolvidas}✓`,
                  title: `Semana de ${semanaLabel(p.periodo)}`,
                }))}
              />
            </div>
          )}
        </>
      )}

      <div>
        <h2 className="text-sm font-semibold text-gray-900 mb-1">Erros que se repetem</h2>
        <p className="text-xs text-gray-400 mb-3">
          {erros.total_com_erro} de {erros.total_submissoes} tentativas tiveram algum erro, somando listas e treino.
        </p>

        {erros.erros.length === 0 ? (
          <div className="bg-white rounded-xl border border-dashed border-gray-200 p-8 text-center">
            <p className="text-sm text-gray-500">
              {superados.length > 0 ? 'Nenhum erro se repetindo agora.' : 'Nenhum erro registrado ainda.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {erros.erros.map(e => {
              const tendencia = TENDENCIA[e.tendencia] ?? TENDENCIA.estavel
              return (
                <div key={e.error_category} className="bg-white rounded-xl border border-gray-200 p-5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900" title={e.error_category}>
                        {shortError(e.error_category)}
                      </span>
                      <Badge color={tendencia.color}>{tendencia.label}</Badge>
                    </div>
                    <span className="text-xs text-gray-400">
                      {e.total}×{e.no_treino > 0 ? ` · ${e.no_treino} no treino` : ''} · {e.recentes} nas últimas tentativas
                    </span>
                  </div>

                  {e.o_que_fazer && (
                    <div className="mt-3 rounded-lg bg-blue-50 border border-blue-100 px-4 py-2.5">
                      <p className="text-xs text-blue-700">{e.o_que_fazer}</p>
                    </div>
                  )}

                  {e.questoes.length > 0 && (
                    <p className="mt-2 text-xs text-gray-400">Aconteceu em: {e.questoes.join(' · ')}</p>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {superados.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-900 mb-1">Erros que você superou</h2>
          <p className="text-xs text-gray-400 mb-3">
            Você acertou um treino feito para eles depois da última vez que apareceram. Se um voltar, ele sobe para a lista de cima.
          </p>
          <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
            {superados.map(s => (
              <div key={s.error_category} className="flex flex-wrap items-center gap-2 px-5 py-3">
                <span className="text-sm text-gray-900" title={s.error_category}>
                  {shortError(s.error_category)}
                </span>
                <Badge color="green">superado</Badge>
                <span className="ml-auto text-xs text-gray-400">
                  em {dataCurta(s.superado_em)} · apareceu {s.total}×
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Passo 3: conferir lint e build**

Rodar: `cd frontend && npm run lint 2>&1 | tail -3`
Esperado: só os 4 erros antigos, em `QuestionPage.jsx` e `TestCasesPage.jsx`

Rodar: `cd frontend && npm run build 2>&1 | tail -3`
Esperado: build ok

- [ ] **Passo 4: commitar**

```bash
/usr/bin/git add frontend/src/utils/datas.js frontend/src/pages/aluno/ProgressoPage.jsx
/usr/bin/git commit -m "feat(frontend): treino e erros superados no progresso do aluno"
```

### Task 9: erros superados e "Treinar de novo" na trilha

**Arquivos:**
- Alterar: `frontend/src/pages/aluno/TreinoPage.jsx`

**Interfaces:**
- Consome: `GET /aluno/treino` com `superados[]` (`error_category`, `total`, `superado_em`), de T7. `dataCurta` de T8. O `gerar(categoria)` que a página já tem
- Produz: nada

- [ ] **Passo 1: reescrever a página**

Trocar o conteúdo de `frontend/src/pages/aluno/TreinoPage.jsx` por:

```jsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { gerarExercicio, getTrilha } from '../../api/aluno'
import Badge from '../../components/Badge'
import Spinner from '../../components/Spinner'
import { dataCurta } from '../../utils/datas'
import { shortError } from '../../utils/errorLabels'

/**
 * A trilha de treino. O painel de progresso já dizia ao aluno o que ele repete;
 * aqui ele treina exatamente isso, com exercício gerado sob medida e tentativas
 * ilimitadas. Nada daqui vale nota.
 */
export default function TreinoPage() {
  const [trilha, setTrilha] = useState(null)
  const [loading, setLoading] = useState(true)
  const [gerando, setGerando] = useState(null)
  const [erro, setErro] = useState('')

  const carregar = () => getTrilha().then(({ data }) => setTrilha(data))

  useEffect(() => {
    carregar().finally(() => setLoading(false))
  }, [])

  const gerar = async (categoria) => {
    setErro('')
    setGerando(categoria || 'auto')
    try {
      const { data } = await gerarExercicio(categoria)
      await carregar()
      window.location.assign(`/aluno/treino/${data.id}`)
    } catch (e) {
      setErro(e.response?.data?.detail || 'Não foi possível gerar agora.')
    } finally {
      setGerando(null)
    }
  }

  if (loading) {
    return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-purple-600" /></div>
  }

  const categorias = trilha?.categorias ?? []
  const superados = trilha?.superados ?? []
  const exercicios = trilha?.exercicios ?? []
  const pendentes = exercicios.filter(e => !e.resolvido)
  const resolvidos = exercicios.filter(e => e.resolvido)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Treino</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Exercícios feitos para o erro que você mais repete. Tentativas ilimitadas,
          e nada daqui entra na sua nota.
        </p>
      </div>

      {erro && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {erro}
        </div>
      )}

      {categorias.length === 0 && superados.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-sm">A trilha começa a partir dos seus erros.</p>
          <p className="text-xs mt-1">
            Resolva alguma questão da sua turma e volte aqui.
          </p>
          <Link to="/aluno/turmas" className="inline-block mt-4 text-sm text-purple-600 hover:text-purple-700">
            Ver minhas turmas
          </Link>
        </div>
      ) : (
        <>
          {pendentes.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Para resolver
              </h2>
              <div className="space-y-2">
                {pendentes.map(e => <CartaoExercicio key={e.id} exercicio={e} />)}
              </div>
            </div>
          )}

          {categorias.length > 0 ? (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                O que você mais erra
              </h2>
              <div className="space-y-2">
                {categorias.map(c => (
                  <div key={c.error_category} className="bg-white rounded-xl border border-gray-200 p-5">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge color="red">{shortError(c.error_category)}</Badge>
                      <span className="text-xs text-gray-400">
                        {c.ocorrencias}× nas suas tentativas
                      </span>
                      {c.exercicios_resolvidos > 0 && (
                        <span className="text-xs text-green-600">
                          · {c.exercicios_resolvidos} treino{c.exercicios_resolvidos !== 1 ? 's' : ''} resolvido{c.exercicios_resolvidos !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                    {c.o_que_fazer && (
                      <p className="text-sm text-gray-600 mt-2">{c.o_que_fazer}</p>
                    )}
                    <button
                      onClick={() => gerar(c.error_category)}
                      disabled={gerando != null}
                      className="mt-3 inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 transition-colors"
                    >
                      {gerando === c.error_category && <Spinner className="w-3.5 h-3.5" />}
                      {c.tem_pendente ? 'Continuar treinando' : 'Treinar isso'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-dashed border-gray-200 p-8 text-center">
              <p className="text-sm text-gray-500">Você superou todos os erros que repetia.</p>
              <p className="text-xs text-gray-400 mt-1">Resolva uma questão da sua turma e volte aqui.</p>
              <Link to="/aluno/turmas" className="inline-block mt-4 text-sm text-purple-600 hover:text-purple-700">
                Ver minhas turmas
              </Link>
            </div>
          )}

          {superados.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Erros que você superou
              </h2>
              <div className="space-y-2">
                {superados.map(s => (
                  <div key={s.error_category} className="bg-white rounded-xl border border-gray-200 p-5">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge color="green">{shortError(s.error_category)}</Badge>
                      <span className="text-xs text-gray-400">superado em {dataCurta(s.superado_em)}</span>
                    </div>
                    <button
                      onClick={() => gerar(s.error_category)}
                      disabled={gerando != null}
                      className="mt-3 inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-purple-200 text-purple-700 hover:bg-purple-50 disabled:opacity-40 transition-colors"
                    >
                      {gerando === s.error_category && <Spinner className="w-3.5 h-3.5" />}
                      Treinar de novo
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {resolvidos.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Já resolvidos
              </h2>
              <div className="space-y-2">
                {resolvidos.map(e => <CartaoExercicio key={e.id} exercicio={e} />)}
              </div>
            </div>
          )}

          <p className="text-xs text-gray-400">
            {trilha.geracoes_restantes_hoje > 0
              ? `Você pode gerar mais ${trilha.geracoes_restantes_hoje} exercício${trilha.geracoes_restantes_hoje !== 1 ? 's' : ''} hoje. Treinar nos que já estão aqui é ilimitado.`
              : 'Você atingiu o limite de exercícios novos por hoje. Treinar nos que já estão aqui continua liberado.'}
          </p>
        </>
      )}
    </div>
  )
}

function CartaoExercicio({ exercicio }) {
  return (
    <Link
      to={`/aluno/treino/${exercicio.id}`}
      className="block bg-white rounded-xl border border-gray-200 p-4 hover:border-purple-300 hover:shadow-sm transition-all"
    >
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm font-medium text-gray-900">{exercicio.titulo}</span>
        {exercicio.resolvido && <Badge color="green">resolvido</Badge>}
        <span className="ml-auto text-xs text-gray-400">
          {exercicio.tentativas} tentativa{exercicio.tentativas !== 1 ? 's' : ''}
        </span>
      </div>
      <p className="text-xs text-gray-400 mt-1">{shortError(exercicio.error_category)}</p>
    </Link>
  )
}
```

- [ ] **Passo 2: conferir lint e build**

Rodar: `cd frontend && npm run lint 2>&1 | tail -3`
Esperado: só os 4 erros antigos, em `QuestionPage.jsx` e `TestCasesPage.jsx`

Rodar: `cd frontend && npm run build 2>&1 | tail -3`
Esperado: build ok

- [ ] **Passo 3: commitar**

```bash
/usr/bin/git add frontend/src/pages/aluno/TreinoPage.jsx
/usr/bin/git commit -m "feat(frontend): erros superados e treinar de novo na trilha"
```
