# Identidade CentralizEd: plano de implementação

> **Para quem executa:** usar a skill `sdd` (recomendado) ou a execução sem subagentes descrita nela. Passos com caixa de seleção (`- [ ]`).

**Objetivo:** trocar visual, organização e marca das 27 páginas do frontend pelo guia CentralizEd, sem mudar o que o sistema faz.

**Arquitetura:** tokens do guia no `@theme` do Tailwind v4, troca automática de todas as classes de cor por um script único, peças em `src/components/ui/`, duas molduras novas e migração de cada página para as peças, na ordem do roteiro da demonstração.

**Stack:** React 19, React Router 7, Tailwind v4, Recharts, `lucide-react`. Sem backend, sem migração.

**Spec:** `docs/specs/2026-11-08-identidade-centralized.md`. Guia visual: `docs/identidade-visual.md`. Leia os dois antes de começar.

## Restrições globais

- Trabalhar só em `frontend/` e, quando indicado, em `docs/`. Nunca em `backend/`.
- Não alterar endereços de rota, chamadas de `src/api/`, `useEffect`, regras de estado nem condições de exibição, salvo onde a tarefa disser.
- Textos que não mudam: "Copiar convite", "Copiar código", "Enviar nova tentativa", "Preciso de uma dica", "Outra pista", "Ver explicação completa", "Treinar isso", "Treinar de novo", "Que tal uma pausa de um minuto?". Em geral, nenhum texto muda sem a tarefa mandar.
- Sem gradiente, sem sombra com desfoque (`shadow-sm`, `shadow`, `shadow-md` e afins saem), sem emoji como ícone.
- Texto branco sobre coral é proibido. Coral sobre violeta só em 32 px ou mais.
- Ícones: `lucide-react`, importados um a um, traço 2, cor `text-noite` ou `text-violeta`, ou a cor do texto do botão em que estão.
- Git dentro do worktree: `/usr/bin/git`, um comando por chamada, a partir da raiz do worktree. Commit sem `Co-Authored-By`.
- Fim de cada tarefa, em `frontend/`: `rtk proxy node_modules/.bin/eslint .` sem erros e `node_modules/.bin/vite build` concluído.

### Receita de migração das páginas

| Hoje | Depois |
|---|---|
| Título da página (`h1` com `text-xl font-semibold`) | `h1` com `className="titulo-pagina"` |
| Título dentro de card (`h2` ou `h3` com `text-sm font-semibold`) | `className="titulo-card"` |
| Cabeçalho de bloco sobre uma lista de cards (`text-sm font-semibold` ou `uppercase tracking-wide`) | `<RotuloSecao as="h2">` |
| Contêiner `bg-white rounded-xl border ... p-5` | `<Card>`. Com `principal` se for o bloco central da tela ou um card clicável de lista |
| Item dentro de card ou linha de lista | sem sombra, `border-2 border-noite/20 rounded-botao` ou `bg-lavanda rounded-botao` |
| Botão cheio (`bg-violeta text-white`) | `<Botao>` |
| Botão de contorno | `<Botao variante="secundario">` |
| Botão de excluir | `<Botao variante="perigo">` |
| `Link` com visual de botão | `<Botao to="...">` |
| Botão só com ícone | `<button>` com `min-h-11 min-w-11` e `aria-label`, sem borda até o hover |
| `<input>`, `<select>`, `<textarea>` de formulário | `className="campo"`. O editor de código continua com `CodeTextarea` |
| Estado vazio com borda tracejada | `<Card className="border-dashed border-noite/30! text-center">` |
| Mudar padding, gap ou cor de borda de um `Card` por `className` | sufixo `!` do Tailwind v4 (`p-0!`, `gap-0!`, `p-10!`, `border-noite/30!`), senão o padrão do `Card` vence no CSS gerado |
| Aviso de erro (`bg-erro-fundo border ...`) | manter o fundo, `rounded-botao`, `border-2 border-erro` |
| `rounded-full` em barra | usar `<Progresso>` quando for barra de progresso. `BarList` tem marcação própria |
| Fundo de página `bg-lavanda` em `min-h-screen` | `bg-white` |

Tabela de ícones:

| Função | Ícone |
|---|---|
| Alunos | `Users` |
| Testar submissão, editor | `FileCode` |
| Envio em lote, upload | `Upload` |
| Resultados | `ChartColumn` |
| Renomear, editar | `Pencil` |
| Excluir | `Trash2` |
| Abrir e fechar lista | `ChevronDown` |
| Voltar | `ArrowLeft` |
| Separador de caminho | `ChevronRight` |
| Adicionar | `Plus` |
| Feito, correto (no lugar de ✓) | `Check` |
| Fechar | `X` |
| Atividades, sem atividade | `ClipboardList` |

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `frontend/package.json`, `package-lock.json` | `lucide-react` versão exata |
| `frontend/index.html` | fontes, título, descrição, cor do tema, `viewport-fit=cover` |
| `frontend/public/favicon.svg` | favicon do guia |
| `frontend/src/index.css` | tokens, utilitários `titulo-pagina`, `titulo-card`, `campo`, foco, movimento reduzido |
| `frontend/src/components/ui/Card.jsx` | card do guia |
| `frontend/src/components/ui/Botao.jsx` | botão ou link com aparência de botão |
| `frontend/src/components/ui/Tag.jsx` | tag com variantes |
| `frontend/src/components/ui/Progresso.jsx` | barra de progresso |
| `frontend/src/components/ui/PainelDestaque.jsx` | painel violeta com órbita |
| `frontend/src/components/ui/RotuloSecao.jsx` | rótulo em maiúsculas |
| `frontend/src/components/Logo.jsx` | símbolo e wordmark |
| `frontend/src/components/Badge.jsx` | delega a `Tag` |
| `frontend/src/hooks/useContextoProfessor.js` | turma e atividade atuais para o menu |
| `frontend/src/components/MenuLateral.jsx` | grupos do menu do professor |
| `frontend/src/components/Layout.jsx` | moldura do professor e gaveta |
| `frontend/src/components/AlunoLayout.jsx` | moldura do aluno e abas |
| `frontend/src/components/TelaDeEntrada.jsx` | tela dividida de login, cadastro e convite |
| `frontend/src/utils/coresGraficos.js` | paleta dos gráficos |
| Páginas e componentes restantes | só marcação e classes |

## Lotes

- Lote A, Tasks 1 a 3: tema, troca automática de cores e peças
- Lote B, Tasks 4 a 6: moldura do professor, moldura do aluno e telas de entrada
- Lote C, Tasks 7 e 8: Início do aluno e turma do professor. **Ao terminar, PARAR: conferência do Otávio no navegador, antes do Lote D**
- Lote D, Tasks 9 a 12: atividade, questão do professor, questão do aluno, demais telas do aluno
- Lote E, Tasks 13 a 16: demais telas do professor e componentes restantes
- Lote F, Task 17: varredura final e documentação

## Varredura

### Pares que dividem arquivo ou interface

| Par | O que uma produz x o que a outra consome | Situação |
|---|---|---|
| T1 → T2 | tokens `violeta`, `noite`, `cinza-texto`, `lavanda`, `sucesso`, `erro`, `aviso`, `*-fundo`, `codigo-*` usados pelas classes geradas | bate |
| T1 → T3 | `rounded-card`, `rounded-botao`, `rounded-tag`, `shadow-bloco`, `font-titulo`, `font-logo` usados pelas peças | bate |
| T2 x T3 | T2 reescreve `Badge.jsx` e `Logo.jsx` só nas classes, T3 substitui os dois arquivos inteiros | sem conflito, T3 vem depois |
| T3 → T4, T5, T6 | `Logo` com `fundo`, `tamanho`, `soSimbolo` | bate |
| T4 → T9 | `avisarContextoMudou` de `useContextoProfessor.js` | bate |
| T4 x T8 | links `?secao=` do menu e leitura de `secao` na página | mesmos valores `panorama`, `atividades`, `desempenho` |
| T8 → T10, T15 | `CORES_CATEGORICAS`, `corDaTaxa`, `COR_ERRO`, `COR_PADRAO` | bate |
| T11 x T16 | T11 migra `TentativaDetalhe`, `CodeBlock`, T16 não toca neles | sem conflito |
| T8 x T16 | T8 migra `FunilDaTurma`, `TrajetoriaDeErros`, `BarList`, T16 não toca neles | sem conflito |

### O teste de cada tarefa bate com o código dela?

O front não tem suíte. A conferência de cada tarefa é lint, build e o critério abaixo.

