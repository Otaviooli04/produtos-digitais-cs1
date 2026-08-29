# HANDOFF — Learning Analytics CS1 → Produtos Digitais

> Documento de passagem de bastão. Reúne **tudo** sobre o projeto para que o Claude
> (e qualquer pessoa) que continuar o desenvolvimento na disciplina de **Produtos
> Digitais** entenda o que existe, por que existe, o que foi validado, o que ficou
> só na ideia e para onde a nova fase aponta. Leia este arquivo antes de mexer no
> código. Detalhes técnicos mais finos estão em `docs/ARQUITETURA.md` e
> `docs/sistema.md` (este último tem trechos datados, ver aviso na seção 14).

**Autor original:** Otávio Rodrigues de Oliveira (UNIFEI, Sistemas de Informação)
**Origem:** TCC de graduação, concluído e defendido.
**Esta fase:** continuação do sistema como **produto digital**, com foco no **aluno como usuário** (feedback personalizado, acompanhamento, engajamento).

---

## 0. Leitura rápida (TL;DR)

- **O que é:** uma plataforma de *Learning Analytics* que corrige código C de provas de CS1 (turmas introdutórias de programação) e organiza a correção como um **funil interpretável**. Cada submissão passa por análise estática (tree-sitter), execução isolada (Docker/GCC) e heurísticas pedagógicas que classificam o erro. As submissões são então **agrupadas por sintoma de falha** para o professor intervir uma vez por grupo, não por aluno.
- **Estado:** sistema funcional ponta a ponta, com backend (FastAPI), frontend (React) e banco (PostgreSQL). Validado contra o corretor do Moodle (CodeRunner) sobre **539 submissões reais de 4 turmas**, com concordância documentada de **98,9%** (re-validação posterior chegou a 537/539 = **99,6%**).
- **De onde veio:** era o TCC. O repositório original do TCC segue mantido por outra pessoa. **Este repo é uma cópia limpa** (sem os artefatos de pesquisa/escrita do TCC) para tocar a nova disciplina de forma independente.
- **Para onde vai:** virar um **produto voltado ao aluno**. Hoje o sistema é 90% "painel do professor". A base para o aluno já existe (submissão pública, feedback pedagógico imediato, checagem estrutural), mas falta conta de aluno, histórico de tentativas, acompanhamento e engajamento. Ver seção 15.
- **Como o autor trabalha:** PT-BR, sem ponto e vírgula na prosa, `rtk` antes de comandos de terminal, commits sem co-autoria, ele mesmo faz os merges. Ver seção 16.

---

## 1. O que é o projeto (contexto e problema)

Em disciplinas introdutórias de programação (CS1), o professor corrige dezenas ou centenas de submissões de código C por prova. A correção é repetitiva e o feedback ao aluno costuma ser tardio e raso ("errado", nota X). Ferramentas de *autograding* comuns (ex.: CodeRunner no Moodle) dizem se passou nos casos de teste, mas **não explicam pedagogicamente o erro** nem **organizam a turma por tipo de dificuldade**.

Este sistema ataca isso com duas ideias centrais:

1. **Funil interpretável e determinístico.** A submissão é diagnosticada por regras auditáveis (não por um LLM decidindo a nota). Cada estágio agrega informação: compila? passa nos testes? qual estrutura de controle usou? qual categoria pedagógica de erro?
2. **Agrupamento por assinatura de falha.** Em vez de agrupar código por semelhança textual, o sistema agrupa alunos que **falham do mesmo jeito** (mesma categoria de erro + mesmo conjunto de casos de teste reprovados). Assim o professor lê um representante por grupo e propaga o feedback para todos.

O diferencial defendido no TCC foi justamente o **agrupamento por assinatura de falha** como eixo de **interpretabilidade** (o professor entende por que aqueles alunos estão juntos), em contraste com abordagens geométricas (embeddings + K-Means) que misturam sintomas e são difíceis de explicar.

---

## 2. Proveniência e separação de repositórios

| | Repo do TCC (original) | Este repo (Produtos Digitais) |
|---|---|---|
| Nome | `learning-analytics-cs1` | `produtos-digitais-cs1` |
| Mantido por | outra pessoa (continuidade do TCC) | Otávio (nova disciplina) |
| Contém | sistema + dados de experimento + escrita do TCC + figuras | **só o sistema** (cópia limpa) |
| Histórico git | completo (todos os commits do TCC) | **zerado** (começa do primeiro commit limpo) |

