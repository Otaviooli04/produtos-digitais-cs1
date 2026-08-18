# CLAUDE.md

Guia para o Claude Code neste repositório. **Leia `HANDOFF.md` primeiro** — ele explica tudo do projeto (o que é, o que foi feito, o que ficou como ideia, para onde vai). Este arquivo é o resumo operacional.

## Contexto

Sistema de *Learning Analytics* para CS1 (turmas introdutórias de programação em C). Originou-se de um TCC concluído e validado. **Esta fase é a disciplina de Produtos Digitais**, com foco em transformá-lo em **produto voltado ao aluno** (feedback personalizado, acompanhamento, engajamento). Detalhes e backlog de produto em `HANDOFF.md` (seção 15).

O sistema corrige código C de provas como um **funil interpretável**: análise estática (tree-sitter) + execução isolada (Docker/GCC) + heurísticas pedagógicas classificam o erro, e as submissões são **agrupadas por assinatura de falha** para o professor intervir por grupo. O lado do aluno já tem conta, entrada por código de turma, modo treino/prova, histórico de tentativas, progresso e painel de erros recorrentes. O que falta está mapeado em `docs/produto/mapa-funcionalidades.md`.

## Arquitetura

```
backend/app/
  main.py              — FastAPI, monta os routers
  api/routes/          — exam.py, submission.py, turma.py, jobs.py, student.py, student_activity.py
  auth/                — JWT de professor e de aluno (papel no token), posse de recursos
  engine/
    dynamic_analyzer.py  — compila/roda C em Docker (gcc:latest, --network none, timeout)
    static_analyzer.py   — tree-sitter (tolerante a erros): estruturas, funções, off-by-one
    heuristics.py        — classify_error: 27 categorias pedagógicas (núcleo)
    error_locator.py     — linhas culpadas pelo erro de compilação
    semantic_extractor.py— Gemini: enunciado → questões + casos de teste
    evaluators/          — por tipo de questão (código, dissertativa, múltipla escolha)
  ml/cluster.py          — agrupamento (determinístico por assinatura de falha; UMAP/HDBSCAN = baseline/visualização)
  llm/feedback_generator.py — insights por grupo p/ o professor (Gemini, 1 chamada/questão, cacheada)
  llm/student_explainer.py  — explicação individual da tentativa p/ o aluno (sob demanda, cacheada)
  services/              — orquestração (exam, submission, bulk, turma, jobs, student_activity, effort_report)
  models/                — orm.py (11 entidades) + schemas.py (Pydantic)
  migrations/            — Alembic (revisões 0001..0012)
frontend/                — painel do professor (`/`) + app do aluno (`/aluno`) (React 19 + Vite + Tailwind v4)
```

**Fluxo:** `CodeRequest` → `dynamic_analyzer` + `static_analyzer` → `heuristics.classify_error` → agrupamento por assinatura de falha → insights (Gemini).

**Princípio central:** sem "modos de correção". Cada questão declara o que exige (`required_structures`, `forbidden_structures`, `required_functions`) e os verificadores só disparam o relevante (sistema adaptativo). O `Exam.modo` (treino/prova) é outra coisa: diz ao aluno o que a atividade é e governa janela e teto de tentativas, nunca como o código é avaliado.

## Comandos

### Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload      # http://localhost:8000  |  Swagger em /docs
alembic upgrade head               # aplica migrações
pytest tests/ --ignore=tests/integration
```

### Frontend
```bash
cd frontend
npm run dev      # dev server (HMR)
npm run build    # build de produção
npm run lint     # ESLint
```

## Dependências-chave

- **Docker** rodando (`gcc:latest`) — `dynamic_analyzer.py` depende dele.
- **GEMINI_API_KEY** no `backend/.env` — extração de prova e insights (`google-genai`, modelo `gemini-2.5-flash`).
- **PostgreSQL 16+**, `DATABASE_URL` no `.env`. Venv em `backend/venv/`.

## Convenções de trabalho (regras do Otávio)

- **PT-BR** em tudo.
- **Sem ponto e vírgula na prosa.** Nunca `;` em texto corrido. Exceções: listas, palavras-chave, código, bibliografia.
- **Commits sem `Co-Authored-By`.** Nunca adicionar co-autoria.
- **Git flow:** commitar na *feature branch* e dar push. **O Otávio faz os merges** em `dev`/`main` pelo GitHub.
- **Clean Architecture**, sem comentários excessivos, sem Canvas.

## RTK — comandos com economia de tokens

**Regra de ouro:** prefixe comandos de terminal com `rtk` sempre que possível (mesmo em cadeias com `&&`). Se o RTK tem filtro para o comando, aplica. Se não, passa direto — é sempre seguro.

```bash
rtk git status | log | diff | add | commit | push     # git compacto
rtk pytest                                            # só falhas
rtk lint | rtk npm run <script>                       # build/lint agrupado
rtk ls <path> | rtk grep <padrão> | rtk read <file>   # arquivos/busca compactos
rtk docker ps | rtk docker logs <c>                   # infra compacta
```
