---
title: Uma lista em Jinja e um pedaço de template reaproveitado
summary: A rota entrega os dados, o template monta a lista e um macro evita repetir
  o mesmo item em duas páginas.
---

## A rota entrega os dados

A rota não monta HTML. Ela passa a lista para o template e devolve o resultado.

```python main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates("templates")
items = ["Caderno", "Caneta"]


@app.get("/items")
def index(request: Request):
    return templates.TemplateResponse(request, "items.html", {"items": items})
```

## O template monta a lista

O `else` do `for` cobre a lista vazia, que é o caso que mais se esquece de testar.

```jinja templates/items.html
{% from "item.html" import item %}
<ul>
{% for name in items %}
  {{ item(name) }}
{% else %}
  <li>Nada por aqui ainda.</li>
{% endfor %}
</ul>
```

## O item vira um macro

Com o item em um arquivo só, a página de busca e a página inicial usam o mesmo HTML.

```jinja templates/item.html
{% macro item(name) %}
  <li>{{ name }}</li>
{% endmacro %}
```

O Jinja escapa `{{ name }}` por padrão: um nome com `<script>` aparece como texto.