**O que NÃO foi copiado para cá** (estava versionado só no TCC ou era artefato de pesquisa, ver `.gitignore`):

- `backend/results/` — dados brutos dos experimentos de clustering e validação real (as 539 submissões, ground-truth, métricas).
- `backend/tools/` — scripts de extração de PDF das provas, auditoria vs CodeRunner, geração de figuras do TCC, `md2pdf`, etc.
- `docs/evidence_pack_resultados.md` e `docs/tcc_artefatos.tex` — pacote de evidências e artefatos LaTeX do TCC.
- `venv/`, `node_modules/`, backups, caches de ferramentas.

> **Consequência prática:** os **números de validação não são reproduzíveis a partir deste repo sozinho** — os dados reais e os scripts de auditoria ficaram no TCC. Se precisar reproduzir a validação, é preciso trazer `backend/tools/` e `backend/results/` do repo/local do TCC. Para a fase de produto isso raramente será necessário.

---

## 3. Arquitetura em funil (visão geral)

```
Prova (PDF/DOCX) ─► Extração (Gemini) ─► Questões + casos de teste
                                              │
Código do aluno ──────────────────────────────┤
                                              ▼
              ┌───────────────────────────────────────────────┐
              │  Análise DINÂMICA          Análise ESTÁTICA     │
              │  (Docker/GCC)              (tree-sitter)        │
              │  compila, roda, testa I/O  estruturas, funções, │
              │                            off-by-one           │
              └────────────────────┬──────────────────────────┘
                                   ▼
                    HEURÍSTICAS (classify_error)
                    → categoria de erro + diagnóstico + feedback acionável
                                   ▼
                    Persistência (PostgreSQL / SQLAlchemy)
                                   ▼
       AGRUPAMENTO por assinatura de falha  ─►  INSIGHTS por grupo (Gemini)
```

**Princípio central — sem "modos".** O sistema não tem "modo P1" ou "modo P2". Cada **questão declara o que exige** (`required_structures`, `forbidden_structures`, `required_functions`, `requires_loop`). Os verificadores só disparam o que é relevante e degradam graciosamente quando o conteúdo não se aplica. Isso torna o sistema **adaptativo** a provas com ou sem funções, com ou sem vetores/matrizes.

**Camadas do backend (Clean Architecture leve):**

| Camada | Pasta | Responsabilidade |
|---|---|---|
| API | `app/api/routes/` | Recebe HTTP, valida, delega a serviços |
| Serviços | `app/services/` | Orquestra a lógica de negócio |
| Engine | `app/engine/` | Processamento técnico: compilação, AST, heurísticas, extração |
| ML | `app/ml/` | Agrupamento e redução de dimensionalidade |
| LLM | `app/llm/` | Integração com Gemini para insights |
| Auth | `app/auth/` | JWT de professores, posse de recursos |
| Modelos | `app/models/` | ORM (SQLAlchemy) + schemas (Pydantic) |

---

## 4. Stack tecnológica

| Camada | Tecnologia |
|--------|-----------|
| API | FastAPI + Uvicorn, Pydantic |
| Execução isolada | Docker (`gcc:latest`, `--network none`, timeout) |
| Análise estática | **tree-sitter** + `tree-sitter-c` (parser tolerante a erros) |
| LLM | Google **Gemini 2.5 Flash** (`gemini-2.5-flash`, SDK `google-genai`) |
| Persistência | PostgreSQL 16, SQLAlchemy 2.x, Alembic (migrações 0001–0009) |
| ML / baseline | scikit-learn, UMAP (`umap-learn`), HDBSCAN, numpy, pandas, matplotlib |
| Extração de documentos | pymupdf (PDF), python-docx (DOCX) |
| Autenticação | passlib + bcrypt, python-jose (JWT) |
| Frontend | React 19 + Vite 8, Tailwind v4, React Router 7, Recharts 3, axios |
| Testes | pytest, pytest-mock, httpx |

Lista canônica de dependências do backend em `backend/requirements.txt`. Do frontend em `frontend/package.json`.

