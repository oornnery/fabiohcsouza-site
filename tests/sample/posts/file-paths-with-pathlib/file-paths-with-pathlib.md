---
title: File paths with pathlib
summary: Read a folder, split extensions and build paths without scattering slashes
  through the code.
created: 2026-08-31
updated: 2026-08-31
status: published
type: tutorial
topic: Python
tags:
- Python
- Linux
read: 1
---

```python paths.py
from pathlib import Path

base = Path("data")
for file in base.glob("*.csv"):
    print(file.stem, file.suffix)

out = base / "processed" / "summary.txt"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("ok")
```

The `/` operator builds the right path on any system, and `stem` and `suffix` split name and extension without slicing strings.
