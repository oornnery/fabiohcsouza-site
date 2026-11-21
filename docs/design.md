# Design

Both sites share one design. Every value lives in `app/static/assets/css/tokens.css`.

## Principles

- Lists instead of cards: no boxes, no borders around icons.
- Each piece of information appears once per page. Career history is on LinkedIn.
- Neutral colors for almost everything; the four signal colors only mark status (below).
- The same item layout, section head and "All →" link on every page.
- AA contrast, touch targets ≥ 24px (icon buttons 32px), keyboard navigation, skip link, `prefers-reduced-motion`.

## Color

Neutral base: **stone** (warm gray). Four signal colors, used like the status LEDs on network equipment. Each has a **text** variant
(≥ 4.5:1 on the background) and a **ui** variant (dots, borders, underlines).

| Signal | Means | Where |
| --- | --- | --- |
| green | active / ok / action | focus, current nav item, table of contents, active filter, status dots, current month, success, action hovers |
| blue | information / reading | title, tag and reading-link hovers, notes, language note, text selection |
| amber | attention | form errors, 4xx pages |
| orange | label | badges next to titles ("Open Source", "Work"), 5xx pages |

Rules: color is never a block background; at most one signal per element; the smallest text is `--faint`
(4.7:1 light, 5.5:1 dark).

| Token | Light | Dark | Use |
| --- | --- | --- | --- |
| `--bg` | `#fafaf9` | `#0c0a09` | page |
| `--fg` | `#1c1917` | `#fafaf9` | titles, strong text |
| `--text` | `#44403c` | `#d6d3d1` | body |
| `--muted` | `#5f5953` | `#a8a29e` | secondary text, quiet links |
| `--faint` | `#757069` | `#8c8782` | meta, labels |
| `--line` / `--line-strong` | `#e7e5e4` / `#d6d3d1` | `#292524` / `#44403c` | rules / underlines |
| `--code-bg` | `#f3f2f0` | `#1c1917` | code, hover backgrounds |
| `--green` / `-ui` | `#047857` / `#10b981` | `#34d399` | |
| `--blue` / `-ui` | `#0369a1` / `#7cc4ec` | `#7dd3fc` | |
| `--amber` / `-ui` | `#a16207` / `#f59e0b` | `#fcd34d` / `#fbbf24` | |
| `--orange` / `-ui` | `#b4580f` / `#fb923c` | `#fdba74` / `#fb923c` | |

Each token is written once with `light-dark(light, dark)`. The scheme follows the system; the sun/moon toggle sets
`data-theme` and a cookie on the parent domain, so the portfolio and the blog share the choice.

## Type

| Use | Font | Size (token) |
| --- | --- | --- |
| headings | Fraunces (serif) | 20 h2 · 30 h1 |
| body | Geist | 16 base · 18 lead |
| nav, buttons, footer | Geist | 14 |
| dates, tags, counts, labels | Geist Mono | 12–13 |

Fonts are self-hosted (Fontsource, latin subset, OFL): no request leaves the domain. Two tokens pick the pairing: `--font-heading`
(headings and item titles) and `--font-body` (everything else).

## Space and layout

- 4px grid: `--space-1` (4) … `--space-24` (96).
- Page: 1024px max, 48px side padding (24px on phones). Header, main and footer share the width.
- Homes, posts and contact use a **2fr / 1fr grid** from 768px; one column below.
- Breakpoints: **sm 560px** and **md 768px** (plain numbers: CSS can't use variables in `@media`).
- Header below 800px (the widest nav, the blog in Portuguese, needs it): wordmark and a menu button; the links, then
  RSS / language / theme, open below (Esc or a tap outside closes). Without JavaScript everything stays visible.

## Components

| Component | Rule |
| --- | --- |
| **Wordmark** | status LED + `~/` + domain + blinking `_`. The LED cycles green → blue → amber → orange (2 s each) and pulses a dotted ring ("sparks"); hover lights `~/` and speeds the pulse. On the first page of a visit the name is typed key by key with the caret lit (`wordmark.js`, once per tab session, skipped with reduced motion). The footer copy is still. |
| **Section head** | title left, link right (`All →`, `All 17 →`, `More →`, `RSS`) |
| **Item** (post/project) | date → title [badge] → summary → tags + links. A project's date is its last commit |
| **Compact item** (side column) | meta on top; title and summary clamp to 1 line on desktop, 2 on phones |
| **Show more** | at the end of lists; loads more in place and says how many are left |
| **Search** | compact (22rem, 14px), green underline on focus, result count, × to clear; filters as you type, `/` focuses, `Esc` clears |
| **Tags** | mono, `#tag`. Blog tags open the Tags page; project tags open the Projects search |
| **Timeline** | current year with the last 3 months (current one marked green) + 2 previous years |
| **Forms** | underlined fields, mono labels, amber error under the field, "Sending…" state, honeypot |
| **Newsletter** | a one-field form in the blog home's side column and on `/subscribe`; a "Subscribe →" line at the end of each post |
| **Share** | copy link, X, LinkedIn, WhatsApp. Side column on desktop, end of the post on phones |
| **Table of contents** | side column on desktop (section in view marked green). On phones a bar sticks to the top: the section in view, a green line that fills as you read, and the full list on tap |
| **Icons** | Lucide, stroke 1.75, no border, hit area ≥ 32px (`.tap`); icon-only controls carry `aria-label` and `title` |
| **Status dots** | "open to work" on the home and the code on error pages pulse with the same ring as the LED |

Templates: one component per file in `app/templates/ui/`, called as `ui.<name>(…)` from any template.

## Motion

150ms color transitions; LED pulse 2s; cursor blink 1s. Everything stops under `prefers-reduced-motion`.

## Error pages

One template for every status. The code dot, the footer LED and the favicon take the status color: amber 4xx,
orange 5xx, blue 503 (maintenance). The header LED keeps cycling.

## Share images and icons

- **Open Graph:** 1200×630, `app/static/assets/img/og-portfolio.png` and `og-blog.png`, served at `/og.png`. Source:
  `dev/og.html`. A post with `image: assets/cover.png` (1200×630) is shared with that image instead.
- **Favicon:** `~/` on a dark tile with the status LED; one file per status (`favicon.svg`, `-warn`, `-error`, `-maint`).
  `touch-icon.png` (180×180, square: iOS rounds it) is `favicon.svg` rendered for the iOS home screen, at `/apple-touch-icon.png`.
- **E-mail signature:** `dev/signature/`, outside the sites. Mail clients drop CSS and SVG, so the LED and the cursor
  are GIFs and the icons PNGs.

## Copy

Direct and specific, first person, short sentences: say what, with what. No stock phrases ("from design to
production", "passionate about…") and no punchlines built to sound clever ("when something breaks, I'm the one
who…"). Portuguese is written, not translated word for word.