---

## 5. Modelo de domínio e banco (PostgreSQL)

Definição em `backend/app/models/orm.py`. Nove entidades:

```
professors ─< turmas ─< exams ─< questions ─< test_cases
                                     │
                                     ├─< submissions ─< submission_test_results
                                     └─< question_clusters
processing_jobs   (tarefas em segundo plano)
```

**Entidades e campos que importam:**

- **Professor** — `email`, `nome`, `senha_hash`, dono das turmas. Auth por JWT.
- **Turma** — `nome`, `codigo`, `professor_id`.
- **Exam** (prova) — `filename`, `raw_text` (texto extraído do PDF/DOCX), `turma_id`.
- **Question** — `number` (ex.: "1", "2a"), `statement`, `points` (peso na nota), `required_structures`/`forbidden_structures`/`required_functions` (JSON), `requires_loop`.
- **TestCase** — `input`, `expected_output`.
- **Submission** — `code`, `compile_error`, `warnings`, `all_tests_passed`, `error_category`, `pedagogical_diagnosis`, `actionable_feedback`, `ast_structures`/`ast_functions` (JSON extraído pelo tree-sitter), `cluster_id`, `umap_x`/`umap_y` (coordenadas de visualização), `matricula` (identifica o aluno — **não há entidade Aluno ainda**, só a matrícula na submissão).
- **SubmissionTestResult** — resultado por caso de teste (`input`, `expected_output`, `actual_output`, `passed`).
- **QuestionCluster** — grupo de uma questão: `cluster_label`, `size`, `dominant_error`, `insight` (síntese do Gemini, cacheada), `highlight_lines` (linhas do erro a destacar), `representative_submission_id`.
- **ProcessingJob** — rastreia tarefas longas (`kind` = `exam_upload` | `bulk_submit`) com `status`/`stage`/`total`/`processed`/`message`/`result` para a barra de progresso.

**Migrações Alembic (`backend/migrations/versions/`):**

| Revisão | O que introduziu |
|---|---|
| 0001 | Esquema base: exams, questions, test_cases, submissions, submission_test_results |
| 0002 | ML/clustering: `ast_structures`, `cluster_id`, `umap_x/y`, tabela `question_clusters` |
| 0003 | Turmas |
| 0004 | Renomeia `student_name` → `matricula` |
| 0005 | Auth de professor |
| 0006 | Suporte a funções (`required_functions`, `ast_functions`) |
| 0007 | `processing_jobs` (tarefas assíncronas) |
| 0008 | `highlight_lines` no cluster |
| 0009 | `points` por questão |

> **Nota sobre o aluno:** hoje o aluno existe apenas como uma `matricula` (string) em cada submissão. Não há tabela `students`, nem conta, nem histórico ligado a um usuário. Isso é o principal buraco a preencher para a fase de produto voltado ao aluno (ver seção 15).

---

## 6. Backend módulo a módulo

### `app/engine/` — o núcleo técnico

- **`dynamic_analyzer.py`** — compila e roda o C em container `gcc:latest` com `--network none` e timeout (dentro e fora do container, para não deixar zumbis em loop infinito). É a fonte de verdade sobre **comportamento**: compilou? passou nos testes? deu timeout? segfault? Retorna `compile_error`, `warnings`, `test_results[]`, `all_tests_passed`.
- **`static_analyzer.py`** — usa **tree-sitter** (parser incremental **tolerante a erros**). Extrai `structures` (If/For/While/DoWhile/Switch), `functions` (nome, tipo de retorno, nº de parâmetros, recursão, parâmetro por ponteiro, retorna valor) e `risky_loops` (off-by-one: laço com `<=` que indexa vetor). Retorna `parse_ok=False` quando há nós de erro, **mas ainda assim popula o que conseguir** — inclusive em código que não compila.
- **`heuristics.py`** (arquivo maior, ~21 KB) — `classify_error` cruza dinâmico + estático + a especificação da questão e produz **um** diagnóstico `{error_category, pedagogical_diagnosis, actionable_feedback}`. Ver seção 8. É o coração pedagógico do sistema.
- **`error_locator.py`** — extrai as linhas culpadas por erros de compilação a partir do parse da saída do GCC (para o destaque no código).
- **`semantic_extractor.py`** — Gemini: recebe o texto bruto da prova e devolve as questões estruturadas (enunciado, estruturas exigidas/proibidas, funções exigidas, casos de teste de exemplo).
- **`document_parser.py`** — extrai texto de PDF (pymupdf) e DOCX (python-docx).
- **`evaluators/`** — orquestra a avaliação por tipo de questão: `code_evaluator.py` (junta dynamic + static + heuristics), `dissertative_evaluator.py`, `multiple_choice_evaluator.py`.

