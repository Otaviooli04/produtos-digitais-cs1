# Alinhamento: landing page × sistema

**Disciplina:** Produtos Digitais · Levantamento de 12/09/2026

A landing page em `analytics-cs1-landing` virou uma promessa pública: ela mostra
telas, descreve jornadas e afirma números. Este documento confere promessa por
promessa contra o código, isola o que não existe e define o plano para fechar a
distância.

Complementa `mapa-funcionalidades.md`, que liga os documentos da disciplina ao
código. A diferença é a fonte: lá a origem é o roadmap, aqui é o que o visitante
lê e passa a esperar.

**Resultado do levantamento:** a landing está honesta em quase tudo. De 24
promessas verificáveis, 18 estão prontas, 6 não. Nenhuma das 6 é invenção de
marketing: são funcionalidades que existem pela metade ou que dependem de um
passo manual que a página não menciona.

---

## 1. Método

Cada afirmação da landing que descreve comportamento do sistema virou uma linha.
Afirmações de valor ("o erro passa a ter nome") só entraram quando têm uma
contrapartida verificável no código. Números medidos (539, 99,6%, 3,91×) não
entram aqui porque são resultado de validação, não funcionalidade.

Evidência é sempre `arquivo:linha`. Onde escrevi "não existe", procurei pelo
conceito no ORM, nas rotas, nos serviços e no frontend antes de concluir.

---

## 2. O que a landing promete e o sistema entrega

### Lado do aluno

| Promessa na landing | Estado | Evidência |
|---|---|---|
| Entra na turma com o código que o professor divulga | Pronta | `api/routes/student.py:72`, `Turma.codigo_acesso` |
| Cria conta própria, separada da do professor | Pronta | `auth/student_service.py`, `frontend/src/pages/aluno/AlunoRegisterPage.jsx` |
| Escreve o C na própria página, sem instalar nada | Pronta | `pages/aluno/QuestaoPage.jsx`, editor embutido |
| Modo treino com tentativas ilimitadas | Pronta | `Exam.modo`, `student_activity_service.py:_restantes` |
| Modo prova com janela e teto de tentativas | Pronta | `Exam.abre_em/fecha_em/max_tentativas`, `_situacao` |
| Recebe tipo do erro, causa, linha e o que fazer | Pronta | `engine/heuristics.py`, 27 categorias |
| Vê os casos de teste: "Testes 2/3 passaram", entrada, esperado, obtido | Pronta | `components/TentativaDetalhe.jsx:89-95`, `TestResult` |
| Botão "explicar meu erro", sob demanda, sobre o próprio código | Pronta | `TentativaDetalhe.jsx:66`, `llm/student_explainer.py` |
| O diagnóstico não entrega a solução | Pronta | restrição no prompt de `student_explainer.py` |
| Histórico de todas as tentativas | Pronta | `Submission.attempt_number`, `historico_questao` |
| Painel: resolvidas, tentativas até acertar, acertos de primeira, dias seguidos | Pronta | `ProgressoResponse`, `pages/aluno/ProgressoPage.jsx` |
| Evolução semana a semana | Pronta | `EvolucaoPonto` |
| Erros que se repetem, com tendência e onde aconteceram | Pronta | `erros_recorrentes`, campo `questoes` |
| Navegação Turmas → Turma → Atividade → Questão | Pronta | `App.jsx:62-67`, igual à URL da tela na landing |
| **A atividade tem nome ("Lista 3 · Vetores e laços")** | **Falta** | **Lacuna 4** |
| **Só aparecem as atividades que o professor publicou** | **Falta** | **Lacuna 3** |

### Lado do professor

| Promessa na landing | Estado | Evidência |
|---|---|---|
| Sobe o arquivo da prova e recebe questões e casos de teste prontos | Pronta | `engine/semantic_extractor.py`, job em `jobs.py` |
| Revisa questões e casos de teste antes de liberar | Parcial | telas existem (`QuestionPage`, `TestCasesPage`), falta o portão: **Lacuna 3** |
| Cria turma, define treino ou prova, divulga o código de acesso | Pronta | `turma.py`, `DisponibilidadeCard.jsx` |
| Cada grupo mostra código de exemplo e as linhas do erro | Pronta | `exam.py:382-430`, `highlight_lines` |
| Vê a lista de quem caiu em cada grupo | Parcial | `QuestionPage.jsx:233`, mas some quem não tem matrícula: **Lacuna 5** |
| Relatório de esforço economizado | Pronta | `services/effort_report_service.py` |
| Nota por questão com peso próprio | Pronta | `Question.points` |
| **"Os envios chegam separados por tipo de erro"** | **Falta** | **Lacuna 1** |
| **"Responda uma vez para o grupo inteiro"** | **Falta** | **Lacuna 2** |
| **"Dificuldades que atravessam a turma de uma prova para a outra"** | **Falta** | **Lacuna 6** |

