# Arquitetura e Fluxo do Sistema

Documento de referência da estrutura e do fluxo de dados do sistema de Learning
Analytics para correção de código C em provas de CS1. Mantido junto ao código —
serve de base para a escrita do TCC. Última revisão: 2026-06-05.

---

## 1. Visão geral — arquitetura em funil

O sistema processa uma submissão de código C em estágios sucessivos, cada um
agregando informação ao anterior (arquitetura em funil):

```
Prova (PDF) ─► Extração (Gemini) ─► Questões + test cases
                                          │
Código do aluno ──────────────────────────┤
                                          ▼
              ┌─────────────────────────────────────────────┐
              │  Análise DINÂMICA        Análise ESTÁTICA     │
              │  (Docker GCC)            (tree-sitter)        │
              │  compila, roda,          estruturas, funções, │
              │  testa I/O               off-by-one           │
              └───────────────────┬──────────────────────────┘
                                  ▼
                         HEURÍSTICAS (classify_error)
                         diagnóstico pedagógico (categoria,
                         diagnóstico, feedback acionável)
                                  ▼
                    Persistência (PostgreSQL / SQLAlchemy)
                                  ▼
              CLUSTERING (UMAP + HDBSCAN)  ─►  INSIGHTS por grupo (Gemini)
```

**Princípio de projeto central:** o sistema não tem "modo P1" ou "modo P2". Cada
questão declara o que exige (`required_structures`, `forbidden_structures`,
`required_functions`) e os verificadores só disparam o que é relevante,
degradando graciosamente quando o conteúdo não se aplica. Isso o torna
**adaptativo** a provas com ou sem funções, com ou sem vetores/matrizes etc.

---

## 2. Stack tecnológica

| Camada | Tecnologia |
|--------|-----------|
| API | FastAPI + Uvicorn, Pydantic |
| Execução isolada | Docker (`gcc:latest`, `--network none`, timeout) |
| Análise estática | **tree-sitter** + `tree-sitter-c` (parser tolerante a erros) |
| LLM | Google Gemini 2.5 Flash (extração de provas + insights) |
| Persistência | PostgreSQL, SQLAlchemy, Alembic (migrações) |
| ML / Clustering | scikit-learn, UMAP, HDBSCAN |
| Frontend | React + Vite, Tailwind v4, React Router, Recharts |
| Autenticação | JWT (professores), bcrypt/passlib |

---

## 3. Estrutura de diretórios (backend)

```
backend/app/
  main.py                — app FastAPI, monta os routers
  api/routes/
    exam.py              — upload de prova, test cases, results, students, cluster, insights
    submission.py        — POST /evaluate (corrige uma submissão)
    turma.py             — turmas e analytics de turma
  engine/
    dynamic_analyzer.py    — compila/roda C em Docker GCC isolado
    static_analyzer.py     — tree-sitter: estruturas, funções, off-by-one (robusto a erro)
    heuristics.py          — classify_error: cruza dinâmico+estático → diagnóstico
    semantic_extractor.py  — Gemini: enunciado → questões/estruturas/funções exigidas
    evaluators/
      code_evaluator.py    — orquestra dynamic+static+heuristics em um resultado
  services/
    exam_service.py        — upload de prova, persistência de questões, results
    submission_service.py  — avalia e persiste submissões
  ml/cluster.py            — UMAP + HDBSCAN, 4 estratégias de feature
  llm/                     — insights pedagógicos por cluster (Gemini)
  models/
    schemas.py             — modelos Pydantic (request/response)
    orm.py                 — tabelas SQLAlchemy
```

---

## 4. Fluxo de dados ponta a ponta

### 4.1 Ingestão da prova
1. Professor faz upload do PDF/DOCX → `exam_service.process_exam_upload`.
2. `document_parser` extrai o texto bruto.
3. `semantic_extractor.extract_exam_structure` (Gemini) devolve as questões de
   código com `required_structures`, `forbidden_structures`, `requires_loop` e
   `required_functions` (nome, nº de parâmetros, tipo de retorno, recursão,
   passagem por ponteiro).
4. Professor adiciona os test cases (input → expected_output).

### 4.2 Avaliação de uma submissão (`code_evaluator.evaluate_code`)
1. **Dinâmica** (`dynamic_analyzer.compile_and_run`): compila com GCC em Docker
   isolado; se compilar, roda contra cada test case com timeout. Retorna
   `compile_error`, `warnings`, `test_results`, `all_tests_passed`.
2. **Estática** (`static_analyzer.extract_control_flow`): com tree-sitter, extrai
   `structures` (If/For/While/DoWhile/Switch), `functions` (assinatura, recursão,
   ponteiro, retorno) e `risky_loops` (off-by-one). Retorna `parse_ok=False`
   quando o código não compila, **mas ainda assim extrai o que for possível**.
