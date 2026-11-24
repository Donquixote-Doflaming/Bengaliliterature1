# বাংলা সাহিত্য — তিন যুগ ধরে

A study website for **বাংলা সাহিত্য** (Bengali literature), built from the source
file `বাংলা সাহিত্য.html.md`.

The visual language is borrowed from a minimal, grid-driven creative portfolio:
one screen, twelve columns, hairline rules, monospaced micro-labels, a single
loud editorial voice — then opened out into a proper reading experience.

---

## Pages

| File | What it is |
| --- | --- |
| `index.html` | **The board** — a one-screen home page: logo, the editorial statement, and a horizontal index of the three eras, the 137 writers and the 880 questions. |
| `study.html` | **পূর্ণ পাঠ** — the whole thing: 12 sections, 252 sub-headings, 78 data tables, 137 writer cards, 15 curated readings and the full 880-question answer sheet. Sticky table of contents, reading progress, live search. |
| `quiz.html` | **অনুশীলনী** — flashcard mode over the 880 exam questions: reveal, next/prev, shuffle, filter, and a full-list view. Keyboard driven (space, ←/→). |

Every page ends with the same footer: the copyright line, the page links, the
issue number **No. 112026**, and the credit **prepared by Rifat** directly
beneath it.

## Design

* 12-column grid (16 px margin / 12 px gutter), max width 1440 px.
* Type: **Geist** (sans), **Geist Mono** (labels & counters), **Instrument Serif**
  (editorial accents) — all self-hosted, with **Noto Sans/Serif Bengali** for the
  Bengali glyphs so nothing depends on a network.
* Paper-white ground, `#111` ink, `#555553` / `#8a8a88` greys, a warm dark mode.
* A film-grain overlay (SVG turbulence, soft-light blend), a loading counter
  with a tile wipe, and a **G** key overlay that reveals the underlying grid.
* Micro-labels are uppercase monospace with tabular numerals; hover states are
  a single hairline that wipes in from the right.

### Typography scale

Sizing is deliberately generous — Bengali glyphs carry more visual weight than
Latin at the same nominal size, so the reader body runs larger than a Latin
editorial site would. Every size below multiplies by `--ts`, the user-adjustable
type scale.

| Role | Size |
| --- | --- |
| Reader body (`.doc`) | `clamp(18px, 1.42vw, 22px)` / 1.76 |
| Reader `h2` | `clamp(34px, 3.9vw, 56px)` |
| Reader `h3` | `clamp(24px, 2.35vw, 34px)` |
| Reader `h4` | `clamp(21px, 1.9vw, 27px)` |
| Reader `h5` | `19px` |
| Home statement | `clamp(24px, 10px + 1.55vw, 46px)` |
| Home index row | `clamp(17px, 1.5vw, 24px)` |
| Quiz question | `clamp(26px, 3vw, 42px)` |
| Quiz answer | `clamp(18.5px, 1.62vw, 25px)` |
| Tables | `.97em` of the reader body |
| Chrome / rail / labels | 11–16px, mono uppercase |

### Text size control

The `ক` button in the top bar (or the `-` / `=` keys) cycles the whole site
through three steps — সাধারণ → বড় → সবচেয়ে বড় — by setting `--ts` on `:root`
(`1` / `1.14` / `1.3`). The choice persists in `localStorage` under
`bangla-lit-size`. Because the scale is a single token, the reader, the board,
the quiz, the table of contents and the search results all grow together.

## Interaction

| Key | Action |
| --- | --- |
| `G` | toggle the 12-column grid overlay |
| `⌘K` / `Ctrl+K` | open search |
| `-` / `=` | shrink / grow the text |
| `Space` / `Enter` | reveal the answer (quiz) |
| `←` `→` | previous / next question (quiz) |
| `Esc` | close search |

Search covers every heading, paragraph, table, writer card and question, and
filters by initial Bengali letter (অ আ ই …). Both the reader and the quiz load
the whole corpus, so a search finds anything from anywhere on the site.