### `app/services/` — orquestração

- **`exam_service.py`** (~16 KB) — upload da prova, chamada ao Gemini, persistência de questões, agregação de resultados por questão.
- **`bulk_submission_service.py`** — avaliação de um ZIP inteiro de submissões, com progresso via `ProcessingJob`.
- **`submission_service.py`** — avalia e persiste uma submissão individual.
- **`turma_service.py`** — CRUD de turma e analytics (KPIs, gráficos).
- **`job_service.py`** — cria e atualiza `ProcessingJob`.

### `app/ml/cluster.py` — agrupamento

Pipeline de comparação (baseline): features → UMAP → HDBSCAN → silhouette → persistência. Cinco estratégias de feature: `tfidf`, `tfidf_ngram`, `tfidf_category`, `tfidf_behavioral`, `tfidf_functional`. **Em produção, o agrupamento que vale é o determinístico por assinatura de falha** (categoria de erro + conjunto de casos de teste reprovados) — UMAP/HDBSCAN ficaram como baseline de comparação e a projeção 2D como recurso de visualização. Ver seção 9.

### `app/llm/feedback_generator.py` — insights

Gera a síntese pedagógica por grupo via Gemini (uma chamada por questão, com batching e cache na coluna `QuestionCluster.insight`). Também atribui as linhas do erro de lógica para o destaque, sob revisão do professor.

### `app/auth/` — autenticação

JWT de professor: `routes.py` (register/login), `service.py` (hash bcrypt, emissão/validação de token), `dependencies.py` (injeta o professor logado), `ownership.py` (garante que o professor só acessa recursos das próprias turmas).

### `app/api/routes/` — endpoints

- **`exam.py`** (~21 KB) — provas, questões, casos de teste, envio em lote, grupos, insights, resultados, alunos.
- **`submission.py`** — avaliar/reavaliar/excluir submissão individual.
- **`turma.py`** — CRUD de turma e analytics.
- **`jobs.py`** — progresso das tarefas em segundo plano.

---

## 7. Pipeline de avaliação de uma submissão

```
POST /submission/evaluate  (ou lote via /exam/{id}/submissions/bulk)
        │
        ▼  code_evaluator.evaluate_code()
        ├─► dynamic_analyzer.compile_and_run()   → compila+roda no Docker isolado
        ├─► static_analyzer.extract_control_flow()→ estruturas, funções, off-by-one
        ├─► heuristics.classify_error()           → categoria + diagnóstico + feedback
        └─► também: structure_check, function_check (conformidade com a spec da questão)
        ▼
   persiste Submission + SubmissionTestResult
```

**Saída para o aluno** (já disponível hoje na submissão pública): resultado por caso de teste (entrada, saída esperada, saída obtida, passou?), a categoria pedagógica do erro, o feedback acionável (o que fazer para corrigir) e a checagem de conformidade estrutural/de funções.

Detalhe importante da robustez: a **normalização de saída** tolera diferenças de whitespace e alinhamento (`%Nd`), para não reprovar um aluno por espaço a mais. E o `dynamic_analyzer` trata `TimeoutExpired` sem abortar o lote inteiro.

---

## 8. Heurísticas — as 27 categorias de erro

`classify_error` aplica regras em **ordem de prioridade**. Se o código **não compila**, classifica pela mensagem do compilador. Se compila, avalia: avisos → violação de estrutura → violação de função → off-by-one → testes → estrutura. As categorias são a "verdade-base pedagógica" (usada também como pseudo ground-truth no agrupamento):

