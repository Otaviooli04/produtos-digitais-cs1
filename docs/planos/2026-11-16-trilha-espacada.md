# Trilha com revisão espaçada: plano de implementação

> **Para quem executa:** usar a skill `sdd` (recomendado) ou a execução sem subagentes descrita nela. Passos com caixa de seleção (`- [ ]`).

**Objetivo:** cada erro superado volta à trilha em 1, 6 e 15 dias, intercalado com os erros ativos, até ficar consolidado.

**Arquitetura:** a agenda é uma função pura sobre o histórico que já existe (`historico_do_aluno.py`), sem tabela nova. O `treino_service` usa a agenda para escolher o próximo exercício depois de um acerto, aquecer a trilha e gerar sem categoria, e devolve a agenda dos superados. O front só mostra o que a API manda.

**Stack:** FastAPI, SQLAlchemy, pytest, React 19 com Tailwind v4.

**Spec:** `docs/specs/2026-11-16-trilha-espacada.md`

## Restrições globais

- Intervalos: `INTERVALOS_DA_REVISAO = (1, 6, 15)`, em dias. Três revisões feitas = consolidado.
- Dia de Brasília: `dia_local(momento) = (momento - timedelta(hours=3)).date()`, com `momento` em UTC sem fuso (o formato do banco).
- Só o primeiro acerto de cada exercício da trilha conta, e só se o `alvo` é a categoria, a categoria do acerto é outra e o momento é depois do `superado_em`.
- "Era uma revisão": `erro.superado_em < tentativa.submitted_at`, com o erro calculado depois do commit da tentativa.
- Ordem do próximo depois de um acerto: se não era revisão, `vencidas + [primeiro ativo]`. Se era, `[primeiro ativo] + vencidas`. Vale o primeiro candidato sem exercício pendente (`tem_pendente`). Vencidas ordenadas por `dias_ate` crescente e depois pelo nome.
- Textos do aluno, exatos: `Hora de revisar`, `Revisar agora`, `Treinar de novo`, `Consolidado`, `Próxima revisão amanhã`, `Próxima revisão em N dias`, e o aviso `Revisão: você já superou este erro. Treinar de novo ajuda a ver se ele ficou para trás.`
- Sem migração, sem rota nova, sem chamada nova ao Gemini. Nada de "atrasado" nem contador de revisões vencidas.
- Testes: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest <alvo> -q`. Nunca `rtk pytest`.
- Git dentro do worktree: `/usr/bin/git`, um comando por chamada, sem `$(...)`.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/services/calendario.py` | Alterar: `dia_local`, a data de Brasília de um momento em UTC |
| `backend/app/services/historico_do_aluno.py` | Alterar: `INTERVALOS_DA_REVISAO`, `Revisao` e `agenda_de_revisao`, puras |
| `backend/tests/unit/test_agenda_de_revisao.py` | Criar: testes puros da agenda e do `dia_local` |
| `backend/app/models/schemas.py` | Alterar: `RevisaoDoErro`, `ErroSuperado.revisao`, `ExercicioDetalhe.revisao` |
| `backend/app/services/treino_service.py` | Alterar: agenda na trilha, aquecimento, gerar sem categoria, `revisao` no detalhe e escolha do próximo no `treinar` |
| `backend/tests/test_treino.py` | Alterar: classe `TestRevisaoEspacada` no fim |
| `frontend/src/pages/aluno/TreinoPage.jsx` | Alterar: situação da revisão e botão nos superados |
| `frontend/src/pages/aluno/ExercicioTreinoPage.jsx` | Alterar: aviso de revisão |
| `HANDOFF.md`, `docs/mapa-funcionalidades.md` | Alterar: registrar a trilha espaçada |

## Lotes

- Lote A, Task 1: agenda pura e dia de Brasília (backend, regra pura)
- Lote B, Tasks 2 e 3: agenda na trilha, no detalhe e na geração, e escolha do próximo depois do acerto (backend, serviço)
- Lote C, Tasks 4 e 5: telas da trilha e do exercício, e documentação (front e docs)

## Varredura

### Pares que dividem arquivo ou interface

| Par | O que uma produz x o que a outra consome | Situação |
|---|---|---|
| T1 → T2 | `agenda_de_revisao(erro, envios, hoje) -> Revisao | None`, `Revisao.feitas/proxima_em/dias_ate/vencida/consolidado`, `dia_local(momento) -> date` usados por `_revisoes` e `_revisao_dict` | bate |
| T2 → T3 | `_historico_e_erros`, `_revisoes`, `_revisoes_vencidas`, `_primeiro_sem_pendente` criados na T2 e usados por `_proximo_depois_do_acerto` na T3 | bate |
| T2 → T4 | `superados[].revisao` com `feitas`, `proxima_em`, `dias_ate`, `vencida`, `consolidado`, e `ExercicioDetalhe.revisao` lidos pelas telas | bate |
| T2 x T3 | as duas mexem em `treino_service.py`: T2 em `trilha`, `gerar_para_categoria`, `_exercicio_detalhe` e helpers novos, T3 só no bloco `if acertou:` do `treinar` e numa função nova | sem conflito |
| T2 x T3 | as duas acrescentam testes à classe `TestRevisaoEspacada` em `test_treino.py`, T2 cria a classe e o helper `_superou`, T3 acrescenta métodos | bate, T3 depende da T2 |

