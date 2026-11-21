---
title: Rodando comandos sem montar uma string gigante
summary: Argumentos, saída e código de retorno ao chamar outro programa a partir do
  Python.
---

```python run.py
import subprocess

r = subprocess.run(
    ["ping", "-c", "3", "8.8.8.8"],
    capture_output=True, text=True,
)
print(r.returncode)
print(r.stdout)
```

Passando a lista de argumentos, você evita problemas com espaços e aspas e não precisa de `shell=True`. O `returncode` diz se deu certo; `stdout` e `stderr` trazem a saída.