| Tarefa | Conferência | Situação |
|---|---|---|
| T1 | build gera CSS com `--color-violeta`, favicon novo | bate |
| T2 | `grep` da lista de famílias retorna zero em `src` | bate, o script cobre os 5 prefixos e todas as famílias levantadas |
| T3 | lint e build, peças ainda sem uso | bate |
| T4 | navegar turma, atividade e questão muda os grupos | bate |
| T5 | abas fixas abaixo de `sm`, bolinha no Início | bate |
| T6 | `grep "Analytics CS1" src` retorna só a linha 102 de `TurmaDetailPage`, tratada na T8 | bate |
| T7 | Início com e sem "Continuar" | bate |
| T8 | `?secao=` válido e inválido, zero "Analytics CS1" em `src` | bate |
| T9 | renomear atualiza o menu | bate |
| T10 | abas continuam, padrão Respostas | bate |
| T11 | duas colunas em `lg`, ordem atual no celular | bate |
| T12 | telas sem SVG solto e sem card antigo | bate |
| T13 | telas sem SVG solto e sem card antigo, card da turma abre no Panorama | bate |
| T14 | telas sem SVG solto e sem card antigo, `pre` de exemplo legível sobre `bg-noite` | bate |
| T15 | tabelas sem estourar em 360 px, cores vindas de `CORES_CATEGORICAS` | bate |
| T16 | modais acima do menu e do `JobDock`, sem card antigo | bate |
| T17 | todas as varreduras do spec zeradas | bate |

---

### Task 1: tema, fontes e favicon

**Arquivos:**
- Alterar: `frontend/package.json`, `frontend/package-lock.json`, `frontend/index.html`, `frontend/public/favicon.svg`, `frontend/src/index.css`

**Interfaces:**
- Produz: tokens de cor, `rounded-card`, `rounded-botao`, `rounded-tag`, `shadow-bloco`, `font-titulo`, `font-logo`, utilitários `titulo-pagina`, `titulo-card`, `campo`.

- [ ] **Passo 1: instalar a biblioteca de ícones em versão exata**

Em `frontend/`: `npm install --save-exact lucide-react@1.70.0 --no-audit --no-fund`

- [ ] **Passo 2: substituir `frontend/src/index.css` inteiro**

```css
@import "tailwindcss";

@theme {
  --color-violeta: #4A2EE0;
  --color-violeta-escuro: #3A1FC2;
  --color-coral: #FF6B4A;
  --color-noite: #14112B;
  --color-cinza-texto: #5A5478;
  --color-lavanda: #F3F0FF;

  --color-sucesso: #0F7654;
  --color-sucesso-fundo: #E3F7EE;
  --color-erro: #C4263B;
  --color-erro-fundo: #FFE9EC;
  --color-aviso: #8A5A00;
  --color-aviso-fundo: #FFF4D6;

  --color-codigo-texto: #E8E5F7;
  --color-codigo-sucesso: #7CE0B5;
  --color-codigo-erro: #FF9EAB;
  --color-codigo-aviso: #FFD76A;

  --font-sans: Nunito, ui-sans-serif, system-ui, sans-serif;
  --font-titulo: "Baloo 2", Nunito, ui-sans-serif, sans-serif;
  --font-logo: "Space Grotesk", ui-sans-serif, sans-serif;

  --radius-card: 20px;
  --radius-botao: 14px;
  --radius-tag: 10px;

  --shadow-bloco: 6px 6px 0 var(--color-violeta);
}

@utility titulo-pagina {
  font-family: var(--font-titulo);
  font-weight: 800;
  line-height: 1.2;
  font-size: 1.875rem;

  @media (min-width: 64rem) {
    font-size: 2.5rem;
  }
}

@utility titulo-card {
  font-family: var(--font-titulo);
  font-weight: 800;
  line-height: 1.2;
  font-size: 1.5rem;
}

@utility campo {
  width: 100%;
  min-height: 2.75rem;
  padding: 0.625rem 0.75rem;
  font-size: 0.875rem;
  background: var(--color-white);
  color: var(--color-noite);
  border: 2px solid var(--color-noite);
  border-radius: var(--radius-botao);
}

@layer base {
  body {
    background: var(--color-white);
    color: var(--color-noite);
    font-family: var(--font-sans);
    -webkit-font-smoothing: antialiased;
  }

  h1,
  h2,
  h3 {
    font-family: var(--font-titulo);
  }

  :focus-visible {
    outline: 2px solid var(--color-violeta);
    outline-offset: 2px;
  }

  button:not(:disabled),
  [role="button"]:not(:disabled),
  label[for],
  summary {
    cursor: pointer;
  }
}

/* No iPhone, campo com letra menor que 16 px dá zoom ao receber o foco. */
@media (max-width: 639px) {
  input,
  textarea,
  select {
    font-size: 16px;
    line-height: 1.5;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}
```

- [ ] **Passo 3: substituir `frontend/index.html` inteiro**

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
    <meta name="theme-color" content="#4A2EE0" />
    <meta name="description" content="CentralizEd: turma virtual de programação que corrige, explica o erro e mostra ao professor onde a turma trava." />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;800&family=Space+Grotesk:wght@500;700&family=Nunito:wght@400;600;700&display=swap" rel="stylesheet" />
    <title>CentralizEd</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Passo 4: substituir `frontend/public/favicon.svg` inteiro**

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 84 84">
  <circle cx="42" cy="42" r="42" fill="#14112B"/>
  <circle cx="42" cy="42" r="28" fill="none" stroke="#FFFFFF" stroke-width="6"/>
  <circle cx="42" cy="42" r="10" fill="#FF6B4A"/>
</svg>
```

- [ ] **Passo 5: conferir e commitar**

Lint e build. Depois: `git add frontend/package.json frontend/package-lock.json frontend/index.html frontend/public/favicon.svg frontend/src/index.css` e `git commit -m "feat(identidade): tokens, fontes e favicon do CentralizEd"`.

---

### Task 2: troca automática das classes de cor

**Arquivos:**
- Alterar: todos os `.jsx` de `frontend/src` que usam as classes antigas
- Script descartável, em qualquer pasta fora do repositório: `trocar_cores.py`

**Interfaces:**
- Consome: tokens da Task 1.

- [ ] **Passo 1: escrever o script**

```python
import pathlib
import re
import sys

EXATOS = {
    "text-gray-100": "text-codigo-texto",
    "text-green-400": "text-codigo-sucesso",
    "text-yellow-400": "text-codigo-aviso",
    "text-red-300": "text-codigo-erro",
    "bg-purple-700": "bg-violeta-escuro",
}

ESTADOS = {
    "purple": ("violeta", "lavanda"),
    "violet": ("violeta", "lavanda"),
    "indigo": ("violeta", "lavanda"),
    "blue": ("violeta", "lavanda"),
    "sky": ("violeta", "lavanda"),
    "red": ("erro", "erro-fundo"),
    "rose": ("erro", "erro-fundo"),
    "green": ("sucesso", "sucesso-fundo"),
    "emerald": ("sucesso", "sucesso-fundo"),
    "yellow": ("aviso", "aviso-fundo"),
    "amber": ("aviso", "aviso-fundo"),
    "orange": ("aviso", "aviso-fundo"),
}


def cinza(prefixo, tom):
    if prefixo == "text":
        if tom >= 800:
            return "noite"
        if tom >= 400:
            return "cinza-texto"
        return "cinza-texto/60"
    if prefixo == "bg":
        return "noite" if tom >= 800 else "lavanda"
    if prefixo == "ring":
        return "noite/20" if tom < 500 else "noite"
    if tom <= 100:
        return "noite/10"
    return "noite/20" if tom == 200 else "noite/30"


def estado(prefixo, tom, cor, fundo):
    if prefixo == "text":
        return cor
    if prefixo == "bg":
        if tom <= 100:
            return fundo
        return f"{cor}/30" if tom <= 300 else cor
    if tom <= 100:
        return f"{cor}/15"
    if tom == 200:
        return f"{cor}/30"
    return f"{cor}/50" if tom == 300 else cor


PADRAO = re.compile(
    r"(?<![\w-])(bg|text|border|ring|divide)-"
    r"(gray|purple|violet|indigo|blue|sky|red|rose|green|emerald|yellow|amber|orange)-(\d{2,3})(?![\w-])"
)


def trocar(m):
    inteiro = m.group(0)
    if inteiro in EXATOS:
        return EXATOS[inteiro]
    prefixo, familia, tom = m.group(1), m.group(2), int(m.group(3))
    if familia == "gray":
        return f"{prefixo}-{cinza(prefixo, tom)}"
    cor, fundo = ESTADOS[familia]
    return f"{prefixo}-{estado(prefixo, tom, cor, fundo)}"


raiz = pathlib.Path(sys.argv[1])
alterados = 0
for arquivo in raiz.rglob("*.jsx"):
    antes = arquivo.read_text(encoding="utf-8")
    depois = PADRAO.sub(trocar, antes)
    if depois != antes:
        arquivo.write_text(depois, encoding="utf-8")
        alterados += 1
