# Mapa de Funcionalidades: documento × sistema

**Disciplina:** Produtos Digitais · Estado do produto em 17/08/2026

Este documento liga o que foi prometido nas entregas da disciplina ao que existe
de fato no código. Cada linha diz onde a funcionalidade mora no repositório ou o
que falta para ela existir.

## 1. Funcionalidades prioritárias

Numeração igual à do documento "Produto, Personas, Mercado e Roadmap", seção 2.

| # | Funcionalidade | Fase | Estado | Onde está |
|---|---|---|---|---|
| 1 | Turma virtual e conta do aluno | MVP | Pronta | `models/orm.py` (Student, Enrollment, `Turma.codigo_acesso`), `auth/student_service.py`, `api/routes/student.py`, `frontend/src/pages/aluno/`, migração 0010 |
| 2 | Correção automática do código | MVP | Pronta | `engine/dynamic_analyzer.py` (Docker isolado), `engine/evaluators/code_evaluator.py` |
| 3 | Diagnóstico pedagógico do erro | MVP | Pronta | `engine/heuristics.py`, 27 categorias. Chega ao aluno em toda tentativa |
| 4 | Modo treino com tentativas ilimitadas | MVP | Pronta | `Exam.modo`, migração 0011, `services/student_activity_service.py`, `components/DisponibilidadeCard.jsx` |
| 5 | Histórico de tentativas | MVP | Pronta | `Submission.attempt_number`, `historico_questao`, `pages/aluno/QuestaoPage.jsx` |
| 6 | Painel de erros recorrentes do aluno | MVP | Pronta | `erros_recorrentes` em `student_activity_service.py`, `pages/aluno/ProgressoPage.jsx` |
| 7 | Agrupamento por assinatura de falha | MVP | Pronta | `ml/cluster.py`, aba de grupos no painel do professor |
| 8 | Montagem da prova a partir do enunciado | MVP | Pronta | `engine/semantic_extractor.py` (Gemini), job em segundo plano |
| 9 | Modo prova com janela e tentativas controladas | v2 | Parcial | Janela e teto valem em `submeter`. Falta antifraude |
| 10 | Trilha direcionada ao erro, com geração de exercícios | v2 | Não iniciada | Ver seção 4 |

Duas funcionalidades do roadmap que não estavam nessa lista também entraram:

| Funcionalidade | Mês | Estado | Onde está |
|---|---|---|---|
| Explicação individual da tentativa | 3 | Pronta | `llm/student_explainer.py`, cache em `submissions.llm_explanation`, migração 0012 |
| Relatório de esforço economizado | 4 | Pronta | `services/effort_report_service.py`, card em `ResultsPage.jsx` |

## 2. Roadmap mês a mês

| Mês | Entregou | Falta |
|---|---|---|
| **1 · Descoberta do Cliente** | O motor roda sobre submissões reais e serve de demonstração | Landing e roteiro de entrevistas, que são trabalho fora do código |
| **2 · Turma virtual e conta do aluno** | Conta do aluno, entrada por código, lista de atividades e histórico de todas as tentativas | Nada |
| **3 · Treino direcionado** | Modo treino, painel de erros recorrentes e explicação individual | Trilha de exercícios e geração do conteúdo que ela consome |
| **4 · Prova, piloto e preço** | Janela controlada e relatório de esforço economizado | Relatório de fim de lista, antifraude e instrumentação das métricas de negócio |

## 3. Métricas do roadmap

O que o sistema já consegue calcular hoje, sem trabalho novo:

| Métrica | Situação |
|---|---|
| Nº de tentativas por aluno | Pronta, em `/aluno/progresso` |
| Queda nas tentativas até acertar | Pronta, `tentativas_por_questao_resolvida` |
| Erros recorrentes eliminados | Aproximada pela tendência por categoria em `/aluno/erros-recorrentes` |
| Taxa de ativação | Derivável de matrículas na turma versus alunos que submeteram, mas sem painel |
| Esforço economizado do professor | Pronta, em `/exam/{id}/effort-report` |
| DAU e WAU, retorno em 7 dias, retenção semanal | Não. O sistema registra submissão, não acesso, então não há como separar quem abriu de quem enviou |
| NPS | Não. Exige coleta dentro do produto |

## 4. O que falta, e o que cada item exige

1. **Trilha direcionada com geração de exercícios.** É a maior peça pendente e o
   valor "treino sob medida" depende dela. Exige uma origem para o exercício
   gerado, um seletor que escolha o próximo exercício a partir das categorias que
   o aluno mais erra e uma etapa de revisão do professor, porque "professor no
   comando" é valor declarado do produto. Também precisa de um teto de custo, já
   que gerar exercício é chamada de LLM por aluno.
2. **Antifraude do modo prova.** Hoje a janela e o teto de tentativas são as
   únicas barreiras. O risco está declarado no próprio roadmap do Mês 4.
3. **Relatório de fim de lista.** Fechamento por atividade para o aluno e para o
   professor, no mesmo espírito do relatório de esforço.
4. **Instrumentação de uso.** Sem registro de acesso não há DAU, WAU nem retorno
   em 7 dias, que são as métricas do Mês 2 e do Mês 3.
5. **Acesso sem turma.** O segmento do autodidata está no documento de personas
   como expansão, e hoje a única porta de entrada é o código da turma.

## 5. Decisões de produto ainda em aberto

- **Feedback imediato ou progressivo.** Hoje é imediato e completo. A alternativa
  discutida, dica antes de solução, muda a tela de resultado do aluno.
- **Métrica de sucesso definitiva.** O sistema já mede tentativas até acertar, que
  é a candidata mais forte, mas isso não foi fechado.
- **Nome oficial do produto.** A pasta de entrega usa "Turma Digital com Apoio de
  IA" e o sistema ainda se apresenta como "Analytics CS1".