3. **Heurísticas** (`heuristics.classify_error`): cruza os dois resultados +
   `required_structures`/`required_functions` da questão e produz um diagnóstico
   pedagógico único `{error_category, pedagogical_diagnosis, actionable_feedback}`.
4. Também devolve `structure_check` e `function_check` (conformidade com a spec).

### 4.3 Persistência e agregação
- `submission_service` grava a submissão (código, erro, categoria, diagnóstico,
  `ast_structures`, `ast_functions`) e os resultados de teste.
- `exam_service` agrega: taxa de acerto, distribuição de erros, matriz aluno×questão.

### 4.4 Clustering e insights
- `ml/cluster.cluster_question`: monta features → UMAP (redução) → HDBSCAN
  (agrupamento) → silhouette → persiste clusters e coordenadas 2D.
- `llm/`: gera insight pedagógico por cluster via Gemini.

---

## 5. Os três analisadores

### 5.1 Análise dinâmica (`dynamic_analyzer.py`)
Compila e executa em container `gcc:latest` com `--network none` e timeout
(inclusive dentro do container, para evitar zumbis em loop infinito). É a fonte
de verdade sobre **comportamento**: compila? passa nos testes? estoura tempo?
segfault?

### 5.2 Análise estática (`static_analyzer.py`) — tree-sitter
**Decisão de arquitetura (2026-06-05):** substituiu-se o pycparser pelo
**tree-sitter** (parser incremental tolerante a erros). Motivação empírica: em
provas reais de CS1, a maioria das submissões com problema **não compila** (erros
de sintaxe). O pycparser exige C válido — para esses casos retornava AST vazio,
justamente para os alunos que mais precisam de diagnóstico. O tree-sitter produz
uma árvore parcial mesmo com erros, então `structures`/`functions`/`risky_loops`
permanecem populados em código quebrado (e alimentam o clustering).

Saída de `extract_control_flow`:
```python
{ "success": True,
  "structures": [...],     # rótulos de controle de fluxo, em ordem de documento
  "functions": [...],      # por função: name, return_type, params, param_count,
                           #   is_recursive, has_pointer_param, returns_value
  "risky_loops": [...],    # off-by-one: {var, op:"<="}
  "parse_ok": bool }       # False ⇒ havia nós de erro (não compila)
```

### 5.3 Heurísticas pedagógicas (`heuristics.py`)
`classify_error` aplica regras em ordem de prioridade. Quando o código **não
compila**, classifica pela mensagem do compilador; quando compila, avalia avisos
→ violação de estrutura → violação de função → off-by-one → testes → estrutura.

**27 categorias de erro** atualmente (a "verdade-base pedagógica" usada também
como pseudo ground-truth no clustering):

- **Sintaxe/Compilação:** Ponto e Vírgula Ausente, Variável ou Função Não
  Declarada, Cabeçalho Faltando, Tipo Incompatível, Retorno Ausente, Erro de
  Compilação, Linker — Função Indefinida.
- **Runtime:** Acesso Indevido à Memória, **Acesso Fora dos Limites — Off-by-One**,
  Erro Aritmético — Divisão por Zero, Loop Infinito — Controle de Fluxo, Timeout
  Anômalo.
- **Avisos:** Variável Não Inicializada, Variável Declarada e Não Utilizada,
  Declaração Implícita de Função.
- **Estrutura:** Violação de Estrutura, Solução Sequencial — Sem Controle de
  Fluxo, Estrutura Suspeita — Excesso de Condicionais, Lógica Estrutural Válida.
- **Funções:** Função Ausente, Tudo no Main, Assinatura Incorreta, Recursão
  Faltando, Por-Valor vs Por-Referência.
- **Saída/outros:** Saída Incorreta, Correto, Erro Desconhecido.

---

## 6. Suporte a funções (análise estática)

Cada questão pode exigir funções via `required_functions`. O verificador
`check_functions` cruza o que o tree-sitter extraiu com a especificação e gera:
- **Tudo no Main** — função exigida ausente e só existe `main`.
- **Função Ausente** — exigida não definida, mas há outras funções.
- **Assinatura Incorreta** — nº de parâmetros ou tipo de retorno divergente.
- **Recursão Faltando** — exige recursão mas a função não chama a si mesma.
- **Por-Valor vs Por-Referência** — exige ponteiro mas usa passagem por valor.

A extração das funções exigidas a partir do enunciado é feita pelo Gemini
(`semantic_extractor`). Como nenhuma questão é checada se a spec estiver vazia,
provas sem funções simplesmente não acionam esses diagnósticos.

> Observação de escopo (achado empírico): a P1 real analisada (Turma 1) não pedia
> funções — todas as questões eram "escreva um programa". O suporte a funções é,
> portanto, capacidade voltada a provas P2/baseadas em função; em P1 fica inerte
> por construção.

---

## 7. Detecção de off-by-one (limites de vetor)