print(alterados, "arquivos alterados")
```

- [ ] **Passo 2: rodar**

Em `frontend/`: `python3 -I <caminho do script> src`.

- [ ] **Passo 3: acertar à mão os trechos sobre fundo escuro**

Em `src/components/CodeBlock.jsx`, no objeto do tema `dark`, trocar `gutter: 'text-cinza-texto'` por `gutter: 'text-white/40'` e `hotGutter: 'text-erro'` por `hotGutter: 'text-codigo-erro'`, só na linha do tema escuro.

Em `src/components/TentativaDetalhe.jsx`, no `pre` de erro de compilação (`bg-noite` com `text-erro`), trocar `text-erro` por `text-codigo-erro`.

Em `src/pages/BulkSubmitPage.jsx`, dentro do bloco `bg-noite` por volta das linhas 128 a 131, trocar os dois `text-cinza-texto` por `text-white/60`.

Em `src/components/CodeTextarea.jsx`, na coluna de numeração de linhas (por volta da linha 123), trocar `text-cinza-texto` por `text-white/60`, porque a Task 11 deixa o editor com fundo `bg-noite`.

Na bolinha de novidades de `AlunoLayout.jsx` nada a fazer, a Task 5 refaz.

- [ ] **Passo 4: conferir e commitar**

Rodar em `frontend/`: `grep -rnE '(bg|text|border|ring|divide)-(gray|purple|violet|indigo|blue|sky|red|rose|green|emerald|yellow|amber|orange)-[0-9]' src`. Esperado: nenhuma linha.

Lint e build. Depois `git add frontend/src` e `git commit -m "refactor(identidade): classes de cor trocadas pelos tokens do guia"`.

---

### Task 3: peças e logo

**Arquivos:**
- Criar: os seis arquivos de `frontend/src/components/ui/`
- Substituir: `frontend/src/components/Logo.jsx`, `frontend/src/components/Badge.jsx`

**Interfaces:**
- Produz: `Card({ principal, as, className, ...props })`, `Botao({ variante, to, className, ...props })`, `Tag({ variante, children })`, `Progresso({ valor, rotulo })`, `PainelDestaque({ className, children })`, `RotuloSecao({ as, className, children })`, `Logo({ fundo, tamanho, soSimbolo })`, `SimboloOrbita({ fundo, className })` (exportação nomeada de `Logo.jsx`).

- [ ] **Passo 1: criar `ui/Card.jsx`**

```jsx
export default function Card({ principal = false, as = 'div', className = '', ...props }) {
  const Elemento = as
  return (
    <Elemento
      className={`bg-white border-2 border-noite rounded-card p-[22px] flex flex-col gap-3.5 ${principal ? 'shadow-bloco' : ''} ${className}`}
      {...props}
    />
  )
}
```

- [ ] **Passo 2: criar `ui/Botao.jsx`**

```jsx
import { Link } from 'react-router-dom'

const VARIANTES = {
  primario: 'bg-violeta text-white hover:bg-violeta-escuro',
  secundario: 'bg-white text-noite hover:bg-lavanda',
  perigo: 'bg-white text-erro hover:bg-erro-fundo',
}

export default function Botao({ variante = 'primario', to, className = '', ...props }) {
  const classes = `inline-flex items-center justify-center gap-2 min-h-11 px-[22px] border-2 border-noite rounded-botao font-bold text-[15px] transition-transform active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed ${VARIANTES[variante]} ${className}`
  if (to) return <Link to={to} className={classes} {...props} />
  return <button type="button" className={classes} {...props} />
}
```

`type="button"` é padrão, e o formulário passa `type="submit"` por `props`, que vem depois e vence.

- [ ] **Passo 3: criar `ui/Tag.jsx`**

```jsx
const VARIANTES = {
  violeta: 'bg-lavanda text-violeta',
  sucesso: 'bg-sucesso-fundo text-sucesso',
  erro: 'bg-erro-fundo text-erro',
  aviso: 'bg-aviso-fundo text-aviso',
  neutro: 'bg-lavanda text-cinza-texto',
}

export default function Tag({ variante = 'violeta', children }) {
  return (
    <span className={`inline-flex items-center text-[13px] font-bold px-3 py-[5px] rounded-tag ${VARIANTES[variante]}`}>
      {children}
    </span>
  )
}
```

- [ ] **Passo 4: criar `ui/Progresso.jsx`**

```jsx
export default function Progresso({ valor, rotulo }) {
  const limitado = Math.max(0, Math.min(100, valor))
  return (
    <div
      role="progressbar"
      aria-label={rotulo}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(limitado)}
      className="h-2.5 rounded-[5px] bg-lavanda overflow-hidden"
    >
      <div className="h-2.5 rounded-[5px] bg-coral" style={{ width: `${limitado}%` }} />
    </div>
  )
}
```

- [ ] **Passo 5: criar `ui/RotuloSecao.jsx`**

```jsx
export default function RotuloSecao({ as = 'p', className = '', children }) {
  const Elemento = as
  return (
    <Elemento className={`font-titulo font-extrabold text-[13px] uppercase tracking-[0.1em] text-cinza-texto ${className}`}>
      {children}
    </Elemento>
  )
}
```

- [ ] **Passo 6: substituir `Logo.jsx`**

```jsx
const CORES = {
  claro: { traco: '#4A2EE0', nome: 'text-noite', ed: 'text-violeta' },
  violeta: { traco: '#FFFFFF', nome: 'text-white', ed: 'text-coral' },
}

export function SimboloOrbita({ fundo = 'claro', className = '' }) {
  const { traco } = CORES[fundo]
  return (
    <svg className={className} viewBox="0 0 84 84" aria-hidden="true">
      <circle cx="42" cy="42" r="38" fill="none" stroke={traco} strokeWidth="3" />
      <circle cx="42" cy="42" r="23" fill="none" stroke={traco} strokeWidth="3" opacity="0.45" />
      <circle cx="42" cy="42" r="10" fill={traco} />
      <circle cx="69" cy="15" r="7" fill="#FF6B4A" />
      <circle cx="20" cy="56" r="5" fill={traco} />
    </svg>
  )
}

const TAMANHOS = {
  md: { simbolo: 'w-8 h-8', texto: 'text-[22px]', espaco: 'gap-2.5' },
  lg: { simbolo: 'w-12 h-12', texto: 'text-[32px]', espaco: 'gap-[18px]' },
}

// Sobre violeta use sempre tamanho `lg`: o guia só aceita coral sobre violeta a partir de 32 px.
export default function Logo({ fundo = 'claro', tamanho = 'md', soSimbolo = false }) {
  const t = TAMANHOS[tamanho]
  const { nome, ed } = CORES[fundo]
  if (soSimbolo) return <SimboloOrbita fundo={fundo} className={t.simbolo} />
  return (
    <span className={`inline-flex items-center ${t.espaco}`}>
      <SimboloOrbita fundo={fundo} className={t.simbolo} />
      <span className={`font-logo font-medium tracking-[-0.03em] ${t.texto} ${nome}`}>
        centraliz<span className={`font-bold ${ed}`}>Ed</span>
      </span>
    </span>
  )
}
```

- [ ] **Passo 7: criar `ui/PainelDestaque.jsx`**

```jsx
import { SimboloOrbita } from '../Logo'

export default function PainelDestaque({ className = '', children }) {
  return (
    <section className={`relative overflow-hidden bg-violeta text-white border-2 border-noite rounded-card p-6 sm:p-8 ${className}`}>
      <SimboloOrbita fundo="violeta" className="absolute -right-20 -top-20 w-80 h-80 opacity-25 pointer-events-none" />
      <div className="relative">{children}</div>
    </section>
  )
}
```

- [ ] **Passo 8: substituir `Badge.jsx`**

```jsx
import Tag from './ui/Tag'

const VARIANTES = { green: 'sucesso', red: 'erro', yellow: 'aviso', purple: 'violeta', gray: 'neutro' }

export default function Badge({ color = 'gray', children }) {
  return <Tag variante={VARIANTES[color]}>{children}</Tag>
}
```

- [ ] **Passo 9: ajustar quem usa `Logo`**

As chamadas `<Logo className="..." />` que ainda existem continuam válidas até as Tasks 4 a 6, porque a prop é ignorada. Nada a alterar agora.

- [ ] **Passo 10: conferir e commitar**

Lint e build. Depois `git add frontend/src/components` e `git commit -m "feat(identidade): pecas do guia e logo novo"`.

---

### Task 4: moldura do professor

**Arquivos:**
- Criar: `frontend/src/hooks/useContextoProfessor.js`, `frontend/src/components/MenuLateral.jsx`
- Substituir: `frontend/src/components/Layout.jsx`

**Interfaces:**
- Consome: `Logo`, `getExam`, `getTurma`.
- Produz: `useContextoProfessor()` retorna `{ turma: { id, nome } | null, atividade: { id, nome } | null }`. `avisarContextoMudou()`, exportada. A constante `CONTEXTO_MUDOU` é interna ao hook. Links de turma com `?secao=panorama`, `?secao=atividades`, `?secao=desempenho`.

- [ ] **Passo 1: criar o hook**

```js
import { useEffect, useState } from 'react'
import { useMatch } from 'react-router-dom'
import { getExam, getTurma } from '../api/exam'

