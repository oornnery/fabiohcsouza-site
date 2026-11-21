---
title: Uma rota FastAPI, do código à resposta HTTP
summary: Um exemplo pequeno para seguir o caminho da requisição, validar a entrada
  e testar a resposta pelo terminal.
---

## Introdução

Antes de adicionar banco de dados, autenticação e uma pasta para cada camada, vale seguir uma requisição do início ao fim. Neste exemplo, uma rota recebe um número, procura um item e devolve uma resposta HTTP.

O objetivo é deixar três coisas visíveis: o que entra, onde o código toma uma decisão e o que chega ao cliente. Tudo cabe em um arquivo.

## Monte um exemplo pequeno

Crie um ambiente Python e instale o FastAPI com os extras usados pelo servidor de desenvolvimento. Use uma pasta separada para poder mudar o exemplo sem afetar outro projeto.

```bash Terminal
python -m venv .venv
# Linux e macOS:
source .venv/bin/activate
# No PowerShell, use: .venv\Scripts\Activate.ps1
python -m pip install "fastapi[standard]"
``` 

Agora crie o `main.py`. O dicionário abaixo funciona como uma pequena coleção em memória; os dados voltam ao estado inicial quando o processo reinicia.

## Escreva o contrato da rota

O caminho identifica o recurso. A anotação `item_id: int` define a entrada esperada. O cliente recebe um objeto quando o item existe e uma resposta de erro quando não é encontrado.

```python main.py
from fastapi import FastAPI, HTTPException

app = FastAPI()

items = {
    1: {"id": 1, "name": "Caderno do lab"},
}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    item = items.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item
``` 

### Por que devolver um erro diferente?

Um identificador válido pode apontar para um item que não existe. Isso é diferente de mandar texto onde a rota espera um número. Testando os dois casos, você enxerga a diferença entre validar a entrada e encontrar o recurso.

## Veja a resposta no terminal

Suba o servidor em um terminal e faça as requisições em outro. A opção `-i` do curl inclui os cabeçalhos na saída, então dá para conferir o status além do corpo.

```bash Terminal · servidor
fastapi dev main.py
``` 

```bash Terminal · requisições
curl -i http://127.0.0.1:8000/items/1
curl -i http://127.0.0.1:8000/items/999
curl -i http://127.0.0.1:8000/items/abc
``` 

Compare as três respostas. Na primeira, o corpo traz o item. Na segunda, o recurso não existe. Na terceira, a entrada não bate com o tipo que a rota espera.

## O próximo passo depende do problema

Se a aplicação precisa manter dados depois de reiniciar, o próximo passo pode ser um banco de dados. Se outros sistemas vão consumir a rota, vale também definir um modelo explícito para a saída. Escolha uma dessas mudanças e repita as requisições para ver o que mudou no contrato.

Para continuar: [o tutorial oficial do FastAPI](https://fastapi.tiangolo.com/tutorial/).
