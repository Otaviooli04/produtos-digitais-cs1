# Treino nas métricas do aluno

**Item do plano:** 1.1 de `docs/produto/plano-implementacao.md` (treino entra nas métricas: progresso, erros recorrentes e trilha passam a ler também `tentativas_de_treino`), que responde ao achado 2 da seção 3
**Requisitos:** RF11 (erros que o aluno repete, com a tendência, e treino daquela categoria na trilha), RF36 (histórico de tentativas que monta a trilha), RN01, RN05, RNF06
**Data:** 2026-11-02

## Objetivo

O progresso, os erros recorrentes e a trilha do aluno passam a ler também as tentativas da trilha. O erro que o aluno supera treinando sai do topo da trilha e aparece como superado, e a falha técnica deixa de contar como erro dele.

## Comportamento

**Aluno, em "Meu progresso"**

1. Os quatro números do topo continuam.
   - "Questões resolvidas X/Y" e "N de M atividades concluídas" contam só as atividades publicadas das turmas do aluno. Hoje a atividade não publicada entra no Y.
   - Os outros três somam lista e treino, com novos textos de apoio:
     - Tentativas até acertar: "média nas questões e treinos que você resolveu"
     - Acertos de primeira: "questões e treinos resolvidos no primeiro envio"
     - Dias seguidos: "42 tentativas no total, 12 no treino". O trecho ", 12 no treino" só aparece quando o número é maior que zero.
2. "Semana a semana" soma lista e treino, com a legenda "Tentativas enviadas e o que você resolveu pela primeira vez, nas listas e no treino."
3. "Erros que se repetem" mostra só os erros ativos.
   - A frase do topo passa a ser "X de Y tentativas tiveram algum erro, somando listas e treino."
   - Cada cartão mostra "5× · 2 no treino · 3 nas últimas tentativas". O trecho "· 2 no treino" só aparece quando é maior que zero.
   - "Aconteceu em" junta questões e exercícios da trilha, como "Trilha · Soma dos pares".
   - Sem erro ativo e com algum superado, a seção mostra "Nenhum erro se repetindo agora." Sem erro nenhum, continua "Nenhum erro registrado ainda."
4. Seção nova "Erros que você superou", abaixo de "Erros que se repetem", só quando há algum.
   - Frase de apoio: "Você acertou um treino feito para eles depois da última vez que apareceram. Se um voltar, ele sobe para a lista de cima."
   - Cada erro numa linha: o nome curto, o selo verde "superado" e "em 28/10 · apareceu 7×".

**Aluno, no "Treino"**

1. "O que você mais erra" mostra só os erros ativos, com o resto igual a hoje.
2. Seção nova "Erros que você superou", entre "O que você mais erra" e "Já resolvidos", só quando há algum. Cada erro tem o selo verde com o nome curto, "superado em 28/10" e o botão secundário "Treinar de novo", com contorno e sem o roxo cheio dos botões dos erros ativos. O botão reabre o exercício pendente daquele erro ou gera um novo, como o "Treinar isso" de hoje.
3. Sem erro ativo e com algum superado, no lugar de "O que você mais erra" aparece "Você superou todos os erros que repetia." e "Resolva uma questão da sua turma e volte aqui.", com o link "Ver minhas turmas". "Para resolver", "Erros que você superou", "Já resolvidos" e a linha das gerações do dia continuam aparecendo.
4. Sem erro nenhum, ativo ou superado, a página continua com a mensagem de hoje, "A trilha começa a partir dos seus erros."
5. Depois de acertar um exercício, a página dele continua como hoje, com o selo "resolvido". Não entra aviso novo.

**Professor:** nada muda. O treino continua fora do painel dele, e o funil da turma não muda de comportamento.

## Definições

Detalham as seções 1 e 2 do desenho, aprovadas em 02/11.

**Histórico do aluno.** Lista, em ordem de tempo, de:
- envios das listas: as `submissions` com o `student_id` do aluno
- tentativas da trilha: as `tentativas_de_treino` do aluno em exercícios não reportados (`exercicios_gerados.reportado` falso)