const CONTEXTO_MUDOU = 'centralized:contexto-mudou'
const VAZIO = { turma: null, atividade: null }

export function avisarContextoMudou() {
  window.dispatchEvent(new Event(CONTEXTO_MUDOU))
}

function nomeDaAtividade(exam, id) {
  return exam.titulo || (exam.filename || '').replace(/\.[^.]+$/, '') || `Atividade ${id}`
}

// A página da turma ou da atividade também busca esses dados. A busca duplicada
// é aceita para o menu não depender de cada página.
export default function useContextoProfessor() {
  const naTurma = useMatch('/turma/:turmaId/*')
  const naAtividade = useMatch('/exam/:id/*')
  const turmaId = naTurma?.params.turmaId ?? null
  const examId = naAtividade?.params.id ?? null
  const chave = `${turmaId}|${examId}`
  const [dados, setDados] = useState({ chave: null, ...VAZIO })
  const [versao, setVersao] = useState(0)

  useEffect(() => {
    const aoMudar = () => setVersao(v => v + 1)
    window.addEventListener(CONTEXTO_MUDOU, aoMudar)
    return () => window.removeEventListener(CONTEXTO_MUDOU, aoMudar)
  }, [])

  useEffect(() => {
    if (!turmaId && !examId) return undefined
    let ativo = true
    const busca = examId
      ? getExam(examId).then(({ data }) => ({
          turma: data.turma_id ? { id: data.turma_id, nome: data.turma_nome } : null,
          atividade: { id: examId, nome: nomeDaAtividade(data, examId) },
        }))
      : getTurma(turmaId).then(({ data }) => ({
          turma: { id: turmaId, nome: data.nome },
          atividade: null,
        }))
    busca
      .then(r => { if (ativo) setDados({ chave, ...r }) })
      .catch(() => { if (ativo) setDados({ chave, ...VAZIO }) })
    return () => { ativo = false }
  }, [chave, turmaId, examId, versao])

  return dados.chave === chave ? dados : VAZIO
}
```

- [ ] **Passo 2: criar `MenuLateral.jsx`**

```jsx
import {
  ChartColumn, ClipboardList, FileCode, GraduationCap, LayoutDashboard, ListChecks, LogOut, Upload, User, Users,
} from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import Logo from './Logo'
import RotuloSecao from './ui/RotuloSecao'

const SECOES = ['panorama', 'atividades', 'desempenho']

function Item({ to, icone, ativo, children, aoNavegar }) {
  const Icone = icone
  return (
    <Link
      to={to}
      onClick={aoNavegar}
      aria-current={ativo ? 'page' : undefined}
      className={`flex items-center gap-2.5 min-h-11 px-3 rounded-botao text-sm font-semibold border-2 transition-colors ${
        ativo ? 'bg-lavanda border-noite text-violeta' : 'border-transparent text-noite hover:bg-lavanda'
      }`}
    >
      <Icone className="w-[18px] h-[18px] shrink-0" />
      <span className="truncate">{children}</span>
    </Link>
  )
}

function Grupo({ titulo, children }) {
  return (
    <div className="space-y-1">
      <RotuloSecao className="px-3 truncate" >{titulo}</RotuloSecao>
      {children}
    </div>
  )
}