### Promessas que não geram trabalho

| Afirmação | Por que está resolvida |
|---|---|
| "Para a coordenação: evidência antes da reprovação" | É proposta de valor, não tela. O que sustenta já existe em `GET /turma/{id}/analytics` |
| "Entrada sem turma" | A landing já diz que ainda não abriu, e coleta e-mail para avisar |
| "Gratuito na fase de piloto" | Não há cobrança no sistema, então a afirmação é verdadeira por construção |
| "No modo prova valem a janela e o limite" | É exatamente o que existe. A landing não promete antifraude, e não deve passar a prometer |

Vale registrar que a landing é **mais conservadora que o roadmap**: ela não
promete trilha direcionada nem geração de exercícios, que continuam sendo o
maior item em aberto do produto. Não há dívida de marketing ali.

---

## 3. As seis lacunas

### Lacuna 1 · O agrupamento não roda sozinho

**A landing diz:** "Os envios chegam separados por tipo de erro."
O verbo "chegam" promete automático.

**O que acontece:** `cluster_question` só é chamada em dois lugares, o fim do
lote (`bulk_submission_service.py:132`) e o botão do professor
(`exam.py:348`). No fluxo real da turma, em que os alunos enviam um a um ao
longo de dias, **nenhum dos dois dispara**. O professor abre a aba de grupos e
vê o estado de quando apertou o botão pela última vez, sem nada indicando que
chegaram submissões novas depois.

**Por que não é só chamar a função a cada envio:** `cluster_question` roda UMAP
(`ml/cluster.py:139`) para produzir o scatter, e isso custa segundos. Rodar em
cada submissão de aluno é desperdício.

**Spec:**

1. Separar o que é barato do que é caro. O agrupamento real é
   `two_level_labels` (`ml/cluster.py:40`), determinístico por assinatura de
   falha e barato. O UMAP só alimenta a visualização.
2. Criar `atribuir_grupo(submission, db)`, chamada no fim de
   `student_activity_service.submeter`: recalcula os rótulos da questão e
   persiste `cluster_id` e `QuestionCluster`, sem tocar em UMAP.
3. Coordenadas do scatter passam a ser recalculadas só no botão "Recalcular" e
   na primeira abertura da aba quando não existirem.
4. `QuestionCluster` ganha `atualizado_em`. A aba mostra "agrupado há X" e, se
   houver envio mais novo que isso, oferece recalcular.
5. Limpeza: `umap_cluster` em `ml/cluster.py:125` é construído e nunca usado.

**Como conferir:** enviar 4 códigos com o mesmo erro por contas diferentes de
aluno e abrir a aba de grupos sem apertar nada. Os 4 precisam estar juntos.

---

### Lacuna 2 · Não existe resposta do professor por grupo

**A landing diz:** "Responda uma vez por grupo" e "em vez de escrever 60
retornos parecidos, você retoma em aula ou responde por escrito ao grupo
inteiro". É o passo 4 da jornada do professor e o centro da proposta de valor.

**O que acontece:** `QuestionCluster.insight` (`orm.py:162`) existe, mas é o
texto que o Gemini escreve **para o professor**, e nunca sai do painel dele. Não
há campo para o professor escrever, não há endpoint para salvar e não há nada no
lado do aluno que leia isso. Hoje "responder ao grupo" acontece fora do sistema.

**É a maior lacuna do levantamento** e a única que quebra uma jornada inteira.

**Spec:**

1. **Banco** (migração 0013): `QuestionCluster.resposta_professor` (Text),
   `resposta_em` (DateTime) e `resposta_por` (FK professor).
   Não reaproveitar `insight`: um é máquina, outro é pessoa, e misturar os dois
   apaga a distinção que a própria landing vende.
2. **Backend:**
   - `PUT /exam/{id}/questions/{num}/groups/{cluster_id}/resposta` salva o texto.
   - O aluno recebe a resposta na tentativa: `TentativaResponse` ganha
     `resposta_do_professor` e `resposta_do_professor_em`, preenchidos quando a
     submissão tem `cluster_id` e aquele grupo tem resposta.
   - Regra: só a submissão **mais recente** do aluno naquela questão carrega a
     resposta, para não repetir o mesmo texto em cinco tentativas antigas.
