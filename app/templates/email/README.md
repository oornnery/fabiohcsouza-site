E-mail texts. First line `Subject: …`, then a blank line, then the body. Rendered by `app.utils.mail.compose()` with
Jinja (no autoescape: plain text, never HTML; the values are validated at the form boundary, see app/core/forms.py).

- lead.txt: a contact message, to the owner, in English (app.api.routes.contact).
- confirm.txt, post.txt: to newsletter subscribers, in their language (app.api.routes.newsletter).
