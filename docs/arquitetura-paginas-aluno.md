# Arquitetura de páginas do lado do aluno

**Disciplina:** Produtos Digitais · Proposta de 21/08/2026

O app do aluno mostra hoje uma lista plana de atividades. A turma aparece como
rótulo, não como lugar. Este documento propõe a hierarquia de páginas que
falta, partindo das funcionalidades que já existem no código e das que estão
no roadmap.

## 1. O que existe hoje

| Rota | Página | Papel |
|---|---|---|
| `/aluno` | `AlunoHomePage` | entrar em turma, cartões de turma e lista de todas as atividades |
| `/aluno/progresso` | `ProgressoPage` | progresso global e erros recorrentes |
| `/aluno/perfil` | `AlunoPerfilPage` | dados da conta |
| `/aluno/atividades/:examId` | `AtividadePage` | questões da atividade |
| `/aluno/atividades/:examId/questoes/:numero` | `QuestaoPage` | enunciado, editor, tentativas |

Dois problemas concretos.

**O cartão da turma não leva a lugar nenhum.** Em `AlunoHomePage.jsx:131` a
turma é renderizada como uma `<div>`, não como um `<Link>`. O aluno vê o nome
da turma, o professor e a contagem de atividades, e não tem como clicar.

**A lista de atividades é plana.** Todas as turmas caem na mesma grade, com o
nome da turma em cinza pequeno sob o título. Com uma turma isso passa. Com
quatro, que é a situação real de um aluno de graduação, vira uma pilha sem
ordem.

A trilha de migalhas confirma a lacuna. De `QuestaoPage` o aluno volta para a
atividade, e da atividade volta direto para `/aluno`. O nível da turma não
existe no caminho.

## 2. O princípio

A hierarquia já existe nos dados:

```
Aluno → Enrollment → Turma → Exam → Question → Submission
```

`Exam.turma_id` amarra toda atividade a exatamente uma turma, e a resposta de
`AtividadeDetalhe` já devolve `turma_id` e `turma_nome`. Falta a navegação
espelhar isso.

A regra que este documento segue: **cada nível do domínio que o aluno precisa
comparar entre si merece uma página, e cada nível que ele só consome dentro de
um pai vira seção.**

Por isso turma vira página, porque o aluno compara turmas. Questão vira página,
porque o aluno navega entre questões. Tentativa continua seção dentro da
questão, porque o histórico só faz sentido ao lado do enunciado.

## 3. A hierarquia proposta

```
/aluno                                     Início
├── /aluno/turmas                          Minhas turmas
│   └── /aluno/turmas/:turmaId             Turma          ← o nível que falta
│       ├── Atividades  (aba padrão)
│       └── Meu desempenho na turma
├── /aluno/atividades/:examId              Atividade
│   └── .../questoes/:numero               Questão
├── /aluno/progresso                       Meu progresso   (transversal)
├── /aluno/trilha                          Treino dirigido (v2, transversal)
└── /aluno/perfil                          Conta
```

| Rota | Estado | Funcionalidades que serve |
|---|---|---|
| `/aluno` | reformular | 1 |
| `/aluno/turmas` | criar | 1 |
| `/aluno/turmas/:turmaId` | **criar** | 1, 4, 9 |
| `/aluno/atividades/:examId` | ajustar migalha | 2, 5 |
| `/aluno/atividades/:examId/questoes/:numero` | manter | 2, 3, 5 |
| `/aluno/progresso` | manter | 6 |
| `/aluno/trilha` | v2 | 10 |
| `/aluno/perfil` | manter | 1 |

Numeração igual à do documento "Produto, Personas, Mercado e Roadmap".

## 4. O que cada nível faz

### `/aluno` · Início

Responde uma pergunta só: **o que eu faço agora.**

- Continuar de onde parou, apontando para a última questão não resolvida.
- Prazos próximos, com as atividades em modo prova que fecham em breve.
- Linha de turmas clicáveis, como atalho.
- Três números do progresso, com link para a página cheia.

Hoje essa rota é a lista de atividades. Com as atividades morando na turma, o
início deixa de ser um depósito e passa a ser um painel. Um aluno com três
turmas precisa saber o que é urgente antes de escolher onde entrar.

### `/aluno/turmas` · Minhas turmas

Gerir vínculos e escolher onde trabalhar.

- Cartões clicáveis com nome, professor, código, número de atividades, número
  de pendências e barra de progresso da turma.
- O formulário de entrar em turma pelo código migra da home para cá, porque é
  uma ação sobre turmas.

### `/aluno/turmas/:turmaId` · Turma

A peça que falta, e o motivo deste documento.

**Cabeçalho:** nome da turma, professor e código de acesso.

**Aba Atividades**, padrão. Agrupada por `Exam.modo`, em duas seções:

| Seção | O que reúne | Por que separar |
|---|---|---|
| Provas | `modo = prova` | é o que vale nota, tem janela e teto de tentativas |
| Treinos | `modo = treino` | prática livre, tentativa ilimitada |

Essa é a primeira pergunta que o aluno faz ao abrir uma turma, e hoje a
resposta está num badge cinza no canto do cartão. Dentro de cada seção, a
ordem segue a situação que o backend já calcula em `_situacao`: aberta, depois
agendada, depois encerrada, com as concluídas ao final.

**Aba Meu desempenho na turma.** Progresso e erros recorrentes filtrados por
esta turma. Exige backend, ver seção 7.

