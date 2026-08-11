# Learning Analytics — CS1

> **Fase atual: Produtos Digitais.** Este repositório continua o sistema (originado de um TCC concluído) como **produto voltado ao aluno**. Para o contexto completo — o que existe, o que foi validado, o que ficou como ideia e o backlog de produto — leia **[`HANDOFF.md`](HANDOFF.md)**.

Sistema de *Learning Analytics* para **apoio à correção docente** em disciplinas introdutórias de programação (CS1) em linguagem C. Em vez de o professor corrigir aluno por aluno, o sistema organiza a avaliação como um **funil interpretável**: cada submissão passa por análise estática, execução isolada e heurísticas pedagógicas, e as submissões são **agrupadas por sintoma de falha** para que o professor intervenha uma vez por grupo, e não por aluno.

O veredito do sistema foi validado contra o avaliador consolidado do Moodle (módulo CodeRunner) sobre **539 submissões reais de 4 turmas**, com **98,9% de concordância** usando apenas os casos de teste do enunciado.

## Principais funcionalidades

- **Funil de avaliação** estática + dinâmica + heurísticas, com diagnóstico determinístico e auditável (sem depender de LLM para decidir a correção).
- **Envio em lote**: o professor sobe um ZIP com as provas da turma; a avaliação roda em segundo plano com barra de progresso.
- **Agrupamento por sintoma**: dois níveis (categoria de erro das heurísticas + **assinatura de falha** nos casos de teste), que reúne alunos com o mesmo defeito e reduz o esforço de revisão.
- **Destaque do erro**: no código representativo de cada grupo, as linhas culpadas são destacadas — de forma determinística pela saída do compilador (erros de compilação) ou atribuídas pelo modelo de linguagem, sob revisão do professor (erros de lógica).
- **Painel docente** em quatro níveis (turma → prova → questão → aluno), com gráficos de taxa de aprovação, distribuição de erros, falha por caso de teste e alunos em risco.
- **Apoio do LLM (Gemini)** em papel restrito: extrair requisitos e casos de teste do enunciado, e redigir uma síntese pedagógica por grupo (uma chamada por questão, com cache).
- **CRUD completo** de turmas, provas, questões, casos de teste e submissões, com autenticação por token.

## Arquitetura

A submissão percorre um funil de cinco estágios:

```
estática (tree-sitter) → dinâmica (Docker/GCC) → heurísticas → agrupamento → apoio do LLM
```

```
backend/app/
  main.py                       — App FastAPI, monta os routers
  api/routes/
    exam.py        — provas, questões, test cases, envio em lote, grupos, insights, resultados
    submission.py  — avaliação, reavaliação e exclusão de submissão individual
    turma.py       — CRUD de turmas e analytics da turma
    jobs.py        — progresso de tarefas em segundo plano
  auth/            — autenticação por token (registro, login, posse de recursos)
  engine/
    static_analyzer.py    — AST com tree-sitter, tolerante a erros de sintaxe
    dynamic_analyzer.py   — compila e executa C em Docker (--network none, timeout)
    heuristics.py         — cascata de verificadores → categoria + diagnóstico + feedback
    error_locator.py      — linhas culpadas pelo erro de compilação (parse do gcc)
    semantic_extractor.py — Gemini: enunciado → requisitos + casos de teste de exemplo
    document_parser.py    — extrai texto de PDF e DOCX
    evaluators/           — avaliadores por tipo de questão (código, dissertativa, múltipla escolha)
  ml/cluster.py             — agrupamento em 2 níveis (categoria + assinatura de falha); UMAP só para visualização
  llm/feedback_generator.py — síntese pedagógica por grupo + linhas do erro de lógica (1 chamada/questão, cacheada)
  models/                   — ORM (9 entidades) + schemas Pydantic
  services/                 — regras de negócio e orquestração (lote e jobs assíncronos)
  migrations/               — versionamento do esquema (Alembic, revisões 0001..0009)
frontend/                   — painel do professor (React + Vite)
```

