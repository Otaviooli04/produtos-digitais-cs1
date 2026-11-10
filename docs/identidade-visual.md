# CentralizEd — Guia de estilo visual

Identidade escolhida: **"Blocos × Órbita"**. Logo e cores da direção Órbita, com a interface lúdica da direção Blocos (títulos arredondados, bordas grossas e sombra "chapada", sem desfoque).

---

## 1. Cores

| Token | Hex | Uso |
|---|---|---|
| `--violeta` | `#4A2EE0` | Cor principal: botões primários, links, painéis de destaque, sombra dos cards |
| `--violeta-escuro` | `#3A1FC2` | Hover/pressionado do violeta |
| `--coral` | `#FF6B4A` | Acento: "Ed" do logo, barras de progresso, badges e alertas leves |
| `--noite` | `#14112B` | Texto principal, bordas dos cards e botões |
| `--cinza-texto` | `#5A5478` | Texto secundário, legendas e rótulos |
| `--lavanda` | `#F3F0FF` | Fundos suaves: tags, trilho da barra de progresso, botão secundário |
| `--branco` | `#FFFFFF` | Fundo da página e dos cards |

**Regras de contraste**
- Texto branco sobre violeta: ok em qualquer tamanho.
- Texto `--noite` sobre coral: ok. Texto branco sobre coral: **não usar** (contraste baixo).
- Coral sobre violeta (como o "Ed" no logo): só em tamanho grande (logo/títulos ≥ 32px), nunca em texto corrido.

```css
:root {
  --violeta: #4A2EE0;
  --violeta-escuro: #3A1FC2;
  --coral: #FF6B4A;
  --noite: #14112B;
  --cinza-texto: #5A5478;
  --lavanda: #F3F0FF;
  --branco: #FFFFFF;

  --borda: 2px solid var(--noite);
  --sombra-bloco: 6px 6px 0 var(--violeta);
  --raio-card: 20px;
  --raio-botao: 14px;
  --raio-tag: 10px;
}
```

---

## 2. Tipografia

Fontes do Google Fonts:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;800&family=Space+Grotesk:wght@500;700&family=Nunito:wght@400;600;700&display=swap" rel="stylesheet">
```

| Papel | Fonte | Peso | Observação |
|---|---|---|---|
| Logo (wordmark) | **Space Grotesk** | 500 + "Ed" em 700 | Só no logo |
| Títulos (h1–h3, títulos de card) | **Baloo 2** | 800 | `line-height: 1.2` |
| Rótulos de seção (MAIÚSCULAS) | **Baloo 2** | 800 | 13px, `letter-spacing: 0.1em`, cor `--cinza-texto` |
| Texto, botões, interface | **Nunito** | 400 / 600 / 700 | Botões em 700 |

Escala sugerida: títulos de página 40px · títulos de card 24px · corpo 16px · secundário 13–14px.

---

## 3. Logo

Wordmark: **centraliz** em Space Grotesk 500 + **Ed** em Space Grotesk 700, tudo minúsculo exceto o "E". Letter-spacing `-0.03em`. O símbolo de órbita fica à esquerda, com espaço de ~18px.

- Sobre fundo claro: "centraliz" em `--noite`, "Ed" em `--violeta`.
- Sobre fundo violeta: "centraliz" em branco, "Ed" em `--coral`.

**Símbolo (órbita) — versão para fundo violeta**
```svg
<svg width="84" height="84" viewBox="0 0 84 84" aria-hidden="true">
  <circle cx="42" cy="42" r="38" fill="none" stroke="#FFFFFF" stroke-width="3"/>
  <circle cx="42" cy="42" r="23" fill="none" stroke="#FFFFFF" stroke-width="3" opacity="0.45"/>
  <circle cx="42" cy="42" r="10" fill="#FFFFFF"/>
  <circle cx="69" cy="15" r="7" fill="#FF6B4A"/>
  <circle cx="20" cy="56" r="5" fill="#FFFFFF"/>
</svg>
```
Para fundo claro, troque os `#FFFFFF` por `#4A2EE0` (o ponto coral continua coral).

**Ícone do app** (quadrado branco, raio 26px em 96px, símbolo simplificado):
```svg
<svg width="60" height="60" viewBox="0 0 84 84" aria-hidden="true">
  <circle cx="42" cy="42" r="36" fill="none" stroke="#4A2EE0" stroke-width="4"/>
  <circle cx="42" cy="42" r="12" fill="#4A2EE0"/>
  <circle cx="68" cy="16" r="8" fill="#FF6B4A"/>
</svg>
```

**Favicon** (círculo `--noite`, símbolo mínimo):
```svg
<svg width="64" height="64" viewBox="0 0 84 84">
  <circle cx="42" cy="42" r="42" fill="#14112B"/>
  <circle cx="42" cy="42" r="28" fill="none" stroke="#FFFFFF" stroke-width="6"/>
  <circle cx="42" cy="42" r="10" fill="#FF6B4A"/>
</svg>
```

---

## 4. Componentes

**Card (o elemento-assinatura do estilo)**
```css
.card {
  background: var(--branco);
  border: var(--borda);
  border-radius: var(--raio-card);
  box-shadow: var(--sombra-bloco);   /* sombra sólida, deslocada, sem blur */
  padding: 22px;
  display: flex; flex-direction: column; gap: 14px;
}
```

**Botões** (altura mínima 44px)
```css
.btn {
  height: 46px; padding: 0 22px;
  border: var(--borda); border-radius: var(--raio-botao);
  font-family: Nunito, sans-serif; font-weight: 700; font-size: 15px;
  cursor: pointer; transition: transform .1s, box-shadow .1s;
}
.btn-primario   { background: var(--violeta); color: var(--branco); }
.btn-primario:hover { background: var(--violeta-escuro); }
.btn-secundario { background: var(--branco); color: var(--noite); }
.btn:active { transform: translate(2px, 2px); }  /* "afunda" como um bloco */
```

**Tag / badge de turma**
```css
.tag {
  background: var(--lavanda); color: var(--violeta);
  font-size: 13px; font-weight: 700;
  padding: 5px 12px; border-radius: var(--raio-tag);
}
```

**Barra de progresso**
```css
.progresso       { height: 10px; border-radius: 5px; background: var(--lavanda); }
.progresso > div { height: 10px; border-radius: 5px; background: var(--coral); }
```

**Painel de destaque** (cabeçalho, tela de login, hero): fundo `--violeta`, texto branco, logo na versão para fundo violeta.

---

## 5. Tom da interface

- Textos curtos e animados nos botões ("Bora pra aula!", "Desafios"), mas claros.
- Fundo da página branco; violeta em blocos de destaque, nunca em tudo.
- Bordas `--noite` de 2px e sombra sólida violeta são a assinatura: use nos cards e botões principais.
- Evitar: gradientes, sombras com desfoque, emojis como ícones. Ícones em traço simples (ex.: Lucide), 2px, cor `--noite` ou `--violeta`.