### `/aluno/atividades/:examId` · Atividade

Já existe e não muda de estrutura. Muda só a migalha, que passa a apontar para
a turma em vez de voltar para a raiz. O dado necessário já vem na resposta.

### `/aluno/atividades/:examId/questoes/:numero` · Questão

Já existe. Enunciado, editor, submissão, diagnóstico pedagógico, histórico de
tentativas e explicação individual. Sem mudança.

### `/aluno/progresso` · Meu progresso

Continua global de propósito. Categoria de erro se repete entre turmas, e é
justamente aí que o painel de erros recorrentes tem valor. A visão recortada
por turma vive na aba da turma.

As duas respondem perguntas diferentes:

| Página | Pergunta |
|---|---|
| Aba da turma | como eu vou nesta disciplina |
| `/aluno/progresso` | onde eu erro sempre, em tudo que já fiz |

## 5. Decisão: a atividade entra sob a turma na URL?

| | A · aninhar | B · manter plana |
|---|---|---|
| URL | `/aluno/turmas/7/atividades/23/questoes/1` | `/aluno/atividades/23/questoes/1` |
| Migalha | vem da própria rota | vem de `turma_id` na resposta |
| Risco | o id da turma na URL pode divergir do `Exam.turma_id` real, e precisa ser validado | nenhum |
| Links atuais | quebram, exigem redirecionamento | continuam válidos |

**Recomendação: B.** A hierarquia fica na navegação e na trilha de migalhas,
não na URL do recurso. `Exam.turma_id` já é fonte única da verdade sobre a
turma de uma atividade, e a resposta de `AtividadeDetalhe` já carrega
`turma_nome`. Colocar o id da turma na URL cria uma segunda cópia dessa
informação, que passa a poder discordar da primeira e precisa de validação em
toda requisição, sem ganho para o aluno.

A opção A só compensaria se uma atividade pudesse pertencer a várias turmas,
o que o modelo não permite.

## 6. Navegação e migalhas

| | Hoje | Proposto |
|---|---|---|
| Menu | Atividades · Meu progresso | Início · Turmas · Progresso |
| Migalha | `← Atividades` | `Turmas › Algoritmos I › Lista 3 › Questão 2` |

O perfil continua no avatar, como está.

## 7. O que exige backend

| # | Endpoint | Para quê | Situação |
|---|---|---|---|
| 1 | `GET /aluno/atividades?turma_id=` | atividades da turma | **já existe**, `student_activity.py:21` |
| 2 | `GET /aluno/turmas/{id}` | cabeçalho da turma | criar, opcional |
| 3 | `GET /aluno/progresso?turma_id=` | aba de desempenho | criar |
| 4 | `GET /aluno/erros-recorrentes?turma_id=` | aba de desempenho | criar |
| 5 | pendências e progresso por turma | cartão em `/aluno/turmas` | criar |

O item 1 é a boa notícia: o filtro por turma já está implementado e o frontend
simplesmente não usa. A página da turma nasce sem endpoint novo.

Os itens 3 e 4 são pequenos. `progresso` e `erros_recorrentes` já partem das
submissões do aluno, e recortar por turma é uma condição a mais na consulta.

O item 2 é opcional. O cabeçalho pode sair de `listarMinhasTurmas()` filtrado
no cliente. Vale criar o endpoint mesmo assim, para a página não precisar
carregar a lista inteira só para desenhar um título.

## 8. Onde encaixa o treino dirigido

A funcionalidade 10 do roadmap ainda não começou, mas a hierarquia precisa
deixar o lugar dela pronto.

A trilha nasce dos erros recorrentes do aluno, que são pessoais e atravessam
turmas. Então ela é transversal, irmã de `/aluno/progresso`, e não filha de uma
turma. O ponto de entrada natural é o próprio painel de erros recorrentes, com
uma ação "treinar este erro" em cada categoria.

Se o professor curar uma trilha específica para a disciplina dele, ela aparece
como terceira aba dentro da turma. As duas formas convivem porque a hierarquia
separa o que é meu do que é da turma.

## 9. Estados vazios

| Situação | Onde | O que mostrar |
|---|---|---|
| Nenhuma turma | `/aluno` e `/aluno/turmas` | tela única com o campo de código, sem seções vazias |
| Turma sem atividade | turma | o professor ainda não publicou nada |
| Só atividades agendadas | turma | quando a primeira abre |
| Nenhuma tentativa | progresso | o que aparece aqui depois da primeira submissão |

O primeiro caso é o estado de toda conta nova. Hoje a home empilha três seções
vazias, e deveria ser uma tela só com o campo de código.

## 10. Ordem de implementação

| Fase | Entrega | Backend |
|---|---|---|
| 1 | Turma clicável, página da turma com atividades agrupadas por modo, migalha até a turma, menu com Turmas. `/aluno` redireciona para `/aluno/turmas` | nenhum |
| 2 | Aba de desempenho na turma, pendências e progresso no cartão | itens 2 a 5 |
| 3 | Início como painel, com continuar e prazos | pequeno |
| 4 | Trilha dirigida | funcionalidade 10 |

A fase 1 resolve sozinha a queixa que originou este documento e não depende de
nenhuma mudança no backend.

Relacionado: `mapa-funcionalidades.md`, `produto/produto-personas-mercado-roadmap.md`.
