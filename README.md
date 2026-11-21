# fabiohcsouza.dev

**English** · [Português](README.pt-BR.md)

My portfolio and my blog, in English and Portuguese.

| Site | Domain |
| --- | --- |
| Portfolio: who I am, what I built, contact | [fabiohcsouza.dev](https://fabiohcsouza.dev) |
| Blog: notes on VoIP, networks, automation, code and AI | [blog.fabiohcsouza.dev](https://blog.fabiohcsouza.dev) |

![The portfolio home](docs/screenshots/home-light.png)

<p>
  <img src="docs/screenshots/projects-dark.png" alt="Projects" width="49%">
  <img src="docs/screenshots/project-light.png" alt="A project's page" width="49%">
</p>
<p>
  <img src="docs/screenshots/blog-home-dark.png" alt="The blog home, with the newsletter" width="49%">
  <img src="docs/screenshots/blog-post-light.png" alt="A post with its table of contents and series" width="49%">
</p>
<p>
  <img src="docs/screenshots/blog-post-mobile-dark.png" alt="A post in Portuguese on a phone" width="24%">
</p>

The blog screenshots use the sample posts from `tests/sample/`.

Python 3.14 and FastAPI render every page on the server with Jinja2; the CSS and JavaScript are plain files, with no
build step. Pages, projects and posts are Markdown folders in `content/`. SQLite keeps the contact messages and the
newsletter, and e-mail goes out over SMTP. One Docker image serves either site.

## Run it

```bash
uv sync
```

```bash
uv run python -m app serve --reload
```

Open http://portfolio.localhost:8000 and http://blog.localhost:8000 (`*.localhost` points to your machine); Portuguese
is under `/pt/`. Settings are optional in development: copy `.env.example` to `.env` to change them. With Docker
instead: `docker compose -f docker/compose.dev.yml up --build`.

## Commands

`uv run python -m app <command>`

| Command | What it does |
| --- | --- |
| `serve [--reload]` | run the sites |
| `leads [--last N]`, `stats` | contact messages |
| `subscribers` | newsletter subscribers |
| `send-post <slug> [--send]` | e-mail a published post to the subscribers (a dry run without `--send`) |
| `projects-dates` | set each project's `updated` to the date of its last commit on GitHub |
| `images` | a lighter WebP next to each PNG/JPEG in `content/` |
| `i18n` | collect the interface strings into the Portuguese catalog |
| `purge` | apply the data retention rules now |

Checks, the same as CI:

```bash
uv run ruff check app tests && uv run ty check && uv run bandit -c pyproject.toml -r app -q && uv run djlint app/templates --lint && uv run pytest
```

## Layout

```
app/main.py     the app: middleware, one sub-app per site, the daily purge
app/api/        routes (portfolio, blog, contact, newsletter, seo), dependencies, the page registry
app/core/       settings, database, security (middleware, rate limits, Turnstile), i18n
app/models.py   tables and form input        app/crud.py   reads and writes
app/content/    reads content/: pages, projects, posts
app/utils/      Markdown, e-mail, rendering, JSON-LD
app/templates/  Jinja templates; app/locales/ the Portuguese catalog
content/        pages, projects and posts, one folder each, images in its assets/; site.yml
static/assets/  CSS, JavaScript, fonts, icons
docker/         Dockerfile, compose.yml (production), compose.dev.yml, .env.example
dev/            fake posts for development, the share image source, the e-mail signature
tests/          pytest, with sample posts in tests/sample/
```

## Documentation

- [Content](docs/content.md): writing pages, projects and posts, with images
- [Deploy](docs/deploy.md): production, one site or both, updates, backups
- [Development](docs/development.md): tests, translations, debugging
- [Architecture](docs/architecture.md): how a request is served and where the code is
- [Rules](docs/business-rules.md): contact, newsletter, data retention, limits
- [Security](docs/security.md) · [Design](docs/design.md)
- [TODO](TODO.md): what may come later (webhook, send queue, observability)