### O teste de cada tarefa bate com o código dela?

| Tarefa | Conferência | Situação |
|---|---|---|
| T1 | 13 testes. Datas às 15h UTC (12h de Brasília) para não cair na virada. Superado dia 2: vence dia 3 (2+1), revisão dia 3 vence dia 9 (3+6), revisão dia 9 vence dia 24 (9+15). Superado 01h UTC de 17/11 é dia 16 em Brasília e vence 17. 652 + 13 = 665 | bate |
| T2 | 4 testes. `_superou` grava erro na lista e acerto na trilha N dias atrás, então com N=3 a 1ª revisão venceu há 2 dias (`dias_ate` = -2) e com N=0 vence amanhã (`dias_ate` = 1). Os testes antigos de "tudo superado" superam no próprio dia, então não há revisão vencida e o aviso continua. 665 + 4 = 669 | bate |
| T3 | 6 testes. O acerto que supera o erro ativo tem `superado_em` igual ao `submitted_at` e não é revisão. Revisão de X superado há 3 dias tem `superado_em` 3 dias antes. Duas vencidas: superada há 5 dias tem `dias_ate` -4 e vem antes da de 3 dias (-2). 669 + 6 = 675 | bate |
| T4 | Sem suíte de front: lint e build. Textos conferidos contra as restrições globais | bate |
| T5 | Só documentação | bate |

---

### Task 1: agenda pura e dia de Brasília

**Arquivos:**
- Alterar: `backend/app/services/calendario.py`
- Alterar: `backend/app/services/historico_do_aluno.py`
- Criar: `backend/tests/unit/test_agenda_de_revisao.py`

**Interfaces:**
- Consome: `Envio`, `Erro`, `erros_do_aluno`, `TRILHA`, `ACERTO` de `historico_do_aluno.py`
- Produz: `dia_local(momento: datetime) -> date` em `calendario.py`. `INTERVALOS_DA_REVISAO`, `Revisao(feitas: int, proxima_em: date | None, dias_ate: int | None)` com as propriedades `consolidado` e `vencida`, e `agenda_de_revisao(erro: Erro, envios: list[Envio], hoje: date) -> Revisao | None` em `historico_do_aluno.py`

- [ ] **Passo 1: escrever os testes que falham**

Criar `backend/tests/unit/test_agenda_de_revisao.py`:

```python
from datetime import date, datetime, timedelta

from app.services.calendario import dia_local
from app.services.historico_do_aluno import (
    ACERTO, ERRO, LISTA, TRILHA, Envio, agenda_de_revisao, erros_do_aluno,
)

CAT = "Acesso Fora dos Limites: Off-by-One"


def _dia(d, hora=15):
    """15h UTC é meio-dia em Brasília, longe da virada do dia."""
    return datetime(2026, 11, d, hora)


def _erro_na_lista(momento):
    return Envio(origem=LISTA, item_id=1, momento=momento, categoria=CAT, resultado=ERRO)


def _acerto_na_trilha(exercicio, momento, categoria="Correto"):
    return Envio(origem=TRILHA, item_id=exercicio, momento=momento, categoria=categoria,
                 resultado=ACERTO, alvo=CAT, titulo="Soma")


def _erro_na_trilha(exercicio, momento):
    return Envio(origem=TRILHA, item_id=exercicio, momento=momento, categoria=CAT,
                 resultado=ERRO, alvo=CAT, titulo="Soma")


def _agenda(envios, hoje):
    erro = next(e for e in erros_do_aluno(envios) if e.categoria == CAT)
    return agenda_de_revisao(erro, envios, hoje)


def test_dia_local_e_o_dia_de_brasilia():
    assert dia_local(datetime(2026, 11, 17, 1, 0)) == date(2026, 11, 16)
    assert dia_local(datetime(2026, 11, 17, 3, 0)) == date(2026, 11, 17)


def test_primeira_revisao_vence_no_dia_seguinte():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2))]
    no_dia = _agenda(envios, date(2026, 11, 2))
    assert (no_dia.feitas, no_dia.proxima_em, no_dia.dias_ate) == (0, date(2026, 11, 3), 1)
    assert not no_dia.vencida
    assert _agenda(envios, date(2026, 11, 3)).vencida


def test_dia_conta_pelo_horario_de_brasilia():
    """Superado às 22h de Brasília do dia 16, que já é dia 17 em UTC."""
    envios = [_erro_na_lista(datetime(2026, 11, 16, 10)),
              _acerto_na_trilha(10, datetime(2026, 11, 17, 1, 0))]
    agenda = _agenda(envios, date(2026, 11, 17))
    assert agenda.proxima_em == date(2026, 11, 17)
    assert agenda.vencida


def test_acerto_antes_do_vencimento_nao_conta():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(11, _dia(2, hora=17))]
    agenda = _agenda(envios, date(2026, 11, 3))
    assert agenda.feitas == 0
    assert agenda.vencida


def test_acerto_depois_do_vencimento_conta():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(11, _dia(3))]
    agenda = _agenda(envios, date(2026, 11, 3))
    assert (agenda.feitas, agenda.proxima_em, agenda.dias_ate) == (1, date(2026, 11, 9), 6)


def test_tres_revisoes_consolidam():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(11, _dia(3)), _acerto_na_trilha(12, _dia(9)),
              _acerto_na_trilha(13, _dia(24))]
    agenda = _agenda(envios, date(2026, 11, 30))
    assert agenda.feitas == 3
    assert agenda.consolidado
    assert agenda.proxima_em is None and agenda.dias_ate is None
    assert not agenda.vencida


def test_refazer_exercicio_resolvido_antes_do_vencimento_nao_conta():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(11, _dia(2, hora=17)), _acerto_na_trilha(11, _dia(3))]
    assert _agenda(envios, date(2026, 11, 3)).feitas == 0


def test_refazer_o_exercicio_que_superou_nao_conta():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(10, _dia(3))]
    assert _agenda(envios, date(2026, 11, 3)).feitas == 0


def test_acerto_com_a_propria_categoria_nao_conta():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(11, _dia(3), categoria=CAT)]
    assert _agenda(envios, date(2026, 11, 3)).feitas == 0


def test_revisao_que_repete_o_erro_volta_a_ativo():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _erro_na_trilha(11, _dia(3))]
    assert _agenda(envios, date(2026, 11, 3)) is None


def test_superado_de_novo_recomeca_a_agenda():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(11, _dia(3)), _erro_na_lista(_dia(4)),
              _acerto_na_trilha(12, _dia(5))]
    agenda = _agenda(envios, date(2026, 11, 5))
    assert (agenda.feitas, agenda.proxima_em) == (0, date(2026, 11, 6))


def test_sem_a_tentativa_reportada_a_revisao_some():
    """Tentativa de exercício reportado não entra no histórico (`ler_historico`)."""
    com = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
           _acerto_na_trilha(11, _dia(3))]
    sem = com[:2]
    assert _agenda(com, date(2026, 11, 3)).feitas == 1
    assert _agenda(sem, date(2026, 11, 3)).feitas == 0


def test_erro_ativo_nao_tem_agenda():
    assert _agenda([_erro_na_lista(_dia(1))], date(2026, 11, 3)) is None
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/unit/test_agenda_de_revisao.py -q`
Esperado: ERRO de coleta com `ImportError` em `dia_local`

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/calendario.py`, trocar a linha `from datetime import datetime, timedelta` por `from datetime import date, datetime, timedelta` e acrescentar depois de `semana_iso`:

```python
def dia_local(momento: datetime) -> date:
    """A data em Brasília (UTC−3, sem horário de verão desde 2019) de um momento
    em UTC sem fuso, que é como o banco guarda. É o "amanhã" que o aluno entende."""
    return (momento - timedelta(hours=3)).date()