3. **Frontend do professor:** campo de texto por grupo em `QuestionPage.jsx`,
   ao lado do insight, com o insight do Gemini oferecido como rascunho em um
   botão "usar como ponto de partida". O professor edita e salva. O insight
   nunca vira resposta sozinho, porque "professor no comando" é valor declarado.
4. **Frontend do aluno:** bloco em `TentativaDetalhe.jsx`, visualmente distinto
   da explicação da IA, identificado como retorno do professor e com a data.

**Decisão de produto embutida:** a resposta é por grupo, mas o aluno nunca vê
que está em um grupo, nem quem mais está. Ele vê "retorno do seu professor".
Expor o agrupamento para o aluno seria dizer a ele que o retorno não é dele.

**Como conferir:** três alunos com o mesmo erro, o professor escreve uma vez,
e os três veem o mesmo texto na última tentativa. Um quarto aluno, com outro
erro, não vê nada.

---

### Lacuna 3 · Toda atividade da turma é visível assim que criada

**A landing diz:** "Revise antes de publicar para a turma", com botão "Publicar
para a turma" na tela de montagem. E, do lado do aluno, "a turma aparece com as
listas e as provas já publicadas".

**O que acontece:** `listar_atividades` (`student_activity_service.py:101`)
devolve todo `Exam` cuja `turma_id` está entre as turmas do aluno. Não existe
estado de rascunho. **No instante em que o professor sobe o PDF, a atividade já
está na tela do aluno**, com as questões que o Gemini acabou de extrair e ainda
não foram revisadas.

Isso não é só divergência com a landing, é um defeito: o aluno pode abrir uma
prova meio montada, ou uma prova que o professor ainda está preparando.

**Spec:**

1. **Banco** (migração 0013, junto com a Lacuna 4): `Exam.publicada` (Boolean,
   default `False`). Atividades existentes recebem `True` no backfill, para não
   sumirem da tela de ninguém.
2. **Backend:** filtro `Exam.publicada == True` em `listar_atividades` e em
   `_atividade_do_aluno`, que é o guarda de acesso por id. `PATCH /exam/{id}`
   passa a aceitar `publicada`.
3. **Frontend do professor:** selo "rascunho" no `ExamDashboard` e no
   `TurmaDetailPage`, com botão "Publicar para a turma". Publicação bloqueada
   enquanto houver questão sem caso de teste, que é a condição que torna a
   atividade insolúvel.
4. **Frontend do aluno:** nada muda, além de a lista passar a ser confiável.

**Como conferir:** subir um PDF numa turma com aluno matriculado e confirmar que
ele não vê nada até o professor publicar.

---

### Lacuna 4 · A atividade se chama pelo nome do arquivo

**A landing diz:** "Lista 3 · Vetores e laços" na tela do aluno e "Prova 1" na
do professor.

**O que acontece:** `titulo` é `exam.filename or f"Atividade {exam.id}"`
(`student_activity_service.py:128`). O aluno vê `prova1_2026.pdf`. O mesmo
nome de arquivo aparece no painel de erros recorrentes
(`student_activity_service.py:420`), onde a landing mostra
"Aconteceu em: Lista 2 · Q4".

**Spec:**

1. **Banco** (mesma migração 0013): `Exam.titulo` (String, nullable).
2. **Backend:** `titulo or filename or "Atividade {id}"`, nas duas funções.
   `PATCH /exam/{id}` aceita `titulo`.
3. **Frontend do professor:** título editável no `ExamDashboard`, sugerido a
   partir do nome do arquivo sem a extensão na primeira vez.

---

### Lacuna 5 · Aluno sem matrícula desaparece do grupo

**A landing mostra:** as matrículas dos alunos dentro de cada grupo
("2023001 2023014 2023022 +15").

**O que acontece:** `Student.matricula` é nullable (`orm.py:29`) e o cadastro
não exige. A submissão do aluno copia esse campo
(`student_activity_service.py:210`), e a lista do grupo filtra por
`p.matricula` (`QuestionPage.jsx:233`). **Aluno que se cadastrou sem matrícula
some da lista do grupo**, mesmo tendo submetido. O professor vê "19 alunos" e
uma lista com 12 nomes.

**Spec:**

1. O scatter passa a devolver também `student_id` e `nome`.
2. A lista do grupo mostra a matrícula quando existe e o nome quando não existe.
3. No cadastro do aluno, a matrícula continua opcional, mas ganha a explicação
   de para que serve. Tornar obrigatório fecharia a porta do autodidata, que
   está no documento de personas.

