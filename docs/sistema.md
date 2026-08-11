# Sistema de Learning Analytics para CS1 — Documentação Técnica

**Autor:** Otávio Rodrigues de Oliveira  
**Instituição:** UNIFEI — Universidade Federal de Itajubá  
**Curso:** Sistemas de Informação  
**Data de última atualização:** 2026-05-05

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Objetivos](#2-objetivos)
3. [Arquitetura Geral](#3-arquitetura-geral)
4. [Stack Tecnológico](#4-stack-tecnológico)
5. [Módulos do Backend](#5-módulos-do-backend)
6. [Pipeline de Avaliação de Código](#6-pipeline-de-avaliação-de-código)
7. [Pipeline de ML — Clustering](#7-pipeline-de-ml--clustering)
8. [LLM — Geração de Feedback por Cluster](#8-llm--geração-de-feedback-por-cluster)
9. [Banco de Dados](#9-banco-de-dados)
10. [API — Endpoints](#10-api--endpoints)
11. [Decisões de Design](#11-decisões-de-design)
12. [Sistema de Testes](#12-sistema-de-testes)
13. [Como Executar](#13-como-executar)
14. [Pendências e Trabalho Futuro](#14-pendências-e-trabalho-futuro)

---

## 1. Visão Geral

O sistema é uma plataforma de **Learning Analytics** voltada para disciplinas introdutórias de programação (CS1) em C. Ele recebe o arquivo de uma prova (PDF ou DOCX), extrai automaticamente as questões via LLM, permite que alunos submetam código C, compila e executa esse código em ambiente isolado, classifica pedagogicamente o erro e, ao final de uma turma, agrupa submissões similares via Machine Learning para apoiar a tomada de decisão do professor.

---

## 2. Objetivos

- Automatizar a correção de questões de código C com feedback imediato para o aluno.
- Classificar erros de forma pedagogicamente significativa (não apenas "errado/certo").
- Identificar padrões de dificuldade recorrentes entre alunos via clustering não supervisionado.
- Gerar insights pedagógicos por grupo de alunos com apoio de LLM.
- Oferecer rastreabilidade completa por questão, submissão e turma.

---

## 3. Arquitetura Geral

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend (React/Vite)                     │
│                        [em desenvolvimento]                      │
└───────────────────────────────┬──────────────────────────────────┘
                                │ HTTP (REST)
┌───────────────────────────────▼──────────────────────────────────┐
│                    Backend (FastAPI + Python)                     │
│                                                                  │
│  ┌─────────────────┐   ┌──────────────────┐   ┌───────────────┐ │
│  │   API (routes)  │   │  Engine (análise) │   │  ML / LLM     │ │
│  │  exam.py        │──▶│  dynamic_analyzer │   │  cluster.py   │ │
│  │  submission.py  │   │  static_analyzer  │   │  feedback_    │ │
│  └─────────────────┘   │  heuristics       │   │  generator.py │ │
│                        │  semantic_extractor│   └───────────────┘ │
│                        └──────────┬────────┘                     │
│                                   │                              │
│  ┌────────────────────────────────▼─────────────────────────┐   │
│  │             Services (orquestração de lógica)            │   │
│  │  exam_service.py        submission_service.py            │   │
│  └────────────────────────────────┬─────────────────────────┘   │
│                                   │                              │
│  ┌────────────────────────────────▼─────────────────────────┐   │
│  │              Models (ORM + schemas Pydantic)             │   │
│  │  orm.py          schemas.py          database.py         │   │
│  └────────────────────────────────┬─────────────────────────┘   │
└───────────────────────────────────┼──────────────────────────────┘
                                    │ SQLAlchemy
                    ┌───────────────▼────────────────┐
                    │        PostgreSQL               │
                    │  (gerenciado via Alembic)       │
                    └────────────────────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │  Docker — gcc:latest           │
                    │  (compilação/execução isolada) │
                    └────────────────────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │  Google Gemini 2.5 Flash (API) │
                    │  (extração de prova + insights) │
                    └────────────────────────────────┘
```

### Princípio de organização

O backend segue uma separação em camadas:

| Camada | Responsabilidade |
|---|---|
| `api/routes/` | Recebe requisições HTTP, valida parâmetros, delega a serviços |
| `services/` | Orquestra a lógica de negócio combinando múltiplos módulos |
| `engine/` | Processamento técnico: compilação, AST, heurísticas, extração semântica |
| `ml/` | Machine Learning: clustering, redução de dimensionalidade |
| `llm/` | Integração com LLM para geração de feedback |
| `models/` | ORM (SQLAlchemy), schemas de validação (Pydantic) e sessão de banco |

---

## 4. Stack Tecnológico

### Backend

| Biblioteca | Versão | Papel |
|---|---|---|
| **FastAPI** | 0.135.3 | Framework web assíncrono; roteamento, validação automática via Pydantic, documentação OpenAPI |
| **SQLAlchemy** | 2.0.49 | ORM para PostgreSQL; define modelos relacionais como classes Python |
| **Alembic** | 1.18.4 | Migrações incrementais do schema do banco; permite evoluir o banco sem perder dados |
| **psycopg2-binary** | 2.9.11 | Driver PostgreSQL para Python |
| **Pydantic** | (via FastAPI) | Validação de tipos nos schemas de entrada e saída da API |
| **python-dotenv** | — | Leitura de variáveis de ambiente do arquivo `.env` |
| **python-multipart** | — | Suporte ao upload de arquivos via `multipart/form-data` |

### Análise de Código C

| Biblioteca | Versão | Papel |
|---|---|---|
| **pycparser** | 3.0 | Parseia código C em uma AST (Abstract Syntax Tree) em Python; permite inspecionar estruturas de controle sem executar o código |
| **Docker CLI** | sistema | Compila e executa código C do aluno em contêiner isolado (`gcc:latest`, `--network none`, timeout de 5 s) |

### Machine Learning

| Biblioteca | Versão | Papel |
|---|---|---|
| **scikit-learn** | 1.8.0 | TF-IDF (`TfidfVectorizer`), binarização de AST (`MultiLabelBinarizer`), one-hot encoding (`OneHotEncoder`), Silhouette Score |
| **umap-learn** | 0.5.12 | UMAP: redução de dimensionalidade; 5 componentes para clustering, 2 para visualização |
| **hdbscan** | 0.8.42 | HDBSCAN: algoritmo de clustering baseado em densidade; detecta clusters de forma e tamanho variados, marca outliers como −1 |
| **numpy** | 2.4.4 | Operações vetoriais e matriciais; manipulação de embeddings |
| **pandas** | 3.0.2 | Manipulação tabular de dados (uso auxiliar) |
| **scipy** | (via sklearn) | `hstack` para concatenação de matrizes esparsas |
| **matplotlib** | 3.10.9 | Geração de gráficos scatter comparativos das estratégias |

### LLM / IA

| Biblioteca | Versão | Papel |
|---|---|---|
| **google-genai** | 1.73.1 | SDK oficial do Google Gemini; utiliza o modelo `gemini-2.5-flash` para extração estruturada de questões e geração de insights pedagógicos |

### Extração de Documentos

| Biblioteca | Papel |
|---|---|
| **pymupdf** | Leitura de arquivos PDF |
| **python-docx** | Leitura de arquivos DOCX |

### Testes

| Biblioteca | Papel |
|---|---|
| **pytest** | Runner de testes; fixtures, markers, parametrização |
| **pytest-mock** | Mocking simplificado com `mocker.patch` |
| **httpx** | Cliente HTTP usado pelo `TestClient` do FastAPI nos testes de integração |

---

## 5. Módulos do Backend

### `app/engine/dynamic_analyzer.py`

Compila e executa código C do aluno usando Docker.

**Funcionamento:**
1. Salva o código em um diretório temporário (`tempfile.TemporaryDirectory`)
2. Executa `docker run gcc:latest gcc -Wall student_code.c -o exe.out` com `--network none` e timeout de 30 s
3. Se compilou, executa `./exe.out` para cada caso de teste com timeout de 5 s por caso
4. Retorna um dict com `success`, `compile_error`, `warnings`, `test_results`, `all_tests_passed`

**Decisão:** usar Docker garante isolamento total — código malicioso do aluno não acessa a rede nem o sistema de arquivos do host. O flag `--network none` é essencial.

---

### `app/engine/static_analyzer.py`

Analisa a AST do código C sem executá-lo.

**Funcionamento:**
1. Remove diretivas `#include` via regex (pycparser não resolve headers da stdlib)
2. Parseia o C limpo com `pycparser.c_parser.CParser`
3. Percorre a AST com `ControlFlowVisitor` (visitor pattern) coletando: `If`, `For`, `While`, `DoWhile`, `Switch`
4. Retorna lista de estruturas encontradas

**Decisão:** remover `#include` antes do parsing é necessário porque pycparser é um parser puro de C — ele não tem acesso aos arquivos de cabeçalho da biblioteca padrão. Isso é suficiente para análise estrutural.

---

### `app/engine/heuristics.py`

Cruza os resultados dinâmico + estático para produzir diagnóstico pedagógico.

**Categorias de erro produzidas:**

| Categoria | Condição de disparo |
|---|---|
| Correto | Todos os testes passaram e estruturas estão conformes |
| Saída Incorreta | Compilou, mas ≥1 teste falhou por saída errada |
| Sintaxe — Ponto e Vírgula Ausente | Compilação falhou com `expected ';'` |
| Sintaxe — Variável Não Declarada | Compilação com `undeclared` ou `was not declared` |
| Sintaxe — Cabeçalho Faltando | `implicit declaration of function` |
| Linker — Função Indefinida | `undefined reference` |
| Semântica — Tipo Incompatível | `incompatible type` ou `invalid conversion` |
| Semântica — Retorno Ausente | `control reaches end of non-void function` |
| Loop Infinito — Controle de Fluxo | Timeout com laço detectado na AST |
| Timeout Anômalo | Timeout sem laço (recursão infinita ou scanf preso) |
| Acesso Indevido à Memória | Segmentation fault |
| Erro Aritmético — Divisão por Zero | Floating point exception |
| Violação de Estrutura | Estrutura obrigatória ausente ou proibida presente |
| Aviso — Variável Não Inicializada | Warning `uninitialized` |
| Aviso — Variável Não Utilizada | Warning `unused variable` |
| Estrutura Suspeita — Excesso de Condicionais | ≥4 `if` sem nenhum laço |

---

### `app/engine/semantic_extractor.py`

Usa Gemini para extrair estruturadamente as questões de um texto de prova.

**Decisão:** usar LLM para isso evita regex frágil. O modelo recebe o texto bruto da prova e retorna JSON com questões, enunciados, estruturas obrigatórias/proibidas e tipo de questão.

---

### `app/ml/cluster.py`

Agrupa submissões de uma questão usando UMAP + HDBSCAN.

Veja detalhes completos na seção [7. Pipeline de ML](#7-pipeline-de-ml--clustering).

---

### `app/llm/feedback_generator.py`

Gera insights pedagógicos por cluster usando Gemini 2.5 Flash.

Veja detalhes na seção [8. LLM — Geração de Feedback por Cluster](#8-llm--geração-de-feedback-por-cluster).

---

### `app/services/exam_service.py`

Orquestra o fluxo de upload e processamento de uma prova:
1. Extrai texto do PDF/DOCX via `document_parser`
2. Chama `semantic_extractor` para obter a estrutura de questões via Gemini
3. Persiste `Exam` e `Question` no banco

---

### `app/services/submission_service.py`

Orquestra a avaliação de uma submissão:
1. Busca questão e casos de teste no banco
2. Chama `dynamic_analyzer` (compilação + execução Docker)
3. Chama `static_analyzer` (AST pycparser)
4. Chama `heuristics.classify_error` para diagnóstico
5. Persiste `Submission` e `SubmissionTestResult` no banco

---

## 6. Pipeline de Avaliação de Código

```
Aluno envia código C
        │
        ▼
POST /submission/evaluate
        │
        ▼
submission_service.evaluate_submission()
        │
        ├──▶ dynamic_analyzer.compile_and_run()
        │         └── docker run gcc:latest (isolado, sem rede, timeout 5s/TC)
        │             retorna: compile_error, warnings, test_results[]
        │
        ├──▶ static_analyzer.extract_control_flow()
        │         └── pycparser AST
        │             retorna: structures["If", "For", "While", ...]
        │
        ├──▶ heuristics.classify_error()
        │         └── cruza dinâmico + estático + regras pedagógicas
        │             retorna: error_category, diagnosis, feedback
        │
        └──▶ Persiste Submission + SubmissionTestResult no PostgreSQL
```

**Saída para o aluno:**
- Resultado de cada caso de teste (entrada, saída esperada, saída obtida, passou?)
- Diagnóstico pedagógico da categoria de erro
- Feedback acionável (o que fazer para corrigir)
- Check de conformidade estrutural (estruturas obrigatórias/proibidas)

---

## 7. Pipeline de ML — Clustering

### Objetivo

Após a prova, o professor dispara o clustering de uma questão para identificar grupos de alunos com padrões de erro similares — sem precisar ler cada submissão individualmente.

### Fluxo

```
POST /exam/{id}/questions/{n}/cluster?strategy=tfidf_behavioral
        │
        ▼
cluster_question(question_id, db, strategy)
        │
        ├──▶ Busca todas as Submission da questão (com test_results via joinedload)
        │
        ├──▶ _build_features(codes, ast_lists, submissions, strategy)
        │         └── constrói matriz de features conforme estratégia
        │
        ├──▶ UMAP (clustering): n_components=min(5, n-1), min_dist=0.0
        │         └── reduz para espaço de baixa dimensão otimizado para densidade
        │
        ├──▶ UMAP (visualização): n_components=2
        │         └── reduz para 2D para scatter plot
        │
        ├──▶ HDBSCAN(min_cluster_size=2).fit_predict()
        │         └── retorna labels; −1 = outlier
        │
        ├──▶ Silhouette Score (sobre embedding de clustering)
        │         └── calculado apenas se ≥2 clusters reais encontrados
        │
        └──▶ Persiste cluster_id, umap_x, umap_y em cada Submission
             Cria registros QuestionCluster (cluster_label, size, dominant_error,
             representative_submission_id)
```

### Estratégias de Features

Quatro estratégias incrementais foram implementadas para comparação:

#### `tfidf` — Baseline

```
Features = TF-IDF(código) ⊕ OneHot(estruturas AST)
```

- TF-IDF sobre tokens do código C (`[a-zA-Z_][a-zA-Z0-9_]*`)
- Binarização das estruturas de controle presentes na AST

**Limitação:** em turmas de CS1, os programas são curtos e compartilham vocabulário comum (main, int, printf, scanf, return). Diferenças semânticas ficam invisíveis ao bag-of-words.

#### `tfidf_ngram` — Bigrams

```
Features = TF-IDF-bigram(código) ⊕ OneHot(AST)
```

- Igual ao baseline, mas com `ngram_range=(1, 2)`: capta pares de tokens adjacentes (ex: `int main`, `return 0`), preservando algum contexto local de sequência.

#### `tfidf_category` — Com Categoria de Erro

```
Features = TF-IDF(código) ⊕ OneHot(AST) ⊕ OneHot(error_category)
```

- Adiciona a categoria de erro classificada pelas heurísticas como feature categórica.
- **Motivação:** alunos com o mesmo tipo de erro tendem a ter padrões semelhantes de código; a categoria atua como sinal discriminativo forte.

#### `tfidf_behavioral` — Comportamental (mais rico)

```
Features = TF-IDF-bigram(código) ⊕ OneHot(AST) ⊕ OneHot(error_category)
           ⊕ [compilou(0/1), fração_testes_passados(0–1)]
```

- Combina todas as anteriores com features comportamentais contínuas:
  - `compilou`: 1.0 se não houve erro de compilação, 0.0 caso contrário
  - `fração_TC`: proporção de casos de teste que passaram

### Parâmetros Adaptativos

Para funcionar com qualquer tamanho de turma (mínimo 3 submissões):

```python
n_components_cluster = min(5, n - 1)   # UMAP não pode ter n_components >= n_samples
n_neighbors          = min(15, n - 1)  # UMAP precisa de n_neighbors < n_samples
umap_init            = "random" if n < 10 else "spectral"  # spectral falha com datasets muito pequenos
```

### Silhouette Score

Métrica de qualidade de clustering calculada sobre o espaço UMAP de clustering (5D):

```
s(i) = (b − a) / max(a, b)
```

- `a`: distância média do ponto i aos demais pontos do **mesmo cluster** (coesão)
- `b`: distância média do ponto i ao **cluster vizinho mais próximo** (separação)
- Score final: média de s(i) para todos os pontos não-outlier
- Escala: −1 (pior) a +1 (melhor); valores acima de 0.5 indicam clusters razoavelmente compactos e separados

**Observação importante:** Silhouette é uma métrica geométrica, não semântica. Um score alto com menos clusters pode indicar oversimplificação (fusão de grupos pedagogicamente distintos). O número de clusters encontrado deve ser comparado com os grupos esperados.

### Script de Comparação Visual

```bash
python scripts/demo_visualization.py --out comparacao.png
# dados sintéticos, sem banco necessário

python scripts/compare_strategies.py --question_id 1 --out comparacao.png
# dados reais do banco
```

Gera um PNG 2×2 com scatter UMAP por estratégia, exibindo Silhouette Score, número de clusters e outliers em cada painel. Cor da borda = grupo verdadeiro (no script de demo); cor de preenchimento = cluster atribuído pelo HDBSCAN.

---

## 8. LLM — Geração de Feedback por Cluster

Após o clustering, o professor pode solicitar insights pedagógicos por grupo:

```
POST /exam/{id}/questions/{n}/insights
        │
        ▼
Para cada QuestionCluster da questão:
    Prompt → Gemini 2.5 Flash
    Contexto: enunciado + código representativo + erro dominante + tamanho do grupo
    Resposta: insight pedagógico (máx. 4 frases)
        │
        ▼
Retorna lista de ClusterInsight {cluster_id, size, dominant_error, insight}
```

**Decisão de modelo:** `gemini-2.5-flash` foi escolhido por oferecer boa qualidade de raciocínio pedagógico com latência aceitável e custo reduzido em relação ao modelo Pro. A API é usada via SDK oficial `google-genai`.

**Representante de cluster:** a submissão enviada ao Gemini é a mais próxima ao centróide geométrico do cluster no espaço UMAP 2D — ou seja, a mais "típica" do grupo.

---

## 9. Banco de Dados

### Schema (PostgreSQL)

```
exams
  id            PK
  filename      VARCHAR
  raw_text      TEXT
  created_at    DATETIME

questions
  id            PK
  exam_id       FK → exams.id
  number        VARCHAR          -- ex: "1", "2a"
  statement     TEXT
  required_structures   JSON     -- ex: ["For", "If"]
  forbidden_structures  JSON
  requires_loop         BOOLEAN

test_cases
  id            PK
  question_id   FK → questions.id
  input         TEXT
  expected_output TEXT

submissions
  id            PK
  question_id   FK → questions.id
  code          TEXT
  compile_error TEXT
  warnings      TEXT
  all_tests_passed  BOOLEAN (nullable)
  error_category    VARCHAR
  pedagogical_diagnosis TEXT
  actionable_feedback   TEXT
  ast_structures    JSON         -- estruturas encontradas pelo static_analyzer
  cluster_id        INTEGER (nullable)  -- label HDBSCAN (−1 = outlier)
  umap_x            VARCHAR (nullable)  -- coordenada X no espaço UMAP 2D
  umap_y            VARCHAR (nullable)
  submitted_at      DATETIME

submission_test_results
  id            PK
  submission_id FK → submissions.id
  input         TEXT
  expected_output TEXT
  actual_output TEXT
  passed        BOOLEAN

question_clusters
  id            PK
  question_id   FK → questions.id
  cluster_label INTEGER          -- label do HDBSCAN
  size          INTEGER          -- quantidade de submissões no cluster
  dominant_error VARCHAR         -- categoria de erro mais frequente no cluster
  representative_submission_id FK → submissions.id (nullable)
```

### Migrações Alembic

| Revisão | Arquivo | Conteúdo |
|---|---|---|
| `0001` | `0001_initial_schema.py` | Cria tabelas base: exams, questions, test_cases, submissions, submission_test_results |
| `0002` | `0002_ml_clustering.py` | Adiciona ast_structures, cluster_id, umap_x, umap_y à submissions; cria question_clusters |

**Decisão:** Alembic foi adotado para garantir que alterações de schema sejam rastreadas em código e versionadas junto ao repositório. O `create_all` automático do SQLAlchemy foi removido para evitar divergências entre ambientes.

Comandos:
```bash
alembic upgrade head       # aplica todas as migrações pendentes
alembic downgrade -1       # reverte a última migração
alembic revision --autogenerate -m "descricao"  # gera nova migração
```

---

## 10. API — Endpoints

Base URL: `http://localhost:8000`

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/` | Health check |
| POST | `/exam/upload` | Upload de prova (PDF/DOCX); extrai questões via Gemini |
| GET | `/exam/{exam_id}` | Retorna estrutura da prova |
| POST | `/exam/{exam_id}/questions/{number}/testcases` | Adiciona casos de teste a uma questão |
| GET | `/exam/{exam_id}/results` | Resultados agregados de todas as questões |
| POST | `/exam/{exam_id}/questions/{number}/cluster` | Executa clustering das submissões |
| POST | `/exam/{exam_id}/questions/{number}/insights` | Gera insights pedagógicos por cluster via LLM |
| POST | `/submission/evaluate` | Aluno submete código; retorna diagnóstico e resultados |

### Query parameters de `/cluster`

| Parâmetro | Tipo | Default | Valores |
|---|---|---|---|
| `strategy` | string | `tfidf` | `tfidf`, `tfidf_ngram`, `tfidf_category`, `tfidf_behavioral` |

### Resposta de `/cluster`

```json
{
  "question_number": "1",
  "total_submissions": 25,
  "strategy": "tfidf_behavioral",
  "silhouette_score": 0.712,
  "clusters": [
    {
      "cluster_id": 0,
      "size": 8,
      "dominant_error": "Saída Incorreta",
      "representative_submission_id": 42,
      "representative_code": null
    }
  ],
  "scatter": [
    {"submission_id": 10, "x": 3.14, "y": -1.27, "cluster_id": 0}
  ]
}
```

---

## 11. Decisões de Design

### Docker para compilação

**Alternativas consideradas:** subprocess direto com GCC instalado no host.  
**Decisão:** Docker com `gcc:latest`, `--network none`, timeout de 5 s por caso de teste.  
**Motivo:** isolamento completo evita que código malicioso do aluno comprometa o servidor. A flag `--network none` é especialmente importante.

### pycparser para AST estática

**Alternativas consideradas:** regex sobre o código-fonte; tree-sitter.  
**Decisão:** pycparser produz uma AST completa e tipada do C padrão. Regex seria frágil para código C arbitrário. tree-sitter seria uma alternativa válida, mas pycparser é puro Python e não requer compilação de binários.  
**Trade-off:** pycparser não resolve headers; a remoção das diretivas `#include` via regex é uma simplificação válida para análise estrutural.

### UMAP + HDBSCAN

**Alternativas consideradas:** PCA + K-Means; t-SNE + DBSCAN.  
**Decisão:** UMAP preserva estrutura local e global melhor que t-SNE para dados de alta dimensão; HDBSCAN detecta clusters de densidade variável sem precisar definir número de clusters a priori.  
**Trade-off:** UMAP tem inicialização não-determinística com `spectral` para datasets pequenos; resolvido com `init="random"` quando `n < 10`.

### Quatro estratégias de features

**Motivação:** código C de CS1 é curto e compartilha vocabulário. TF-IDF puro produz vetores quase idênticos para programas semanticamente diferentes. As estratégias adicionam informação ortogonal progressivamente: bigrams → contexto local; error_category → semântica de resultado; features comportamentais → comportamento de execução.

### Alembic para migrações

**Alternativas consideradas:** `Base.metadata.create_all()` automático.  
**Decisão:** Alembic foi adotado para ter rastreabilidade de mudanças de schema em código versionado, permitindo evoluir o banco em produção sem perder dados.

### Gemini 2.5 Flash

**Alternativas consideradas:** GPT-4o; modelos locais (Ollama).  
**Decisão:** Gemini 2.5 Flash oferece boa qualidade de raciocínio pedagógico, resposta em PT-BR nativa, custo inferior ao Pro e integração simples via SDK oficial do Google.

---

## 12. Sistema de Testes

### Estrutura

```
tests/
  conftest.py              -- fixtures compartilhadas: banco de teste, client, factories
  test_exam.py             -- testes de upload e gerenciamento de provas (10 testes)
  test_submission.py       -- testes de submissão e avaliação de código (5 testes)
  test_clustering.py       -- testes de clustering via API (7 testes)
  test_insights.py         -- testes de geração de insights via LLM (4 testes)
  unit/
    test_cluster_logic.py  -- testes unitários das funções de ML (12 testes)
  integration/
    test_full_flow.py      -- testes de integração com Docker e Gemini reais (6 testes)
```

**Total: 38 testes automatizados** (excluindo integração)

### Banco de testes

O conftest cria um banco PostgreSQL separado (`learning_analytics_test`) com o mesmo schema do banco de produção. Cada teste começa com as tabelas limpas via fixture `clean_tables` (autouse).

### Fixtures principais

| Fixture | Descrição |
|---|---|
| `db` | Sessão SQLAlchemy conectada ao banco de teste |
| `client` | `TestClient` do FastAPI com `get_db` sobrescrito para usar o banco de teste |
| `exam_factory` | Cria `Exam` + `Question`s no banco com parâmetros configuráveis |
| `submission_factory` | Cria `Submission` com código, categoria de erro e AST configuráveis |
| `clean_tables` | Limpa todas as tabelas após cada teste (autouse) |

### Mocking do ML

Os testes de clustering mockam UMAP e HDBSCAN para ter resultados determinísticos:

```python
umap_patch = patch("app.ml.cluster.UMAP", side_effect=[mock_umap(n), mock_umap(n)])
hdbscan_patch = patch("app.ml.cluster.HDBSCAN", return_value=mock_hdbscan([0, 0, 1]))
with umap_patch, hdbscan_patch:
    resp = client.post(f"/exam/{exam.id}/questions/1/cluster")
```

### Testes de integração (marcados com `@pytest.mark.integration`)

Requerem Docker rodando e `GEMINI_API_KEY` configurada. Executam o pipeline completo com código C real:
- Grupos de código correto com `for` / `while` / recursão
- Verificação de que HDBSCAN separa os grupos
- Validação de que o Gemini retorna texto coerente

```bash
pytest tests/integration/ -m integration -v
```

### Como rodar os testes

```bash
cd backend
source venv/bin/activate

# Testes rápidos (sem Docker nem Gemini)
pytest tests/ --ignore=tests/integration

# Testes de integração (requer Docker + GEMINI_API_KEY)
pytest tests/integration/ -m integration -v
```

---

## 13. Como Executar

### Pré-requisitos

- Python 3.12+
- PostgreSQL rodando localmente
- Docker com imagem `gcc:latest` (`docker pull gcc:latest`)
- `GEMINI_API_KEY` válida

### Configuração

```bash
# 1. Clone o repositório
cd backend

# 2. Crie e ative o virtualenv
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com DATABASE_URL e GEMINI_API_KEY

# 5. Crie o banco e aplique as migrações
createdb learning_analytics
alembic upgrade head

# 6. Inicie o servidor
uvicorn app.main:app --reload
# API disponível em http://localhost:8000
# Documentação interativa em http://localhost:8000/docs
```

### Banco de testes

```bash
createdb learning_analytics_test
pytest tests/ --ignore=tests/integration
```

### Gerar visualização comparativa de clustering

```bash
# Com dados sintéticos (não precisa de banco)
python scripts/demo_visualization.py --out comparacao_demo.png

# Com dados reais do banco
python scripts/compare_strategies.py --question_id 1 --out comparacao.png
```

---

## 14. Pendências e Trabalho Futuro

| Item | Status | Descrição |
|---|---|---|
| Frontend React/Vite | Não iniciado | Interface visual para professor e aluno; boilerplate Vite criado |
| Deploy | Não iniciado | Planejado: ngrok para testes, Oracle Cloud Free Tier para produção |
| Autenticação | Não implementado | Sistema sem auth por enquanto; necessário para deploy |
| Feedback LLM por submissão individual | Não implementado | Gemini poderia gerar feedback personalizado por aluno além do por cluster |
| Comparação entre turmas/semestres | Não implementado | Análise longitudinal de evolução dos erros |
| Exportação de relatórios | Não implementado | PDF ou CSV com resultados agregados por questão |
| Suporte a outras linguagens | Fora de escopo | Sistema projetado para C; extensível com novos analisadores |
