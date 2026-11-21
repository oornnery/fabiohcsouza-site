# Later

What was left out on purpose, why, and how to put each piece back. The code of the webhook and the queue existed and
was tested before the cut: a copy is in `.local/antes-dos-cortes.tar.gz` on the development machine (not in git).

## Webhook for new contacts

**What it was:** besides the e-mail, each contact was POSTed to a URL (n8n → WhatsApp, for example).

**Why it is out:** not used yet, and it was the only reason to keep an HTTP client and a signing secret around.

**Where it goes:** `app/core/mail.py`, called from `notify_owner` next to `send_email`.

```python
import hashlib, hmac, json
import httpx

async def fire_webhook(settings: Settings, event_id: str, event: str, data: dict) -> None:
    """POST {"id","event","data"}; header X-Signature-SHA256 = hex HMAC-SHA256(body, WEBHOOK_SECRET)."""
    if not settings.webhook_url:
        return
    body = json.dumps({"id": event_id, "event": event, "data": data}, ensure_ascii=False).encode()
    signature = hmac.new(settings.webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.post(settings.webhook_url, content=body, headers={
            "Content-Type": "application/json", "X-Signature-SHA256": signature})
    if res.is_error:
        raise ProviderError(f"webhook answered {res.status_code}")
```

What comes with it:

- `app/core/config.py`: `webhook_url: str = ""` and `webhook_secret: str = ""`; in `_safe`, refuse a URL with a
  secret shorter than 32 characters.
- `notify_owner`: call it with `f"lead-{lead.id}"` as the id and the lead's fields as `data`, inside its own
  `try`, so a webhook failure doesn't stop the e-mail (and the other way round).
- The receiver must check the signature and drop ids it has already seen.
- Privacy page: name whoever receives the data (the n8n host, WhatsApp).

## Send queue (outbox)

**What it was:** a table of notifications saved in the same transaction as the record, drained after the response
and every 30 s, with retries (30 s doubling up to 6 h, 12 tries) and a `python -m app outbox [--retry]` command.

**Why it is out:** the mail server runs on the same machine and has its own queue and retries. The only gap is the
mail server being down at the moment of a contact; then the message is still in the database.

**When to bring it back:** if the e-mail moves to a remote provider (an API or a relay that can be unreachable), or
if the webhook above becomes important. The newsletter doesn't need it: `send-post` records each delivery as it
goes and a second run continues where the first stopped.

**Shape:** a table `outbox(id, event, channel, ref, status, attempts, next_at, locked_until, last_error,
created_at)`; `enqueue()` in the route's transaction; `drain()` claims a batch in one `UPDATE … RETURNING` (so two
workers never send the same job), runs a handler per event and records the result; a loop in the app's lifespan.
Rows hold ids, never personal data. Retention: delivered or failed rows go after 30 days.

## Observability

Not built yet. The plan:

- **Logs:** the app already writes to the container's output. Collect with Grafana Alloy or Promtail into Loki.
  The access log holds the tunnel's address (127.0.0.1), not the visitor's; if that changes, so must the privacy
  page.
- **Metrics:** `node_exporter`, `cAdvisor` and a `blackbox_exporter` probe on `/healthz` need no code. For
  application metrics, `prometheus-client` and a `/metrics` route on the outer app (next to `/healthz`), on a port
  the tunnel doesn't publish.
- **Google Analytics:** sets cookies and sends data to Google, so it needs a consent notice, CSP exceptions and a
  rewrite of the privacy page ("no cross-site tracking" stops being true). Cloudflare Web Analytics is already wired
  in and needs none of that.
