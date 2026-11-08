# Identidade CentralizEd: visual e estrutura do sistema inteiro

**Item do plano:** fora das fases numeradas. Fecha a decisão D5 (nome do produto), que passa a ser CentralizEd.
**Requisitos:** nenhum RF novo. Preserva RN05, RN09 e RNF04 (ver "Regras de uso responsável").
**Data:** 2026-11-08
**Guia de origem:** `docs/identidade-visual.md`, cópia versionada do guia escolhido pelo Otávio.

## Objetivo

Trocar o visual, a organização das telas e a identidade das 27 páginas do professor e do aluno, sem mudar o que o sistema faz, a tempo da apresentação de 12/11/2026.

## Comportamento

### O que não muda

- Endereços das páginas, chamadas à API, regras de negócio e dados.
- Lógica já existente nas telas: bolinha de novidades, registro de acessos, geração de insights, envio de código, janelas e tetos de tentativa.
- Textos de ação que o roteiro cita: "Copiar convite", "Enviar nova tentativa", "Preciso de uma dica", "Outra pista", "Ver explicação completa", "Treinar isso", "Treinar de novo".

### Professor

Menu lateral fixo no computador, com grupos que acompanham onde ele está:

- **Sempre:** logo, Turmas, e no rodapé Perfil e Sair.
- **Dentro de uma turma ou de uma atividade dela:** grupo com o nome da turma e os itens Panorama, Atividades e Desempenho.
- **Dentro de uma atividade:** grupo com o nome da atividade e os itens Questões, Alunos, Resultados, Testar submissão e Envio em lote.

Em largura menor que `lg`, o menu vira gaveta aberta por botão na barra do topo, e fecha ao navegar, ao tocar fora ou com Esc.

A página da turma passa a ter um painel violeta (nome, código da turma, código de acesso, alunos com conta, Copiar código, Copiar convite, Ver área do aluno, Nova atividade, Adicionar lista de aquecimento) e três seções escolhidas por `?secao=`:

| Seção | Conteúdo | Observação |
|---|---|---|
| `panorama` | `FunilDaTurma` | É a seção padrão. Valor ausente ou inválido cai nela |
| `atividades` | Provas e Listas | |
| `desempenho` | Cartões de resumo, taxa de aprovação, erros frequentes, trajetória | |

A página da atividade usa o mesmo painel violeta com nome, tipo e situação, e mantém renomear e excluir nele. Os links Alunos, Testar submissão, Envio em lote e Resultados saem da página e ficam no menu.

Na questão do professor, as abas Respostas e Grupos de dificuldade continuam, com Respostas como padrão. Na aba de grupos, cada grupo é um card principal.

Em todas as telas internas, o caminho "Turmas › turma › atividade" deixa de existir como texto solto no topo em largura `lg` ou maior, porque o menu já diz onde o professor está. Abaixo disso ele continua visível.

### Aluno

- **Computador:** barra branca no topo com logo, Início, Turmas, Treino, Meu progresso, perfil e Sair.
- **Celular:** barra do topo só com logo, perfil e Sair, e abas fixas embaixo (Início, Turmas, Treino, Progresso), com ícone, rótulo e a bolinha de novidades no Início. O conteúdo reserva espaço para as abas, incluindo a área segura do aparelho.
- **Início:** "Continuar" vira painel violeta no topo quando existe. Abaixo, em duas colunas no computador e uma no celular: Novidades e Prova chegando à esquerda, Prazos à direita. Sem "Continuar", a tela abre com o título normal. Conta sem turma mantém a tela única de entrada.
- **Questão e exercício da trilha:** duas colunas a partir de `lg`, com enunciado, casos e histórico à esquerda, e editor, envio, resultado e ajuda à direita. No celular, uma coluna, na ordem atual.
- **Progresso:** cartão "Erros superados" em destaque no topo, seguido de Provas, Listas, semana a semana, erros que se repetem e erros superados.
- **Turmas, Turma, Atividade, Treino e Perfil:** mesma ordem de hoje, com as peças novas.

### Entrada

