# Novidades no Início do aluno

**Item do plano:** experimento 1 da seção 10 de `docs/produto/plano-implementacao.md` ("Novidades no app"), com os itens 3.1 (Início como painel: continuar de onde parou, prazos próximos e novidades) e 3.2 ("Seu professor respondeu" dentro do app, marcando o que o aluno já viu)
**Requisitos:** RF20 (indicador de novidades no app), RF26 (aviso "Seu professor respondeu"), RN01, RN04, RN06, RN07, RNF02, RNF04
**Data:** 2026-11-04

## Objetivo

O aluno passa a abrir o app num Início que mostra o que chegou para ele (a resposta do professor ao erro dele e o exercício novo pronto na trilha), onde ele parou e o que vence logo. Cada novidade fica guardada com o momento em que chegou e o momento em que o aluno a viu, que é o dado de que o experimento 1 precisa para comparar o retorno em 7 dias de quem encontrou uma novidade esperando com o de quem não encontrou.

## Comportamento

**Aluno, ao abrir o app**

1. `/aluno` abre o Início. Hoje essa rota redireciona para Turmas. O menu ganha o item "Início" na frente de Turmas, Treino e Meu progresso, no computador e no celular.
2. O Início mostra, de cima para baixo, só os blocos que têm conteúdo:
   - **Novidades**, da mais recente para a mais antiga:
     - "Seu professor respondeu ao seu erro", com o título "Questão 2 · Lista 3" e o link para a questão. O texto da resposta não aparece no Início. Ele continua na tela da questão, onde já aparece hoje.
     - "Exercício novo pronto na trilha", com o título do exercício e o link para ele.
   - **Continuar de onde parou:** um cartão com o nome do item, o número de tentativas, o último erro e o botão "Continuar".
     - Em andamento é o item mais recente em que o aluno enviou algo, questão de lista ou exercício da trilha, que ele ainda não acertou e que ainda aceita envio.
     - Sem item em andamento, o cartão mostra a próxima atividade aberta que ainda tem questão por resolver, com o botão "Começar".
     - Sem as duas coisas, o cartão não aparece.
   - **Prazos próximos:** atividades das turmas do aluno, ainda com o que fazer, que fecham nos próximos 7 dias ("Prova · fecha amanhã") ou que abrem nos próximos 3 dias ("Prova · abre em 3 dias"). Em ordem de data, com o nome da turma.
   - **Tudo em dia:** sem novidade, sem cartão de continuar e sem prazo, o Início mostra "Tudo em dia. Que tal treinar?" com o link para a trilha.
3. O aluno sem turma vê no Início o "Comece entrando na sua turma" com o campo do código, que hoje aparece em Turmas.
4. A tela de Turmas continua igual, só deixa de ser a primeira.

**A bolinha do menu**

1. O item "Início" mostra o número de novidades não vistas que ainda valem, num círculo roxo pequeno. Sem novidade, não mostra nada.
2. A contagem é pedida ao abrir o app e a cada troca de página. Se o pedido falhar, a bolinha some e nada mais muda.

**Quando uma novidade conta como vista**

1. Resposta do professor: quando a tela da questão entrega a resposta ao aluno, seja no histórico da questão (a tentativa mais recente é a que traz a resposta) ou no resultado de um envio que caiu num grupo já respondido. Só conta como vista a novidade daquele grupo.
2. Exercício novo: quando o aluno abre o exercício, envia uma tentativa nele ou recebe esse exercício ao pedir um na trilha (o pendente que a trilha devolve em vez de gerar outro).
3. Abrir o Início não marca nada como visto. A novidade fica lá até o aluno abri-la.

**Professor:** nada muda na tela. Salvar a resposta de um grupo passa a criar as novidades dos alunos, sem nada visível para ele.

## Definições

- **Aluno alcançado por uma resposta:** aluno com conta (`submissions.student_id`) cuja tentativa mais recente na questão (maior `attempt_number`, e no empate o maior `id`) está no grupo, isto é, tem `cluster_id` igual ao `cluster_label` atual do grupo. É a mesma regra da tela da questão, que só mostra a resposta na tentativa mais recente.
- **Novidade que ainda vale:**
  - Retorno: a questão é de atividade publicada de uma turma em que o aluno está matriculado, existe um grupo da questão com aquela `chave` e com `resposta_professor` preenchida, e a tentativa mais recente do aluno na questão está nesse grupo.
  - Exercício: o exercício não está resolvido nem reportado.
