---
title: Running commands without building a giant string
summary: Arguments, output and exit code when calling another program from Python.
created: 2026-08-30
updated: 2026-08-30
status: published
type: article
topic: Python
tags:
- Python
- Shell
- Linux
read: 1
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

Passing a list of arguments avoids trouble with spaces and quotes, and you don't need `shell=True`. `returncode` tells you whether it worked; `stdout` and `stderr` hold the output.
