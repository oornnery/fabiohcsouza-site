# Rules

## Contact (portfolio)

- Subject (3–120), name (2–80), e-mail, phone (optional, 8+ digits), message (10–5000).
- The message is saved first, then e-mailed to `OWNER_EMAIL` with the visitor as Reply-To. If the mail server is
  down, the visitor still sees "Message received" and the message is in `leads`.
- Works with JavaScript and without it (a plain form POST, then a redirect).

## Newsletter (blog)

- Only the e-mail address, with the page's language. Subscribing sends a confirmation link; only confirmed addresses
  get posts. Subscribing again sends a new link only if the address isn't confirmed and the last one is over 10
  minutes old; the answer is always the same.
- The confirm and unsubscribe links open a page with a button; only the button acts, because mail scanners open every
  link they see. The links are signed with `SECRET_KEY` and stop working once the address is deleted.
- Posts go out only with `send-post <slug> --send`: published posts, confirmed addresses, once each, in the
  subscriber's language when the post has it.
- `NEWSLETTER=false` hides the form and answers 404 on `/subscribe`; the links in e-mails already sent keep working.
- Every post e-mail has an unsubscribe link and one-click unsubscribe for Gmail, Yahoo and Apple Mail (RFC 8058).
  Unsubscribing deletes the address at once.

## Likes (blog)

- A heart under each post and the total. Only the total is stored (`post_like`), nothing about who liked it.
- The browser remembers it liked the post (localStorage) and shows the heart filled. Without JavaScript the button is a
  plain form POST that comes back to the post.
- 20 likes per 10 minutes per IP; the CSRF check applies as for the forms.

## Data retention

Applied at start and once a day (`python -m app purge` applies it now).

| Data | Kept |
| --- | --- |
| contact messages | 2 years |
| newsletter addresses never confirmed | 7 days |
| newsletter addresses confirmed | until unsubscribed |
| rate-limit counters (by IP) | until their window ends |

No ads, no tracking across sites. Cloudflare Web Analytics counts visits without cookies when its token is set. One
cookie, `theme`, keeps the light or dark choice. The privacy page (`content/pages/privacy/`) says this to visitors:
change both together.

## Limits

- Any request: 240 a minute per IP.
- Each form: 5 per 10 minutes per IP, plus a honeypot and, when configured, Cloudflare Turnstile. If Turnstile can't
  be reached, the form is refused and the visitor is asked to try again.
- Likes: 20 per 10 minutes per IP.
- In front of it all, the Cloudflare rate-limit rule (see [deploy](deploy.md)).

## Content

- `status: published` goes live; a draft shows only in development.
- A post only in Portuguese shows in Portuguese on the English site too, with a note.
- `BLOG=false` hides every link from the portfolio to the blog.
- How to write each item: [content](content.md).