- **Item que aceita envio:**
  - Questão de lista: a atividade está publicada, é de uma turma do aluno, está aberta (`situacao_da_atividade`) e o aluno ainda tem tentativa (sem `max_tentativas`, ou com menos envios na questão do que o teto).
  - Exercício da trilha: não está resolvido nem reportado.
- **Item resolvido:** questão com algum envio `Correto`, ou exercício com `resolvido` verdadeiro. Para a questão vale o histórico unificado (`ler_historico`), em que o acerto é `resultado == ACERTO`.
- **Atividade com o que fazer:** atividade publicada de uma turma do aluno com ao menos uma questão, e com ao menos uma questão sem acerto que ainda aceita envio. Para a atividade que ainda não abriu basta ter questão, porque ninguém enviou nada.
- **Prazo próximo:**
  - "fecha": a atividade está aberta, tem `fecha_em`, e `agora < fecha_em <= agora + 7 dias`.
  - "abre": a atividade ainda não abriu e `abre_em <= agora + 3 dias`, a mesma `ANTECEDENCIA_DA_PROVA` que o funil usa para a prova chegando. Vale para os dois modos, treino e prova.
  - A mesma atividade aparece uma vez só. A ordem é pela data que importa (a de fechar ou a de abrir), da mais próxima para a mais distante.
- **Próxima atividade** (quando não há item em andamento): entre as atividades abertas com o que fazer, a que fecha primeiro. As sem `fecha_em` vêm depois, da criada mais recentemente para a mais antiga.
- **Último erro do cartão de continuar:** a categoria do último envio do item. Fica vazio quando o último envio foi falha técnica (`resultado == FALHA`).

## Dados

**Migração 0019** (`down_revision = '0018'`), que só cria a tabela `novidades`. O 0.2 do plano, de tirar `umap_x` e `umap_y`, passa a ser a 0020.

| Coluna | Tipo | Observação |
|---|---|---|
| `id` | inteiro, chave primária | |
| `student_id` | FK `students.id`, obrigatório, com índice | de quem é a novidade |
| `tipo` | `String(16)`, obrigatório | `retorno` ou `exercicio` |
| `question_id` | FK `questions.id`, opcional, com índice | só no retorno |
| `grupo_chave` | `String`, opcional | só no retorno, a `chave` do grupo, que vale mesmo depois de os grupos serem refeitos ou de a linha do grupo ser apagada |
| `exercicio_id` | FK `exercicios_gerados.id`, opcional | só no exercício |
| `chegou_em` | `DateTime`, obrigatório | quando a novidade chegou |
| `vista_em` | `DateTime`, opcional | quando o aluno a viu, ou vazio |

Dois índices únicos parciais garantem no máximo uma novidade não vista por aluno e origem:
- `uq_novidade_retorno_aberta` em `(student_id, question_id, grupo_chave)`, onde `tipo = 'retorno' AND vista_em IS NULL`
- `uq_novidade_exercicio_aberta` em `(student_id, exercicio_id)`, onde `tipo = 'exercicio' AND vista_em IS NULL`

Os índices vão também no modelo do ORM (`postgresql_where`), para o `create_all` dos testes criá-los. Como a tabela é nova, o banco de teste não precisa de `ALTER TABLE`.

A tabela começa vazia. Respostas escritas antes da 0019 e exercícios já prontos não viram novidade.

A linha que deixa de valer não é apagada nem alterada. Ela continua com `vista_em` vazio, que é o registro de uma novidade que chegou e não foi vista.

## Backend

**Serviço novo `app/services/novidades_service.py`**, o único que grava e lê a tabela.

- `registrar_resposta(grupo, db)`, chamado depois de o professor salvar a resposta de um grupo.
  - Com texto: se a atividade da questão está publicada e o grupo tem `chave`, cria uma novidade `retorno` para cada aluno alcançado, com `chegou_em = grupo.resposta_em`. A gravação é um `INSERT ... ON CONFLICT DO NOTHING` sobre o índice parcial, então quem ainda não viu a anterior continua com ela (e com o `chegou_em` dela), e quem já viu ganha uma nova.
  - Sem texto (resposta apagada): apaga as novidades não vistas de `(question_id, grupo_chave)`. As já vistas ficam.
  - Grupo sem `chave` (linha antiga, de antes da chave estável) não gera novidade.