- **Sintaxe/Compilação:** Ponto e Vírgula Ausente, Variável ou Função Não Declarada, Cabeçalho Faltando, Tipo Incompatível, Retorno Ausente, Erro de Compilação, Linker — Função Indefinida.
- **Runtime:** Acesso Indevido à Memória, Acesso Fora dos Limites — Off-by-One, Erro Aritmético — Divisão por Zero, Loop Infinito — Controle de Fluxo, Timeout Anômalo.
- **Avisos:** Variável Não Inicializada, Variável Declarada e Não Utilizada, Declaração Implícita de Função.
- **Estrutura:** Violação de Estrutura, Solução Sequencial — Sem Controle de Fluxo, Estrutura Suspeita — Excesso de Condicionais, Lógica Estrutural Válida.
- **Funções:** Função Ausente, Tudo no Main, Assinatura Incorreta, Recursão Faltando, Por-Valor vs Por-Referência.
- **Saída/outros:** Saída Incorreta, Correto, Erro Desconhecido.

A **fundamentação** dessas categorias no TCC combina metodologia dedutivo-indutiva com âncoras da literatura (McCall & Kölling para severidade, Altadmri & Brown para erros comuns de novatos, Becker, Keuning, Hattie & Timperley para feedback). O rótulo de **severidade** de McCall & Kölling é usado para priorizar o que mostrar ao professor.

**Suporte a funções** (`check_functions`): cruza o que o tree-sitter extraiu com `required_functions` e gera "Tudo no Main", "Função Ausente", "Assinatura Incorreta", "Recursão Faltando", "Por-Valor vs Por-Referência". Provas sem funções simplesmente não acionam esses diagnósticos (spec vazia → verificador inerte).

**Off-by-one:** sinaliza o padrão clássico `for(i=0; i<=n; i++) a[i]=...` (limite superior inclusivo indexando vetor). Restringe-se a `<=` para evitar falso-positivo em laços reversos. Enriquece o diagnóstico de segfault e a dica em saída incorreta. Funciona mesmo em código que não compila.

---

## 9. Agrupamento por assinatura de falha (o pivô)

Este é o coração conceitual do trabalho e a decisão de design mais importante.

**Como funciona em produção (determinístico, dois níveis):**
1. **Nível 1 — categoria de erro** das heurísticas (ex.: todos os "Saída Incorreta").
2. **Nível 2 — assinatura de falha:** dentro da categoria, agrupa por **qual conjunto de casos de teste** cada submissão reprova. Alunos que erram exatamente os mesmos casos caem no mesmo grupo.

Cada grupo ganha um representante (código exibido ao professor), um rótulo de sintoma (quais casos falham), as linhas do erro destacadas e, opcionalmente, uma síntese pedagógica do Gemini que o professor pode propagar à turma inteira (*human-in-the-loop*).

**Por que NÃO embeddings/K-Means/banco vetorial:** o projeto **começou** com representações vetoriais densas + agrupamento geométrico (UMAP + HDBSCAN) e **migrou** para o funil interpretável. Motivos empíricos:
- Código de CS1 é curto e compartilha vocabulário (`main`, `int`, `printf`, `scanf`, `return`) — TF-IDF puro produz vetores quase idênticos para programas semanticamente diferentes.
- A geometria **mistura sintomas**: só ~36% dos clusters geométricos eram "puros" (um só tipo de erro), silhouette ~0,30, e K-Means exige escolher `k` a priori.
- O eixo do valor é **interpretabilidade**, não recuperabilidade: o professor precisa entender **por que** aqueles alunos estão juntos. A assinatura de falha responde isso diretamente, é determinística e é validada pelo próprio veredito do sistema.

**UMAP/HDBSCAN/K-Means permanecem** apenas como *baseline* de comparação (no estudo de avaliação) e a projeção UMAP 2D como recurso de visualização (scatter). No estudo de features, `tfidf_behavioral` (TF-IDF-bigram + categoria de erro + comportamento: compilou?, fração de testes passados) foi a melhor estratégia geométrica (score ~0,864), e as features de função (`tfidf_functional`, ~0,854) mostraram-se redundantes com os sinais léxico+estrutural — o valor pedagógico das funções vive no **diagnóstico por questão**, não no clustering.

**Harness de avaliação do clustering:** `backend/evaluate_clustering.py` (~32 KB) roda os experimentos comparativos. `backend/scripts/demo_visualization.py` (dados sintéticos, sem banco) e `backend/scripts/compare_strategies.py` (dados reais do banco) geram o PNG 2×2 comparando estratégias.