```

Em `backend/app/services/historico_do_aluno.py`, trocar `from app.services.calendario import semana_iso` por `from app.services.calendario import dia_local, semana_iso` e acrescentar logo depois da função `superados`:

```python
# Os três primeiros intervalos do SM-2 com facilidade 2,5. Três sessões espaçadas
# dão quase todo o ganho da reaprendizagem sucessiva, e cada uma custa uma geração.
INTERVALOS_DA_REVISAO = (1, 6, 15)


@dataclass(frozen=True)
class Revisao:
    """A agenda de um erro superado. `dias_ate` é zero ou negativo quando venceu."""
    feitas: int
    proxima_em: date | None
    dias_ate: int | None

    @property
    def consolidado(self) -> bool:
        return self.proxima_em is None

    @property
    def vencida(self) -> bool:
        return self.dias_ate is not None and self.dias_ate <= 0


def agenda_de_revisao(erro: Erro, envios: list[Envio], hoje: date) -> Revisao | None:
    """Quantas revisões do erro superado já foram feitas e quando vence a próxima.

    Revisão é o primeiro acerto de um exercício da trilha feito para o erro, sem
    repeti-lo, numa data a partir do vencimento da vez. Refazer um exercício já
    resolvido não conta, senão o aluno consolidaria o erro refazendo o mesmo
    exercício nas datas certas. Erro ativo não tem agenda."""
    if erro.ativo:
        return None
    primeiros: dict[tuple[str, int], Envio] = {}
    for e in envios:
        if e.origem == TRILHA and e.resultado == ACERTO and e.item not in primeiros:
            primeiros[e.item] = e

    marco = dia_local(erro.superado_em)
    feitas = 0
    for e in primeiros.values():
        if feitas == len(INTERVALOS_DA_REVISAO):
            break
        if (e.alvo != erro.categoria or e.categoria == erro.categoria
                or e.momento <= erro.superado_em):
            continue
        dia = dia_local(e.momento)
        if dia >= marco + timedelta(days=INTERVALOS_DA_REVISAO[feitas]):
            feitas += 1
            marco = dia

    if feitas == len(INTERVALOS_DA_REVISAO):
        return Revisao(feitas, None, None)
    proxima = marco + timedelta(days=INTERVALOS_DA_REVISAO[feitas])
    return Revisao(feitas, proxima, (proxima - hoje).days)
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2, e depois a suíte inteira `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q`
Esperado: 13 passam, e a suíte com 665

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/calendario.py backend/app/services/historico_do_aluno.py backend/tests/unit/test_agenda_de_revisao.py
/usr/bin/git commit -m "feat(trilha): agenda de revisao espacada dos erros superados"
```

---

### Task 2: agenda na trilha, no detalhe e na geração sem categoria

**Arquivos:**
- Alterar: `backend/app/models/schemas.py:772-776` (`ErroSuperado`) e `backend/app/models/schemas.py:839-846` (`ExercicioDetalhe`)
- Alterar: `backend/app/services/treino_service.py` (imports, `trilha`, `gerar_para_categoria`, `_exercicio_detalhe` e helpers novos)
- Teste: `backend/tests/test_treino.py` (classe nova no fim)

**Interfaces:**
- Consome: `agenda_de_revisao`, `Revisao`, `dia_local` da Task 1
- Produz, em `treino_service.py`:
  - `_historico_e_erros(student, db) -> tuple[list[Envio], list[Erro]]`
  - `_revisoes(erros: list[Erro], envios: list[Envio]) -> dict[str, Revisao]`
  - `_revisoes_vencidas(revisoes: dict[str, Revisao]) -> list[str]`, da vencida há mais tempo para a mais recente
  - `_primeiro_sem_pendente(student_id: int, candidatos: list[str], db) -> str | None`
  - `trilha(...)["superados"][i]["revisao"]` com `feitas`, `proxima_em` (ISO ou `None`), `dias_ate`, `vencida`, `consolidado`
  - `_exercicio_detalhe(...)["revisao"]: bool`
- Produz, em `test_treino.py`: `_superou(db, aluno, exam, categoria, dias_atras) -> ExercicioGerado` e `_errou(db, aluno, exam, categoria)`

- [ ] **Passo 1: escrever os testes que falham**

Acrescentar ao fim de `backend/tests/test_treino.py`:

```python
def _superou(db, aluno, exam, categoria, dias_atras):
    """Erro na lista e, uma hora depois, o acerto na trilha que o supera, tudo
    `dias_atras` dias antes de agora. Devolve o exercício resolvido."""
    quando = agora_utc() - timedelta(days=dias_atras)
    db.add(Submission(
        question_id=exam.questions[0].id, code="int main(){}", error_category=categoria,
        all_tests_passed=False, student_id=aluno.id, submitted_at=quando - timedelta(hours=1)))
    exercicio = ExercicioGerado(
        student_id=aluno.id, error_category=categoria, titulo="Soma",
        enunciado="Some os n primeiros inteiros.",
        casos_teste=[{"input": "3", "expected_output": "6"}],
        resolvido=True, created_at=quando - timedelta(minutes=30))
    db.add(exercicio)
    db.flush()
    db.add(TentativaDeTreino(
        exercicio_id=exercicio.id, student_id=aluno.id, code="int main(){}",
        all_tests_passed=True, error_category="Correto", submitted_at=quando))
    db.commit()
    return exercicio


