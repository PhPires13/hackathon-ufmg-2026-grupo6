# Apresentação Banco UFMG × Enter AI — Guia de execução

## Por que existem duas pastas

O `node_modules` **não pode ser instalado neste diretório do Google Drive**. A sincronização automática do Drive corrompe arquivos durante `npm install` (agravado pelo emoji `🚀` no caminho). Por isso a instalação funcional vive em:

```
C:\temp\banco-ufmg-slides\
```

Todo o conteúdo editável (`slides.md`, `components/`, `styles/`, `public/`) vive nas duas pastas. **Edite aqui no Drive** (versionado em git) e sincronize para `C:\temp\banco-ufmg-slides\` antes de rodar.

---

## 1 · Rodar a apresentação (o caminho feliz)

Abra o **Git Bash** e cole:

```bash
cd /c/temp/banco-ufmg-slides
./node_modules/.bin/slidev slides.md --port 3030
```

Aguarde ~10 segundos. Vai aparecer:

```
public slide show   > http://localhost:3030/
```

Abra essa URL no **Chrome** (recomendado) ou Edge. Pronto — apresentação rodando.

### Atalhos de teclado

| Tecla | Ação |
|-------|------|
| `Space` / `→` / `↓` | avançar (passa cliques dentro do slide antes de trocar) |
| `←` / `↑` | voltar |
| `F` | tela cheia — **use isto durante a apresentação** |
| `O` | visão geral de todos os slides |
| `D` | Presenter Mode (abre janela extra com notas + timer) |
| `Esc` | sai da tela cheia / fecha diálogos |

**Importante:** pressione `F` para tela cheia assim que começar a apresentar. A barra lateral de navegação já está oculta via CSS; em tela cheia os controles do navegador também somem.

---

## 2 · Editar e sincronizar

Edite os arquivos **aqui no Drive** (esta pasta) e depois rode o comando de sincronização:

```bash
cd "e:/Google Drive/Meu Drive/04 - Anotações & Rascunhos/Claude/claude-workspace/🚀_Projects/UFMG/hackathon-ufmg-2026-grupo6"

cp presentation/slides.md /c/temp/banco-ufmg-slides/
cp presentation/styles/index.css /c/temp/banco-ufmg-slides/styles/
cp presentation/components/*.vue /c/temp/banco-ufmg-slides/components/
cp presentation/public/*.svg /c/temp/banco-ufmg-slides/public/
cp -r presentation/public/screenshots /c/temp/banco-ufmg-slides/public/
```

Com o dev server rodando, o Slidev faz **hot reload automático** — a alteração aparece em segundos sem refresh manual.

---

## 3 · Exportar

### PDF (entregável final)

```bash
cd /c/temp/banco-ufmg-slides
./node_modules/.bin/slidev export slides.md --output apresentacao.pdf
```

O PDF aparece em `C:\temp\banco-ufmg-slides\apresentacao.pdf`. Copie para este diretório quando quiser versionar.

### PowerPoint (se o comitê exigir)

```bash
./node_modules/.bin/slidev export slides.md --format pptx
```

### SPA estática (para hospedar)

```bash
./node_modules/.bin/slidev build slides.md
# saída em ./dist/
```

---

## 4 · Troubleshooting

**"Entry file does not exist"** — você esqueceu de passar `slides.md` como argumento. Use `slidev slides.md`, não `slidev dev`.

**Tela branca no `localhost:3030/`** — abra o DevTools do Chrome (F12 → Console). Se houver erro Vue, costuma ser aspas dentro de atributos HTML. Cole o erro e eu ajusto.

**Barra lateral com "2 undefined, 3 undefined..." volta a aparecer** — pressione `Esc`. É o "slide goto dialog" que abre com `G`; já está oculto via CSS mas pode reaparecer se o cache CSS falhar. Force refresh com `Ctrl+Shift+R`.

**Screenshots quebrados** — o Django precisa estar rodando para **recapturar**, mas os PNGs já estão em `public/screenshots/` e são servidos estaticamente pelo Slidev. Se algum estiver corrompido pelo Drive:
```bash
cd "src/estrangeirosplatform" && python manage.py runserver 8010
# depois, em outro terminal, recapture com Chrome/Edge e salve no mesmo path
```

**Porta 3030 ocupada** — use outra: `slidev slides.md --port 3031`.

---

## 5 · Checklist pré-apresentação (10 min antes)

1. [ ] `cd /c/temp/banco-ufmg-slides && ./node_modules/.bin/slidev slides.md` rodando sem erros
2. [ ] Chrome aberto em `http://localhost:3030/`
3. [ ] Pressionar `F` → tela cheia
4. [ ] Passar rapidamente pelos 14 slides com `Space` para confirmar que as animações reproduzem (especialmente os `StatNumber` animados e o `ArchitectureFlow` revelando nó a nó)
5. [ ] Verificar que os 4 screenshots (cases-list, case-detail, monitoramento-aderência, monitoramento-efetividade) carregam
6. [ ] Opcional: abrir Presenter Mode (`D`) em um segundo monitor para ver timer e notas

---

## Resumo da estrutura

```
presentation/
├── slides.md              # 14 slides (editar aqui)
├── package.json
├── RUN.md                 # este arquivo
├── components/            # Vue components com animações
│   ├── StatNumber.vue
│   ├── CodeReveal.vue
│   ├── ArchitectureFlow.vue
│   ├── QuoteReveal.vue
│   └── TerminalDemo.vue
├── styles/
│   └── index.css          # paleta Enter + hide sidebar
└── public/
    ├── enter-logo.svg     # logo Enter AI
    └── screenshots/       # telas Django capturadas
```

**Paleta Enter (dark mode) aplicada:**
- Fundo: `#0A0A0A` (preto)
- Superfície: `#141414` (cards/notes)
- Texto primário: `#F3F4F6` (branco suave)
- Destaque: `#F5A623` (âmbar — a cor da logo)
- Muted: `#9CA3AF` (cinza)

Zero gradientes. Zero emoji. Tipografia Inter + JetBrains Mono. Tudo consistente com a identidade dark do [getenter.ai](https://www.getenter.ai/).

**Grupo:** Estrangeiros (Hackathon UFMG 2026 · Banco UFMG × Enter AI Challenge).