- `registrar_exercicio(exercicio, db)`, chamado pela pré-geração da trilha: cria uma novidade `exercicio` com `chegou_em = exercicio.created_at`, com a mesma gravação que ignora a repetida.
- `marcar_resposta_vista(student_id, question_id, chave, db)`: preenche `vista_em` com o momento atual nas novidades não vistas de `(student_id, 'retorno', question_id, chave)`.
- `marcar_exercicio_visto(student_id, exercicio_id, db)`: o mesmo para `(student_id, 'exercicio', exercicio_id)`.
- `novidades_do_aluno(student, db)`: as não vistas que ainda valem, da mais recente para a mais antiga pelo `chegou_em`, já com o título e os ids do link.
- `contar(student, db)`: quantas `novidades_do_aluno` devolve.

**Serviço novo `app/services/inicio_service.py`**, que monta o painel e não grava nada.

- `painel(student, db, agora=None)` devolve `tem_turma`, `novidades`, `continuar` e `prazos`. Sem matrícula, devolve `tem_turma` falso e o resto vazio.
- A regra fica em duas funções puras, testadas com listas montadas à mão:
  - `escolher_continuar(envios, disponiveis, proxima)`: percorre o histórico unificado do mais recente para o mais antigo e devolve o primeiro item sem acerto que esteja entre os que aceitam envio. Sem nenhum, devolve a próxima atividade, que pode ser vazia.
  - `prazos_proximos(atividades, agora)`: aplica a definição de prazo próximo às atividades com o que fazer.
- Constante nova `JANELA_DO_PRAZO = timedelta(days=7)`. A janela de abertura importa `ANTECEDENCIA_DA_PROVA` de `funil_regras`.
- O histórico vem de `ler_historico`, o mesmo do progresso e da trilha, para os três concordarem sobre o que está resolvido.

**Ganchos nos serviços que já existem**, uma chamada em cada:

- `routes/exam.py`, `put_resposta_do_grupo`: chama `registrar_resposta(grupo, db)` depois do `commit` que salva a resposta.
- `student_activity_service`:
  - `resposta_do_grupo` passa a devolver também a `chave` do grupo.
  - `historico_questao`: quando a tentativa mais recente sai com resposta, chama `marcar_resposta_vista` com a chave daquele grupo.
  - `submeter`: quando a tentativa devolvida sai com resposta, faz o mesmo.
- `treino_service`:
  - a tarefa de `preparar_proximo` chama `registrar_exercicio` com o exercício que `_gerar_e_salvar` gravou.
  - `detalhe`, `treinar` e o ramo de `gerar_para_categoria` que devolve o pendente chamam `marcar_exercicio_visto`.
- `exam_service._delete_questions`: apaga as novidades das questões antes de apagar as questões. A exclusão de atividade e a de turma passam por ela.

A marcação de visto e a gravação da novidade são secundárias ao que a rota entrega. Nos ganchos do aluno (`historico_questao`, `submeter`, `detalhe`, `treinar` e `gerar_para_categoria`), a marcação vem depois da conferência de posse que a função já faz, e uma falha nela vai para o log com `rollback` e não derruba a resposta, como o `_agrupar_em_silencio` faz com o agrupamento. Na rota do professor, a falha ao gravar as novidades também vai para o log e não desfaz a resposta já salva. Na pré-geração, `registrar_exercicio` usa a sessão da própria tarefa em segundo plano.

**Rotas novas** no router do aluno (`app/api/routes/student_activity.py`, prefixo `/aluno`), as duas com `get_current_student`:

- `GET /aluno/inicio` devolve `InicioResponse`.
- `GET /aluno/novidades/contagem` devolve `ContagemNovidadesResponse` (`{ "total": n }`).

As duas só leem dados do próprio aluno e não recebem id no caminho, então a posse se resume ao token. Sem token, ou com token de professor, respondem 401.

**Esquemas novos em `app/models/schemas.py`**

- `NovidadeItem`: `tipo` (`retorno` ou `exercicio`), `titulo`, `chegou_em`, `exam_id`, `question_number` e `exercicio_id`, os três últimos opcionais conforme o tipo.
- `ContinuarItem`: `origem` (`lista` ou `trilha`), `situacao` (`em_andamento` ou `proxima`), `titulo`, `turma_nome` (vazio na trilha), `tentativas`, `ultimo_erro`, `exam_id`, `question_number` e `exercicio_id`.
- `PrazoItem`: `exam_id`, `titulo`, `turma_nome`, `modo`, `tipo` (`fecha` ou `abre`) e `quando`.
- `InicioResponse`: `tem_turma`, `novidades` (lista), `continuar` (opcional) e `prazos` (lista).
- `ContagemNovidadesResponse`: `total`.

Os títulos seguem o que o aluno já vê: `titulo_da_atividade` para a atividade e "Questão N · \<atividade\>" para a questão. As datas saem em ISO e em UTC, como no resto da API.