**Por que não usa *embeddings*/K-Means/banco vetorial:** o projeto começou com representações vetoriais densas e agrupamento geométrico, mas migrou para um funil interpretável. A representação combina atributos legíveis; o agrupamento é determinístico pela assinatura de falha (mais explicável e validado pelo próprio veredito); e o LLM ficou restrito ao apoio textual. UMAP/HDBSCAN/K-Means permanecem apenas como *baseline* de comparação e a projeção UMAP, como recurso de visualização.

## Fluxo de uso

1. **Professor** faz upload da prova (PDF/DOCX); o Gemini estrutura as questões de código e extrai os casos de teste de exemplo.
2. **Professor** revisa/edita os requisitos e os casos de teste por questão.
3. **Professor** envia em lote o ZIP com as submissões da turma; o sistema compila (Docker), roda contra os casos de teste, classifica por heurísticas e **agrupa por sintoma**.
4. **Professor** revisa os grupos, vê o código representativo com as linhas do erro destacadas, gera (opcionalmente) a síntese pedagógica do grupo e a propaga à turma (*human-in-the-loop*).

## Pré-requisitos

- Python 3.10+
- **Docker** rodando — usado para compilar e executar o código C de forma isolada
- PostgreSQL 16+
- Node.js 18+ (frontend)
- Chave da API Gemini — [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

## Instalação

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Crie `backend/.env`:

```env
GEMINI_API_KEY=sua_chave_aqui
DATABASE_URL=postgresql://analytics_user:analytics_pass@localhost:5432/learning_analytics
```

### Banco de dados (PostgreSQL)

```bash
sudo -u postgres psql -c "CREATE USER analytics_user WITH PASSWORD 'analytics_pass';"
sudo -u postgres psql -c "CREATE DATABASE learning_analytics OWNER analytics_user;"
```

Crie o esquema aplicando as migrações:

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### Frontend

```bash
cd frontend
npm install
```

## Execução

### Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
# API em http://localhost:8000  |  Swagger em http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm run dev
```

## API (principais rotas)

Autenticação por token (Bearer) exceto cadastro, login e leitura pública da prova.

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Health check |
| POST | `/auth/register` · `/auth/login` | Cadastro e sessão do professor |
| POST | `/exam/upload` | Upload da prova (PDF/DOCX) → questões via Gemini |
| GET · DELETE | `/exam/{id}` | Consulta e exclusão de prova (cascata) |
| POST · PUT · DELETE | `/exam/{id}/questions[/{num}]` | CRUD de questões |
| GET · POST · PUT · DELETE | `/exam/{id}/questions/{num}/testcases[/{tc}]` | CRUD de casos de teste |
| POST | `/exam/{id}/submissions/bulk` | Envio em lote (ZIP), avaliação assíncrona |
| GET | `/exam/{id}/results` | Resultados agregados por questão |
| GET | `/exam/{id}/questions/{num}/groups` | Grupos por sintoma (com linhas destacadas) |
| POST | `/exam/{id}/questions/{num}/cluster` | (Re)agrupar a questão |
| POST | `/exam/{id}/questions/{num}/insights` | Gerar a síntese pedagógica (Gemini) |
| GET | `/exam/{id}/students[/detail]` | Desempenho por aluno |
| POST · DELETE | `/submission/evaluate` · `/submission/{id}` | Avaliar / reavaliar / excluir submissão |
| GET | `/turmas[...]` | CRUD de turmas e `/turmas/{id}/analytics` |
| GET | `/jobs/{id}` · `/jobs/active` | Progresso das tarefas em segundo plano |

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3, FastAPI, Pydantic, Uvicorn |
| Banco de dados | PostgreSQL 16 + SQLAlchemy, migrações com Alembic |
| Análise estática | tree-sitter (+ gramática C) |
| Análise dinâmica | Docker + GCC |
| Agrupamento | determinístico (categoria + assinatura de falha); scikit-learn/UMAP/HDBSCAN como baseline e visualização |
| IA / LLM | Google Gemini (apoio: extração de requisitos e síntese de grupos) |
| Autenticação | passlib, bcrypt, python-jose |
| Frontend | React + Vite |

## Estrutura de Branches

| Branch | Finalidade |
|--------|-----------|
| `main` | Produção — releases estáveis |
| `dev` | Integração de features |
| `feature/<nome>` | Novas funcionalidades |
| `fix/<nome>` | Correções de bugs |