Login e cadastro do professor, login e cadastro do aluno e convite usam tela dividida: painel violeta com o logo e o símbolo de órbita de um lado, formulário no outro. No celular, o painel vira faixa no topo.

### Textos

- A marca vira CentralizEd em todas as telas, no título da aba, na descrição, no favicon, na cor do tema e na mensagem de convite do professor.
- Tom animado só em três ações de entrada do aluno: "Continuar" vira "Bora continuar!", "Começar" vira "Bora começar!" e "Ir para a trilha" vira "Bora treinar!". Todo o resto mantém o texto atual.

## Dados

Nenhuma alteração. Sem migração.

## Backend

Nenhuma alteração.

## Frontend

### Base

- `src/index.css`: tokens do guia no `@theme` do Tailwind (`violeta`, `violeta-escuro`, `coral`, `noite`, `cinza-texto`, `lavanda`), cores de estado (`sucesso` `#12805C` sobre `sucesso-fundo` `#E3F7EE`, `erro` `#C4263B` sobre `erro-fundo` `#FFE9EC`, `aviso` `#8A5A00` sobre `aviso-fundo` `#FFF4D6`), fontes, raios e `--sombra-bloco`. Foco visível em violeta. Animações desligadas com `prefers-reduced-motion`.
- Durante a migração, as cores antigas do Tailwind (`purple`, `gray` e demais usadas hoje) são redefinidas no tema para os valores novos. Assim todas as telas mudam de cor desde o primeiro lote. Essa redefinição sai no último lote.
- `index.html`: fontes do guia pelo Google Fonts, título, descrição e `theme-color` `#4A2EE0`.
- `public/favicon.svg`: favicon do guia.
- `lucide-react` em versão exata no `package.json`, importando ícone por ícone. Substitui os SVGs de interface escritos à mão e os caracteres usados como ícone (✓, ←, ›, +).

### Peças em `src/components/ui/`

| Peça | Faz | Usa |
|---|---|---|
| `Card` | Card do guia. Prop `principal` liga a sombra chapada | todas as telas |
| `Botao` | Primário, secundário e de perigo, altura mínima de 44 px, afunda ao clicar. Renderiza `button` ou `Link` | todas as telas |
| `Tag` | Tag do guia com variantes de estado. `Badge` passa a delegar a ela | listas e cabeçalhos |
| `Progresso` | Barra do guia, com `role="progressbar"` | progresso e funil |
| `PainelDestaque` | Fundo violeta com o símbolo de órbita grande cortado na borda | entrada, turma, atividade, Início |
| `RotuloSecao` | Rótulo em maiúsculas do guia | cabeçalhos de bloco |

- `Logo` é reescrito: prop `fundo` (`claro` ou `violeta`) escolhe as cores do símbolo e do wordmark. Prop `soSimbolo` omite o wordmark.
- O símbolo grande é só decoração: `aria-hidden` e sem interceptar cliques.

### Molduras

- `Layout.jsx`: menu lateral, gaveta e `JobDock`.
- `components/MenuLateral.jsx`: desenha os grupos. Usa o hook abaixo.
- `hooks/useContextoProfessor.js`: lê a rota com `useMatch` e busca a turma (`getTurma`) ou a atividade (`getExam`, que traz `turma_id` e `turma_nome`). Falha na busca, ou atividade sem turma, só esconde o grupo correspondente, porque a própria página mostra o erro.
- Renomear turma ou atividade dispara o evento `CONTEXTO_MUDOU`, que o hook escuta, no mesmo padrão de `NOVIDADES_MUDARAM`. Assim o menu não fica com o nome velho.
- `AlunoLayout.jsx`: troca apenas a marcação. Os três `useEffect` ficam como estão.
- `JobDock` fica acima das abas e abaixo de modais.

### Páginas

Todas as páginas de `src/pages/` e os componentes de `src/components/` trocam classes e usam as peças. Mudanças de arranjo só nas descritas em "Comportamento". A lógica de estado e os efeitos não mudam, salvo o que for preciso para ler `?secao=` e disparar `CONTEXTO_MUDOU`.

