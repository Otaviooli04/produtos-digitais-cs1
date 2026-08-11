# Sistema de Learning Analytics para CS1 — Documentação Técnica

**Autor:** Otávio Rodrigues de Oliveira
**Instituição:** UNIFEI — Universidade Federal de Itajubá
**Curso:** Sistemas de Informação
**Origem:** TCC concluído · **Fase atual:** disciplina de Produtos Digitais (foco no aluno)
**Data de última atualização:** 2026-08-11

> **Leia antes:** o documento de passagem de bastão **[`../HANDOFF.md`](../HANDOFF.md)** dá a visão completa e atual (o que é, o que foi feito, o que ficou como ideia, para onde vai). Este arquivo detalha a parte técnica do sistema. Para a arquitetura em uma página, ver **[`ARQUITETURA.md`](ARQUITETURA.md)**.

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Objetivos](#2-objetivos)
3. [Arquitetura Geral](#3-arquitetura-geral)
4. [Stack Tecnológico](#4-stack-tecnológico)
5. [Módulos do Backend](#5-módulos-do-backend)
6. [Pipeline de Avaliação de Código](#6-pipeline-de-avaliação-de-código)
7. [Agrupamento por Assinatura de Falha](#7-agrupamento-por-assinatura-de-falha)
8. [LLM — Extração e Insights](#8-llm--extração-e-insights)
9. [Banco de Dados](#9-banco-de-dados)
10. [API — Endpoints](#10-api--endpoints)
11. [Frontend](#11-frontend)
12. [Decisões de Design](#12-decisões-de-design)
13. [Sistema de Testes](#13-sistema-de-testes)
14. [Como Executar](#14-como-executar)
15. [Pendências e Trabalho Futuro](#15-pendências-e-trabalho-futuro)

---

## 1. Visão Geral

O sistema é uma plataforma de **Learning Analytics** voltada para disciplinas introdutórias de programação (CS1) em C. Ele recebe o arquivo de uma prova (PDF ou DOCX), extrai automaticamente as questões via LLM, recebe submissões de código C, compila e executa esse código em ambiente isolado, classifica pedagogicamente o erro e **agrupa as submissões por assinatura de falha** para apoiar a decisão do professor — que intervém uma vez por grupo, e não por aluno.

O veredito do sistema foi validado contra o avaliador consolidado do Moodle (módulo CodeRunner) sobre **539 submissões reais de 4 turmas**, com concordância de **98,9%** (re-validação posterior: 537/539 = **99,6%**), usando apenas os casos de teste do enunciado.

---

## 2. Objetivos

- Automatizar a correção de questões de código C com feedback pedagógico imediato.
- Classificar erros de forma pedagogicamente significativa (não apenas "certo/errado").
- Reunir alunos com o mesmo defeito via agrupamento **interpretável** por assinatura de falha.
- Gerar uma síntese pedagógica por grupo com apoio de LLM, sob revisão do professor.
- Oferecer rastreabilidade completa por turma, prova, questão, submissão e aluno.

---

## 3. Arquitetura Geral

```
┌──────────────────────────────────────────────────────────────────┐
│                 Frontend (React 19 + Vite + Tailwind v4)          │
│        painel do professor  +  submissão pública do aluno        │
└───────────────────────────────┬──────────────────────────────────┘
                                │ HTTP (REST, token JWT)
┌───────────────────────────────▼──────────────────────────────────┐
│                    Backend (FastAPI + Python)                     │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  API (routes)   │  │  Engine (análise) │  │  ML / LLM      │  │
│  │  auth exam      │─▶│  dynamic_analyzer │  │  cluster.py    │  │
│  │  submission     │  │  static_analyzer  │  │  feedback_     │  │
│  │  turma jobs     │  │  heuristics       │  │  generator.py  │  │
│  └─────────────────┘  │  semantic_extractor│  └────────────────┘  │
│                       └──────────┬────────┘                      │
│  ┌───────────────────────────────▼──────────────────────────┐   │
│  │        Services (orquestração: exam, submission,          │   │
│  │        bulk_submission, turma, job)                       │   │
│  └───────────────────────────────┬──────────────────────────┘   │
│  ┌───────────────────────────────▼──────────────────────────┐   │
│  │        Models (ORM SQLAlchemy + schemas Pydantic)         │   │
│  └───────────────────────────────┬──────────────────────────┘   │
└──────────────────────────────────┼───────────────────────────────┘
                                   │ SQLAlchemy / Alembic
                    ┌──────────────▼─────────────┐
                    │   PostgreSQL (9 tabelas)   │
                    └──────────────┬─────────────┘
        ┌──────────────────────────┼──────────────────────────┐
        ▼                                                     ▼
┌──────────────────────────┐              ┌───────────────────────────┐
│ Docker — gcc:latest      │              │ Google Gemini 2.5 Flash   │
│ compilação/execução      │              │ extração de prova +       │
│ isolada (--network none) │              │ insights por grupo        │
└──────────────────────────┘              └───────────────────────────┘
```

### Princípio de organização

O backend segue separação em camadas:

| Camada | Responsabilidade |
|---|---|
| `api/routes/` | Recebe HTTP, valida parâmetros, delega a serviços |
| `auth/` | Autenticação JWT do professor e posse de recursos |
| `services/` | Orquestra a lógica de negócio combinando módulos |
| `engine/` | Processamento técnico: compilação, AST, heurísticas, extração |
| `ml/` | Agrupamento e redução de dimensionalidade |
| `llm/` | Integração com LLM para insights |
| `models/` | ORM (SQLAlchemy), schemas (Pydantic) e sessão de banco |

---

## 4. Stack Tecnológico

A lista canônica e versionada vive em `backend/requirements.txt` (backend) e `frontend/package.json` (frontend). Abaixo, o papel de cada peça.

### Backend / API

| Biblioteca | Papel |
|---|---|
| **FastAPI** | Framework web assíncrono: roteamento, validação via Pydantic, OpenAPI |
| **Uvicorn** | Servidor ASGI |
| **SQLAlchemy 2.x** | ORM para PostgreSQL |
| **Alembic** | Migrações incrementais do schema (revisões 0001..0009) |
| **psycopg2-binary** | Driver PostgreSQL |
| **Pydantic** | Validação de entrada/saída da API |
| **python-dotenv** | Variáveis de ambiente do `.env` |
| **python-multipart** | Upload de arquivos (`multipart/form-data`) |

### Análise de código C

| Biblioteca | Papel |
|---|---|
| **tree-sitter** + **tree-sitter-c** | Parser **incremental e tolerante a erros**: produz AST parcial mesmo em código que não compila (o caso comum em CS1) |
| **Docker CLI** | Compila e executa o C em contêiner isolado (`gcc:latest`, `--network none`, timeout) |

### Autenticação

| Biblioteca | Papel |
|---|---|
| **passlib** + **bcrypt** | Hash de senha do professor |
| **python-jose** | Emissão e validação de JWT (HS256, expiração de 8 h) |

### Machine Learning (baseline e visualização)

| Biblioteca | Papel |
|---|---|
| **scikit-learn** | TF-IDF, one-hot, binarização de AST, Silhouette Score |
| **umap-learn** | UMAP: redução de dimensionalidade (5D para clustering baseline, 2D para o scatter) |
| **hdbscan** | HDBSCAN: agrupamento por densidade (baseline de comparação) |
| **numpy / pandas / scipy** | Operações vetoriais/matriciais e tabulares |
| **matplotlib** | Gráficos comparativos das estratégias de feature |

> Em produção o agrupamento é **determinístico por assinatura de falha** — UMAP/HDBSCAN são baseline de comparação e a projeção 2D é recurso de visualização (ver seção 7).

### LLM / IA

| Biblioteca | Papel |
|---|---|
| **google-genai** | SDK oficial do Google Gemini. Modelo `gemini-2.5-flash` para extração estruturada de provas e síntese pedagógica por grupo |

### Extração de documentos

| Biblioteca | Papel |
|---|---|
| **pymupdf** | Leitura de PDF |
| **python-docx** | Leitura de DOCX |

### Frontend

| Biblioteca | Papel |
|---|---|
| **React 19 + Vite** | SPA com HMR e build de produção |
| **Tailwind v4** | Estilo utilitário |
| **React Router 7** | Roteamento (páginas em lazy-load) |
| **Recharts 3** | Gráficos do painel |
| **axios** | Cliente HTTP com token |

### Testes

| Biblioteca | Papel |
|---|---|
| **pytest** + **pytest-mock** | Runner, fixtures, mocking |
| **httpx** | Cliente usado pelo `TestClient` do FastAPI |

---

## 5. Módulos do Backend

### `app/engine/dynamic_analyzer.py`

Compila e executa o código do aluno usando Docker.

1. Salva o código em diretório temporário.
2. Compila com `docker run gcc:latest gcc -Wall ...` com `--network none` e timeout.
3. Se compilou, executa contra cada caso de teste com timeout por caso (inclusive dentro do contêiner, para não deixar processos zumbis em loop infinito).
4. Retorna `success`, `compile_error`, `warnings`, `test_results`, `all_tests_passed`.

Trata `TimeoutExpired` sem abortar o lote inteiro. É a fonte de verdade sobre **comportamento** (compila?, passa?, timeout?, segfault?).

### `app/engine/static_analyzer.py`

Analisa a AST do C **sem executá-lo**, com **tree-sitter** (parser tolerante a erros).

Extrai `structures` (If/For/While/DoWhile/Switch), `functions` (nome, tipo de retorno, nº de parâmetros, recursão, parâmetro por ponteiro, retorna valor) e `risky_loops` (off-by-one). Retorna `parse_ok=False` quando há nós de erro, **mas ainda assim popula o que conseguir** — inclusive em código que não compila, que é o caso mais comum em provas de CS1.

### `app/engine/heuristics.py`

Cruza os resultados dinâmico + estático + a especificação da questão e produz **um** diagnóstico pedagógico `{error_category, pedagogical_diagnosis, actionable_feedback}`. Aplica regras em **ordem de prioridade**: se não compila, classifica pela mensagem do GCC. Se compila: avisos → violação de estrutura → violação de função → off-by-one → testes → estrutura. É o núcleo pedagógico. Ver seção 6 para as 27 categorias.

### `app/engine/error_locator.py`

Faz o parse da saída do GCC para descobrir as **linhas culpadas** por um erro de compilação (usadas no destaque do código representativo).

### `app/engine/semantic_extractor.py`

Usa Gemini para transformar o texto bruto da prova em questões estruturadas (enunciado, `required_structures`, `forbidden_structures`, `required_functions`, `requires_loop`) e casos de teste de exemplo. Usar LLM evita regex frágil sobre PDFs de layout variável.

### `app/engine/document_parser.py`

Extrai texto de PDF (pymupdf) e DOCX (python-docx).

### `app/engine/evaluators/`

Orquestra a avaliação por tipo de questão: `code_evaluator.py` (junta dinâmico + estático + heurísticas em um resultado), `dissertative_evaluator.py`, `multiple_choice_evaluator.py`.

### `app/ml/cluster.py`

Agrupamento e o estudo de estratégias de feature (baseline UMAP + HDBSCAN). Ver seção 7.

### `app/llm/feedback_generator.py`

Gera a síntese pedagógica por grupo via Gemini (uma chamada por questão, com batching e cache em `QuestionCluster.insight`). Também atribui as linhas do erro de lógica para o destaque.

### `app/auth/`

`routes.py` (register/login), `service.py` (hash bcrypt, JWT), `dependencies.py` (injeta o professor logado), `ownership.py` (garante que o professor só acessa recursos das próprias turmas).

### `app/services/`

- `exam_service.py` — upload da prova, chamada ao Gemini, persistência de questões, agregação de resultados.
- `bulk_submission_service.py` — avaliação de um ZIP inteiro, com progresso via `ProcessingJob`.
- `submission_service.py` — avalia e persiste uma submissão individual.
- `turma_service.py` — CRUD de turma e analytics.
- `job_service.py` — cria e atualiza `ProcessingJob`.

---

## 6. Pipeline de Avaliação de Código

```
Código do aluno
        │
        ▼  POST /submission/evaluate   (ou lote via /exam/{id}/submissions/bulk)
   code_evaluator.evaluate_code()
        ├──▶ dynamic_analyzer.compile_and_run()   docker gcc isolado, sem rede, timeout
        ├──▶ static_analyzer.extract_control_flow() tree-sitter: estruturas, funções, off-by-one
        ├──▶ heuristics.classify_error()           categoria + diagnóstico + feedback
        └──▶ structure_check / function_check      conformidade com a spec da questão
        ▼
   persiste Submission + SubmissionTestResult
```

**Saída para o aluno:** resultado por caso de teste (entrada, saída esperada, saída obtida, passou?), a categoria pedagógica do erro, o feedback acionável e a checagem de conformidade estrutural/de funções.

**Normalização de saída:** a comparação tolera diferenças de whitespace e alinhamento (`%Nd`), para não reprovar um aluno por espaço a mais.

### As 27 categorias de erro

São a "verdade-base pedagógica" (usada também como pseudo ground-truth no agrupamento):

- **Sintaxe/Compilação:** Ponto e Vírgula Ausente, Variável ou Função Não Declarada, Cabeçalho Faltando, Tipo Incompatível, Retorno Ausente, Erro de Compilação, Linker — Função Indefinida.
- **Runtime:** Acesso Indevido à Memória, Acesso Fora dos Limites — Off-by-One, Erro Aritmético — Divisão por Zero, Loop Infinito — Controle de Fluxo, Timeout Anômalo.
- **Avisos:** Variável Não Inicializada, Variável Declarada e Não Utilizada, Declaração Implícita de Função.
- **Estrutura:** Violação de Estrutura, Solução Sequencial — Sem Controle de Fluxo, Estrutura Suspeita — Excesso de Condicionais, Lógica Estrutural Válida.
- **Funções:** Função Ausente, Tudo no Main, Assinatura Incorreta, Recursão Faltando, Por-Valor vs Por-Referência.
- **Saída/outros:** Saída Incorreta, Correto, Erro Desconhecido.

A fundamentação combina metodologia dedutivo-indutiva com âncoras da literatura (McCall & Kölling para severidade, Altadmri & Brown para erros de novatos, Becker, Keuning, Hattie & Timperley para feedback).

---

## 7. Agrupamento por Assinatura de Falha

Após a prova, o professor dispara o agrupamento de uma questão para reunir alunos com o mesmo defeito — sem ler cada submissão.

### Em produção (determinístico, dois níveis)

1. **Nível 1 — categoria de erro** das heurísticas (ex.: todos os "Saída Incorreta").
2. **Nível 2 — assinatura de falha:** dentro da categoria, agrupa por **qual conjunto de casos de teste** cada submissão reprova. Alunos que erram exatamente os mesmos casos caem no mesmo grupo.

Cada grupo recebe um representante (código exibido ao professor), um rótulo de sintoma (quais casos falham), as linhas do erro destacadas e, opcionalmente, a síntese pedagógica do Gemini que o professor pode propagar à turma (*human-in-the-loop*).

### Baseline geométrico (UMAP + HDBSCAN) — comparação e visualização

Pipeline do estudo: features → UMAP (parâmetros adaptativos ao tamanho da turma) → HDBSCAN (densidade, marca outliers como −1) → Silhouette → persistência de `cluster_id` e coordenadas 2D para o scatter.

**Cinco estratégias de feature** comparadas:

| Estratégia | Features |
|---|---|
| `tfidf` | TF-IDF(código) ⊕ one-hot(estruturas AST) |
| `tfidf_ngram` | idem com bigrams (contexto local) |
| `tfidf_category` | ⊕ one-hot(categoria de erro) |
| `tfidf_behavioral` | ⊕ [compilou 0/1, fração de testes passados] |
| `tfidf_functional` | behavioral ⊕ features de função (nº, recursão, ponteiro, nº máx. de parâmetros) |

**Achado empírico:** `tfidf_behavioral` foi a melhor (score ~0,864). `tfidf_functional` (~0,854) não superou — as features de função mostraram-se **redundantes** com os sinais léxico+estrutural para o agrupamento. O valor pedagógico das funções vive no **diagnóstico por questão** (heurísticas "Tudo no Main", "Recursão Faltando"), não no clustering.

### Parâmetros adaptativos (baseline)

Para funcionar com qualquer tamanho de turma (mínimo ~3 submissões):

```python
n_components_cluster = min(5, n - 1)   # UMAP exige n_components < n_samples
n_neighbors          = min(15, n - 1)
umap_init            = "random" if n < 10 else "spectral"  # spectral falha em datasets pequenos
```

`min_cluster_size` do HDBSCAN é adaptado ao tamanho da turma.

### Silhouette Score

Métrica **geométrica** de qualidade, calculada no espaço UMAP de clustering:

```
s(i) = (b − a) / max(a, b)
```

- `a`: distância média do ponto ao próprio cluster (coesão).
- `b`: distância média ao cluster vizinho mais próximo (separação).
- Escala −1 (pior) a +1 (melhor). Acima de 0,5 indica clusters razoavelmente compactos e separados.

**Cuidado:** silhouette é geométrica, não semântica. Score alto com poucos clusters pode indicar fusão de grupos pedagogicamente distintos. Foi um dos motivos do pivô para o agrupamento por assinatura de falha (mais interpretável). Ver a discussão em `ARQUITETURA.md` e no `HANDOFF.md`.

### Scripts de visualização

```bash
python backend/scripts/demo_visualization.py --out comparacao.png     # dados sintéticos, sem banco
python backend/scripts/compare_strategies.py --question_id 1 --out comparacao.png  # dados reais
python backend/evaluate_clustering.py                                 # harness de avaliação (experimentos)
```

---

## 8. LLM — Extração e Insights

O LLM tem papel **restrito** — nunca decide a correção. Faz apenas duas coisas.

### Extração da prova (`semantic_extractor.py`)

Recebe o texto (ou o PDF nativo, multimodal) e devolve as questões de código estruturadas + casos de teste de exemplo. Modelo `gemini-2.5-flash` pela boa qualidade de raciocínio, PT-BR nativo e custo baixo.

### Síntese pedagógica por grupo (`feedback_generator.py`)

```
POST /exam/{id}/questions/{n}/insights
        │
        ▼  Para a questão inteira, em uma única chamada (batching):
    Prompt → Gemini 2.5 Flash
    Contexto: enunciado + código representativo + erro dominante + tamanho de cada grupo
    Resposta: insight pedagógico curto (~4 frases) por grupo
        │
        ▼  grava em QuestionCluster.insight (cache persistente)
```

**Engenharia de custo:**
- **Cache** — o insight fica gravado, não se regenera à toa.
- **Batching** — K grupos de uma questão viram **1 chamada**, não K.

---

## 9. Banco de Dados

### Schema (PostgreSQL) — 9 tabelas

```
professors  ─< turmas ─< exams ─< questions ─< test_cases
                                      │
                                      ├─< submissions ─< submission_test_results
                                      └─< question_clusters
processing_jobs   (tarefas em segundo plano)
```

Campos que importam (definição em `backend/app/models/orm.py`):

- **professors** — `email`, `nome`, `senha_hash`.
- **turmas** — `nome`, `codigo`, `professor_id`.
- **exams** — `filename`, `raw_text`, `turma_id`.
- **questions** — `number`, `statement`, `points`, `required_structures`, `forbidden_structures`, `required_functions`, `requires_loop`.
- **test_cases** — `input`, `expected_output`.
- **submissions** — `code`, `compile_error`, `warnings`, `all_tests_passed`, `error_category`, `pedagogical_diagnosis`, `actionable_feedback`, `ast_structures`, `ast_functions`, `cluster_id`, `umap_x`, `umap_y`, `matricula`.
- **submission_test_results** — `input`, `expected_output`, `actual_output`, `passed`.
- **question_clusters** — `cluster_label`, `size`, `dominant_error`, `insight`, `highlight_lines`, `representative_submission_id`.
- **processing_jobs** — `kind` (`exam_upload` | `bulk_submit`), `status`, `stage`, `total`, `processed`, `message`, `result`.

> **Sobre o aluno:** hoje o aluno existe apenas como a string `matricula` em cada submissão. Não há tabela `students` nem conta de aluno — é o principal buraco a preencher na fase de produto (ver `HANDOFF.md`, seção 15).

### Migrações Alembic

| Revisão | Conteúdo |
|---|---|
| 0001 | Esquema base: exams, questions, test_cases, submissions, submission_test_results |
| 0002 | ML/clustering: `ast_structures`, `cluster_id`, `umap_x/y`, tabela `question_clusters` |
| 0003 | Turmas |
| 0004 | Renomeia `student_name` → `matricula` |
| 0005 | Auth de professor |
| 0006 | Suporte a funções (`required_functions`, `ast_functions`) |
| 0007 | `processing_jobs` |
| 0008 | `highlight_lines` no cluster |
| 0009 | `points` por questão |

Comandos:
```bash
alembic upgrade head       # aplica migrações pendentes
alembic downgrade -1       # reverte a última
alembic revision --autogenerate -m "descricao"
```

---

## 10. API — Endpoints

Base: `http://localhost:8000` · Swagger em `/docs`. Autenticação por token Bearer (JWT), exceto cadastro, login e a submissão pública do aluno. Routers montados: `auth`, `exam`, `submission`, `turma`, `jobs`.

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Health check |
| POST | `/auth/register` · `/auth/login` | Cadastro e sessão do professor |
| POST | `/exam/upload` | Upload da prova (PDF/DOCX) → questões via Gemini |
| GET · DELETE | `/exam/{id}` | Consulta e exclusão (cascata) |
| POST · PUT · DELETE | `/exam/{id}/questions[/{num}]` | CRUD de questões |
| GET · POST · PUT · DELETE | `/exam/{id}/questions/{num}/testcases[/{tc}]` | CRUD de casos de teste |
| POST | `/exam/{id}/submissions/bulk` | Envio em lote (ZIP), avaliação assíncrona |
| GET | `/exam/{id}/results` | Resultados agregados por questão |
| GET | `/exam/{id}/questions/{num}/groups` | Grupos por sintoma (com linhas destacadas) |
| POST | `/exam/{id}/questions/{num}/cluster` | (Re)agrupar a questão |
| POST | `/exam/{id}/questions/{num}/insights` | Gerar síntese pedagógica (Gemini) |
| GET | `/exam/{id}/students[/detail]` | Desempenho por aluno |
| POST · DELETE | `/submission/evaluate` · `/submission/{id}` | Avaliar / reavaliar / excluir submissão |
| GET | `/turmas[...]` | CRUD de turmas e `/turmas/{id}/analytics` |
| GET | `/jobs/{id}` · `/jobs/active` | Progresso das tarefas em segundo plano |

---

## 11. Frontend

Painel do professor + submissão pública do aluno. React 19 + Vite + Tailwind v4 + React Router 7 + Recharts + axios. Páginas em lazy-load (bundle inicial leve). Rotas em `frontend/src/App.jsx`.

**Fluxo do professor (protegido):** `TurmaListPage` → `TurmaDetailPage` → upload da prova (`ExamUploadPage`) → `ExamDashboard` → por questão: `QuestionPage` (grupos, insights, destaque do erro), `TestCasesPage`, `SubmissionsPage`, envio em lote (`BulkSubmitPage`), `ResultsPage`, `StudentsPage` / `StudentDetailPage`.

**Fluxo do aluno (público):** rota `/submit/:examId` → `StudentSubmitPage`. Submete código e recebe o diagnóstico imediato. É a base do produto voltado ao aluno.

**Componentes reutilizáveis:** `Modal`, `ConfirmDialog`, `QuestionForm`, `JobDock` (progresso das tarefas), `BarList`, `Badge`, `CodeBlock`, `FunctionCheckCard`, `ListControls`, `WhoList`, `Logo`. Auth em `context/AuthContext.jsx`, cliente HTTP em `api/client.js`.

CORS liberado para `http://localhost:5173` (Vite dev) e `http://localhost:4173` (Vite preview).

---

## 12. Decisões de Design

### Docker para compilação

**Decisão:** `gcc:latest` com `--network none` e timeout por caso de teste.
**Motivo:** isolamento total — código malicioso do aluno não acessa rede nem o sistema de arquivos do host. A flag `--network none` é essencial.

### tree-sitter para AST estática (trocado de pycparser)

**Decisão de arquitetura:** substituiu-se **pycparser** por **tree-sitter**.
**Motivo empírico:** em provas reais de CS1, a maioria das submissões com problema **não compila** (erros de sintaxe). O pycparser exige C válido e, para esses casos, retornava AST vazio — justamente para os alunos que mais precisam de diagnóstico. O tree-sitter produz uma árvore parcial mesmo com erros, mantendo `structures`/`functions`/`risky_loops` populados em código quebrado (e alimentando o agrupamento).

### Funil interpretável vs geometria densa

**Decisão:** o agrupamento em produção é **determinístico por assinatura de falha**, não por embeddings + K-Means.
**Motivo:** código de CS1 é curto e compartilha vocabulário, então TF-IDF puro gera vetores quase idênticos. A geometria mistura sintomas (poucos clusters "puros", silhouette baixa, K exigido a priori). O eixo do valor é **interpretabilidade** — o professor precisa entender por que aqueles alunos estão juntos. UMAP/HDBSCAN ficam como baseline e visualização.

### Verificadores orientados à especificação da questão

**Decisão:** sem "modos de prova". Cada questão declara o que exige e só os verificadores relevantes disparam. Isso torna o sistema adaptativo a provas com ou sem funções, vetores etc.

### Alembic para migrações

**Decisão:** Alembic em vez de `create_all` automático, para rastrear mudanças de schema em código versionado e evoluir o banco sem perder dados.

### Gemini 2.5 Flash

**Decisão:** boa qualidade de raciocínio pedagógico, PT-BR nativo, custo inferior ao Pro, SDK oficial. Papel restrito (extração + insights), nunca decide a correção.

---

## 13. Sistema de Testes

Estrutura em `backend/tests/`:

```
tests/
  conftest.py                       fixtures: banco de teste, client, factories, limpeza
  test_exam.py                      upload e gerenciamento de provas
  test_submission.py                submissão e avaliação
  test_clustering.py                clustering via API (UMAP/HDBSCAN mockados)
  test_insights.py                  geração de insights via LLM (mockado)
  unit/
    test_static_analyzer.py         extração via tree-sitter
    test_heuristics_functions.py    verificadores de função
    test_heuristics_offbyone.py     detecção de off-by-one
    test_heuristics_precision.py    precisão decimal na saída
    test_output_normalization.py    tolerância de whitespace/alinhamento
    test_cluster_logic.py           lógica de agrupamento
    test_adaptive_mcs.py            min_cluster_size adaptativo
    test_dynamic_timeout.py         timeout do analisador dinâmico
    test_crud_cascade.py            exclusão em cascata
  integration/
    test_full_flow.py               pipeline completo com Docker + Gemini reais
```

Marcador `integration` (em `pytest.ini`) separa os testes lentos que exigem Docker e `GEMINI_API_KEY`. O `conftest` usa um banco PostgreSQL de teste separado, limpo entre os testes.

```bash
pytest tests/ --ignore=tests/integration     # rápidos (sem Docker/Gemini)
pytest tests/integration/ -m integration -v  # requer Docker + GEMINI_API_KEY
```

---

## 14. Como Executar

### Pré-requisitos

- Python 3.10+
- **Docker** rodando (`docker pull gcc:latest`)
- **PostgreSQL 16+**
- Node.js 18+ (frontend)
- `GEMINI_API_KEY` válida

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env (ver ../.env.example): GEMINI_API_KEY, DATABASE_URL, SECRET_KEY
createdb learning_analytics       # ou via CREATE DATABASE
alembic upgrade head

uvicorn app.main:app --reload     # http://localhost:8000  |  /docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Banco de testes

```bash
createdb learning_analytics_test
pytest tests/ --ignore=tests/integration
```

---

## 15. Pendências e Trabalho Futuro

O backlog completo e priorizado (com o ângulo de **produto voltado ao aluno**) está em **[`../HANDOFF.md`](../HANDOFF.md), seção 15**. Em resumo:

| Item | Status | Nota |
|---|---|---|
| Conta e identidade do aluno | **A fazer (bloqueio nº 1)** | Hoje o aluno é só uma `matricula`. Precisa de tabela `students` + auth |
| Histórico de tentativas (dados de processo) | A fazer | Guarda-se só a submissão final. Abre acompanhamento temporal |
| Feedback personalizado por aluno via LLM | A fazer | Hoje o insight é por grupo. Estender ao indivíduo (com cache/batching) |
| Painel/jornada do aluno + engajamento | A fazer | Progresso, erros recorrentes, gamificação leve |
| Frontend do professor | **Feito** | Painel em 4 níveis, grupos, insights, destaque do erro |
| Autenticação | **Feito** | JWT de professor (falta auth de aluno) |
| Deploy | A fazer | Planejado: túnel para testes, nuvem para produção |
| Refino das heurísticas em registro plugável | Parcial | Facilita novos verificadores (matriz, precisão etc.) |
| Análise de fluxo de dados no off-by-one | A fazer | Ligar tamanho declarado do vetor ao limite do laço |
| Suporte a outras linguagens | Fora de escopo | Projetado para C, extensível com novos analisadores |
