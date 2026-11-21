# Deploy

CI builds the image on every push to `main` and, once the checks pass, publishes it as
`ghcr.io/oornnery/fabiohcsouza` (tags `latest` and `sha-<commit>`). The VPS doesn't build anything: it needs only
`docker/compose.yml` and `docker/.env`.

| Service | Site | Listens on |
| --- | --- | --- |
| `portfolio` | fabiohcsouza.dev | `127.0.0.1:8001` |
| `blog` | blog.fabiohcsouza.dev | `127.0.0.1:8002` |

Each has its own SQLite database in a Docker volume. The Cloudflare Tunnel on the VPS is the way in.

## 1. Cloudflare

- **Tunnel**, public hostnames: `fabiohcsouza.dev` and `www.fabiohcsouza.dev` to `http://localhost:8001`;
  `blog.fabiohcsouza.dev` to `http://localhost:8002`. The app redirects `www`.
- **Turnstile** (anti-bot on the forms): add a widget for both hostnames, *Managed* mode. Its two keys go in `.env`.
- **Rate limit** (Security > WAF): 100 requests in 10 s per IP, block for 10 s, on the three hostnames.
- **Web Analytics** (optional, no cookies): add the hostnames with manual setup; the snippet's token goes in `.env`.

## 2. E-mail

The sites send through the Stalwart server on the same VPS.

1. Create an account for the site in Stalwart, allowed to send as `contact@fabiohcsouza.dev`.
2. DNS on Cloudflare, all *DNS only* (grey cloud): `A email` to the VPS, `MX` to `email.fabiohcsouza.dev`,
   SPF `v=spf1 mx -all`, the DKIM record Stalwart shows, DMARC `v=DMARC1; p=quarantine; rua=mailto:<you>`.
3. Reverse DNS (PTR) of the VPS address = `email.fabiohcsouza.dev`, at the VPS provider.
4. Send a contact from the site to yourself: SPF, DKIM and DMARC say `pass` in the headers.

Contact messages only reach your own mailbox. Newsletter e-mails go to other people's providers: without step 2 and 3
right, Gmail and Outlook junk them. Check before the first `send-post --send`.

## 3. Settings

On the VPS, with this repository's `docker/` folder (or just its two files):

```bash
cp docker/.env.example docker/.env
```

```bash
chmod 600 docker/.env
```

Fill in `SMTP_USER`, `SMTP_PASSWORD`, `OWNER_EMAIL`, the Turnstile keys and, for the blog, `SECRET_KEY`
(`python -c "import secrets; print(secrets.token_urlsafe(32))"`; keep it: a new one breaks the links already sent).
The URLs and the mail server are already there. With something missing or insecure the app doesn't start, and the log
says why.

After the first CI run, make the image public once: GitHub > your profile > Packages > fabiohcsouza > Package
settings > Change visibility > Public. GitHub creates packages as private even for a public repository; once public,
the VPS pulls it without logging in.

## 4. Start

**Portfolio only** (the blog comes later): keep `BLOG=false` in `.env`, so the portfolio doesn't link to it.

```bash
docker compose -f docker/compose.yml up -d portfolio
```

**Blog only**:

```bash
docker compose -f docker/compose.yml up -d blog
```

Its links to the portfolio point to fabiohcsouza.dev, so they work only once the portfolio is up.

**Without the newsletter**: `NEWSLETTER=false` in `.env` hides the subscribe form; turn it on later and restart.

**Both**: set `BLOG=true` in `.env`, then

```bash
docker compose -f docker/compose.yml up -d
```

Moving from one site to both is the same command after `BLOG=true`; the portfolio restarts with the new setting.
Check with `docker compose -f docker/compose.yml ps`: each service `healthy`. To take one site down:
`docker compose -f docker/compose.yml stop blog`.

Then, on the real domain: the pages open in both languages, `/nope` shows the 404 page, and a contact (or a
newsletter subscription) reaches the inbox.

## Updates

Push to `main`. When CI is green:

```bash
docker compose -f docker/compose.yml pull && docker compose -f docker/compose.yml up -d
```

Back to an earlier version: `TAG=sha-<commit> docker compose -f docker/compose.yml up -d`.

## Daily use

```bash
alias portfolio="docker compose -f docker/compose.yml exec portfolio python -m app"
```

```bash
alias blog="docker compose -f docker/compose.yml exec blog python -m app"
```

| Task | Command |
| --- | --- |
| Contact messages | `portfolio leads` |
| E-mail a post to the subscribers | `blog send-post <slug>` to see it, then with `--send` |
| A send stopped halfway | run the same `--send` again: it continues with whoever is missing |
| Subscribers | `blog subscribers` |
| Maintenance page | `MAINTENANCE=true` in `.env`, then `up -d` |
| Logs | `docker compose -f docker/compose.yml logs -f` |

When the blog goes live, the privacy page gets back the blog and the newsletter: in
`content/pages/privacy/privacy.md` and `privacy.pt.md`, the `lead` says "this site and the blog" ("o site e o blog"),
and "What I keep" gets this paragraph:

> **Blog newsletter.** Your e-mail, the language of the page where you subscribed, and the dates you subscribed and confirmed. I use them only to send new posts. If you don't confirm, the address is deleted after 7 days. Every e-mail has a link to unsubscribe, and unsubscribing deletes the address at once.

> **Newsletter do blog.** Seu e-mail, o idioma da página onde você se inscreveu e as datas de inscrição e de confirmação. Uso só para mandar os posts novos. Se você não confirmar, o endereço é apagado em 7 dias. Todo e-mail tem um link para cancelar, e cancelar apaga o endereço na hora.

## Backup and restore

What matters is two files, both `/data/app.sqlite`: in the volumes `fabiohcsouza_portfolio-data` (contact messages)
and `fabiohcsouza_blog-data` (subscribers). Everything else is in git.

SQLite writes in WAL mode, so a file copied while the app writes can be broken. Before the VPS backup runs, take a
consistent copy (the backup then picks up `backup.sqlite`):

```bash
docker compose -f docker/compose.yml exec -T portfolio python -c "import sqlite3; sqlite3.connect('/data/app.sqlite').backup(sqlite3.connect('/data/backup.sqlite'))"
```

```bash
docker compose -f docker/compose.yml exec -T blog python -c "import sqlite3; sqlite3.connect('/data/app.sqlite').backup(sqlite3.connect('/data/backup.sqlite'))"
```

To restore: stop the site, put the copy back as `app.sqlite` in its volume, start it.
