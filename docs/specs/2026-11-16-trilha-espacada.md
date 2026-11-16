# Trilha com revisão espaçada dos erros superados

**Item do plano:** 2.5 Trilha intercalada (fase 2, `docs/produto/plano-implementacao.md`)
**Requisitos:** RF32 (trilha intercalada). Preserva RN03, RN05, RNF05 e RNF06 (ver "Regras de uso responsável").
**Data:** 2026-11-16

## Objetivo

Trazer de volta, em intervalos crescentes, cada erro que o aluno já superou, misturado com os erros que ele ainda tem, até o erro ficar consolidado. Hoje um erro superado só volta se o aluno tocar em "Treinar de novo".

## Base

A pesquisa feita em 16/11/2026 levou a esta forma:

- **Reaprendizagem sucessiva** (Rawson e Dunlosky): praticar até um critério e voltar a praticar em sessões espaçadas. Uma sessão já aumenta muito a retenção, e por volta de três sessões espaçadas dão quase todo o ganho. O critério aqui é o acerto na trilha que supera o erro.
- **Espaçamento** (Cepeda e colegas, 2008): o melhor intervalo cresce com a distância até a cobrança. Para provas a cada poucas semanas, intervalos de um dia a duas semanas. Não houve vantagem clara de intervalo crescente sobre fixo, então uma agenda fixa e curta basta.
- **Intercalação** (Rohrer, Brunmair e Richter, 2019): misturar tipos de problema ajuda, com efeito de cerca de 0,34 desvio-padrão.

Os intervalos são os três primeiros do SM-2 com facilidade 2,5 (1, 6 e 15 dias), os mesmos que o roteiro do Plano de Hábito apresenta. O SM-2 completo, com nota por resposta, fica no item 4.6, onde a revisão é uma pergunta barata. Aqui cada revisão custa uma geração do Gemini e uma execução no Docker, então a agenda é fixa e para em três.

## Comportamento

### A agenda de um erro superado

1. O aluno supera o erro, pela regra que já existe: acerta na trilha um exercício feito para aquele erro, sem repeti-lo, depois da última vez que ele apareceu.
2. A 1ª revisão vence 1 dia depois do acerto que superou o erro, a 2ª 6 dias depois da 1ª revisão feita, e a 3ª 15 dias depois da 2ª.
3. Uma revisão é feita quando o aluno acerta, sem repetir o erro, um exercício da trilha feito para aquele erro, numa data a partir do vencimento. Acerto antes do vencimento (por "Treinar de novo") vale como treino, mas não avança a agenda.
   - Só conta o **primeiro** acerto de cada exercício. Refazer um exercício já resolvido não avança a agenda, inclusive o exercício que superou o erro e o que foi resolvido antes do vencimento. Assim o aluno não consolida o erro refazendo o mesmo exercício nas datas certas.
   - Tentativa de exercício reportado sai do histórico, como já acontece hoje. Reportar uma revisão desfaz aquela revisão, e reportar o exercício que superou o erro faz o erro voltar a ativo.
4. Feitas as três revisões, o erro fica **consolidado** e não volta mais pela agenda.
5. Se o aluno repetir o erro em qualquer lugar (lista, prova ou trilha), o erro volta a ser ativo, pela regra que já existe. Quando ele superar de novo, a agenda recomeça do zero.

Os dias contam pela data do calendário no horário de Brasília (UTC−3, sem horário de verão desde 2019). Quem supera às 22h do dia 16 tem a 1ª revisão vencida desde a meia-noite do dia 17.

### Qual é o próximo exercício

Quando o aluno acerta um exercício da trilha, o sistema prepara o próximo em segundo plano, como hoje. A escolha passa a ser:

- se o exercício que ele acabou de acertar **não** era uma revisão, vem primeiro uma revisão vencida e depois o primeiro erro ativo
- se **era** uma revisão, vem primeiro o primeiro erro ativo e depois uma revisão vencida

Assim duas revisões seguidas só acontecem quando não há erro ativo. Entre as revisões vencidas, vem a que venceu há mais tempo. A lista de candidatos é percorrida em ordem e vale o primeiro que ainda não tem exercício pendente: uma revisão vencida com pendente é pulada e a próxima vencida é tentada antes do erro ativo.

"Era uma revisão" quer dizer: a categoria do exercício já estava superada antes do acerto, ou seja, o `superado_em` calculado depois do commit da tentativa é anterior ao momento dela. O acerto que supera um erro ativo tem `superado_em` igual ao próprio momento e não é revisão.