## Frontend

- `pages/aluno/InicioPage.jsx` (novo), com os blocos do Comportamento, no visual dos cartões que já existem (fundo branco, borda cinza, destaque roxo) e empilhados no celular. Ao abrir, pede `getInicio()`. Voltar ao Início depois de abrir uma novidade pede de novo, e a novidade vista some.
- `components/EntrarNaTurma.jsx` (novo): o formulário de entrar com o código sai da `TurmasPage` para ser usado também no Início do aluno sem turma. A `TurmasPage` passa a importá-lo, sem mudar o que mostra.
- `App.jsx`: a rota `aluno` abre `InicioPage` no lugar do redirecionamento para `/aluno/turmas`.
- `components/AlunoLayout.jsx`: o link "Início" (`to="/aluno"`, com `end`, para não ficar marcado nas outras páginas) entra na frente, nos dois menus, com a bolinha. A contagem é pedida ao montar e a cada mudança de `location.pathname`.
- `api/aluno.js`: `getInicio()` e `contarNovidades()`.
- `utils/datas.js`: `prazoRelativo(iso, agora)`, que devolve "hoje", "amanhã" ou "em N dias" no fuso do aluno, em cima da `paraData`.

## Regras de uso responsável

- **RN07:** o aluno lê "Seu professor respondeu ao seu erro". Nada fala de grupo nem de colegas.
- **RN01:** a bolinha só conta o que chegou para o aluno. Nada é sorteado, e não entra ponto, sequência nem ranking.
- **RN04:** nada sai do app. A novidade não é aviso e não há push.
- **RN06:** nenhuma informação de colega aparece no Início.
- **RNF04:** cada aluno só lê as próprias novidades. O professor não vê quem leu a resposta.
- **RNF02:** os blocos do Início empilham no celular, e a bolinha aparece também no menu do celular.

## Testes

**Nascimento das novidades (`registrar_resposta` e `registrar_exercicio`)**
1. A resposta cria uma novidade para cada aluno cuja tentativa mais recente está no grupo.
2. Não cria para o aluno cuja tentativa antiga está no grupo e a mais recente não.
3. Não cria para envio sem conta (só matrícula).
4. Não cria em atividade não publicada.
5. Não cria para grupo sem `chave`.
6. Editar a resposta antes de o aluno ver não cria outra, e o `chegou_em` continua o da primeira.
7. Editar depois de o aluno ver cria uma nova, com o `chegou_em` da edição.
8. Apagar a resposta remove as não vistas daquele grupo e mantém as vistas.
9. A pré-geração da trilha cria a novidade do exercício, e o exercício pedido e gerado na hora não cria.
10. Gravar duas vezes a mesma novidade não vista não duplica nem dá erro.

**Visto**
11. O histórico da questão com resposta marca a novidade daquele grupo, e sem resposta não marca.
12. O histórico não marca a novidade de outro grupo da mesma questão.
13. O envio que cai num grupo respondido marca a novidade daquele grupo.
14. `detalhe`, `treinar` e o pendente devolvido por `gerar_para_categoria` marcam a novidade do exercício.

**Conferência na leitura (`novidades_do_aluno` e `contar`)**
15. Somem: grupo apagado, aluno que mudou de grupo com envio novo, atividade despublicada, aluno que saiu da turma, exercício resolvido e exercício reportado. A linha continua no banco com `vista_em` vazio.
16. A lista sai do `chegou_em` mais recente para o mais antigo, com título e ids certos para os dois tipos.
17. `contar` bate com o tamanho da lista.
18. A novidade de um aluno não aparece para outro.

**Continuar (`escolher_continuar`, pura)**
19. Pega o item mais recente sem acerto.
20. Pula o item resolvido, mesmo que seja o mais recente.
21. Pula a questão de atividade encerrada e a que esgotou as tentativas.
22. Pula o exercício resolvido.
23. Mistura lista e trilha pela ordem do tempo.
24. O último erro fica vazio quando o último envio foi falha técnica.
25. Sem item em andamento, devolve a próxima atividade. Sem ela, devolve vazio.

**Prazos (`prazos_proximos`, pura) e próxima atividade**
26. Fecha em 7 dias entra, fecha em 8 dias não entra, e a que já fechou não entra.
27. Abre em 3 dias entra e abre em 4 dias não entra.
28. A atividade sem o que fazer (resolvida, ou com as tentativas das questões que faltam esgotadas) não entra.
29. A ordem é pela data, e a atividade aparece uma vez só.
30. A próxima atividade é a que fecha primeiro, e as sem `fecha_em` vêm depois, da mais recente para a mais antiga.