---

## 10. LLM (Gemini) — papel restrito e engenharia de custo

O LLM tem papel **deliberadamente restrito** — nunca decide a correção. Só faz:
1. **Extração** do enunciado → questões estruturadas + casos de teste de exemplo (`semantic_extractor.py`). Recebe o PDF nativamente (multimodal), sem tools de geometria.
2. **Síntese pedagógica por grupo** (`feedback_generator.py`) — máx. ~4 frases, em PT-BR.

**Otimização de custo** (munição do TCC sobre engenharia de uso de LLM):
- **Cache persistente** — o insight fica gravado em `QuestionCluster.insight`, não se regenera à toa.
- **Batching** — K grupos de uma questão viram **1 chamada** ao Gemini, não K.

Modelo: `gemini-2.5-flash` (bom raciocínio pedagógico, PT-BR nativo, custo baixo, latência aceitável). Requer `GEMINI_API_KEY` no `.env`.

---

## 11. Frontend (painel do professor)

React 19 + Vite 8 + Tailwind v4 + React Router 7 + Recharts 3 + axios. Páginas em *lazy-load* (bundle inicial leve). Rotas em `frontend/src/App.jsx`.

**Fluxo do professor (protegido por login):**
`TurmaListPage` → `TurmaDetailPage` → upload da prova (`ExamUploadPage`) → `ExamDashboard` → por questão: `QuestionPage` (grupos, insights, destaque do erro — arquivo maior, ~27 KB), `TestCasesPage`, `SubmissionsPage`, envio em lote (`BulkSubmitPage`), `ResultsPage`, `StudentsPage`/`StudentDetailPage`.

**Rota pública do aluno:** `submit/:examId` → `StudentSubmitPage`. **Este é o ponto de entrada do aluno hoje** — ele submete código e recebe o diagnóstico. É a base sobre a qual o produto voltado ao aluno vai crescer.

**Componentes reutilizáveis:** `Modal`, `ConfirmDialog`, `QuestionForm`, `JobDock` (barra de progresso das tarefas em segundo plano), `BarList`/`Badge`/`CodeBlock`/`FunctionCheckCard`/`ListControls`/`WhoList`/`Logo`. Contexto de auth em `context/AuthContext.jsx`. Cliente HTTP em `api/client.js` (axios com token). Utilidades: `errorLabels.js`, `highlightLines.js`.

**Analytics ao professor:** gráficos em barras horizontais (para evitar sobreposição), falha por caso de teste, acerto parcial, top erros de compilação, alunos em risco, taxa de aprovação por nota (≥60%) com pesos por questão.

---

## 12. Fluxo de uso ponta a ponta

1. **Professor** cadastra-se/loga, cria uma **turma**.
2. **Professor** faz upload da **prova** (PDF/DOCX). O Gemini estrutura as questões de código e extrai os casos de teste de exemplo (roda em segundo plano, com progresso).
3. **Professor** revisa/edita os requisitos e os casos de teste por questão.
4. **Professor** envia em **lote** o ZIP com as submissões da turma. O sistema compila (Docker), roda contra os casos de teste, classifica por heurísticas e **agrupa por sintoma** (também assíncrono).
5. **Professor** revisa os **grupos**, vê o código representativo com as **linhas do erro destacadas**, gera (opcionalmente) a **síntese pedagógica** do grupo e a **propaga** à turma.
6. **Aluno** (fluxo público) submete código e recebe **diagnóstico imediato** + resultado por caso de teste + feedback acionável.

---

## 13. Como rodar (setup completo)

**Pré-requisitos:** Python 3.10+, Docker rodando (`docker pull gcc:latest`), PostgreSQL 16+, Node 18+, `GEMINI_API_KEY`.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Crie `backend/.env` (ver `.env.example`):

```env
GEMINI_API_KEY=sua_chave_aqui
DATABASE_URL=postgresql://analytics_user:analytics_pass@localhost:5432/learning_analytics
```

Banco:

```bash
sudo -u postgres psql -c "CREATE USER analytics_user WITH PASSWORD 'analytics_pass';"
sudo -u postgres psql -c "CREATE DATABASE learning_analytics OWNER analytics_user;"
cd backend && source venv/bin/activate && alembic upgrade head
```

Servidor:

```bash
uvicorn app.main:app --reload   # API em http://localhost:8000  |  Swagger em /docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # HMR
npm run build    # produção
npm run lint     # ESLint
```

### Testes

```bash
cd backend && source venv/bin/activate
createdb learning_analytics_test
pytest tests/ --ignore=tests/integration        # rápidos (sem Docker/Gemini)
pytest tests/integration/ -m integration -v     # requer Docker + GEMINI_API_KEY
```

> Docker é **obrigatório** — sem ele a análise dinâmica não roda. No WSL, garanta que o Docker Desktop/daemon esteja ativo antes de subir o backend.

---

## 14. Resultados validados (referência histórica do TCC)

- **539 submissões reais de 4 turmas**, corrigidas pelo sistema e comparadas ao corretor consolidado do Moodle (CodeRunner) usando **apenas os casos de teste do enunciado**.
- **Concordância:** 98,9% documentada no README, re-validação posterior chegou a **537/539 = 99,6%**. As duas divergências restantes eram comportamento indefinido em C (variável não inicializada zerada pelo CodeRunner), não erro de extração nem de veredito.
- **Distribuição** (exemplo de uma turma): Correto 282, Saída Incorreta 148, resto entre as demais categorias.
- **Redução de esforço (hipótese H2):** as submissões colapsaram em ~138 grupos, uma redução de **≈3,91×** no número de itens a revisar.

> **Cuidado:** `docs/sistema.md` foi escrito em 2026-05-05 e tem trechos **desatualizados** — cita `pycparser` (foi trocado por **tree-sitter**), diz "frontend não iniciado" (está pronto) e lista só 2 migrações (são 9). Trate `docs/ARQUITETURA.md` (revisão 2026-06-05) e **este HANDOFF** como as fontes atuais. `sistema.md` serve para detalhe conceitual de ML/silhouette que continua válido.

---

## 15. Transição para Produtos Digitais — foco no ALUNO

A disciplina de Produtos Digitais reposiciona o sistema: de **ferramenta de correção do professor** para **turma virtual com os dois lados** (o aluno treina, faz prova, vê o que errou e acompanha a evolução; o professor mantém o painel). O motor pedagógico já era forte — o que foi construído aqui é a camada de produto para o aluno.

### O que já serve de base (não precisa reconstruir)
- **Submissão pública do aluno** (`StudentSubmitPage`, rota `/submit/:examId`) com diagnóstico imediato.
- **Feedback pedagógico acionável** por submissão (categoria + o que fazer para corrigir), não só "passou/falhou".
- **Checagem estrutural e de funções** por questão.
- **Motor de avaliação** determinístico, isolado (Docker) e robusto a código que não compila.

### O que já foi construído nesta fase (agosto/2026)
1. **Conta e identidade do aluno.** Tabelas `students` e `enrollments`, JWT com papel próprio, entrada na turma por `codigo_acesso` de 6 caracteres e religação das submissões antigas pela matrícula (migração 0010).
2. **Histórico de tentativas.** `Submission.attempt_number` e persistência de toda tentativa, não só a final. Histórico por questão com o diagnóstico de cada envio.
3. **Modo treino e modo prova.** `Exam.modo`, janela (`abre_em`/`fecha_em`) e teto de tentativas (`max_tentativas`), aplicados na submissão do aluno (migração 0011).
4. **Painel do aluno.** Lista de atividades, progresso (tentativas até acertar, acertos de primeira, sequência de dias, evolução semanal) e painel de erros recorrentes com tendência por categoria.
5. **Feedback individual via LLM.** `llm/student_explainer.py`: o aluno pede a explicação da própria tentativa, gerada uma vez e cacheada em `submissions.llm_explanation` (migração 0012). O prompt proíbe entregar a solução.
6. **Frontend do aluno.** App próprio em `/aluno` (contexto e token separados do professor), em `frontend/src/pages/aluno/`.
7. **Lado do professor.** Código de acesso visível na turma e configuração de disponibilidade da atividade. Relatório de esforço economizado em `/exam/{id}/effort-report`.

