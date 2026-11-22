# AGENTS.md

Notes for coding agents working on this repository. Humans: start at [README.md](README.md).

## The project

Two sites from one FastAPI app: the portfolio (fabiohcsouza.dev) and the blog (blog.fabiohcsouza.dev), in English
(`/`) and Portuguese (`/pt/`). Pages are rendered on the server with Jinja2; CSS and JavaScript are plain files with
no build step. Content is Markdown in `content/`. SQLite keeps contact messages and newsletter subscribers. In
production each site runs in its own container (`SITE=portfolio|blog`) behind a Cloudflare Tunnel.

## Commands

```bash
uv sync                                   # dependencies
uv run task dev                           # both sites: http://portfolio.localhost:8000, http://blog.localhost:8000
uv run task check                         # ruff, ty, bandit, djlint and pytest: what CI runs
uv run task i18n                          # after changing interface strings; then fill the empty msgstr lines
```

Run `uv run task check` before saying a change is done. CI runs the same, plus `pip-audit` and the image build.

## Where things are

| Path | What |
| --- | --- |
| `app/main.py` | `create_app`: the Guard middleware, one sub-app per site, the daily purge |
| `app/api/routes/` | `portfolio`, `blog`, `contact`, `newsletter`, `seo` |
| `app/api/main.py` | the routers of each site |
| `app/api/pages.py` | `Pages`: one `router.add(...)` gives the route, the sitemap entry, the menu link and the page test |
| `app/api/deps.py` | settings, database, content, `render_page`, `Submit` (validation, rate limit, Turnstile for forms) |
| `app/core/` | `config` (Settings), `db`, `security` (Guard, rate limits, Turnstile, signed links), `i18n` |
| `app/models.py`, `app/crud.py` | tables and form input; reads, writes and data retention |
| `app/content/` | reads `content/`: pages, `projects.py`, `posts.py` |
| `app/utils/` | `markdown`, `mail` (SMTP), `web` (Page, render), `schema` (JSON-LD) |
| `app/templates/` | `layout/`, `ui/` (one macro per file, called as `ui.<name>(…)`), `portfolio/`, `blog/`, `email/` |
| `content/` | `pages/`, `projects/`, `posts/`: one folder per item, `<slug>.md` (English) + `<slug>.pt.md`, images in `assets/` |
| `tests/` | pytest; `tests/sample/posts/` are the sample posts (production ships no fake posts) |
| `app/static/` | CSS, JavaScript, fonts and icons, served at `/assets` |
| `docker/`, `.github/` | Dockerfile (dev/prod targets), compose files; CI that publishes the image to GHCR |
| `.env.example` | every setting, with the development values; production reads `.env` at the root |

## Rules

- **Least code.** Reuse what exists, prefer the standard library and the installed dependencies, no speculative
  options or layers. Delete before adding.
- **No functions inside functions.** Routes live on module-level `APIRouter`s; helpers and dependencies at module
  level; a class with `__call__` instead of a closure.
- **Security and privacy are not optional.** Validate input at the boundary (`app/models.py`), keep the CSP strict
  (no inline script or style anywhere), never log message contents or addresses, never commit secrets (`.env` is
  ignored). Production refuses insecure settings: keep that check in step with new settings.
- **Every user-facing string in both languages.** Write it in English in the code (`_("…")`, `N_("…")`, `FS.t("…")`),
  then translate it in `app/locales/pt_BR/LC_MESSAGES/messages.po`. A test fails while one is missing.
- **Copy:** short, direct, first person, each sentence adds a fact. No stock phrases, punchlines, CV tone or bold
  labels in running text. Portuguese is written naturally, not translated word for word.
- **Docs are in English** (`docs/`, README.md); README.pt-BR.md mirrors the README. Update the docs when behavior or
  layout changes.
- **Tests:** a new page is covered by the page registry; new logic (a branch, a parser, a data write, security) gets
  one focused test.

## Commits

- Small conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `build:`, `chore:`), one phase each.
- Each commit bumps `version` in `pyproject.toml`, runs `uv lock`, and gets an annotated tag `vX.Y.Z`.
- `Co-Authored-By: Claude …` goes only on commits that change docs or the READMEs, never on code commits.
- Commit or push only when asked.