def _errou(db, aluno, exam, categoria):
    db.add(Submission(
        question_id=exam.questions[0].id, code="int main(){}", error_category=categoria,
        all_tests_passed=False, student_id=aluno.id, submitted_at=agora_utc()))
    db.commit()


def _pendente_de(db, aluno, categoria):
    exercicio = ExercicioGerado(
        student_id=aluno.id, error_category=categoria, titulo="Pendente",
        enunciado="Some os n primeiros inteiros.",
        casos_teste=[{"input": "3", "expected_output": "6"}], created_at=agora_utc())
    db.add(exercicio)
    db.commit()
    return exercicio


class TestRevisaoEspacada:
    """Erro superado volta à trilha em 1, 6 e 15 dias, intercalado com os ativos."""

    X = "Tudo no Main"
    W = "Recursão Faltando"
    Y = "Acesso Fora dos Limites: Off-by-One"
    Z = "Saída Incorreta"

    def test_trilha_devolve_a_agenda_com_os_vencidos_primeiro(
        self, db, aluno, exam_factory, pre_geracoes
    ):
        from app.services.treino_service import trilha

        exam = exam_factory(questions=[{"number": "1"}])
        _superou(db, aluno, exam, self.W, dias_atras=0)
        _superou(db, aluno, exam, self.X, dias_atras=3)

        superados = trilha(aluno, db)["superados"]
        assert [s["error_category"] for s in superados] == [self.X, self.W]
        assert superados[0]["revisao"] == {
            "feitas": 0, "proxima_em": superados[0]["revisao"]["proxima_em"],
            "dias_ate": -2, "vencida": True, "consolidado": False}
        assert superados[1]["revisao"]["dias_ate"] == 1
        assert superados[1]["revisao"]["vencida"] is False

    def test_trilha_sem_erro_ativo_aquece_a_revisao_vencida(
        self, db, aluno, exam_factory, pre_geracoes
    ):
        from app.services.treino_service import trilha

        exam = exam_factory(questions=[{"number": "1"}])
        _superou(db, aluno, exam, self.X, dias_atras=3)
        trilha(aluno, db)
        assert pre_geracoes == [self.X]

    def test_gerar_sem_categoria_e_sem_ativo_usa_a_revisao_vencida(
        self, db, aluno, exam_factory, gemini_ok
    ):
        from app.services.treino_service import gerar_para_categoria

        exam = exam_factory(questions=[{"number": "1"}])
        _superou(db, aluno, exam, self.X, dias_atras=3)
        exercicio = gerar_para_categoria(aluno, None, db)
        assert exercicio["error_category"] == self.X
        assert exercicio["revisao"] is True

    def test_detalhe_traz_revisao_so_para_categoria_superada(self, db, aluno, exam_factory):
        from app.services.treino_service import detalhe

        exam = exam_factory(questions=[{"number": "1"}])
        resolvido = _superou(db, aluno, exam, self.X, dias_atras=3)
        _errou(db, aluno, exam, self.Z)
        do_ativo = _pendente_de(db, aluno, self.Z)

        assert detalhe(aluno, resolvido.id, db)["revisao"] is True
        assert detalhe(aluno, do_ativo.id, db)["revisao"] is False
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_treino.py::TestRevisaoEspacada -q`
Esperado: 4 FALHAS, por `KeyError: 'revisao'`, ordem dos superados, `pre_geracoes == []` e `TreinoIndisponivel` no gerar

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/models/schemas.py`, trocar a classe `ErroSuperado` por:

```python
class RevisaoDoErro(BaseModel):
    feitas: int
    proxima_em: Optional[str] = None  # ISO, data de Brasília
    dias_ate: Optional[int] = None    # zero ou negativo quando venceu
    vencida: bool = False
    consolidado: bool = False


class ErroSuperado(BaseModel):
    error_category: str
    total: int
    superado_em: str  # ISO, como ultima_ocorrencia
    # Só a trilha preenche. Os erros recorrentes não mostram a agenda.
    revisao: Optional[RevisaoDoErro] = None
```

E em `ExercicioDetalhe`, depois de `reaproveitado: bool = False`, acrescentar:

```python
    # True quando a categoria do exercício já foi superada: é uma revisão.
    revisao: bool = False
```

Em `backend/app/services/treino_service.py`:

1. Trocar o bloco de import de `historico_do_aluno` por:

```python
from app.services.calendario import dia_local
from app.services.historico_do_aluno import (
    ACERTO, FALHA, Envio, Erro, Revisao, agenda_de_revisao, erros_do_aluno, ler_historico,
    resultado_da_trilha, superados,
)
```

2. Logo depois da função `_erros`, acrescentar:

```python
def _historico_e_erros(student: Student, db: Session) -> tuple[list[Envio], list[Erro]]:
    """O histórico e os erros lidos uma vez, porque a agenda precisa dos dois."""
    envios = ler_historico(student, db)
    return envios, erros_do_aluno(envios)


def _revisoes(erros: list[Erro], envios: list[Envio]) -> dict[str, Revisao]:
    hoje = dia_local(agora_utc())
    return {e.categoria: agenda_de_revisao(e, envios, hoje) for e in erros if not e.ativo}


def _revisoes_vencidas(revisoes: dict[str, Revisao]) -> list[str]:
    """Da que venceu há mais tempo para a mais recente, e depois pelo nome."""
    vencidas = sorted((r.dias_ate, categoria) for categoria, r in revisoes.items() if r.vencida)
    return [categoria for _, categoria in vencidas]


def _primeiro_sem_pendente(student_id: int, candidatos: list[str], db: Session) -> str | None:
    return next((c for c in candidatos if not tem_pendente(student_id, c, db)), None)


def _revisao_dict(r: Revisao) -> dict:
    return {
        "feitas": r.feitas,
        "proxima_em": r.proxima_em.isoformat() if r.proxima_em else None,
        "dias_ate": r.dias_ate,
        "vencida": r.vencida,
        "consolidado": r.consolidado,
    }


def _superados_com_agenda(erros: list[Erro], revisoes: dict[str, Revisao]) -> list[dict]:
    """Os vencidos primeiro, sem dizer há quanto tempo: nada de pilha de atrasados."""
    lista = [{**s, "revisao": _revisao_dict(revisoes[s["error_category"]])}
             for s in superados(erros)]
    return sorted(lista, key=lambda s: not s["revisao"]["vencida"])
```

3. Trocar a função `trilha` inteira por:

```python
def trilha(student: Student, db: Session) -> dict:
    envios, erros = _historico_e_erros(student, db)
    revisoes = _revisoes(erros, envios)
    categorias = _categorias([e for e in erros if e.ativo], student, db)
    # Aquece a categoria que ele mais erra, que é a que o botão grande oferece.
    # Sem exercício pendente ali, o primeiro clique esperaria o Gemini. Sem erro
    # ativo, o botão grande vira a revisão vencida, e é ela que fica pronta.
    if categorias:
        if not categorias[0]["tem_pendente"]:
            preparar_proximo(student.id, categorias[0]["error_category"])
    else:
        vencida = _primeiro_sem_pendente(student.id, _revisoes_vencidas(revisoes), db)
        if vencida:
            preparar_proximo(student.id, vencida)

    exercicios = (
        db.query(ExercicioGerado)
        .filter(ExercicioGerado.student_id == student.id,
                ExercicioGerado.reportado.is_(False))
        .order_by(ExercicioGerado.created_at.desc())
        .all()
    )
    return {
        "categorias": categorias,
        "superados": _superados_com_agenda(erros, revisoes),
        "exercicios": [_exercicio_resumo(e) for e in exercicios],
        "geracoes_restantes_hoje": _restantes_hoje(student, db),
    }
```

4. Em `gerar_para_categoria`, trocar a linha `    erros = _erros(student, db)` por `    envios, erros = _historico_e_erros(student, db)` e trocar o bloco `else:` inteiro (de `        ativos = [e for e in erros if e.ativo]` até `        alvo = next(e for e in ativos if e.categoria == pronta["error_category"])`) por:

