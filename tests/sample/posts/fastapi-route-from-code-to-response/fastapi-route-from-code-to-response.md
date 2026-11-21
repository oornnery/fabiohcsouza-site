---
title: A FastAPI route, from code to HTTP response
summary: A small example to follow the request's path, validate the input and test
  the response from the terminal.
created: 2026-09-28
updated: 2026-09-28
status: published
type: guide
topic: Python
tags:
- Python
- FastAPI
- APIs
- Web
read: 3
series: python-meets-the-web
part: 1
---

## Introduction

Before adding a database, authentication and a folder for each layer, it's worth following one request from start to finish. In this example, a route receives a number, looks up an item and returns an HTTP response.

The goal is to make three things visible: what comes in, where the code makes a decision and what reaches the client. It all fits in one file.

## Build a small example

Create a Python environment and install FastAPI with the extras the development server uses. Use a separate folder so you can change the example without affecting another project.

```bash Terminal
python -m venv .venv
# Linux and macOS:
source .venv/bin/activate
# In PowerShell, use: .venv\Scripts\Activate.ps1
python -m pip install "fastapi[standard]"
```

Now create `main.py`. The dictionary below works as a small in-memory collection; the data goes back to its initial state when the process restarts.

## Write the route's contract

The path identifies the resource. The annotation `item_id: int` defines the expected input. The client gets an object when the item exists and an error response when it isn't found.

```python main.py
from fastapi import FastAPI, HTTPException

app = FastAPI()

items = {
    1: {"id": 1, "name": "Lab notebook"},
}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    item = items.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

### Why return a different error?

A valid identifier can point to an item that doesn't exist. That's different from sending text where the route expects a number. Testing both cases shows you the difference between validating the input and finding the resource.

## See the response in the terminal

Start the server in one terminal and make the requests in another. curl's `-i` option includes the headers in the output, so you can check the status as well as the body.

```bash Terminal · server
fastapi dev main.py
```

```bash Terminal · requests
curl -i http://127.0.0.1:8000/items/1
curl -i http://127.0.0.1:8000/items/999
curl -i http://127.0.0.1:8000/items/abc
```

Compare the three responses. In the first, the body holds the item. In the second, the resource doesn't exist. In the third, the input doesn't match the type the route expects.

## The next step depends on the problem

If the application needs to keep data after a restart, the next step may be a database. If other systems will consume the route, it's also worth defining an explicit model for the output. Pick one of these changes and repeat the requests to see what changed in the contract.

To keep going: [the official FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/).
