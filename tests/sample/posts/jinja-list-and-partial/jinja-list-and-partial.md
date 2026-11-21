---
title: A Jinja list and a reused piece of template
summary: The route hands over the data, the template builds the list and a macro avoids
  repeating the same item on two pages.
created: 2026-10-12
updated: 2026-10-12
status: published
type: guide
topic: Python
tags:
- Python
- Jinja
- HTML
- Web
read: 2
series: python-meets-the-web
part: 3
---

## The route hands over the data

The route builds no HTML. It passes the list to the template and returns the result.

```python main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates("templates")
items = ["Notebook", "Pen"]


@app.get("/items")
def index(request: Request):
    return templates.TemplateResponse(request, "items.html", {"items": items})
```

## The template builds the list

The `else` of the `for` covers the empty list, the case most often left untested.

```jinja templates/items.html
{% from "item.html" import item %}
<ul>
{% for name in items %}
  {{ item(name) }}
{% else %}
  <li>Nothing here yet.</li>
{% endfor %}
</ul>
```

## The item becomes a macro

With the item in a single file, the search page and the home page use the same HTML.

```jinja templates/item.html
{% macro item(name) %}
  <li>{{ name }}</li>
{% endmacro %}
```

Jinja escapes `{{ name }}` by default: a name with `<script>` shows up as text.