`static_analyzer` sinaliza o padrão clássico de CS1: laço com limite **`<=`** que
**indexa um vetor pela variável de controle** (ex.: `for(i=0;i<=n;i++) a[i]=...`).
Restringe-se a `<=` (limite superior inclusivo) — laços reversos `>=0` costumam
ser corretos e não são sinalizados, evitando falso-positivo. O sinal é usado para:
- **enriquecer o diagnóstico de Segmentation Fault** (causa típica de off-by-one);
- **acrescentar uma dica** ao diagnóstico de Saída Incorreta quando há testes falhos.

Funciona mesmo em código que não compila, graças ao tree-sitter.

---

## 8. Clustering (`ml/cluster.py`)

Pipeline: features → **UMAP** (redução dimensional, parâmetros adaptativos ao
tamanho da turma) → **HDBSCAN** (agrupamento por densidade) → **silhouette**
(qualidade) → persistência de clusters + coordenadas 2D para o scatter.

Cinco estratégias de feature extraction (comparadas no estudo de avaliação):
`tfidf`, `tfidf_ngram`, `tfidf_category` (one-hot das categorias de erro),
`tfidf_behavioral` (tfidf + categorias + comportamento: compila?, fração de
testes passados) e `tfidf_functional` (behavioral + features de função:
nº de funções, recursão, ponteiro, nº máx. de parâmetros).

**Achado empírico (exp1, 7 famílias):** `tfidf_behavioral` continua a melhor
estratégia (score 0.864); `tfidf_functional` (0.854) é comparável a
`tfidf_category` mas não supera a behavioral. As features de função mostraram-se
**redundantes com os sinais léxico+estrutural para o agrupamento** — o valor
pedagógico das funções está no diagnóstico por questão (heurísticas "Tudo no
Main", "Recursão Faltando"), não no clustering. Os dados sintéticos passaram a
derivar o AST do parser real (tree-sitter), tornando a avaliação fiel à produção
(o que re-baseliniza os scores absolutos em relação a versões anteriores).

---

## 9. Persistência (principais tabelas — `orm.py`)

- `turmas` → `exams` → `questions` → `test_cases`
- `questions`: inclui `required_structures`, `forbidden_structures`,
  `required_functions` (JSON).
- `submissions`: código, `compile_error`, `error_category`, diagnóstico,
  `ast_structures`, `ast_functions`, `cluster_id`, `umap_x/umap_y`, `matricula`.
- `submission_test_results`: resultado por test case.
- `question_clusters`: rótulo, tamanho, erro dominante, submissão representativa.

---

## 10. Principais endpoints

| Método | Rota | Função |
|--------|------|--------|
| POST | `/exams/upload` | Upload da prova (PDF/DOCX) → extração Gemini |
| POST | `/exams/{id}/questions/{n}/testcases` | Adiciona test cases |
| POST | `/submissions/evaluate` | Corrige uma submissão (dry_run não persiste) |
| POST | `/exams/{id}/submissions/bulk` | Upload em lote (ZIP) |
| GET | `/exams/{id}/results` | Taxa de acerto + distribuição de erros |
| GET | `/exams/{id}/students` | Matriz aluno × questão |
| POST | `/exams/{id}/questions/{n}/cluster` | Roda o clustering da questão |
| POST | `/exams/{id}/questions/{n}/insights` | Insights pedagógicos (Gemini) |
| GET | `/turmas/{id}/analytics` | KPIs e gráficos da turma |

---

## 11. Decisões de arquitetura registradas (para justificar no TCC)

1. **Caixa-preta + estática (não harness unitário).** A correção de função é
   verificada indiretamente (output dos testes) + estaticamente (assinatura/
   recursão via AST), sem construir um harness de teste unitário ciente de tipos.
   Justificativa: o valor pedagógico das funções vive quase todo na análise
   estática; o analisador dinâmico não muda.
2. **Parser tolerante a erros (tree-sitter > pycparser).** Motivado por evidência
   real: o modo de falha dominante em CS1 é código que não compila. Robustez
   estática destrava diagnóstico e features para a maioria das submissões.
3. **Verificadores orientados à especificação da questão.** Adaptatividade sem
   "modos": cada questão ativa só os checadores relevantes.

---

## 12. Limitações conhecidas e trabalho futuro

- **Refatoração das heurísticas em registro de verificadores plugáveis** (ainda
  monolítico em `classify_error`) — facilita adicionar verificadores de matriz,
  precisão de saída, etc.
- **Dados sintéticos do clustering** precisam refletir AST vazio em código que
  não compila (hoje famílias de erro de compilação têm AST artificial).
- **Off-by-one** cobre só o padrão `<=` + indexação direta; não liga o tamanho
  declarado do vetor ao limite do laço (análise de fluxo de dados fica como
  trabalho futuro).
- **Dados de processo** (histórico de tentativas do aluno) não são usados — só a
  submissão final. Potencial para analytics temporais.
```