Envio sem momento (`submitted_at` nulo) fica fora, como no funil. Ordem: momento, e no empate a lista antes da trilha e depois o id.

**Envio.** Cada linha do histórico tem:
- `origem`: `lista` ou `trilha`
- `item_id`: o id da questão ou do exercício
- `momento`: o `submitted_at`
- `categoria`: o `error_category`, vazio quando nulo
- `resultado`: acerto, erro ou falha
- `o_que_fazer`: o `actionable_feedback`, vazio quando nulo
- `alvo`: na trilha, o `error_category` do exercício, ou seja, o erro para o qual ele foi feito. Na lista, vazio
- `titulo`: na trilha, o título do exercício. Na lista, vazio

**Resultado.** É a mesma classificação do funil:
- acerto: na lista, categoria `Correto`. Na trilha, `all_tests_passed` verdadeiro, que é o mesmo critério que marca o exercício como resolvido.
- falha: não é acerto e a categoria é vazia ou `Erro Desconhecido`. É o Docker fora do ar, não erro do aluno.
- erro: o resto.

**Tentativa válida.** Acerto ou erro. A falha conta como envio, mas não como tentativa válida.

**Rótulo de onde o erro aconteceu.** Na lista, "<título da atividade> · Q<número>", só quando a questão é de atividade publicada de uma turma do aluno, como hoje. Fora disso, o envio não ganha rótulo. Na trilha, "Trilha · <título do exercício>".

**Erro ativo e erro superado.** Para cada categoria X com pelo menos um envio de resultado erro e categoria X:
- a última ocorrência de X é o momento do último envio de resultado erro e categoria X
- X está superado quando existe envio da trilha com alvo X, resultado acerto e momento depois da última ocorrência de X. `superado_em` é o momento do primeiro desses acertos.
- senão, X está ativo

Se X aparecer como erro depois do acerto, a última ocorrência passa a ser essa, e X volta a ser ativo até um novo acerto num exercício feito para ele. A falha técnica nunca vira categoria, porque não tem resultado erro.

Os erros recorrentes e a trilha usam o histórico inteiro do aluno, então os dois sempre concordam sobre o que está ativo e o que foi superado.

**Contas de cada erro:**
- `total`: envios de resultado erro e categoria X, somando lista e trilha
- `no_treino`: os desses envios que são da trilha
- `o_que_fazer`: o do último envio de resultado erro e categoria X
- `questoes`: os rótulos dos envios de erro de X, do mais recente para o mais antigo, sem repetir, no máximo 5
- `ultima_ocorrencia`: o momento da última ocorrência

**Tendência.** A regra de hoje, aplicada às tentativas válidas no lugar de todas as submissões:
- janela recente: as 10 últimas tentativas válidas do histórico
- recentes: os erros de X dentro dela
- anteriores: o total menos os recentes
- "melhorando", "piorando" e "estavel" com os mesmos limites de hoje (0,8 e 1,2), e "estavel" quando não há tentativa válida fora da janela

**Ordem.** Ativos pelo total, do maior para o menor, e no empate pelo nome da categoria. Superados por `superado_em`, do mais recente para o mais antigo.

**Progresso.**
- Escopo da lista: as questões das atividades publicadas das turmas do aluno. Escopo da trilha: todos os exercícios não reportados dele. Os envios fora desses escopos não entram no progresso.
- Item: o par origem e id, então a questão 5 e o exercício 5 são itens diferentes. Item resolvido: questão ou exercício com pelo menos um acerto.
- Questões resolvidas e atividades concluídas: só a lista, como hoje.
- Tentativas até acertar de um item resolvido: quantas tentativas válidas do item vieram até o primeiro acerto, contando o acerto. A média é sobre todos os itens resolvidos, lista e trilha, com uma casa decimal.
- Acerto de primeira: item resolvido cuja primeira tentativa válida é acerto.
- Total de tentativas: todos os envios dos dois escopos, falhas incluídas, porque o aluno enviou.
- Tentativas no treino: os desses envios que são da trilha.
- Exercícios resolvidos: exercícios do escopo com pelo menos um acerto.
- Dias seguidos: a regra de hoje, sobre os dias com qualquer envio dos dois escopos.
- Última tentativa: o maior momento entre os envios dos dois escopos.
- Evolução por semana (`semana_iso`): tentativas são os envios da semana, e resolvidas são os primeiros acertos de cada item naquela semana. Só aparecem as semanas com alguma tentativa, como hoje.