export default function MenuLateral({ contexto, professor, aoSair, aoNavegar }) {
  const { pathname, search } = useLocation()
  const { turma, atividade } = contexto
  const pedida = new URLSearchParams(search).get('secao')
  const secao = SECOES.includes(pedida) ? pedida : 'panorama'

  const baseTurma = turma && `/turma/${turma.id}`
  const naPaginaDaTurma = pathname === baseTurma
  const baseAtividade = atividade && `/exam/${atividade.id}`
  const em = (sufixo) => Boolean(baseAtividade) && pathname.startsWith(`${baseAtividade}/${sufixo}`)

  return (
    <div className="h-full flex flex-col gap-6 p-5">
      <Link to="/" onClick={aoNavegar} aria-label="Início do CentralizEd"><Logo /></Link>

      <nav className="flex-1 space-y-6 overflow-y-auto">
        <div className="space-y-1">
          <Item to="/" icone={GraduationCap} ativo={pathname === '/'} aoNavegar={aoNavegar}>Turmas</Item>
        </div>

        {turma && (
          <Grupo titulo={turma.nome}>
            <Item to={`${baseTurma}?secao=panorama`} icone={LayoutDashboard} ativo={naPaginaDaTurma && secao === 'panorama'} aoNavegar={aoNavegar}>Panorama</Item>
            <Item
              to={`${baseTurma}?secao=atividades`}
              icone={ClipboardList}
              ativo={(naPaginaDaTurma && secao === 'atividades') || pathname === `${baseTurma}/upload`}
              aoNavegar={aoNavegar}
            >
              Atividades
            </Item>
            <Item to={`${baseTurma}?secao=desempenho`} icone={ChartColumn} ativo={naPaginaDaTurma && secao === 'desempenho'} aoNavegar={aoNavegar}>Desempenho</Item>
          </Grupo>
        )}

        {atividade && (
          <Grupo titulo={atividade.nome}>
            <Item to={baseAtividade} icone={ListChecks} ativo={pathname === baseAtividade || em('questions')} aoNavegar={aoNavegar}>Questões</Item>
            <Item to={`${baseAtividade}/students`} icone={Users} ativo={em('students')} aoNavegar={aoNavegar}>Alunos</Item>
            <Item to={`${baseAtividade}/results`} icone={ChartColumn} ativo={em('results')} aoNavegar={aoNavegar}>Resultados</Item>
            <Item to={`${baseAtividade}/submit`} icone={FileCode} ativo={em('submit')} aoNavegar={aoNavegar}>Testar submissão</Item>
            <Item to={`${baseAtividade}/bulk-submit`} icone={Upload} ativo={em('bulk-submit')} aoNavegar={aoNavegar}>Envio em lote</Item>
          </Grupo>
        )}
      </nav>

      <div className="space-y-1 pt-4 border-t-2 border-noite/10">
        <Item to="/profile" icone={User} ativo={pathname === '/profile'} aoNavegar={aoNavegar}>{professor.nome}</Item>
        <button
          type="button"
          onClick={aoSair}
          className="w-full flex items-center gap-2.5 min-h-11 px-3 rounded-botao text-sm font-semibold text-cinza-texto hover:bg-lavanda transition-colors"
        >
          <LogOut className="w-[18px] h-[18px] shrink-0" />
          Sair
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Passo 3: substituir `Layout.jsx`**

```jsx
import { useEffect, useState } from 'react'
import { Menu, X } from 'lucide-react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import useContextoProfessor from '../hooks/useContextoProfessor'
import JobDock from './JobDock'
import Logo from './Logo'
import MenuLateral from './MenuLateral'

export default function Layout() {
  const { professor, logout } = useAuth()
  const navigate = useNavigate()
  const contexto = useContextoProfessor()
  const { pathname, search } = useLocation()
  const aqui = pathname + search
  // Guarda onde a gaveta foi aberta: navegar para outro lugar já a fecha.
  const [gavetaEm, setGavetaEm] = useState(null)
  const gavetaAberta = gavetaEm === aqui

  useEffect(() => {
    if (!gavetaAberta) return undefined
    const aoTeclar = (e) => { if (e.key === 'Escape') setGavetaEm(null) }
    window.addEventListener('keydown', aoTeclar)
    return () => window.removeEventListener('keydown', aoTeclar)
  }, [gavetaAberta])

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const menu = professor && (
    <MenuLateral
      contexto={contexto}
      professor={professor}
      aoSair={handleLogout}
      aoNavegar={() => setGavetaEm(null)}
    />
  )

  return (
    <div className="min-h-screen bg-white lg:grid lg:grid-cols-[272px_minmax(0,1fr)]">
      <aside className="hidden lg:block sticky top-0 h-screen border-r-2 border-noite">
        {menu}
      </aside>

      <header className="lg:hidden sticky top-0 z-30 bg-white border-b-2 border-noite h-14 px-4 flex items-center justify-between">
        <Link to="/" aria-label="Início do CentralizEd"><Logo /></Link>
        {professor && (
          <button
            type="button"
            onClick={() => setGavetaEm(aqui)}
            aria-label="Abrir menu"
            aria-expanded={gavetaAberta}
            className="min-h-11 min-w-11 inline-flex items-center justify-center rounded-botao hover:bg-lavanda"
          >
            <Menu className="w-6 h-6" />
          </button>
        )}
      </header>

      {gavetaAberta && (
        <div className="lg:hidden fixed inset-0 z-40">
          <button
            type="button"
            aria-label="Fechar menu"
            onClick={() => setGavetaEm(null)}
            className="absolute inset-0 w-full h-full bg-noite/40"
          />
          <aside className="absolute inset-y-0 left-0 w-[280px] max-w-[85vw] bg-white border-r-2 border-noite">
            <button
              type="button"
              onClick={() => setGavetaEm(null)}
              aria-label="Fechar menu"
              className="absolute top-3 right-3 z-10 min-h-11 min-w-11 inline-flex items-center justify-center rounded-botao hover:bg-lavanda"
            >
              <X className="w-5 h-5" />
            </button>
            {menu}
          </aside>
        </div>
      )}

      <main className="min-w-0 w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-10 py-6 lg:py-10">
        <Outlet />
      </main>
      {professor && <JobDock />}
    </div>
  )
}
```

- [ ] **Passo 4: conferir e commitar**

Lint e build. Depois `git add frontend/src/hooks frontend/src/components/MenuLateral.jsx frontend/src/components/Layout.jsx` e `git commit -m "feat(identidade): menu lateral e gaveta do professor"`.

---

### Task 5: moldura do aluno

**Arquivos:**
- Alterar: `frontend/src/components/AlunoLayout.jsx`

**Interfaces:**
- Consome: `Logo`.

- [ ] **Passo 1: trocar os imports e o que vem antes de `export default`**

No topo do arquivo, adicionar `import { GraduationCap, House, LogOut, Target, TrendingUp } from 'lucide-react'`. Substituir `linkClass` e `LinkInicio` por:

```jsx
const linkClass = ({ isActive }) =>
  `min-h-11 inline-flex items-center px-3 rounded-botao text-sm font-semibold transition-colors whitespace-nowrap ${
    isActive ? 'bg-lavanda text-violeta' : 'text-noite hover:bg-lavanda'
  }`

function Bolinha({ novidades }) {
  if (novidades <= 0) return null
  return (
    <span className="min-w-[1.125rem] h-[1.125rem] px-1 rounded-full bg-coral text-noite text-[10px] font-bold leading-[1.125rem] text-center">
      <span aria-hidden="true">{novidades > 9 ? '9+' : novidades}</span>
      <span className="sr-only">{`${novidades} novidade${novidades === 1 ? '' : 's'}`}</span>
    </span>
  )
}

function Aba({ to, end, icone, rotulo, novidades = 0 }) {
  const Icone = icone
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `relative flex flex-col items-center justify-center gap-0.5 min-h-14 text-[11px] font-bold ${
          isActive ? 'text-violeta' : 'text-cinza-texto'
        }`
      }
    >
      <span className="relative">
        <Icone className="w-[22px] h-[22px]" />
        <span className="absolute -top-1.5 left-4"><Bolinha novidades={novidades} /></span>
      </span>
      {rotulo}
    </NavLink>
  )
}
```

- [ ] **Passo 2: substituir o `return` final do componente, sem tocar nos `useEffect` nem em `handleLogout`**

```jsx
  return (
    <div className="min-h-screen bg-white">
      <nav className="bg-white border-b-2 border-noite sm:sticky sm:top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
          <div className="flex items-center gap-6">
            <Link to="/aluno" aria-label="Início do CentralizEd"><Logo /></Link>
            <div className="hidden sm:flex items-center gap-1">
              <NavLink to="/aluno" end className={linkClass}>
                <span className="inline-flex items-center gap-1.5">Início <Bolinha novidades={novidades} /></span>
              </NavLink>
              <NavLink to="/aluno/turmas" className={linkClass}>Turmas</NavLink>
              <NavLink to="/aluno/treino" className={linkClass}>Treino</NavLink>
              <NavLink to="/aluno/progresso" className={linkClass}>Meu progresso</NavLink>
            </div>
          </div>

          {aluno && (
            <div className="flex items-center gap-1">
              <NavLink to="/aluno/perfil" className="min-h-11 flex items-center gap-2 px-2 rounded-botao hover:bg-lavanda transition-colors">
                <span className="w-8 h-8 rounded-full bg-lavanda border-2 border-noite flex items-center justify-center text-xs font-bold text-violeta">
                  {aluno.nome?.[0]?.toUpperCase()}
                </span>
                <span className="text-sm font-semibold hidden sm:block">{aluno.nome}</span>
              </NavLink>
              <button
                type="button"
                onClick={handleLogout}
                aria-label="Sair"
                className="min-h-11 min-w-11 inline-flex items-center justify-center rounded-botao text-cinza-texto hover:bg-lavanda transition-colors"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-5 sm:py-8 pb-[calc(6rem+env(safe-area-inset-bottom))] sm:pb-8">
        <Outlet />
      </main>

      <nav
        aria-label="Navegação principal"
        className="sm:hidden fixed bottom-0 inset-x-0 z-30 bg-white border-t-2 border-noite grid grid-cols-4 pb-[env(safe-area-inset-bottom)]"
      >
        <Aba to="/aluno" end icone={House} rotulo="Início" novidades={novidades} />
        <Aba to="/aluno/turmas" icone={GraduationCap} rotulo="Turmas" />
        <Aba to="/aluno/treino" icone={Target} rotulo="Treino" />
        <Aba to="/aluno/progresso" icone={TrendingUp} rotulo="Progresso" />
      </nav>
    </div>
  )
```

- [ ] **Passo 3: conferir e commitar**

Lint e build. Depois `git add frontend/src/components/AlunoLayout.jsx` e `git commit -m "feat(identidade): barra e abas do aluno"`.

---

### Task 6: telas de entrada

**Arquivos:**
- Criar: `frontend/src/components/TelaDeEntrada.jsx`
- Alterar: `frontend/src/pages/LoginPage.jsx`, `RegisterPage.jsx`, `pages/aluno/AlunoLoginPage.jsx`, `pages/aluno/AlunoRegisterPage.jsx`, `pages/aluno/ConvitePage.jsx`, `frontend/src/components/SeletorPerfil.jsx`

**Interfaces:**
- Produz: `TelaDeEntrada({ frase, children })`.

- [ ] **Passo 1: criar `TelaDeEntrada.jsx`**

```jsx
import Logo, { SimboloOrbita } from './Logo'

export default function TelaDeEntrada({ frase, children }) {
  return (
    <div className="min-h-screen bg-white lg:grid lg:grid-cols-2">
      <div className="relative overflow-hidden bg-violeta text-white border-b-2 lg:border-b-0 lg:border-r-2 border-noite px-6 py-6 lg:p-14 flex flex-col lg:justify-between">
        <SimboloOrbita fundo="violeta" className="absolute -right-24 -bottom-24 w-[28rem] h-[28rem] opacity-25 pointer-events-none" />
        <div className="relative"><Logo fundo="violeta" tamanho="lg" /></div>
        <p className="relative hidden lg:block titulo-pagina max-w-md">{frase}</p>
      </div>
      <div className="flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-sm">{children}</div>
      </div>
    </div>
  )
}
```

- [ ] **Passo 2: aplicar nas cinco páginas**

Em cada página, trocar o par externo `<div className="min-h-screen ... flex items-center justify-center px-4">`, `<div className="w-full max-w-sm">` e o bloco do logo (`<div ...><Logo .../><span ...>Analytics CS1</span></div>`) por `<TelaDeEntrada frase="...">`. Remover o `import Logo`. Manter o card com o formulário, formulário e estados como estão, aplicando a receita: card vira `<Card principal>`, inputs `campo`, envio `<Botao type="submit" className="w-full">`, erro no modelo da receita. Conferir nos arquivos o trecho exato do logo antes de cortar.

Frases:

- `LoginPage`, `RegisterPage`: `frase="Veja onde a turma trava e ajude por grupo."`
- `AlunoLoginPage`, `AlunoRegisterPage`, `ConvitePage`: `frase="Entenda o seu erro e tente de novo."`

- [ ] **Passo 3: migrar `SeletorPerfil.jsx`**

Trocar `IconeAluno` por `GraduationCap` e o ícone do professor por `Presentation`, ambos de `lucide-react`. Item ativo: `bg-lavanda text-violeta border-2 border-noite rounded-botao`. Inativo: `text-cinza-texto border-2 border-transparent hover:bg-lavanda rounded-botao`. Altura mínima `min-h-11`.

- [ ] **Passo 4: conferir e commitar**

`grep -rn "Analytics CS1" src` em `frontend/`. Esperado: só `pages/TurmaDetailPage.jsx`. Lint e build. Depois `git add frontend/src` e `git commit -m "feat(identidade): telas de entrada com painel violeta"`.

---

### Task 7: Início do aluno

**Arquivos:**
- Alterar: `frontend/src/pages/aluno/InicioPage.jsx`

- [ ] **Passo 1: adicionar imports**

`import { Check } from 'lucide-react'`, `import Botao from '../../components/ui/Botao'`, `import Card from '../../components/ui/Card'`, `import PainelDestaque from '../../components/ui/PainelDestaque'`, `import RotuloSecao from '../../components/ui/RotuloSecao'`.

- [ ] **Passo 2: substituir `Novidades`**

```jsx
function Novidades({ itens }) {
  return (
    <section className="space-y-3">
      <RotuloSecao as="h2">Novidades</RotuloSecao>
      <div className="space-y-3">
        {itens.map(n => (
          <Link
            key={`${n.tipo}-${n.exam_id ?? ''}-${n.question_number ?? ''}-${n.exercicio_id ?? ''}`}
            to={linkDaNovidade(n)}
            className="flex items-center gap-3 bg-white border-2 border-noite rounded-card p-4 shadow-bloco transition-transform active:translate-x-0.5 active:translate-y-0.5"
          >
            <span className="w-2.5 h-2.5 rounded-full bg-coral shrink-0" aria-hidden="true" />
            <div className="min-w-0">
              <p className="font-bold">{TEXTO_DA_NOVIDADE[n.tipo]}</p>
              <p className="text-sm text-cinza-texto truncate">{n.titulo}</p>
            </div>
          </Link>
        ))}
      </div>
    </section>
  )
}
```

- [ ] **Passo 3: em `ProvaChegando`, trocar só a marcação**

A `section` externa vira `<Card as="section" principal>`. O `h2` usa `className="titulo-card break-words"`. O texto "✓ feito" vira `<span className="inline-flex items-center gap-1 text-[13px] font-bold text-sucesso shrink-0"><Check className="w-4 h-4" />feito</span>`. O botão vira `<Botao onClick={() => treinar(e.error_category)} disabled={gerando !== null} className="shrink-0">`, com o mesmo conteúdo. `divide-noite/10` permanece. Lógica intacta.

- [ ] **Passo 4: substituir `Continuar` a partir do `return`**

```jsx
  return (
    <PainelDestaque>
      <div className="flex flex-col sm:flex-row sm:items-center gap-5 pr-0 sm:pr-24">
        <div className="flex-1 min-w-0">
          <p className="font-titulo font-extrabold text-[13px] uppercase tracking-[0.1em] text-white/80">
            {emAndamento ? 'Continuar de onde parou' : 'Próxima atividade'}
          </p>
          <p className="mt-1 titulo-pagina break-words">
            {item.origem === 'trilha' ? `Trilha · ${item.titulo}` : item.titulo}
          </p>
          {detalhes.length > 0 && (
            <p className="text-sm text-white/80 mt-1">{detalhes.join(' · ')}</p>
          )}
        </div>
        <Botao to={linkDoContinuar(item)} variante="secundario" className="shrink-0">
          {emAndamento ? 'Bora continuar!' : 'Bora começar!'}
        </Botao>
      </div>
    </PainelDestaque>
  )
```

- [ ] **Passo 5: substituir `Prazos` a partir do `return`**

```jsx
  return (
    <section className="space-y-3">
      <RotuloSecao as="h2">Prazos próximos</RotuloSecao>
      <Card className="p-0! gap-0! divide-y-2 divide-noite/10 overflow-hidden">
        {itens.map(p => (
          <Link
            key={p.exam_id}
            to={`/aluno/atividades/${p.exam_id}`}
            className="flex flex-col gap-1 px-5 py-3 hover:bg-lavanda transition-colors"
          >
            <p className="font-bold truncate">{p.titulo}</p>
            <p className="text-sm text-cinza-texto truncate">{p.turma_nome}</p>
            <p className={`text-[13px] font-bold ${p.tipo === 'fecha' ? 'text-aviso' : 'text-violeta'}`}>
              {modoLabel(p.modo)} · {p.tipo} {prazoRelativo(p.quando)}
            </p>
          </Link>
        ))}
      </Card>
    </section>
  )
```

- [ ] **Passo 6: trocar o final de `InicioPage`**

Na tela sem turma, `h1` usa `titulo-pagina`. Nos estados de erro e `tudoEmDia`, a `div` tracejada vira `<Card className="border-dashed border-noite/30! text-center p-10!">`. O link de `tudoEmDia` vira `<Botao to="/aluno/treino" className="self-center">Bora treinar!</Botao>`. O `return` principal fica:

```jsx
  return (
    <div className="space-y-8">
      {continuar ? (
        <Continuar item={continuar} />
      ) : (
        <div>
          <h1 className="titulo-pagina">Início</h1>
          <p className="text-cinza-texto mt-1">O que chegou para você, onde você parou e o que vence logo.</p>
        </div>
      )}

      {(novidades.length > 0 || provaChegando || prazos.length > 0) && (
        <div className="grid gap-8 lg:grid-cols-2 items-start">
          {(novidades.length > 0 || provaChegando) && (
            <div className="space-y-8 min-w-0">
              {novidades.length > 0 && <Novidades itens={novidades} />}
              {provaChegando && <ProvaChegando prova={provaChegando} />}
            </div>
          )}
          {prazos.length > 0 && <div className="min-w-0"><Prazos itens={prazos} /></div>}
        </div>
      )}

      {tudoEmDia && (
        <Card className="border-dashed border-noite/30! text-center p-10!">
          <p className="text-cinza-texto">Tudo em dia. Que tal treinar?</p>
          <Botao to="/aluno/treino" className="self-center">Bora treinar!</Botao>
        </Card>
      )}
    </div>
  )
```

- [ ] **Passo 7: conferir e commitar**

Lint e build. Depois `git add frontend/src/pages/aluno/InicioPage.jsx` e `git commit -m "feat(identidade): inicio do aluno com painel de continuar"`.

---

### Task 8: turma do professor em seções

**Arquivos:**
- Criar: `frontend/src/utils/coresGraficos.js`
- Alterar: `frontend/src/pages/TurmaDetailPage.jsx`, `frontend/src/components/FunilDaTurma.jsx`, `frontend/src/components/TrajetoriaDeErros.jsx`, `frontend/src/components/BarList.jsx`, `frontend/src/components/ListControls.jsx`

**Interfaces:**
- Produz: `CORES_CATEGORICAS` (array de 8), `corDaTaxa(r)`, `COR_ERRO`, `COR_PADRAO`.
- Consome: `?secao=` no mesmo formato da Task 4.

- [ ] **Passo 1: criar `coresGraficos.js`**

Paleta validada pelo `validate_palette.js` da skill `dataviz` (todas as checagens passam, e o aviso de contraste do coral é coberto porque toda barra tem rótulo e valor em texto).

```js
export const CORES_CATEGORICAS = [
  '#4A2EE0', '#FF6B4A', '#0B8F86', '#8F84F0',
  '#A8711A', '#2F7FD8', '#C2379F', '#7A5A00',
]
export const COR_PADRAO = '#4A2EE0'
export const COR_ERRO = '#C4263B'
export const corDaTaxa = (r) => (r >= 70 ? '#0F7654' : r >= 40 ? '#8A5A00' : '#C4263B')
```

- [ ] **Passo 2: `BarList.jsx`**

`import { COR_PADRAO } from '../utils/coresGraficos'` e `color = COR_PADRAO` no parâmetro. Nome em `text-sm`, largura do rótulo `w-28` mantida, trilho `bg-lavanda rounded-[5px] h-2.5`, barra `rounded-[5px]`. Sem `transition-all`.

- [ ] **Passo 3: `TurmaDetailPage.jsx`, seção e marca**

- Trocar `const ERR_COLOR = '#e11d48'` e `const rateColor = ...` por `import { COR_ERRO, corDaTaxa } from '../utils/coresGraficos'`. Substituir os usos: `color={COR_ERRO}` e `color: corDaTaxa(d.taxa)`.
- Na mensagem de `copiarConvite`, trocar `vai usar o Analytics CS1 nas listas` por `vai usar o CentralizEd nas listas`.
- Importar `useSearchParams` e, junto dos demais hooks, antes de qualquer `return` antecipado:

```js
const [searchParams] = useSearchParams()
const secaoPedida = searchParams.get('secao')
const secao = ['panorama', 'atividades', 'desempenho'].includes(secaoPedida) ? secaoPedida : 'panorama'
```

- [ ] **Passo 4: `TurmaDetailPage.jsx`, novo arranjo**

Substituir o cabeçalho e o bloco "Código de acesso" por um único `<PainelDestaque>`:

- Linha de caminho "Turmas ›" em `lg:hidden`, fora do painel.
- No painel: `h1 titulo-pagina` com `turma.nome`, `Tag` com `turma.codigo`. Depois: rótulo em `text-white/80` "Código de acesso da turma", o código em `font-titulo font-extrabold text-2xl`, e a frase existente "Passe o código ou o convite com link...".
- Linha de ações, com `flex flex-wrap gap-2`: `Copiar código`, `Copiar convite`, `Ver área do aluno`, `Adicionar lista de aquecimento` (mesma condição de hoje) e `Nova atividade`, como `<Botao variante="secundario">`, com os mesmos `onClick`, `disabled`, `to` e `target`. O `erroAquecimento` fica logo abaixo da linha, em `text-white font-bold`.

O corpo vira, com `hidden` para não remontar nada e não refazer buscas:

```jsx
<div hidden={secao !== 'panorama'}>
  <FunilDaTurma turmaId={turmaId} recarga={recargaFunil} />
</div>

<div hidden={secao !== 'atividades'} className="space-y-4">
  <RotuloSecao as="h2">Atividades</RotuloSecao>
  {/* bloco atual de Atividades, a partir de turma.exams.length === 0 */}
</div>

<div hidden={secao !== 'desempenho'} className="space-y-6">
  {/* cartões de resumo (KPIs) */}
  {/* gráficos: taxa de aprovação e erros frequentes */}
  {/* TrajetoriaDeErros */}
</div>
```

Aplicar a receita ao restante: card de atividade clicável vira `<Card principal>`, `KpiCard` usa `<Card>` com valor em `font-titulo font-extrabold text-3xl`. `PassRateBar` usa `<Progresso valor={rate} rotulo="Taxa de aprovação" />` e continua com o número em texto. `ConfirmDialog` permanece.

- [ ] **Passo 5: `FunilDaTurma.jsx` e `TrajetoriaDeErros.jsx`**

Aplicar a receita. Bloco do funil vira `<Card principal>`. Cada etapa (aquisição, ativação, retenção) vira `<Card>`. Barras em CSS usam `bg-violeta`, trilho `bg-lavanda`. Vermelho e amarelo dos alunos em risco viram `<Tag variante="erro">` e `<Tag variante="aviso">`. Nenhuma condição, cálculo ou ordem interna muda.

- [ ] **Passo 6: `ListControls.jsx`**

Inputs e selects com `campo`, ícones pela tabela da receita. Busca ocupa o espaço restante, e a ordenação tem largura automática.

- [ ] **Passo 7: conferir e commitar**

`grep -rn "Analytics CS1" src` em `frontend/`. Esperado: nenhuma linha. Lint e build. Depois `git add frontend/src` e `git commit -m "feat(identidade): turma do professor em panorama, atividades e desempenho"`.

---

### PORTÃO: conferência do Otávio

Subir backend e front da branch e pedir que ele abra o Início do aluno e a turma do professor. Só seguir para o Lote D com o ok dele. Ajustes pedidos entram aqui, como commits próprios.

---

### Task 9: atividade do professor

**Arquivos:**
- Alterar: `frontend/src/pages/ExamDashboard.jsx`, `frontend/src/components/PublicacaoCard.jsx`, `frontend/src/components/DisponibilidadeCard.jsx`, `frontend/src/pages/ExamUploadPage.jsx`

**Interfaces:**
- Consome: `avisarContextoMudou` de `hooks/useContextoProfessor.js`.

- [ ] **Passo 1: disparar a atualização do menu ao renomear**

Em `ExamDashboard.jsx`, importar `{ avisarContextoMudou } from '../hooks/useContextoProfessor'`. Logo depois de `await updateExam(id, { titulo: renameValue.trim() })`, acrescentar `avisarContextoMudou()`.

- [ ] **Passo 2: novo cabeçalho**

Linha de caminho em `lg:hidden`. Seu link para a turma passa a `/turma/${exam.turma_id}?secao=atividades`. O cabeçalho vira `<PainelDestaque>` com `h1 titulo-pagina` e `nomeDaAtividade`, `Badge` de modo e rascunho, e os botões de renomear e excluir em `min-h-11 min-w-11 rounded-botao hover:bg-white/15 text-white`, com `Pencil` e `Trash2`. Remover os quatro `Link` Alunos, Testar submissão, Submissões em lote e Resultados, que agora estão no menu. Em largura menor que `lg` eles ficam na gaveta.

- [ ] **Passo 3: depois de excluir**

Na navegação que segue a exclusão da atividade (por volta da linha 71), acrescentar `?secao=atividades` ao destino da turma, se houver `turma_id`.

- [ ] **Passo 4: resto da página e cartões**

Aplicar a receita em `ExamDashboard`, `PublicacaoCard`, `DisponibilidadeCard`. Card de questão vira `<Card principal>`. Modais continuam. No estado vazio, trocar `<Logo className="w-10 h-10 mx-auto mb-3 opacity-30" />` por `<ClipboardList className="w-10 h-10 mx-auto mb-3 text-cinza-texto" />` e remover o `import Logo`.

- [ ] **Passo 5: `ExamUploadPage.jsx`**

Caminho em `lg:hidden` com link para `?secao=atividades`. Área de envio vira `<Card className="border-dashed border-noite/30!">`. Ícone `Upload` no lugar do SVG. Receita no restante.

- [ ] **Passo 6: conferir e commitar**

Lint e build. Depois `git add frontend/src` e `git commit -m "feat(identidade): atividade do professor com painel e menu"`.

---

### Task 10: questão do professor

**Arquivos:**
- Alterar: `frontend/src/pages/QuestionPage.jsx`, `frontend/src/components/RespostaAoGrupo.jsx`, `frontend/src/components/WhoList.jsx`, `frontend/src/components/FunctionCheckCard.jsx`

**Interfaces:**
- Consome: `CORES_CATEGORICAS`.

- [ ] **Passo 1: cores**

Remover `CLUSTER_COLORS` e `ERROR_COLORS` e importar `{ CORES_CATEGORICAS } from '../utils/coresGraficos'`. Trocar `ERROR_COLORS[i % ERROR_COLORS.length]` por `CORES_CATEGORICAS[i % CORES_CATEGORICAS.length]` e `CLUSTER_COLORS[(idx < 0 ? 0 : idx) % CLUSTER_COLORS.length]` por `CORES_CATEGORICAS[(idx < 0 ? 0 : idx) % CORES_CATEGORICAS.length]`.

- [ ] **Passo 2: abas**

Mantidas, com `tab` padrão `respostas` intacto. Classes: base `min-h-11 px-4 text-sm font-bold border-b-[3px] -mb-[2px]`, ativa `border-violeta text-violeta`, inativa `border-transparent text-cinza-texto hover:text-noite`. A linha sob as abas: `border-b-2 border-noite`.

- [ ] **Passo 3: cabeçalho e receita**

Caminho em `lg:hidden`. "Q{num}" vira `h1 titulo-pagina` com "Questão {num}". "+ Test cases" vira `<Botao variante="secundario" to=...><Plus className="w-4 h-4" />Test cases</Botao>`. Aplicar a receita ao resto. Na aba de grupos, cada grupo é `<Card principal>`, com a cor do grupo como bolinha ao lado do título. Em `RespostaAoGrupo`, `WhoList` e `FunctionCheckCard`, só a receita. Nenhum efeito muda.

- [ ] **Passo 4: conferir e commitar**

Lint e build. Depois `git add frontend/src` e `git commit -m "feat(identidade): questao do professor com grupos em destaque"`.

---

### Task 11: questão do aluno e exercício

**Arquivos:**
- Alterar: `frontend/src/pages/aluno/QuestaoPage.jsx`, `frontend/src/pages/aluno/ExercicioTreinoPage.jsx`, `frontend/src/components/TentativaDetalhe.jsx`, `frontend/src/components/AjudaEmEtapas.jsx`, `frontend/src/components/RitmoDaTentativa.jsx`, `frontend/src/components/CodeTextarea.jsx`, `frontend/src/components/CodeBlock.jsx`

- [ ] **Passo 1: duas colunas sem mudar a ordem no celular**

Nas duas páginas, criar um `div` com `grid gap-6 lg:grid-cols-2 items-start`, envolvendo os blocos abaixo, com três `div` novos como filhos, cada um com `min-w-0 space-y-6`, nesta ordem no DOM:

1. O card do enunciado (casos e requisitos dentro dele): `lg:col-start-1 lg:row-start-1`
2. O card do editor e o bloco "Resultado", com a ajuda, juntos num só `div`: `lg:col-start-2 lg:row-start-1 lg:row-span-2`
3. O bloco "Tentativas anteriores", quando existir: `lg:col-start-1 lg:row-start-2`

Ficam fora do grid: cabeçalho e caminho antes dele, e a linha de questão anterior e próxima depois dele. Em `ExercicioTreinoPage`, o aviso "reaproveitado" e o caminho também ficam antes do grid.

- [ ] **Passo 2: componentes do resultado**

`TentativaDetalhe`: resultado correto e incorreto com `Tag variante="sucesso"` e `variante="erro"`. O caso que falhou em `<Card>`. `pre` de código continua `bg-noite` com `rounded-botao`.

`RitmoDaTentativa`: o avanço continua em cor de sucesso e o aviso de pausa em cor de aviso, cada um em bloco `rounded-botao border-2`, borda da mesma cor, fundo `*-fundo`.

`AjudaEmEtapas`: botões "Preciso de uma dica", "Outra pista" e "Ver explicação completa" com `<Botao variante="secundario">`, textos intactos.

`CodeTextarea` e `textarea` da `ExercicioTreinoPage`: fundo `bg-noite`, `text-codigo-texto`, `rounded-botao`, borda `border-2 border-noite`, foco visível. Fonte `font-mono`.

- [ ] **Passo 3: receita no resto e botão principal**

"Enviar nova tentativa" e o primeiro envio viram `<Botao onClick={...}>`, com o mesmo `onClick` e `disabled` de hoje e textos iguais. `h1` em `titulo-pagina`. "← voltar" vira `ArrowLeft` mais texto.

- [ ] **Passo 4: conferir e commitar**

Lint e build. Depois `git add frontend/src` e `git commit -m "feat(identidade): questao do aluno em duas colunas"`.

---

### Task 12: demais telas do aluno

**Arquivos:**
- Alterar: `frontend/src/pages/aluno/TreinoPage.jsx`, `ProgressoPage.jsx`, `TurmaPage.jsx`, `TurmasPage.jsx`, `AtividadePage.jsx`, `AlunoPerfilPage.jsx`, `frontend/src/components/AtividadeCard.jsx`, `frontend/src/components/EntrarNaTurma.jsx`

- [ ] **Passo 1: Progresso**

Mover o cartão "Erros superados" para antes dos demais cartões e transformá-lo em `<PainelDestaque>`, com o valor em `font-titulo font-extrabold text-5xl`, rótulo em `text-white/80` e a frase atual dele. Depois: cartões de Provas e Listas, semana a semana, erros que se repetem, erros que você superou. Condições de exibição iguais.

- [ ] **Passo 2: Treino**

Receita. Superados em `Tag variante="sucesso"`. Botões "Treinar isso" e "Treinar de novo" com `<Botao>` e `<Botao variante="secundario">`, textos intactos.

- [ ] **Passo 3: Turmas, Turma, Atividade, Perfil, AtividadeCard, EntrarNaTurma**

Receita, mesma ordem de hoje. `AtividadeCard` é `<Card principal>` clicável. Barra de progresso, quando houver, com `<Progresso>`.

- [ ] **Passo 4: conferir e commitar**

Lint e build. Depois `git add frontend/src` e `git commit -m "feat(identidade): treino, progresso e turmas do aluno"`.

---

### Task 13: lista de turmas e perfil

**Arquivos:**
- Alterar: `frontend/src/pages/TurmaListPage.jsx`, `frontend/src/pages/ProfilePage.jsx`

- [ ] **Passo 1: aplicar a receita**

Linha de caminho de `ProfilePage` em `lg:hidden`, com `ChevronRight`. Card de turma é `<Card principal>` clicável, abrindo no Panorama, sem `?secao=`. Botões de editar e excluir só com ícone (`Pencil`, `Trash2`), com `aria-label`. "Nova turma" com `<Botao><Plus className="w-4 h-4" />...`, mesmo texto de hoje.

- [ ] **Passo 2: conferir e commitar**

Lint e build. Depois `git add frontend/src` e `git commit -m "feat(identidade): lista de turmas e perfil do professor"`.

---

### Task 14: casos de teste, submissões e envios

**Arquivos:**
- Alterar: `frontend/src/pages/TestCasesPage.jsx`, `frontend/src/pages/SubmitPage.jsx`, `frontend/src/pages/BulkSubmitPage.jsx`, `frontend/src/pages/SubmissionsPage.jsx`

- [ ] **Passo 1: aplicar a receita**

Linhas de caminho em `lg:hidden`. Exemplos de formato em `pre` de `BulkSubmitPage` continuam em `bg-noite` com `text-codigo-sucesso`. Em `BulkSubmitPage:154` e similares, SVG de upload vira `Upload`.

- [ ] **Passo 2: conferir e commitar**

Lint e build. Depois `git add frontend/src` e `git commit -m "feat(identidade): casos de teste e envios do professor"`.

---

### Task 15: alunos e resultados

**Arquivos:**
- Alterar: `frontend/src/pages/StudentsPage.jsx`, `frontend/src/pages/StudentDetailPage.jsx`, `frontend/src/pages/ResultsPage.jsx`

**Interfaces:**
- Consome: `CORES_CATEGORICAS`.

- [ ] **Passo 1: cores**

Em `ResultsPage.jsx`, remover `ERROR_COLORS` e importar `{ CORES_CATEGORICAS } from '../utils/coresGraficos'`. Substituir os usos de `ERROR_COLORS` por `CORES_CATEGORICAS`.

- [ ] **Passo 2: receita**

Linhas de caminho em `lg:hidden`. Alunos em risco em `Tag variante="erro"` e `variante="aviso"`, mantendo as condições. Tabelas: cabeçalho `RotuloSecao`, linhas `divide-y-2 divide-noite/10`, contêiner com `overflow-x-auto` para não estourar em 360 px.

- [ ] **Passo 3: conferir e commitar**

Lint e build. Depois `git add frontend/src` e `git commit -m "feat(identidade): alunos e resultados do professor"`.

---

### Task 16: componentes restantes

**Arquivos:**
- Alterar: `frontend/src/components/Modal.jsx`, `ConfirmDialog.jsx`, `JobDock.jsx`, `QuestionForm.jsx`, `Spinner.jsx`

- [ ] **Passo 1: aplicar a receita**

`Modal`: fundo `bg-noite/40`, caixa como `Card principal` em marcação própria, botão de fechar com `X`, `z-50` mantido. `ConfirmDialog`: confirmação com `<Botao variante="perigo">`, cancelar `secundario`. `JobDock`: `z-40` mantido, cartões `border-2 border-noite rounded-card bg-white shadow-bloco`. `QuestionForm`: `campo` e `Botao`. `Spinner`: sem alteração de lógica, cor herdada.

- [ ] **Passo 2: conferir e commitar**

Lint e build. Depois `git add frontend/src` e `git commit -m "feat(identidade): modais, envio em segundo plano e formulario de questao"`.

---

### Task 17: varredura final e documentação

**Arquivos:**
- Alterar: o que as varreduras acusarem. `CLAUDE.md`, `HANDOFF.md`

- [ ] **Passo 1: varreduras em `frontend/`, todas devem retornar zero linhas**

`grep -rnE '(bg|text|border|ring|divide)-(gray|purple|violet|indigo|blue|sky|slate|red|rose|green|emerald|yellow|amber|orange)-[0-9]' src`

`grep -rn 'Analytics CS1' src index.html`

`grep -rnE 'linear-gradient|bg-gradient|shadow-(sm|md|lg|xl)|shadow"|shadow ' src --include=*.jsx`

`grep -rnE '<svg' src --include=*.jsx` deve mostrar só `Logo.jsx` e `Spinner.jsx`.

`grep -rnE '✓|←|›' src --include=*.jsx` deve mostrar nada que seja ícone. Aspas de citação e texto corrido podem ficar, e o separador `›` usa `ChevronRight`.

A verificação em navegador fica fora desta tarefa. Quem executa o `sdd` faz, depois deste lote e antes do `fechamento`, a lista da seção Testes do spec: backend com 625 testes, navegador em 360, 390 e 1280 px como professor e como aluno sem estouro nem erro no console, os casos-limite, contraste, foco de teclado e o ensaio com Docker e Gemini reais.

- [ ] **Passo 2: documentar**

`CLAUDE.md`: na seção de contexto, acrescentar que o produto se chama CentralizEd e que o guia visual está em `docs/identidade-visual.md`. Em Arquitetura, acrescentar `components/ui/` e `hooks/`. `HANDOFF.md`: acrescentar item curto com a mudança de identidade e a decisão D5.

- [ ] **Passo 3: conferir e commitar**

Lint e build. Depois `git add frontend/src CLAUDE.md HANDOFF.md` e `git commit -m "docs(identidade): varredura final e registro da nova marca"`.
