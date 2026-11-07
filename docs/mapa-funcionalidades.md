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
| 2 | Correção automática do código | MVP | Pronta | `engine/dynamic_analyzer.py` (Docker isolado, com limite de memória, processos e CPU, sem root e imagem fixa), `engine/evaluators/code_evaluator.py` |
| 3 | Diagnóstico pedagógico do erro | MVP | Pronta | `engine/heuristics.py`, 27 categorias. Chega ao aluno em toda tentativa |
| 4 | Modo treino com tentativas ilimitadas | MVP | Pronta | `Exam.modo`, migração 0011, `services/student_activity_service.py`, `components/DisponibilidadeCard.jsx`. Nas telas o modo `treino` se chama **Lista** (o nome Treino fica para a trilha), e a turma do professor e a do aluno separam Provas e Listas |
| 5 | Histórico de tentativas | MVP | Pronta | `Submission.attempt_number`, `historico_questao`, `pages/aluno/QuestaoPage.jsx`. Cada envio diz quantos casos passaram a mais que a tentativa anterior e sugere uma pausa depois de três envios errados e quase iguais em até cinco minutos (`services/ritmo_da_tentativa.py`, `components/RitmoDaTentativa.jsx`). O campo de código aceita Tab, mantém o recuo no Enter e numera as linhas (`components/CodeTextarea.jsx`) |
| 6 | Painel de erros recorrentes do aluno | MVP | Pronta | `erros_recorrentes` em `student_activity_service.py`, sobre o histórico de `services/historico_do_aluno.py` (listas e trilha juntas, falha técnica fora, erros superados à parte), `pages/aluno/ProgressoPage.jsx` |
| 7 | Agrupamento por assinatura de falha | MVP | Pronta | `ml/cluster.py`, aba de grupos no painel do professor |
| 8 | Montagem da prova a partir do enunciado | MVP | Pronta | `engine/semantic_extractor.py` (Gemini), job em segundo plano |
| 9 | Modo prova com janela e tentativas controladas | v2 | Parcial | Janela e teto valem em `submeter`, com trava contra envios simultâneos passarem do teto. Falta antifraude |
| 10 | Trilha direcionada ao erro, com geração de exercícios | v2 | Parcial | `services/treino_service.py`, `llm/exercise_generator.py`, `pages/aluno/TreinoPage.jsx`, migração 0016. Mostra só os erros ativos, com os superados e o "Treinar de novo" à parte. Falta a revisão do professor, ver seção 4 |

Duas funcionalidades do roadmap que não estavam nessa lista também entraram:

| Funcionalidade | Mês | Estado | Onde está |
|---|---|---|---|
| Início com novidades, continuar e prazos (RF20, RF26, experimento 1 do Plano de Growth) | 3 | Pronta | `services/novidades_service.py` (tabela `novidades` da migração 0019, com `chegou_em` e `vista_em`), `services/inicio_service.py`, `GET /aluno/inicio`, `GET /aluno/novidades/contagem`, `pages/aluno/InicioPage.jsx` e a bolinha no `AlunoLayout`. A resposta do professor ao grupo e o exercício pré-gerado viram novidade, e abrir a questão ou o exercício marca como visto |
| Dica em etapas e explicação da tentativa (RF28, experimento 2) | 3 | Pronta | `llm/student_explainer.py`, `POST /aluno/tentativas/{id}/ajuda`, `components/AjudaEmEtapas.jsx`, colunas `llm_explanation`, `llm_pistas`, `nivel_de_ajuda` e `ajuda_pedida_em` (migrações 0012 e 0021). Pista geral, pista que aponta a parte e explicação, uma de cada vez. Bloqueada na prova enquanto a questão aceita envio |
| Uso pelo celular nas telas do aluno (RNF02, item 3.4) | 3 | Em parte | Telas do aluno medidas em 360 e 390 px, sem estouro de largura e com campos em 16 px (`index.css`), menu que não gruda no celular (`AlunoLayout`) e numeração do código que acompanha a rotação (`CodeTextarea`). Falta o teste em aparelho real e o lembrete, que dependem da hospedagem e dos avisos (fases 4 e 7) |
| Relatório de esforço economizado | 4 | Pronta | `services/effort_report_service.py`, card em `ResultsPage.jsx` |

## 2. Roadmap mês a mês

| Mês | Entregou | Falta |
|---|---|---|
| **1 · Descoberta do Cliente** | O motor roda sobre submissões reais e serve de demonstração | Landing e roteiro de entrevistas, que são trabalho fora do código |
| **2 · Turma virtual e conta do aluno** | Conta do aluno, entrada por código ou convite com link, lista de atividades e histórico de todas as tentativas | Nada |
| **3 · Treino direcionado** | Modo treino, painel de erros recorrentes e explicação individual | Trilha de exercícios e geração do conteúdo que ela consome |
| **4 · Prova, piloto e preço** | Janela controlada e relatório de esforço economizado | Relatório de fim de lista, antifraude e instrumentação das métricas de negócio |