Clicking a result takes you there. The overlay closes and releases the scroll
lock first, then the page scrolls to the target with an offset that clears the
sticky header, and the URL hash is updated so the destination can be shared.
Results on the current page scroll in place; results on the other page are
followed as a normal navigation. Question links use a one-based `#qN`, where
`#q1` is the first question — the same numbering the quiz page shows and
writes back into its own address bar.

The theme defaults to **light** — the OS `prefers-color-scheme` is deliberately
ignored so a dark-mode device still lands on the paper-white board. The `◐`
button switches to the warm dark mode and that choice is remembered.

### Responsive

One layout system, every device:

| Range | Behaviour |
| --- | --- |
| ≥ 1600px | wider measure, the article column grows to 7 of 12 columns |
| ≥ 2200px | the page is capped at 1760px so the type never runs away |
| 1100–1599px | full three-column reader: contents · article · sidebar |
| 781–1100px | tablet — the sidebar reflows into a row beneath the article, in the reading column so it can never slide under the sticky contents |
| ≤ 780px | phone — single column; the sidebar becomes a stack below the article |
| ≤ 420px | narrow phone — tighter margins, smaller gutters, the quiz counter drops to its own line |
| landscape, short | the chrome compacts so the article keeps the height |

Touch devices get 44px minimum tap targets, no hover-only affordances, no
double-tap zoom delay, and the tap highlight is suppressed in favour of the
site's own states.

`prefers-reduced-motion` is honoured: the loader is skipped, the fade-in is
removed and every transition is reduced to near-zero.

## Content pipeline

`build.py` parses the source markdown into a structured payload:

1. **Heading tree** — the document is split into sections → subsections → blocks.
2. **Block parser** — paragraphs, bullet/numbered lists, definition lists
   (`term` / `: description`), tables, chip rows, and parenthetical kickers.
3. **Link resolution** — the source's own anchors (`#author-20`,
   `#original-scan-author-51`, `#birthrange-3`, `#literary-profile-4`, …) are
   mapped by anchor number *and* by link text, so every internal link in the
   original resolves to a real destination here.
4. **Latin slugs** — headings and writers get transliterated, shareable ids
   (`#a-rabinadaranatha-thakura-2`).

### Rebuild

```bash
python3 build.py          # content/*.md -> data/*.js
python3 serve.py 8080     # static server with gzip
```

The source markdown lives in `content/`, so a fresh clone can rebuild the
payloads without anything else. Pass a path as the first argument to build
from a file kept elsewhere.

## Hosting on GitHub Pages

The site is entirely static — HTML, CSS, JS and self-hosted fonts, with every
path relative — so it deploys to GitHub Pages unchanged.

**1. Push it**

```bash
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

**2. Turn on Pages**

* **Settings → Pages → Build and deployment → Source: Deploy from a branch**
* Branch: `main`, folder: `/ (root)`
* Save, then wait for the green check

Your site will be at `https://<you>.github.io/<repo>/`. A repository named
`<you>.github.io` publishes at `https://<you>.github.io/` instead.

**3. Optional — a custom domain**

Add `CNAME` to the repo root containing your domain, then point a `CNAME` or
`A` record at GitHub's servers and enable **Enforce HTTPS**.

Notes:

* `.nojekyll` is committed, so Pages serves the files as-is instead of
  running them through Jekyll (which would otherwise skip files starting with
  `_`).
* Pages compresses responses automatically, so `serve.py` is only needed for
  local development.
* `build.py`, `serve.py` and `content/` are committed for convenience — they
  are harmless on Pages and make the repo self-contained.

## Files

```
index.html      home board
study.html      full reader
quiz.html       flashcard mode
style.css       design system
app.js          loader · theme · grid overlay · search
fonts.css       self-hosted @font-face rules
fonts/          Geist · Geist Mono · Instrument Serif · Noto Bengali
data/site.js    meta, eras, writer names, stats      (17 KB)
data/read.js    sections · writer cards · readings   (1.2 MB → 234 KB gzipped)
data/quiz.js    880 questions and answers             (154 KB → 26 KB gzipped)
build.py        markdown → data
serve.py        static server with gzip
```

## Numbers

* 12 sections · 252 sub-headings · 78 tables
* 137 writer cards · 15 curated readings
* 880 questions with answers — every one of them
* 0 broken internal links