**Painel e rotas**
31. `painel` lê só atividades publicadas das turmas do aluno.
32. Aluno sem turma recebe `tem_turma` falso e o resto vazio.
33. `GET /aluno/inicio` e `GET /aluno/novidades/contagem` dão 401 sem token e com token de professor.
34. Dois alunos com dados diferentes recebem cada um só o seu.

**Exclusão e falhas**
35. Apagar uma atividade, uma questão e uma turma com novidades não quebra e remove as novidades das questões apagadas.
36. Uma falha simulada na marcação de visto não derruba o histórico da questão nem o envio, e uma falha ao gravar as novidades não desfaz a resposta do professor.

**Fechamento**
37. Smoke com o Docker de verdade: envio real que cai num grupo, resposta do professor pela rota, novidade no Início e na contagem, histórico da questão marcando como vista. Como o Gemini está sem crédito, o exercício "pré-gerado" é gravado por script no banco de desenvolvimento, junto com a novidade dele, e apagado no fim.

## Fora do escopo

- O treino curto da prova chegando (experimento 5), que depende da geração de exercícios pelo Gemini.
- A comparação do experimento 1, em script ou no painel do professor. Fica para depois do piloto, com os dados que esta volta passa a guardar.
- O lembrete pendente do RF20 e qualquer push, que são da fase 4.
- O professor ver quem leu a resposta.
- Novidade de atividade nova publicada, que o RF20 não pede.
- Preencher novidades do passado.
- A novidade de quando o reagrupamento muda o aluno de grupo sem envio novo dele.
- O desempenho por turma (3.3) e a passada de layout para o celular nas outras páginas (3.4).

## Decisões

1. **Abordagem A, tabela gravada quando a novidade chega** (Otávio). É a única que guarda o momento da chegada mesmo quando o grupo é apagado (todos corrigiram o erro) ou a resposta é editada. Calcular na hora perderia o dado nesses casos, e um carimbo único por aluno marcaria tudo como visto só por abrir o Início.
2. **Bolinha no menu além do bloco no Início** (Otávio). Serve para quem cai direto numa questão por um link e não passa pelo Início.
3. **Esta volta só guarda os dados do experimento** (Otávio). Hoje não há uso real para comparar, e a comparação vira uma volta pequena depois do piloto.
4. **O texto da resposta não aparece no Início.** O experimento diz que o Início mostra a novidade "até o aluno abrir", e é a tela da questão que mostra a resposta, junto do código e do diagnóstico.
5. **O visto é marcado pelo servidor ao entregar a resposta ou o exercício**, inclusive nas rotas de leitura (histórico da questão e detalhe do exercício). Não depende de uma chamada a mais do front, que poderia faltar, e a marcação só passa de vazio para preenchido, então repetir a leitura não muda nada.
6. **O aluno alcançado é o da tentativa mais recente no grupo**, a mesma regra da tela da questão, que só mostra a resposta na tentativa mais recente. A contagem `alunos_alcancados` que o professor vê continua como está.
7. **Edição depois de visto cria uma novidade nova**, porque o texto mudou e o aluno ainda não leu o novo. Edição antes de visto não duplica e mantém a primeira chegada.
8. **A novidade que deixa de valer fica no banco como não vista**, porque foi o que aconteceu. Apagar a linha esconderia do experimento quem recebeu e não voltou.
9. **Resposta apagada remove as novidades não vistas dela.** Não há o que ver, e a resposta desfeita não conta como novidade que chegou.
10. **Exercício pedido pelo aluno não vira novidade**, porque ele abre na hora. Só o da pré-geração espera por ele.
11. **Sem preenchimento do passado.** A tabela começa com a 0019. Antes de uma demonstração, o professor escreve uma resposta nova para a novidade aparecer.
12. **O reagrupamento que muda o aluno de grupo sem envio novo não gera novidade.** É raro e resolver pediria mexer no agrupamento, que roda a cada envio.
13. **"Prazos" vale para treino e prova**, com o modo escrito no cartão, porque a lista de treino com data também vence.
14. **Migração 0019 para as novidades**, e o 0.2 passa para a 0020. A única branch remota ainda não mergeada em 04/11 (`feature/conta-do-aluno`) é de documentação e não tem migração.
15. **Falha na novidade não derruba a rota** (recomendação do revisor de spec). O aluno precisa do diagnóstico e o professor precisa da resposta salva. A novidade é o registro em volta disso.