Abrir a trilha continua aquecendo o primeiro erro ativo. Sem erro ativo, aquece a revisão vencida há mais tempo. Gerar sem categoria (o botão principal) segue a mesma ordem: erro ativo primeiro, revisão vencida se não houver ativo, e o aviso "Você superou todos os erros" só quando não há nenhum dos dois. Entre as revisões vencidas, como já acontece entre os ativos, a que tem exercício pronto vem antes da que venceu há mais tempo.

### O que o aluno vê

Na trilha, cada erro da seção "Erros que você superou" mostra uma das situações:

| Situação | Texto | Botão |
|---|---|---|
| Revisão vencida | "Hora de revisar" | **Revisar agora** (principal) |
| Próxima revisão no futuro | "Próxima revisão amanhã" ou "Próxima revisão em N dias", com N calculado no servidor pelo dia de Brasília | Treinar de novo (secundário) |
| Consolidado | "Consolidado" | Treinar de novo (secundário) |

Os erros com revisão vencida aparecem primeiro na seção. Não existe contador de revisões atrasadas, a palavra "atrasado" nem cobrança por revisão que passou do dia: uma revisão vencida há dez dias aparece igual a uma vencida hoje.

Na tela do exercício, quando a categoria dele está superada, aparece o aviso: "Revisão: você já superou este erro. Treinar de novo ajuda a ver se ele ficou para trás." O texto não promete que o acerto conta na agenda, porque um exercício aberto antes do vencimento não conta.

A revisão preparada depois de um acerto registra a novidade "Exercício novo pronto na trilha", como qualquer preparo depois de acerto já registra hoje. Ela ocupa o lugar do preparo do erro ativo, então a bolinha não acende mais vezes do que já acende.

O progresso e os erros recorrentes não mudam.

## Dados

Sem tabela nova, sem coluna nova e sem migração. A agenda sai do histórico que já existe (`ler_historico`): os acertos da trilha em cada categoria, com as datas deles. Os dados existentes passam a ter agenda na hora: um erro superado há 20 dias com nenhuma revisão fica com a 1ª revisão vencida.

## Backend

**`app/services/calendario.py`:** `dia_local(momento) -> date`, a data no horário de Brasília de um momento em UTC sem fuso.

**`app/services/historico_do_aluno.py`:**
- `INTERVALOS_DA_REVISAO = (1, 6, 15)`, em dias.
- `Revisao`, dataclass com `feitas`, `proxima_em: date | None` e as propriedades `consolidado` (feitas == 3) e `vencida(hoje: date)`.
- `agenda_de_revisao(erro, envios, hoje) -> Revisao | None`: `None` para erro ativo. Toma o primeiro acerto de cada exercício da trilha em todo o histórico, fica com os que têm `alvo` igual à categoria, categoria diferente dela e momento depois de `superado_em`, em ordem de tempo, e conta como revisão o que cai em data a partir do vencimento da vez. `Revisao` também leva `dias_ate` (dias de Brasília até `proxima_em`, zero ou negativo quando vencida).
- Função pura, testada com listas montadas à mão, como as outras do arquivo.

**`app/services/treino_service.py`:**
- `trilha`: lê o histórico uma vez e passa os envios para os erros e para a agenda. Cada superado ganha `revisao` (`feitas`, `proxima_em` em ISO ou nulo, `dias_ate`, `vencida`, `consolidado`), com os vencidos primeiro. O aquecimento sem erro ativo usa a revisão vencida.
- `gerar_para_categoria` sem categoria: sem erro ativo, escolhe a revisão vencida há mais tempo.
- `treinar`, no acerto: escolhe o próximo pela ordem da seção acima e chama `preparar_proximo`, que já trata pendente, teto e espera depois de falha.
- `_exercicio_detalhe`: campo `revisao`, verdadeiro quando a categoria do exercício está superada.

Nenhuma rota nova nem mudança de papel ou posse. As rotas são as de `/aluno/treino`, com `get_current_student`, e a agenda só lê o histórico do próprio aluno.

**`app/models/schemas.py`:** `RevisaoDoErro` e o campo opcional `revisao` em `ErroSuperado` (nulo nos erros recorrentes, preenchido na trilha), e `revisao: bool = False` em `ExercicioDetalhe`.

## Frontend