### O que ainda falta
Trilha direcionada com geração de exercícios, antifraude do modo prova, relatório de fim de lista, instrumentação de uso (DAU/WAU) e acesso sem turma. O mapa completo, ligando cada funcionalidade dos documentos da disciplina ao código, está em `docs/mapa-funcionalidades.md`.

### Perguntas de produto ainda em aberto (decisões a tomar com o novo Claude)
- ~~Prova ou treino?~~ **Decidido:** os dois. Cada atividade declara seu `modo`, e a janela e o teto de tentativas controlam a avaliação. Falta o antifraude do modo prova.
- O feedback ao aluno deve ser **imediato e completo** (hoje é assim) ou **progressivo** (dica → dica → solução, para não entregar a resposta)?
- Métricas de sucesso do produto: retenção do aluno? nº de submissões até acertar? redução de erros recorrentes?

> Estas perguntas são de **produto**, não de código. Traga-as para a discussão da disciplina antes de codar features grandes.

---

## 16. Como o autor trabalha (regras para o Claude do novo projeto)

Regras absolutas do Otávio, reunidas para evitar retrabalho:

- **Idioma:** PT-BR em tudo (código, docs, mensagens).
- **Sem ponto e vírgula na prosa.** Nunca usar `;` no meio de texto corrido. Exceções: itens de lista, palavras-chave, código/prompts, bibliografia. Regra absoluta e reiterada.
- **`rtk` antes de comandos de terminal.** Prefixar comandos de CLI com `rtk` sempre que possível (economia de tokens). Mesmo em cadeias com `&&`. `rtk` é sempre seguro (se não tem filtro, passa direto).
- **Commits sem co-autoria.** **Nunca** adicionar `Co-Authored-By` nos commits.
- **Git flow:** commitar na *feature branch* e dar push. **O Otávio faz os merges** em `dev` e `main` pelo GitHub. Não fazer merge para main sozinho.
- **Código:** Clean Architecture, sem comentários excessivos, sem Canvas. Comentário só quando agrega.
- **Não usar Canvas.**

---

## 17. Glossário

- **Assinatura de falha (failure signature):** conjunto de casos de teste que uma submissão reprova, usado como chave de agrupamento. É o diferencial do trabalho.
- **Funil interpretável:** arquitetura em estágios sucessivos e determinísticos, cada um auditável, em oposição a uma caixa-preta de ML.
- **Adaptativo (sem modos):** cada questão declara o que exige e os verificadores só disparam o relevante.
- **`required_structures` / `forbidden_structures` / `required_functions`:** especificação por questão do que a solução deve/não deve conter, extraída pelo Gemini e revisável pelo professor.
- **Categoria de erro:** rótulo pedagógico produzido pelas heurísticas (27 categorias).
- **Insight:** síntese pedagógica curta gerada pelo Gemini por grupo, cacheada em `QuestionCluster.insight`.
- **`highlight_lines`:** linhas do código representativo a destacar (erro de compilação via GCC, erro de lógica via Gemini sob revisão).

---

## 18. Ponteiros rápidos

| Preciso de… | Vá para |
|---|---|
| Arquitetura e decisões atuais | `docs/ARQUITETURA.md` |
| Detalhe conceitual de ML/silhouette (datado no resto) | `docs/sistema.md` |
| Heurísticas (núcleo pedagógico) | `backend/app/engine/heuristics.py` |
| Análise estática (tree-sitter) | `backend/app/engine/static_analyzer.py` |
| Execução isolada | `backend/app/engine/dynamic_analyzer.py` |
| Rotas principais | `backend/app/api/routes/exam.py` |
| Modelo de dados | `backend/app/models/orm.py` + `backend/migrations/versions/` |
| Agrupamento / estudo de features | `backend/app/ml/cluster.py`, `backend/evaluate_clustering.py` |
| Insights e custo do LLM | `backend/app/llm/feedback_generator.py` |
| Entrada do aluno (base do produto) | `frontend/src/pages/StudentSubmitPage.jsx` + rota `/submit/:examId` |
| Painel de grupos/insights/destaque | `frontend/src/pages/QuestionPage.jsx` |

---

*Fim do handoff. Se algo aqui divergir do código, o código vence — e atualize este arquivo.*