## Dados

Nenhuma tabela, coluna ou migração. O serviço lê `submissions`, `questions`, `exams`, `tentativas_de_treino` e `exercicios_gerados`, que já existem.

## Backend

**`app/services/historico_do_aluno.py` (novo).**
- O registro `Envio` (dataclass congelada) e as constantes de resultado `ACERTO`, `ERRO` e `FALHA`.
- A classificação: `CATEGORIA_CORRETA`, `CATEGORIA_FALHA_TECNICA`, `resultado_da_lista` e `resultado_da_trilha`. Elas saem de `funil_regras.py` e de `student_activity_service.py` e passam a morar aqui, porque o módulo novo não pode importar nenhum dos dois sem criar import circular. `funil_regras`, `funil_service`, `student_activity_service`, `treino_service` e `tests/unit/test_funil_regras.py` passam a importar daqui. A constante repetida em `treino_service.py` sai. O comportamento do funil não muda.
- `ler_historico(student, db) -> list[Envio]`: duas consultas por `student_id`, uma em `submissions` e outra em `tentativas_de_treino` junto com `exercicios_gerados`, filtrando os reportados e os sem momento, e o resultado em ordem.
- As regras puras, sobre `list[Envio]` e sem banco: o agrupamento dos erros por categoria com as contas, os superados com `superado_em`, a tendência e a ordem. Cada uma se testa com listas montadas à mão, como em `funil_regras`.

**`app/services/student_activity_service.py`.**
- `erros_recorrentes(student, db)` passa a ler o histórico. Os rótulos da lista continuam vindo do mapa de questões publicadas das turmas do aluno (`titulo_da_atividade` fica onde está).
- `progresso(student, db)` passa a filtrar as atividades por `Exam.publicada` e a ler o histórico nos dois escopos da definição.

**`app/services/treino_service.py`.**
- `categorias_para_treinar(student, db)` devolve só os erros ativos, a partir do histórico. Os campos `exercicios_gerados`, `exercicios_resolvidos` e `tem_pendente` continuam como hoje.
- `trilha(student, db)` devolve também `superados`. A pré-geração ao abrir a trilha continua mirando o primeiro erro ativo, e não faz nada quando não há erro ativo.
- `gerar_para_categoria(student, categoria, db)`:
  - Sem categoria e sem erro ativo, com algum superado: `TreinoIndisponivel("Você superou todos os erros que repetia. Resolva uma questão da sua turma e volte aqui.")`.
  - Sem erro nenhum: a mensagem de hoje.
  - Com categoria: aceita um erro ativo ou um superado. Fora dos dois, a mensagem de hoje, "Você não tem erros nessa categoria."
  - O "o que fazer" que vai para a geração é o do erro, ativo ou superado.
- `treinar(...)`: depois de um acerto, a pré-geração passa a preparar o primeiro erro ativo, recalculado depois do commit. Sem erro ativo, não prepara nada. Hoje ela prepara outro exercício do mesmo erro, que acabou de ser superado, e gastaria uma das 8 gerações do dia num exercício que a trilha não vai oferecer.
- `preparar_proximo` busca o "o que fazer" entre os erros ativos e os superados.

**Rotas.** Nenhuma rota nova e nenhum caminho muda. `GET /aluno/progresso`, `GET /aluno/erros-recorrentes`, `GET /aluno/treino`, `POST /aluno/treino/gerar` e `POST /aluno/treino/{exercicio_id}/tentativas` continuam com `get_current_student`, e tudo é lido pelo `student_id` do aluno logado. O `POST /aluno/treino/gerar` continua devolvendo 409 com a mensagem do `TreinoIndisponivel`.

