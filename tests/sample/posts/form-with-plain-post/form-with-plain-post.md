---
title: A form with a plain POST, no JavaScript
summary: The browser already knows how to send a form. The route validates, saves
  and redirects; JavaScript comes later, if it's missed.
created: 2026-10-05
updated: 2026-10-05
status: published
type: guide
topic: Python
tags:
- Python
- FastAPI
- HTML
- Web
read: 2
series: python-meets-the-web
part: 2
---

## The form

The HTML below works on its own. Each field's `name` becomes the key the route receives, and `required` makes the browser block an empty submit.

```html templates/new.html
<form method="post" action="/items">
  <label>Name <input name="name" required maxlength="80"></label>
  <button>Save</button>
</form>
```

## The route

`Form()` reads the body sent by the browser. After saving, the route answers with a 303 redirect: if the person reloads the page, the form is not sent again.

```python main.py
from typing import Annotated

from fastapi import FastAPI, Form
from fastapi.responses import RedirectResponse

app = FastAPI()
items: list[str] = []


@app.post("/items")
def create(name: Annotated[str, Form(max_length=80)]):
    items.append(name)
    return RedirectResponse("/items", status_code=303)
```

## Test it from the terminal

```bash Terminal
curl -i -d "name=Notebook" http://127.0.0.1:8000/items
curl -i -d "" http://127.0.0.1:8000/items
```

The first call returns 303 with the `location` header. The second returns 422, because the required field is missing.