---

### Lacuna 6 · Não existe a dificuldade de uma prova para a outra

**A landing diz:** "ainda vê quais dificuldades atravessam a turma de uma prova
para a outra".

**O que acontece:** `get_turma_analytics` (`turma_service.py:169`) calcula
`top_erros` somando **todas as provas da turma juntas**, sem recorte por prova.
Dá para saber que off-by-one é o erro mais comum da turma, não que ele caiu
entre a Lista 2 e a Prova 1. O `provas[]` tem taxa de aprovação por prova, mas
nenhuma categoria de erro.

**Spec:**

1. Cada item de `provas[]` ganha `top_erros` próprio, com as 5 categorias mais
   frequentes daquela prova.
2. Resposta ganha `trajetoria`: para cada categoria que aparece em duas ou mais
   provas, a série de ocorrências por prova, em ordem cronológica.
3. Tela na turma do professor: uma linha por categoria persistente, mostrando se
   subiu ou caiu da prova anterior para a seguinte. Mesmo espírito da tendência
   que o aluno já vê em erros recorrentes, um nível acima.

---

## 4. Planejamento

Quatro fases. A ordem não é por tamanho, é por dependência e por quanto cada uma
torna a landing verdadeira.

### Fase 1 · Fundação da turma (Lacunas 3, 4 e 5)

Uma migração só (0013: `Exam.publicada`, `Exam.titulo`), superfície pequena,
nenhuma dependência. Fecha o defeito de vazamento de prova não revisada, que é
o item mais urgente do levantamento inteiro, e faz a tela do aluno parar de
mostrar nome de arquivo.

- Migração 0013 com backfill `publicada = True` nas atividades existentes
- Filtro de publicação nas duas funções de acesso do aluno
- `PATCH /exam` aceitando `publicada` e `titulo`
- Selo de rascunho, botão de publicar e título editável no painel do professor
- Matrícula ou nome na lista do grupo

**Destrava:** o piloto pode receber turma de verdade sem risco de prova vazada.

### Fase 2 · O grupo se forma sozinho (Lacuna 1)

- `atribuir_grupo` chamada no fim de `submeter`
- Separação entre rótulo (barato, a cada envio) e scatter (caro, sob demanda)
- `atualizado_em` no `QuestionCluster` e aviso de desatualizado na aba
- Remoção do `umap_cluster` morto

**Destrava:** a Fase 3. Sem grupo formado no fluxo da turma não há a quem
responder.

### Fase 3 · O retorno por grupo (Lacuna 2)

A maior. Depende inteiramente da Fase 2.

- Migração 0014 com os três campos de resposta
- Endpoint de gravação e propagação para `TentativaResponse`
- Campo do professor com o insight como rascunho opcional
- Bloco do aluno, identificado como retorno do professor

**Destrava:** a jornada do professor passa a existir ponta a ponta, e o passo 4
da landing deixa de ser promessa.

### Fase 4 · A turma ao longo do semestre (Lacuna 6)

Isolada, pode ser feita a qualquer momento depois da Fase 1. Fica por último
porque é a única cuja ausência ninguém percebe no piloto de uma prova só.

- `top_erros` por prova e série `trajetoria`
- Tela de categorias persistentes na turma

---

## 5. O que fazer com a landing enquanto isso

Nada. Nenhuma das seis lacunas exige mudar o texto, porque nenhuma é falsa por
invenção: são funcionalidades que o sistema quase tem. O caminho certo é
construir, não recuar o texto.

Duas ressalvas, se alguma fase for adiada:

- **Se a Fase 3 não sair antes do piloto**, o passo 4 da jornada do professor
  precisa mudar de "responde por escrito ao grupo inteiro" para só "retoma em
  aula", que é verdade hoje.
- **Se a Fase 2 não sair antes do piloto**, "os envios chegam separados por tipo
  de erro" vira "você agrupa os envios com um clique".

---

## 6. Fora deste plano, de propósito

| Item | Por quê |
|---|---|
| Trilha direcionada com geração de exercícios | Continua sendo o maior item do roadmap, mas a landing não promete. Entra depois do piloto |
| Antifraude do modo prova | A landing promete janela e teto, que existem. Risco conhecido, registrado no roadmap do Mês 4 |
| Instrumentação de uso (DAU, WAU) | Nenhuma promessa pública depende disso. É necessidade de métrica interna |
| Acesso sem turma | A landing já declara como não disponível e coleta e-mail |
| Papel de coordenação | A promessa é de valor, não de tela, e o que a sustenta já existe |
