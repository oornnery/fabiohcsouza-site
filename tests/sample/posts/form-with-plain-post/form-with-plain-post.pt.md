---
title: Um formulário com POST comum, sem JavaScript
summary: O navegador já sabe enviar um formulário. A rota valida, grava e redireciona;
  o JavaScript só entra depois, se fizer falta.
---

## O formulário

O HTML abaixo já funciona sozinho. O `name` de cada campo vira a chave que a rota recebe, e `required` faz o navegador barrar o envio vazio.

```html templates/novo.html
<form method="post" action="/items">
  <label>Nome <input name="name" required maxlength="80"></label>
  <button>Salvar</button>
</form>
```

## A rota

`Form()` lê o corpo enviado pelo navegador. Depois de gravar, a rota responde com um redirecionamento 303: se a pessoa recarregar a página, o formulário não é enviado de novo.

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

## Teste pelo terminal

```bash Terminal
curl -i -d "name=Caderno" http://127.0.0.1:8000/items
curl -i -d "" http://127.0.0.1:8000/items
```

A primeira chamada devolve 303 com o cabeçalho `location`. A segunda devolve 422, porque o campo obrigatório não veio.
