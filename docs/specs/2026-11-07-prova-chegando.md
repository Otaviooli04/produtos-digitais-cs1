# Prova chegando, dentro do app

**Item do plano:** experimento 5 do Plano de Growth (seção 10 de `docs/produto/plano-implementacao.md`), sobre o Início do item 3.1
**Requisitos:** RF24 em parte, RN01, RN04, RN06 e RN09
**Data:** 2026-11-07

## Objetivo

Nos três dias antes de uma prova abrir, oferecer no Início um treino curto com os erros que o aluno mais repete, para trazer de volta quem tinha parado. A volta guarda os dados do experimento, e a comparação fica para depois do piloto.

## Comportamento

**Quando o cartão aparece.** Do instante `abre_em - 3 dias` até `abre_em`, sem incluir `abre_em`. A atividade precisa estar publicada, ser de uma turma do aluno, ter `modo = prova` e ter ao menos uma questão sem acerto e com tentativa sobrando. Prova sem `abre_em` nunca aparece, a mesma regra do funil. Lista também não. Quando a prova abre, o cartão some.

**Duas provas na janela.** Vale a que abre primeiro, com desempate pelo menor `exam_id`. A outra continua em "Prazos próximos".

**Onde.** No Início, abaixo de Novidades e acima de Continuar.

**O que o aluno vê.**

```
Prova 1 abre em 2 dias
Um treino curto com o que mais trava você. Nada aqui vale nota.

✓ Saída incorreta       feito
  Casas decimais      [Treinar]
  Compilação          [Treinar]

1 de 3 feitos
```

- O tempo usa o `prazoRelativo` que o cartão de prazos já usa.
- **Treinar** chama `POST /aluno/treino/gerar` com a categoria e abre `/aluno/treino/{id}?via=prova_chegando`. Enquanto espera, aquele botão mostra o carregando e os outros ficam desativados. Se a chamada falhar, o cartão mostra o `detail` da resposta, inclusive o do teto de gerações e o do limite de requisições.
- **Tudo feito.** O cartão fica até a prova abrir, com "Treino feito" no lugar de "3 de 3 feitos". Sem prêmio nem animação.
- **Sem erros para mostrar.** Sem cartão. A prova aparece só em "Prazos próximos", sem cobrança.
- A prova do cartão sai de "Prazos próximos", para não aparecer duas vezes na mesma tela.
- A bolinha do menu não muda, porque ela conta o que chegou de alguém.

O professor não vê nada de novo.

## Dados

Sem tabela, coluna ou migração. O cartão é calculado na hora, a partir do histórico (`ler_historico`) e dos erros (`erros_do_aluno`).

A medição sai do que o banco já guarda ou passa a guardar assim:

| Pergunta | De onde sai |
|---|---|
| Quem fez o treino | `tentativas_de_treino` dentro da janela |
| Quem veio pelo cartão | `acessos.via = 'prova_chegando'`, valor novo em `VIAS_ACEITAS` |
| Se errou menos depois | `submissions` da prova, por `error_category` |

Efeito nos dados existentes: nenhum.

## Backend

**Módulo novo `app/services/prova_chegando.py`,** só com funções puras sobre registros simples, testáveis sem banco:

- `prova_na_janela(atividades, agora)` recebe a lista de `AtividadeDoPainel` e devolve a atividade da janela ou `None`, aplicando as regras de "Quando o cartão aparece" e de "Duas provas na janela".
- `erros_do_treino(erros, envios, inicio_da_janela)` devolve até 3 itens `{error_category, feito}`.
- `montar_cartao(atividade, erros, envios)` devolve o dicionário do cartão ou `None` quando não há erro para mostrar.

**Como os erros são escolhidos.**

1. **Feitos, primeiro.** São as categorias de `erros` com um acerto na trilha desde o início da janela, em ordem do acerto. Acerto é um `Envio` com `origem = TRILHA`, `alvo` igual à categoria, `resultado = ACERTO`, `categoria` diferente do alvo e `momento >= inicio_da_janela`. É a mesma condição que `erros_do_aluno` usa para superar, porque violação de estrutura e aviso saem antes dos testes e o exercício passa com o erro ainda ali. Nesse caso, a categoria igual ao alvo não conta.
2. **Depois, os ativos sem acerto na janela,** na ordem que `erros_do_aluno` já devolve, do mais frequente para o menos.
3. **Corta em 3.**

Um erro feito continua feito até a prova abrir, mesmo que volte a aparecer. Um erro superado antes da janela só entra se o aluno treinar de novo dentro dela.

**Resposta.** `InicioResponse` ganha `prova_chegando: Optional[ProvaChegandoItem] = None`, com:

```
exam_id: int
titulo: str
turma_nome: str
abre_em: str               (ISO, como `quando` em PrazoItem)
erros: list[{error_category: str, feito: bool}]
```

O total e os feitos o front conta na lista.

**`inicio_service.painel`.** Calcula o cartão, tira a prova dele de `prazos` e devolve o campo novo. Sem matrícula, o retorno atual ganha `prova_chegando: None`. A rota `GET /aluno/inicio` continua com `get_current_student` e continua delegando ao serviço. A posse vem de `_atividades_e_questoes`, que só lê atividades publicadas das turmas do aluno.