- `pages/aluno/TreinoPage.jsx`: a seção dos superados com a situação e o botão da tabela acima.
- `pages/aluno/ExercicioTreinoPage.jsx`: o aviso de revisão, no mesmo estilo do aviso de exercício reaproveitado.
- O texto da próxima revisão ("amanhã", "em N dias") sai do `dias_ate` que a API devolve, sem conta de data no navegador.

## Regras de uso responsável

- **RN03:** a agenda depende só do diagnóstico das regras, sem chamada ao Gemini para decidir.
- **RN05:** a agenda é só do aluno. O professor não vê revisão de ninguém.
- **Cuidado da pilha de atrasados** (Plano de Hábito): sem contador, sem "atrasado" e sem aviso por revisão perdida.
- **Nada sorteado** (Plano de Growth): a escolha do próximo é determinística.
- **RNF05:** o exercício de revisão é gerado e conferido pela solução de referência, como qualquer outro.
- **RNF06:** no máximo três revisões por superação, dentro do teto de 8 gerações por dia. A revisão ocupa o lugar de uma geração que já aconteceria no preparo do próximo.

## Testes

Funções puras (`historico_do_aluno`):
- erro superado sem revisão: 1ª vence no dia seguinte ao acerto, e no mesmo dia não está vencida
- superado às 22h de Brasília (01h UTC do dia seguinte): vence no dia seguinte pelo calendário de Brasília
- acerto antes do vencimento não conta, e o mesmo acerto depois do vencimento conta
- três revisões espaçadas deixam o erro consolidado, sem `proxima_em`
- dois acertos no mesmo exercício contam uma vez
- exercício resolvido antes do vencimento e refeito depois não conta, e o exercício que superou o erro refeito depois do vencimento também não
- acerto com a própria categoria do erro não conta como revisão
- revisão que repete o erro deixa o erro ativo, sem agenda
- histórico sem a tentativa de um exercício reportado: a revisão dele deixa de contar
- erro que reaparece volta a ativo e, superado de novo, recomeça a agenda
- erro ativo não tem agenda

Serviço (`treino_service`):
- acerto num exercício de erro ativo com revisão vencida prepara a revisão
- acerto numa revisão prepara o erro ativo
- acerto numa revisão sem erro ativo prepara outra revisão vencida
- revisão vencida com exercício pendente é pulada: entra a próxima revisão vencida, e sem ela o erro ativo
- sem revisão vencida, prepara o erro ativo como hoje
- entre duas revisões vencidas, prepara a que venceu há mais tempo
- trilha devolve `revisao` nos superados com os vencidos primeiro, e aquece a revisão vencida sem erro ativo
- gerar sem categoria e sem erro ativo usa a revisão vencida, e sem nenhum dos dois mantém o aviso
- detalhe do exercício traz `revisao` só para categoria superada

Frontend: lint e build limpos, e a trilha e o exercício conferidos em 360, 390 e 1280 px.

Smoke com Docker e Gemini reais: aluno `SMOKE-` supera um erro, os envios são deslocados no banco para simular a passagem dos dias, a trilha mostra "Revisar agora", e o acerto num erro ativo prepara a revisão.

## Fora do escopo

- Aviso por push quando a revisão vence (fase 4).
- SM-2 completo com nota por resposta e troca para FSRS (item 4.6).
- Mostrar a agenda no progresso ou ao professor.
- Mudar a regra do superado.

## Decisões

1. **Agenda fixa de 1, 6 e 15 dias, parando em três.** É o que a reaprendizagem sucessiva indica, e cada revisão custa uma geração. Bate com os números do SM-2 do roteiro.
2. **Revisão só conta a partir do vencimento.** Sem isso, três "Treinar de novo" seguidos consolidariam o erro sem espaçamento nenhum.
3. **Contagem pelo dia de Brasília.** O aluno pensa em "amanhã", não em 24 horas.
4. **Revisão e erro ativo se alternam.** A revisão não toma o lugar do erro que ainda está aberto, e a mistura é a intercalação do RF32.
5. **Sem tabela.** A agenda é derivada do histórico, então os dados que já existem ganham agenda na hora e não há migração para desfazer.
6. **Revisão vencida há muito tempo aparece igual à vencida hoje.** É o cuidado da pilha de atrasados.
7. **Só o primeiro acerto de cada exercício conta.** Fecha o atalho de consolidar refazendo o mesmo exercício.
8. **Os dias até a próxima revisão vêm do servidor.** O navegador pode estar em outro fuso, e a agenda conta pelo dia de Brasília.
9. **A revisão preparada registra novidade como qualquer preparo.** Ela substitui o preparo do erro ativo, então não aumenta o número de avisos.
