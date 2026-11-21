---
title: Caminhos de arquivo com pathlib
summary: Ler uma pasta, separar extensões e montar caminhos sem espalhar barras pelo
  código.
---

```python paths.py
from pathlib import Path

base = Path("dados")
for arquivo in base.glob("*.csv"):
    print(arquivo.stem, arquivo.suffix)

saida = base / "processados" / "resumo.txt"
saida.parent.mkdir(parents=True, exist_ok=True)
saida.write_text("ok")
```

O operador `/` monta o caminho certo em qualquer sistema, e `stem` e `suffix` separam nome e extensão sem fatiar strings.
