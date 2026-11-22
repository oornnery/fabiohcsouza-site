# Architecture

The layout follows the [full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template):
`api/` for routes, `core/` for settings and security, `models.py` and `crud.py` for the data.

## A request

```
visitor → Cloudflare → Tunnel → the site's container → Guard (app/core/security.py) → the site's FastAPI app
                                                                                     ├─ /assets   CSS, JS, fonts, icons
                                                                                     └─ routers   app/api/main.py
```

| Site | Routers (`app/api/routes/`) |
| --- | --- |
| portfolio | `portfolio.py` (pages), `contact.py` (`/api/contact`), `seo.py` (sitemap, robots, og.png, /media) |
| blog | `blog.py` (pages, `/api/posts/<slug>/like`), `newsletter.py` (`/api/subscribe`, confirm, unsubscribe), `seo.py` (+ rss.xml) |

- One image, one container per site (`SITE=portfolio` or `blog`); in development one process serves both. The
  `Host` header picks the site.
- `/pt/…` is Portuguese: the Guard strips the prefix, so both languages share the routes.
- The Guard also checks the host, the origin of writes, the rate limit and the body size, and adds the security
  headers to every answer.
- Pages answer with an ETag (an unchanged page is a 304); `/assets` with a content hash in the URL is cached for a
  year.
- Once a day the app deletes old data (`crud.purge`, see [rules](business-rules.md)).

## Code

```
app/
  main.py          create_app(): the Guard, one sub-app per site, /healthz, the daily purge
  __main__.py      the command line
  models.py        tables (Lead, Subscriber, Delivery, PostLike, RateLimit) and form input (ContactIn, SubscribeIn)
  crud.py          reads and writes of those tables, and the data retention rules
  api/
    main.py        the routers of each site
    deps.py        settings, database, content, render_page, Submit (the gate every form post goes through)
    pages.py       Pages: the page registry (route + sitemap + menu)
    errors.py      JSON under /api, the error page elsewhere
    routes/        portfolio, blog, contact, newsletter, seo
  core/            config (Settings), db (engine), security (Guard, rate limits, Turnstile, signed links), i18n
  content/         reads content/ once (reloads in development): pages, projects.py, posts.py
  utils/           markdown, mail (SMTP), web (Page, render), schema (JSON-LD)
  templates/       layout/, ui/ (one component per file, `ui.<name>(…)`), portfolio/, blog/, email/, error.html
  locales/         pt_BR/LC_MESSAGES/messages.po
```

Routes are plain `def` functions at module level that take what they need from FastAPI dependencies.

## Pages

A page is declared once on its site's router:

```python
router.add("/projects/{slug}", "portfolio/project.html", nav="/projects", context=_project, each=…, lastmod=…)
```

That gives the GET route, the sitemap entry with its hreflang links, the menu link (with `menu=`) and the test that
opens every page in both languages.

## Templates and translation

Jinja2 with autoescape and `StrictUndefined` (a missing variable fails loudly). `p` builds every link, asset URL and
date; `c` is the content; `me` is `content/site.yml`. Interface strings are English in the code and Portuguese in the
`.po` (Babel); dates and month names come from CLDR.

## Data and e-mail

SQLite in WAL mode, one file per site. E-mail goes over SMTP to the mail server on the VPS, which keeps its own queue
and retries. A contact is saved, then e-mailed after the answer; if the server is down, the log says so and the
message is in `leads`. Newsletter posts go out with `send-post`, one message per subscriber, each recorded as it
leaves, so a second run continues where the first stopped.