```python
    else:
        ativos = [e for e in erros if e.ativo]
        if ativos:
            # Sem categoria pedida, vale o que já está pronto: a lista vem ordenada
            # pelo que ele mais erra, e entregar na hora um exercício da categoria
            # certa vale mais do que fazer o aluno esperar uma geração de outra.
            # A regra era a inversa antes de existir pré-geração, e nesse arranjo
            # ela passava por cima do exercício que já estava esperando.
            categorias = _categorias(ativos, student, db)
            pronta = next((c for c in categorias if c["tem_pendente"]), categorias[0])
            alvo = next(e for e in ativos if e.categoria == pronta["error_category"])
        else:
            vencidas = _revisoes_vencidas(_revisoes(erros, envios))
            if not vencidas:
                raise TreinoIndisponivel(
                    "Você superou todos os erros que repetia. "
                    "Resolva uma questão da sua turma e volte aqui.")
            pronta = next((c for c in vencidas if tem_pendente(student.id, c, db)), vencidas[0])
            alvo = next(e for e in erros if e.categoria == pronta)
```

5. Trocar `_exercicio_detalhe` inteira por:

```python
def _e_revisao(e: ExercicioGerado, db: Session) -> bool:
    student = db.get(Student, e.student_id)
    erro = next((x for x in _erros(student, db) if x.categoria == e.error_category), None)
    return bool(erro and not erro.ativo)


def _exercicio_detalhe(e: ExercicioGerado, db: Session, reaproveitado: bool = False) -> dict:
    tentativas = sorted(e.tentativas, key=lambda t: t.attempt_number, reverse=True)
    return {
        **_exercicio_resumo(e),
        "enunciado": e.enunciado,
        "required_structures": e.required_structures or [],
        "total_testes": len(e.casos_teste or []),
        "reaproveitado": reaproveitado,
        "revisao": _e_revisao(e, db),
        "tentativas_lista": [_tentativa_dict(t) for t in tentativas],
    }
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2, e depois a suíte inteira `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q`
Esperado: 4 passam, e a suíte com 669

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/models/schemas.py backend/app/services/treino_service.py backend/tests/test_treino.py
/usr/bin/git commit -m "feat(trilha): agenda dos superados na trilha, no detalhe e na geracao"
```

---

### Task 3: próximo exercício depois do acerto

**Arquivos:**
- Alterar: `backend/app/services/treino_service.py` (bloco `if acertou:` do `treinar` e função nova)
- Teste: `backend/tests/test_treino.py` (métodos novos em `TestRevisaoEspacada`)

**Interfaces:**
- Consome: `_historico_e_erros`, `_revisoes`, `_revisoes_vencidas`, `_primeiro_sem_pendente` da Task 2. Nos testes, `_superou`, `_errou` e `_pendente_de` da Task 2
- Produz: `_proximo_depois_do_acerto(student, exercicio: ExercicioGerado, momento: datetime, db) -> str | None`

- [ ] **Passo 1: escrever os testes que falham**

Acrescentar dentro da classe `TestRevisaoEspacada`, no fim de `backend/tests/test_treino.py`:

```python
    @pytest.fixture()
    def acerta(self, monkeypatch):
        from app.services import treino_service

        monkeypatch.setattr(treino_service, "evaluate_code",
                            lambda *a, **k: _resultado_referencia([True]))

    def test_acerto_num_erro_ativo_prepara_a_revisao_vencida(
        self, db, aluno, exam_factory, pre_geracoes, acerta
    ):
        from app.services.treino_service import treinar

        exam = exam_factory(questions=[{"number": "1"}])
        _superou(db, aluno, exam, self.X, dias_atras=3)
        _errou(db, aluno, exam, self.Y)
        _errou(db, aluno, exam, self.Z)
        exercicio = _pendente_de(db, aluno, self.Y)

        treinar(aluno, exercicio.id, "int main(){}", db)
        assert pre_geracoes == [self.X]

    def test_acerto_numa_revisao_prepara_o_erro_ativo(
        self, db, aluno, exam_factory, pre_geracoes, acerta
    ):
        from app.services.treino_service import treinar

        exam = exam_factory(questions=[{"number": "1"}])
        _superou(db, aluno, exam, self.X, dias_atras=3)
        _superou(db, aluno, exam, self.W, dias_atras=5)
        _errou(db, aluno, exam, self.Z)
        revisao = _pendente_de(db, aluno, self.X)

        treinar(aluno, revisao.id, "int main(){}", db)
        assert pre_geracoes == [self.Z]

    def test_acerto_numa_revisao_sem_ativo_prepara_outra_revisao(
        self, db, aluno, exam_factory, pre_geracoes, acerta
    ):
        from app.services.treino_service import treinar

        exam = exam_factory(questions=[{"number": "1"}])
        _superou(db, aluno, exam, self.X, dias_atras=3)
        _superou(db, aluno, exam, self.W, dias_atras=5)
        revisao = _pendente_de(db, aluno, self.X)

        treinar(aluno, revisao.id, "int main(){}", db)
        assert pre_geracoes == [self.W]

    def test_entre_duas_vencidas_vem_a_mais_antiga(
        self, db, aluno, exam_factory, pre_geracoes, acerta
    ):
        from app.services.treino_service import treinar

        exam = exam_factory(questions=[{"number": "1"}])
        _superou(db, aluno, exam, self.X, dias_atras=3)
        _superou(db, aluno, exam, self.W, dias_atras=5)
        _errou(db, aluno, exam, self.Y)
        exercicio = _pendente_de(db, aluno, self.Y)

        treinar(aluno, exercicio.id, "int main(){}", db)
        assert pre_geracoes == [self.W]

    def test_vencida_com_pendente_e_pulada_pela_proxima_vencida(
        self, db, aluno, exam_factory, pre_geracoes, acerta
    ):
        from app.services.treino_service import treinar

        exam = exam_factory(questions=[{"number": "1"}])
        _superou(db, aluno, exam, self.X, dias_atras=3)
        _superou(db, aluno, exam, self.W, dias_atras=5)
        _pendente_de(db, aluno, self.W)
        _errou(db, aluno, exam, self.Y)
        _errou(db, aluno, exam, self.Z)
        exercicio = _pendente_de(db, aluno, self.Y)

        treinar(aluno, exercicio.id, "int main(){}", db)
        assert pre_geracoes == [self.X]

    def test_vencida_com_pendente_e_pulada_pelo_erro_ativo(
        self, db, aluno, exam_factory, pre_geracoes, acerta
    ):
        from app.services.treino_service import treinar

        exam = exam_factory(questions=[{"number": "1"}])
        _superou(db, aluno, exam, self.X, dias_atras=3)
        _pendente_de(db, aluno, self.X)
        _errou(db, aluno, exam, self.Y)
        _errou(db, aluno, exam, self.Z)
        exercicio = _pendente_de(db, aluno, self.Y)

        treinar(aluno, exercicio.id, "int main(){}", db)
        assert pre_geracoes == [self.Z]
```

