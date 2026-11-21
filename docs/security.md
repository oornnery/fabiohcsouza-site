# Security

To report a problem: [SECURITY.md](../SECURITY.md).

| Area | What the app does |
| --- | --- |
| Hosts | only the configured domains answer (anything else: 421); `www.` redirects |
| Forms | the origin must be the site itself (CSRF); every field is validated and capped; honeypot, rate limit and Turnstile |
| Output | autoescaped templates; Markdown without raw HTML; a strict Content-Security-Policy with no inline script or style |
| Headers | HSTS, `nosniff`, no framing, `Referrer-Policy`, `Permissions-Policy` |
| Errors | never echo the input back; 500 shows a generic page and logs the cause |
| Newsletter links | signed with `SECRET_KEY` (HMAC), compared in constant time |
| Settings | production refuses to start with an http URL, no mail server or a short `SECRET_KEY` |
| Files | `/assets` and `/media` serve only their own folders; `/media` serves only images, and no draft post's images in production |
| Privacy | fonts on the same domain, no ads or tracking, logs without message contents or addresses |
| Dependencies | `pip-audit` in CI; pinned base images |

## Up to you in production

- Turn Turnstile on and add the Cloudflare rate-limit rule ([deploy](deploy.md)).
- `CLIENT_IP_HEADER=cf-connecting-ip` trusts Cloudflare for the visitor's IP. That is safe because the containers
  listen on `127.0.0.1` only; keep them that way.
- Keep SPF, DKIM, DMARC and the reverse DNS right, or other providers junk what the sites send.
- Back up the two databases ([deploy](deploy.md#backup-and-restore)).