**Schemas** (`app/models/schemas.py`). Todos os campos novos têm valor padrão, então o front antigo continua funcionando.
- `ErroSuperado` novo: `error_category: str`, `total: int`, `superado_em: str` (ISO, como o `ultima_ocorrencia`).
- `ErroRecorrente` ganha `no_treino: int = 0`.
- `ErrosRecorrentesResponse` ganha `superados: List[ErroSuperado] = []`. `total_submissoes` passa a ser o número de tentativas válidas do histórico, e `total_com_erro` o de envios de resultado erro.
- `TrilhaResponse` ganha `superados: List[ErroSuperado] = []`.
- `ProgressoResponse` ganha `tentativas_no_treino: int = 0` e `exercicios_resolvidos: int = 0`.

## Frontend

- `frontend/src/pages/aluno/ProgressoPage.jsx`: os textos de apoio dos números, a legenda do gráfico, o trecho "no treino" nos cartões de erro, a mensagem sem erro ativo e a seção "Erros que você superou", como em Comportamento.
- `frontend/src/pages/aluno/TreinoPage.jsx`: a seção "Erros que você superou" com o botão "Treinar de novo", que chama o `gerar(categoria)` que já existe, e a mensagem de tudo superado, como em Comportamento.
- A data do superado aparece como "28/10", com `toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })`, como a semana do gráfico.
- `frontend/src/api/aluno.js` não muda.

## Regras de uso responsável

- **RN01:** o superado nasce só de um acerto real do código do aluno num exercício feito para aquele erro. Não entra ponto, medalha por volume nem ranking.
- **RN05:** os superados aparecem só para o próprio aluno. O professor não vê nada novo. Os dias seguidos já existem e só passam a somar o treino. Quem os tira é o 2.6.
- **RN06 e RN07:** não mudam, porque o aluno só vê o próprio histórico.
- **RNF06:** nenhuma chamada nova ao Gemini. A mudança na pré-geração depois do acerto economiza gerações.
- **Ordem do plano:** o aviso de superado na hora do acerto fica fora, porque o 2.4 (pausa na tentativa às cegas) entra antes de qualquer recompensa nova. A lista de superados é informação sobre o histórico, na página do aluno.

## Testes

**Regras puras**, em `tests/unit/test_historico_do_aluno.py` (novo), com listas de `Envio` montadas à mão:
- Classificação: `Correto` na lista é acerto, `all_tests_passed` na trilha é acerto mesmo com categoria vazia, categoria vazia ou `Erro Desconhecido` é falha, e o resto é erro.
- Superado:
  - erro X na lista e depois acerto num exercício da trilha com alvo X: superado, com `superado_em` no momento do acerto
  - acerto num exercício de X antes da última ocorrência de X: ativo
  - X de novo depois do acerto: volta a ativo
  - acerto num exercício de alvo Y: não supera X
  - dois acertos depois da última ocorrência: `superado_em` é o primeiro
- Erro que nasce no treino (categoria Y numa tentativa de exercício de alvo X) vira categoria ativa com `no_treino` 1.
- Falha técnica não vira categoria e não entra na janela da tendência.
- Contas: `total`, `no_treino`, `o_que_fazer` do último erro e rótulos sem repetir, no máximo 5.
- Ordem: ativos pelo total e no empate pelo nome, superados do mais recente para o mais antigo.
- Tendência: melhorando, piorando e estável sobre as tentativas válidas, e estável sem tentativa válida fora da janela.
- Progresso: tentativas até acertar contando só as válidas, acerto de primeira com uma falha antes do acerto, evolução com o primeiro acerto de um exercício na semana certa.