- `TurmaDetailPage`: seções por `?secao=`. O funil e os dados de `analytics` continuam carregados como hoje.
- Links internos que hoje levam à turma para ver as atividades passam a apontar para `?secao=atividades`.

### Gráficos

As constantes de cor em `ResultsPage`, `TurmaDetailPage`, `QuestionPage` e `BarList` saem para `src/utils/coresGraficos.js`, com paleta categórica derivada de violeta e coral. Taxas usam as cores de estado.

## Regras de uso responsável

- **RN05:** a North Star continua só agregada. Nada do reagrupamento expõe valor por aluno.
- **RN09 e RNF04:** alunos em risco continuam visíveis só ao professor dono da turma, no Panorama.
- O aviso de pausa continua com cor de aviso e na mesma posição do fluxo de envio.
- O tom animado não entra em prova, envio, resultado nem ajuda. Nenhum elemento de ranking, sequência ou pontos é introduzido pelo estilo.

## Testes

O front não tem testes automatizados. O que prova que funciona:

- `eslint` e `vite build` sem erro. Suíte do backend com os mesmos 625 testes passando.
- Varredura sem resto de marca ou cor antiga em `frontend/src` e `frontend/index.html`: zero ocorrências de `Analytics CS1`, de classes `purple-`, `gray-`, `blue-`, `indigo-`, `sky-`, `slate-`, `violet-`, `emerald-`, `amber-`, `yellow-`, `green-`, `red-`, `orange-` seguidas de número, e de `linear-gradient`.
- Navegador automatizado em 360, 390 e 1280 px, logado como professor e como aluno, em todas as páginas: sem largura estourada, sem erro no console.
- Casos-limite conferidos na tela: nome longo de turma e de atividade em 360 px, `?secao=` inválido, atividade sem turma, conta sem turma, Início sem "Continuar", bolinha com mais de 9 novidades, gaveta com Esc, e renomear atividade atualizando o menu.
- Contraste de texto e fundo calculado para as combinações novas, no mínimo 4,5:1 em texto normal.
- Foco de teclado visível em menu, botões e abas.
- Conferência do Otávio no navegador depois da moldura, antes de migrar as demais telas.
- Ensaio completo do roteiro, com Docker e Gemini reais, sobre a versão final.

## Fora do escopo

- Landing page, que fica para depois da apresentação.
- Modo escuro.
- Texto `Learning Analytics CS1` da rota de status do backend, que o usuário não vê.
- Funcionalidades novas e correções de diagnóstico.

## Decisões

1. **Peças novas e todas as telas migradas, com reorganização ampla no professor** (escolha do Otávio).
2. **Panorama é a seção padrão da turma:** responde primeiro a quem está sumindo.
3. **Seções por parâmetro na URL:** mesmo recurso das abas da questão, sem rota nova.
4. **Questão do professor abre em Respostas:** abrir em Grupos dispararia insight do Gemini a cada questão nova visitada, por causa do efeito automático da aba. O destaque dos grupos fica no tratamento visual.
5. **Cartões de resumo vão para Desempenho:** o Panorama fica só com o funil.
6. **Cores de estado fora do guia:** o guia não cobre Correto, Erro e aviso. Coral continua acento, para não se confundir com erro.
7. **Sombra chapada só em card e botão principal:** como o guia pede, e para não pesar nas telas densas.
8. **Código com fonte monoespaçada do sistema:** nenhuma fonte do guia serve para código.
9. **Título de página com cerca de 30 px no celular:** 40 px quebra nome longo em 360 px.
10. **`lucide-react` em versão exata:** só ícones, exceção aprovada à regra de não adicionar biblioteca de UI.
11. **Google Fonts direto, como o guia manda:** o sistema já depende de rede, e a troca por arquivos locais fica para a hospedagem.
12. **Tom animado só em três ações de entrada do aluno** (aprovado pelo Otávio).
13. **Cores antigas redefinidas durante a migração:** se o tempo apertar, nenhuma tela fica com aparência antiga.
14. **A `dev` atual é o plano B:** se a branch não estabilizar a tempo, a apresentação usa a `dev` como está.