- [ ] **Passo 2: rodar e ver falhar**

Rodar: `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/test_treino.py::TestRevisaoEspacada -q`
Esperado: os 4 da Task 2 passam e os 6 novos FALHAM, porque o código de hoje prepara sempre o primeiro erro ativo (por exemplo `[self.Z] != [self.X]`, e `[] != [self.W]` quando não há ativo)

- [ ] **Passo 3: escrever o mínimo para passar**

Em `backend/app/services/treino_service.py`, trocar o bloco do `treinar`:

```python
    # Acabou de resolver: o próximo a ficar pronto é o do primeiro erro que
    # continua ativo, que em geral já não é o deste exercício. Assim, quando
    # ele voltar à trilha, não há espera.
    if acertou:
        proximo = next((e.categoria for e in _erros(student, db) if e.ativo), None)
        if proximo:
            preparar_proximo(student.id, proximo)
```

por:

```python
    # Acabou de resolver: o próximo já fica pronto para não haver espera quando
    # ele voltar à trilha. Revisão vencida e erro ativo se alternam.
    if acertou:
        proximo = _proximo_depois_do_acerto(student, exercicio, tentativa.submitted_at, db)
        if proximo:
            preparar_proximo(student.id, proximo)
```

E acrescentar logo antes de `def treinar`:

```python
def _proximo_depois_do_acerto(student: Student, exercicio: ExercicioGerado,
                              momento: datetime, db: Session) -> str | None:
    """A revisão vencida há mais tempo e o primeiro erro ativo se alternam: depois
    de uma revisão vem o erro ativo, e depois de qualquer outro acerto vem a
    revisão. Duas revisões seguidas só sem erro ativo.

    Era revisão quando o erro do exercício já estava superado antes deste acerto.
    O acerto que supera um erro ativo tem `superado_em` igual ao próprio momento."""
    envios, erros = _historico_e_erros(student, db)
    vencidas = _revisoes_vencidas(_revisoes(erros, envios))
    ativo = [e.categoria for e in erros if e.ativo][:1]
    erro = next((e for e in erros if e.categoria == exercicio.error_category), None)
    era_revisao = bool(erro and not erro.ativo and erro.superado_em < momento)
    candidatos = ativo + vencidas if era_revisao else vencidas + ativo
    return _primeiro_sem_pendente(student.id, candidatos, db)
```

- [ ] **Passo 4: rodar e ver passar**

Rodar: o mesmo comando do passo 2, e depois a suíte inteira `cd backend && /home/otavio/produtos-digitais-cs1/backend/venv/bin/python -m pytest tests/ --ignore=tests/integration -q`
Esperado: os 10 da classe passam, e a suíte com 675. Os testes antigos de `TestPreGeracao` continuam passando: `test_resolver_prepara_o_proximo_erro_ativo` não tem superado vencido, e `test_resolver_o_ultimo_erro_ativo_nao_prepara_nada` supera no próprio dia.

- [ ] **Passo 5: commitar**

```bash
/usr/bin/git add backend/app/services/treino_service.py backend/tests/test_treino.py
/usr/bin/git commit -m "feat(trilha): revisao vencida e erro ativo se alternam depois do acerto"
```

---

### Task 4: telas da trilha e do exercício

**Arquivos:**
- Alterar: `frontend/src/pages/aluno/TreinoPage.jsx` (seção "Erros que você superou")
- Alterar: `frontend/src/pages/aluno/ExercicioTreinoPage.jsx` (depois do aviso de `reaproveitado`)

**Interfaces:**
- Consome: `trilha.superados[].revisao` (`feitas`, `proxima_em`, `dias_ate`, `vencida`, `consolidado`) e `exercicio.revisao` da Task 2

- [ ] **Passo 1: a situação da revisão na trilha**