**Serviços e rotas**, em `tests/test_student_activity.py` e `tests/test_treino.py`:
- `GET /aluno/erros-recorrentes`: `no_treino`, o rótulo "Trilha · <título>", a lista `superados`, `total_submissoes` e `total_com_erro` sem as falhas, e o erro superado fora de `erros`.
- Exercício reportado: as tentativas dele não contam em nenhuma das três rotas.
- `GET /aluno/treino`: `categorias` só com os ativos e `superados` preenchido.
- `POST /aluno/treino/gerar`:
  - sem categoria e com tudo superado: 409 com a mensagem nova
  - com categoria superada: reabre o pendente ou gera, com o gerador simulado
  - com categoria que o aluno nunca errou: 409 com a mensagem de hoje
- Pré-geração: depois de um acerto, `preparar_proximo` é chamado com o primeiro erro ativo, e não é chamado quando não sobra erro ativo.
- `GET /aluno/progresso`:
  - atividade não publicada fora do total de atividades e de questões
  - tentativas até acertar e acertos de primeira juntando questão e exercício
  - falha técnica fora das tentativas até acertar
  - dias seguidos e evolução com o treino
  - `tentativas_no_treino` e `exercicios_resolvidos`
  - aluno sem envio nenhum recebe zeros
- Isolamento: tentativas de treino e envios de outro aluno não entram em nenhuma das três rotas.
- O funil continua passando sem mudança nos testes, além do import.

**Frontend:** `npm run lint` sem erro novo e `npm run build`. A conferência no navegador vai no smoke test do `fechamento`, com tentativas de treino criadas pela API.

## Fora do escopo

- O aviso "Você superou" na hora do acerto, porque o 2.4 entra antes de qualquer recompensa nova.
- A trilha intercalada (2.5), o registro de acertos e a troca dos dias seguidos (2.6).
- O treino no painel do professor e o progresso por turma (3.3).
- Mudar a geração do exercício ou o prompt.
- O `new Date(iso)` sem `Z` no front, que é dívida do repositório inteiro.

## Decisões

1. **Superado pela trilha.** Um erro só conta como superado quando o aluno acerta um exercício da trilha feito para ele depois da última vez que o erro apareceu. Escolha do Otávio em 02/11. Acertar a mesma questão seria generoso demais, porque o erro que se repete em toda questão nova viraria superado a cada correção.
2. **Superado sai do topo, mas fica visível.** O aluno vê o que superou, e o erro volta para a lista se reaparecer. Escolha do Otávio em 02/11, que também prepara o 2.5 e o 2.6.
3. **O treino soma onde é esforço.** Tentativas até acertar, acertos de primeira, dias seguidos e o gráfico somam lista e trilha, e "Questões resolvidas X/Y" continua só da turma, porque o Y é o total da turma. Escolha do Otávio em 02/11, igual ao que o funil já faz.
4. **Um histórico só, num módulo novo.** A trilha e o painel leem a mesma lista e a mesma regra de superado, então nunca discordam. Abordagem A do desenho, aprovada em 02/11.
5. **A falha técnica sai das contas de erro.** Ela continua no total de tentativas, mas não vira erro recorrente, não entra na tendência e não monta trilha. Hoje, com o Docker fora do ar, a trilha pode montar um exercício para "Erro Desconhecido". É a mesma regra do funil.
6. **Erro que nasce no treino conta.** Se o aluno comete Y treinando X, Y passa a ser erro recorrente dele, como se tivesse aparecido numa lista.
7. **A classificação muda de módulo.** `CATEGORIA_CORRETA`, `CATEGORIA_FALHA_TECNICA`, `resultado_da_lista` e `resultado_da_trilha` passam para `historico_do_aluno.py`, que fica embaixo do funil e dos serviços do aluno, sem import circular.
8. **Pré-geração para o próximo erro ativo.** Depois de um acerto, preparar outro exercício do erro que acabou de ser superado gastaria uma geração do dia à toa.
9. **O progresso passa a filtrar por atividade publicada.** É a correção de um problema que já existia na função que esta volta reescreve, e a lista de atividades e os erros recorrentes já filtram assim.
10. **Tentativas até acertar contam só as válidas.** Antes, o número da tentativa incluía as falhas técnicas. Agora segue a regra de proteção do funil.
11. **Sem aviso na hora do acerto.** O 2.4 vem antes de qualquer recompensa nova.