**Exercício pronto antes do toque.** Quando o cartão tem um erro pendente, o `painel` chama `treino_service.preparar_proximo(student.id, categoria)` para o primeiro pendente. Essa função já não faz nada com exercício pendente na categoria, com o teto do dia esgotado ou com geração em voo. A chamada roda em thread própria, então o `painel` continua sem gravar nada na sessão dele, e a docstring do módulo passa a dizer isso.

**Sem rota nova.** Treinar usa `POST /aluno/treino/gerar`, que já tem papel, posse pelo próprio aluno, teto de 8 gerações por dia e limite de requisições.

**Via.** `acesso_service.VIAS_ACEITAS` passa a ser `{"convite", "prova_chegando"}`. O funil conta como "sem aviso" quem tem acesso com `via` nula na semana. O acesso do Início, sem origem, é anterior ao toque no cartão, então a via nova não apaga esse sinal.

## Frontend

- `pages/aluno/InicioPage.jsx`: componente `ProvaChegando`, no visual dos cartões da página, renderizado entre Novidades e Continuar quando `prova_chegando` existe. Usa `gerarExercicio`, que já está em `api/aluno.js`, e `navigate` para abrir o exercício com `?via=prova_chegando`. `AlunoLayout` já registra a via e a tira da URL.
- O nome do erro aparece pelo `shortError`, como no resto da página.
- Precisa caber em 360 px sem estouro, com botões de pelo menos 36 px de altura.

## Regras de uso responsável

- **RN01:** a lista vem só dos erros do próprio aluno. Nada é sorteado.
- **RN04:** sem push e sem aviso. O cartão só existe dentro do app.
- **RN06:** o cartão é individual. Ninguém da turma vê nada.
- **RN09:** quem não tem erro para treinar não recebe cartão nem cobrança, e o texto não fala em atraso.
- **Treino não vale nota,** e o cartão diz isso.

## Testes

**Funções puras (`prova_na_janela`).** Exatamente 3 dias antes entra, um segundo antes disso não entra, um segundo antes de abrir entra, no instante de abrir não entra. Sem `abre_em`, lista, sem nada por fazer e encerrada não entram. Duas provas na janela escolhem a que abre primeiro, com desempate pelo `exam_id`.

**Funções puras (`erros_do_treino`).** Só ativos, na ordem de frequência, cortados em 3. Acerto na janela vira feito e vem primeiro. Acerto antes da janela não conta. Acerto com categoria igual ao alvo não conta. Erro superado na janela continua na lista como feito. Erro feito que reaparece continua feito. Sem erros, lista vazia. Acerto na trilha para outra categoria não marca esta.

**Serviço e rota, com banco e `preparar_proximo` simulado.** O cartão vem em `GET /aluno/inicio` e sai de `prazos`, enquanto a outra prova da janela continua lá. Sem erro, sem cartão e com a prova em `prazos`. Sem matrícula, `null`. Prova de turma em que o aluno não está não aparece. Erros de outro aluno não entram. `preparar_proximo` é chamado com o primeiro pendente e não é chamado com tudo feito nem sem cartão. Sem token, 401.

**Via.** `prova_chegando` é gravada. Um valor fora da lista continua virando acesso sem origem. O aluno com acesso sem origem e depois `prova_chegando` na mesma semana continua em "sem aviso" no funil.

**Testes existentes do Início.** Precisam continuar passando. Os que têm prova na janela e erro passam a simular `preparar_proximo`, para nenhum teste chamar o Gemini.

**Tela, no smoke.** Cartão em 360 e 390 px, toque em Treinar abrindo o exercício, volta ao Início marcando feito depois do acerto, teto de gerações esgotado mostrando a mensagem. Em 1280 px, sem estouro.

## Fora do escopo

- "Como você se sente?" e o aviso por push, que ficam para o item 4.8. Por isso o RF24 continua parcial.
- Comparação do experimento e tela ou métrica para o professor, depois do piloto.
- Prova com só `fecha_em`, que não puxa, como decidido no funil.
- Exercício intercalado, tabela do treino curto e congelar a lista de erros. Se o experimento der resultado, a tabela pode vir depois.

## Decisões

1. **Até 3 erros, com "feito" no cartão.** Escolha do Otávio. Reaproveita a trilha e ainda parece um preparo para a prova.
2. **"Como se sente?" fica para o 4.8.** Escolha do Otávio. Oferecer o treino a todos é o que o Plano de Growth pede, e assim não há tabela nova.
3. **Calcular na hora, sem tabela.** Abordagem A, aprovada por ele. A lista pode mudar se o aluno errar algo novo durante a janela, e tudo bem, porque ela continua sobre os erros atuais dele.
4. **Só guardar os dados,** como no experimento 1.
5. **A janela só vale antes de a prova abrir.** Depois disso o aluno está fazendo a prova, e treinar não é mais preparo.
6. **O exercício do primeiro pendente é preparado ao abrir o Início.** O primeiro toque tende a ser imediato, e os outros podem esperar a geração, cerca de 25 segundos no ensaio de 07/11. O gasto com o Gemini fica dentro do teto que já existe.
7. **A prova do cartão sai de "Prazos próximos",** para não repetir a mesma informação na mesma tela.
8. **Um erro feito não volta atrás dentro da janela.** O cartão é sobre o preparo que o aluno fez, e quem errou de novo já vê isso na tentativa e no progresso.