Em `frontend/src/pages/aluno/TreinoPage.jsx`, acrescentar logo antes de `export default function TreinoPage()`:

```jsx
function situacaoDaRevisao(revisao) {
  if (!revisao) return ''
  if (revisao.consolidado) return 'Consolidado'
  if (revisao.vencida) return 'Hora de revisar'
  return revisao.dias_ate === 1
    ? 'Próxima revisão amanhã'
    : `Próxima revisão em ${revisao.dias_ate} dias`
}
```

E trocar o bloco do cartão de cada superado:

```jsx
                {superados.map(s => (
                  <Card key={s.error_category} className="gap-2!">
                    <div className="flex flex-wrap items-center gap-2">
                      <Tag variante="sucesso">{shortError(s.error_category)}</Tag>
                      <span className="text-xs text-cinza-texto">superado em {dataCurta(s.superado_em)}</span>
                    </div>
                    <div>
                      <Botao variante="secundario" onClick={() => gerar(s.error_category)} disabled={gerando != null}>
                        {gerando === s.error_category && <Spinner className="w-3.5 h-3.5" />}
                        Treinar de novo
                      </Botao>
                    </div>
                  </Card>
                ))}
```

por:

```jsx
                {superados.map(s => {
                  const vencida = s.revisao?.vencida
                  return (
                    <Card key={s.error_category} className="gap-2!">
                      <div className="flex flex-wrap items-center gap-2">
                        <Tag variante="sucesso">{shortError(s.error_category)}</Tag>
                        <span className="text-xs text-cinza-texto">superado em {dataCurta(s.superado_em)}</span>
                      </div>
                      {s.revisao && (
                        <p className={`text-xs ${vencida ? 'font-bold text-violeta' : 'text-cinza-texto'}`}>
                          {situacaoDaRevisao(s.revisao)}
                        </p>
                      )}
                      <div>
                        <Botao
                          variante={vencida ? 'primario' : 'secundario'}
                          onClick={() => gerar(s.error_category)}
                          disabled={gerando != null}
                        >
                          {gerando === s.error_category && <Spinner className="w-3.5 h-3.5" />}
                          {vencida ? 'Revisar agora' : 'Treinar de novo'}
                        </Botao>
                      </div>
                    </Card>
                  )
                })}
```

- [ ] **Passo 2: o aviso de revisão no exercício**

Em `frontend/src/pages/aluno/ExercicioTreinoPage.jsx`, logo depois do bloco `{exercicio.reaproveitado && ( ... )}`, acrescentar:

```jsx
      {exercicio.revisao && (
        <div className="rounded-botao border-2 border-violeta bg-lavanda px-4 py-2.5 text-xs text-violeta">
          Revisão: você já superou este erro. Treinar de novo ajuda a ver se ele ficou para trás.
        </div>
      )}
```

- [ ] **Passo 3: lint e build**

Rodar: `cd frontend && rtk proxy ./node_modules/.bin/eslint .` e `cd frontend && npm run build`
Esperado: lint sem erro e build ok

- [ ] **Passo 4: commitar**

```bash
/usr/bin/git add frontend/src/pages/aluno/TreinoPage.jsx frontend/src/pages/aluno/ExercicioTreinoPage.jsx
/usr/bin/git commit -m "feat(trilha): situacao da revisao nos superados e aviso no exercicio"
```

---

### Task 5: documentação

**Arquivos:**
- Alterar: `HANDOFF.md` (seção 15, item 9 e item novo no fim da lista)
- Alterar: `docs/mapa-funcionalidades.md` (linha 10 da tabela, a trilha)

- [ ] **Passo 1: HANDOFF**

Na seção 15 do `HANDOFF.md`, depois do item `16. **Diagnósticos e tempo do Gemini (novembro de 2026).** ...`, acrescentar:

```markdown
17. **Trilha com revisão espaçada (novembro de 2026).** Item 2.5 do plano (RF32). Cada erro superado volta à trilha em 1, 6 e 15 dias, contados pelo dia de Brasília, e fica consolidado depois da terceira revisão. Revisão é o primeiro acerto de um exercício novo para o erro, a partir do vencimento. Depois de um acerto, a revisão vencida e o erro ativo se alternam no preparo do próximo. A agenda sai do histórico (`agenda_de_revisao` em `services/historico_do_aluno.py`), sem tabela. Na trilha, o superado mostra "Hora de revisar" com "Revisar agora", a próxima revisão ou "Consolidado", sem pilha de atrasados. A base é a reaprendizagem sucessiva (Rawson e Dunlosky), o espaçamento de Cepeda e colegas (2008) e a intercalação de Rohrer. O SM-2 completo fica no item 4.6.
```

- [ ] **Passo 2: mapa de funcionalidades**

Em `docs/mapa-funcionalidades.md`, na linha da funcionalidade 10 (`Trilha direcionada ao erro, com geração de exercícios`), trocar o trecho `Mostra só os erros ativos, com os superados e o "Treinar de novo" à parte.` por `Mostra só os erros ativos, com os superados à parte, cada um com revisão em 1, 6 e 15 dias até ficar consolidado, intercalada com os erros ativos.`

- [ ] **Passo 3: commitar**

```bash
/usr/bin/git add HANDOFF.md docs/mapa-funcionalidades.md
/usr/bin/git commit -m "docs(trilha): revisao espacada no handoff e no mapa"
```