## 3. Métricas do roadmap

O que o sistema já consegue calcular hoje, sem trabalho novo:

| Métrica | Situação |
|---|---|
| Nº de tentativas por aluno | Pronta, em `/aluno/progresso`, somando provas, listas e trilha, com `tentativas_no_treino` à parte e as questões resolvidas separadas por provas e listas (`por_modo`). O cartão de dias seguidos deu lugar aos erros superados |
| Queda nas tentativas até acertar | Pronta, `tentativas_por_questao_resolvida` |
| Erros recorrentes eliminados | Pronta para o aluno: os erros superados em `/aluno/erros-recorrentes` e `/aluno/treino` (acertou um treino feito para o erro, sem repeti-lo, depois da última vez que ele apareceu). Para a turma, segue a North Star |
| North Star, erros corrigidos por semana | Pronta, no bloco "Funil da turma" (`GET /turmas/{id}/funil`) e no total de todas as turmas pelo `backend/scripts/funil.py`. Junto, a proteção (tentativas até acertar e acerto de primeira). A trilha conta numa turma só a partir da matrícula do aluno nela. A North Star também sai repartida por onde o erro foi corrigido, em provas, listas ou na trilha (`por_tipo`), e o aproveitamento da turma aparece separado por provas e listas |
| Taxa de ativação | Pronta, no bloco "Funil da turma": quem corrigiu o primeiro erro até 7 dias depois de entrar, com a meta de 60%. Ao lado, o momento de sucesso (RF16): a mediana do tempo da matrícula até o primeiro erro corrigido e quantos chegaram a ele na mesma sessão |
| Aquisição | Pronta, no bloco "Funil da turma": matriculados contra o tamanho da turma (`turmas.alunos_previstos`, que o professor preenche) e a taxa da primeira semana, com a meta de 80%. Também a origem de cada matrícula, pelo convite com link ou pelo código digitado (`enrollments.origem`) |
| Alunos em risco (vermelho e amarelo) | Pronta, no bloco "Funil da turma", só para quem tem questão em aberto (RN09) |
| Esforço economizado do professor | Pronta, em `/exam/{id}/effort-report` |
| Retenção semanal | Pronta pelo acesso, no bloco "Funil da turma": quem abriu o app na semana e já tinha feito algo antes, com a meta de 50%. Ao lado, a retenção pelo envio e os sinais de hábito: voltou sem prova marcada, abriu sem aviso e enviou por conta própria (treino ou trilha) |
| DAU e WAU, retorno medido pelo acesso | Parcial. Cada abertura do app do aluno vira um acesso (`POST /aluno/acessos`, tabela `acessos` da migração 0018), com descarte em 30 minutos e a origem `convite` quando vem do link. A retenção já usa o acesso. DAU e WAU como número ainda não aparecem em tela |
| Retorno em 7 dias com e sem novidade (experimento 1) | Dados prontos: cada novidade guarda `chegou_em` e `vista_em`, e o acesso guarda quando o aluno abriu. A comparação fica para depois do piloto |
| NPS | Não. Exige coleta dentro do produto |

## 4. O que falta, e o que cada item exige

1. **Revisão do professor na trilha.** A trilha existe desde a migração 0016,
   com o exercício gerado para o erro que o aluno mais repete, o teto de 8
   gerações por dia e o aluno reportando o exercício ruim. Desde o item 1.1 ela
   entra no progresso e nos erros recorrentes. Falta a etapa de revisão do
   professor, porque "professor no comando" é valor declarado do produto, e a
   trilha intercalada (2.5).
2. **Antifraude do modo prova.** Hoje a janela e o teto de tentativas são as
   únicas barreiras. O risco está declarado no próprio roadmap do Mês 4.
3. **Relatório de fim de lista.** Fechamento por atividade para o aluno e para o
   professor, no mesmo espírito do relatório de esforço.
4. **Instrumentação de uso.** O acesso já é registrado e a retenção semanal usa
   ele. Falta mostrar DAU, WAU e o retorno em 7 dias, que são as métricas do Mês 2
   e do Mês 3.
5. **Acesso sem turma.** O segmento do autodidata está no documento de personas
   como expansão, e hoje a única porta de entrada é a turma, pelo código ou pelo convite com link.

## 5. Decisões de produto ainda em aberto

- ~~**Feedback imediato ou progressivo.**~~ Decidido em novembro de 2026: progressivo, com a dica em etapas (item 2.3).
- **Métrica de sucesso definitiva.** O sistema já mede tentativas até acertar, que
  é a candidata mais forte, mas isso não foi fechado.
- **Nome oficial do produto.** A pasta de entrega usa "Turma Digital com Apoio de
  IA" e o sistema ainda se apresenta como "Analytics CS1".
