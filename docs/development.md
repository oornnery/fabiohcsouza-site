# Development

```bash
uv sync
```

```bash
uv run python -m app serve --reload
```

http://portfolio.localhost:8000 and http://blog.localhost:8000, Portuguese under `/pt/`; one process serves both
sites. Settings are optional: `.env.example` lists them (copy it to `.env`). Without `SMTP_HOST` nothing is sent and
the log shows the e-mail, with the newsletter's confirm link. `DEMO_POSTS=50` adds fake posts from
`dev/demo-posts.json` to try lists and pages. The local database is `.local/app.sqlite`; delete it to start over.

With Docker, `docker compose -f docker/compose.dev.yml up --build` builds the `dev` target, mounts the code and
reloads on changes, on the same addresses.

## Tests and checks

```bash
uv run pytest
```

| File | Covers |
| --- | --- |
| `test_portfolio.py` | every portfolio page in both languages, projects, the contact form, `BLOG` on and off |
| `test_blog.py` | every blog page, series, tags, RSS, images, the newsletter |
| `test_core.py` | errors, assets and caching, dates, the SMTP message |
| `test_security.py` | headers, CSRF, limits, input validation, production settings, Turnstile |
| `test_i18n.py` | the Portuguese catalog is complete and keeps placeholders and markup |

The tests read `content/` plus the sample posts in `tests/sample/posts/`. CI also runs `ruff`, `ty`, `bandit`,
`djlint` and `pip-audit`, then builds and publishes the image (the README has the one-line version).

## Translations

1. Write the string in English where it is used: `{{ _("Posts") }}` in templates, `N_("Projects")` or
   `i18n.t("…", lang)` in Python, `FS.t("Sending…")` in JavaScript.
2. `uv run python -m app i18n` updates `app/locales/pt_BR/LC_MESSAGES/messages.po`.
3. Fill in the empty `msgstr` lines and restart the server: the catalog is read at start.

## A new page

One line on the site's router, `app/api/routes/portfolio.py` or `app/api/routes/blog.py`:

```python
router.add("/uses", "portfolio/uses.html", menu=N_("Uses"))
```

and the template, extending `layout/base.html`. That line gives the route, the sitemap entry, the menu link and the
test that opens it in both languages.

## When something is off

| Symptom | Cause |
| --- | --- |
| The app doesn't start | a broken front matter (the error names the file) or, in production, an insecure setting |
| 421 "unknown host" | the address doesn't match `PORTFOLIO_URL` / `BLOG_URL`, or `SITE` serves the other site |
| 403 "forbidden origin" | a form posted from another origin |
| "Too many tries" on a form | 5 posts per 10 minutes per IP |
| A string in English on a Portuguese page | missing from the `.po`: run `i18n` and translate |
| No blog links on the portfolio | `BLOG=false` |

## Share images and the e-mail signature

- `dev/og.html#portfolio` and `#blog` are the sources of the two share images (1200×630). Serve the repository root
  (`python3 -m http.server`), open them at that size, screenshot, and save as `static/assets/img/og-portfolio.png`
  and `og-blog.png`.
- `uv run python dev/signature/make.py` writes `dev/signature/email-signature.html`: open it and press **Copy**. It
  isn't part of the sites; for real use, its images (`dev/signature/img/`) have to be online.
