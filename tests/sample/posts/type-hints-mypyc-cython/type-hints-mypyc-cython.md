---
title: Type hints don't speed Python up. Compiling with them does
summary: The same three algorithms in plain Python, typed Python compiled with mypyc
  and Cython with C types, actually measured and explained one by one.
created: 2026-10-02
updated: 2026-10-02
tags:
- python
- mypyc
- cython
- performance
- benchmark
read: 9
---

Annotating `n: int` doesn't make CPython faster. The interpreter reads the
annotation and ignores it. The useful question is a different one: what changes
when a tool **uses** that information to generate code?

I set up an experiment with three versions of the same algorithms:

1. Python without types.
2. Python with type hints, compiled with **mypyc**.
3. **Cython** with C types (`cdef`, `cpdef`).

Every number in this post comes from my own runs, described at the end. Where I
only have a hypothesis, I say it's a hypothesis.

## The three algorithms

Each one stresses something different, and that's what makes the comparison
interesting:

- `fib(35)`: pure recursion, 29,860,703 function calls. The cost is the call.
- `work(20_000_000)`: an integer arithmetic loop, with multiplication and modulo
  by constants.
- `count_primes(200_000)`: a loop with division by a divisor that changes on
  every turn, 7,167,463 iterations of the `while`.

## The code

The untyped version:

```python
# python_impl.py
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)


def work(n):
    total = 0
    for i in range(n):
        total += (i % 1000) * (i % 997)
        total %= 1_000_003
    return total


def count_primes(n):
    count = 0
    for x in range(2, n + 1):
        prime = True
        d = 2
        while d * d <= x:
            if x % d == 0:
                prime = False
                break
            d += 1
        if prime:
            count += 1
    return count
```

The mypyc version is a copy of the file above, `mypyc_impl.py`, changing only the
three `def` lines (the bodies stay identical):

```python
def fib(n: int) -> int:
def work(n: int) -> int:
def count_primes(n: int) -> int:
```

The Cython one swaps the Python types for C types:

```cython
# cython_impl.pyx
cpdef long long fib(int n):
    if n <= 1:
        return n

    return fib(n - 1) + fib(n - 2)


cpdef int work(int n):
    cdef int total = 0
    cdef int i

    for i in range(n):
        total += (i % 1000) * (i % 997)
        total %= 1000003

    return total


cpdef int count_primes(int n):
    cdef int count = 0
    cdef int x
    cdef int d
    cdef bint prime

    for x in range(2, n + 1):
        prime = True
        d = 2

        while d * d <= x:
            if x % d == 0:
                prime = False
                break

            d += 1

        if prime:
            count += 1

    return count
```

And the benchmark. Each function runs once to warm up and then five times; the
median counts. The line with `module.__file__` is mine, and I'll explain shortly
why it's there.

```python
# bench.py
import importlib
import statistics
import sys
import time

CASES = {
    "fib": 35,
    "work": 20_000_000,
    "count_primes": 200_000,
}


def benchmark(module_name: str) -> None:
    module = importlib.import_module(module_name)

    print(f"\n{module_name}  <- {module.__file__}")
    print("=" * 50)

    for name, argument in CASES.items():
        fn = getattr(module, name)
        fn(argument)  # warm-up

        times = []
        result = None
        for _ in range(5):
            start = time.perf_counter()
            result = fn(argument)
            times.append(time.perf_counter() - start)

        print(f"{name:16} result={result:<12} median={statistics.median(times):.6f}s")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python bench.py MODULE")
        sys.exit(1)

    benchmark(sys.argv[1])
```

## Setting up the environment

You need a C compiler (on Arch, `sudo pacman -S base-devel`).

```bash
uv init --bare
printf '\n[tool.setuptools]\npy-modules = []\n' >> pyproject.toml
uv add --dev "mypy[mypyc]" cython

uv run mypyc mypyc_impl.py
uv run cythonize -i cython_impl.pyx

uv run python bench.py python_impl
uv run python bench.py mypyc_impl
uv run python bench.py cython_impl
```

### The trap that invalidates the experiment

The full `uv init` (without `--bare`) creates a `src/` layout, and mypyc leaves
the `.so` inside `src/`. But `bench.py` runs with the project folder at the front
of `sys.path`, where `mypyc_impl.py` is. Result: Python imports the **`.py`
file**, and the benchmark called "mypyc" measures plain Python without any
warning. That's exactly what happened when I followed the original recipe.

I only noticed because I printed `module.__file__`. The fix is to keep the `.so`
next to the `.py`: when both are in the same folder, Python prefers the compiled
extension over the source. Hence `--bare`. And `py-modules = []` is there
because, without it, setuptools looks at the folder full of loose modules and
aborts with `Multiple top-level modules discovered in a flat-layout`.

If your `__file__` ends in `.py` in the mypyc test, you're not measuring mypyc
yet.

## Results

Median of 5 runs, plus one warm-up. The three modules return the same result
(`9227465`, `717644` and `17984`), so they're computing the same thing.

|                         |  Python |             mypyc |            Cython |
| ----------------------- | ------: | ----------------: | ----------------: |
| `fib(35)`               | 1.356 s | 0.073 s (**19×**) | 0.016 s (**86×**) |
| `work(20_000_000)`      | 2.363 s | 0.088 s (**27×**) | 0.059 s (**40×**) |
| `count_primes(200_000)` | 0.496 s | 0.034 s (**15×**) | 0.035 s (**14×**) |

Environment: Ryzen 7 5700U on WSL2, Python 3.13.14, mypy 2.4.0 (compiled),
Cython 3.3.0, the system gcc. A second round in the same session came within 7%
of the first. A third, later on, came out 25% to 55% slower for the compiled
versions (I didn't rerun plain Python in it). It's a laptop: treat the absolute
values as an order of magnitude and look at the ratios.

### Control: type hints only

To separate "having types" from "compiling with types", I ran the annotated file
as regular Python, without compiling:

|                         |         Python | type hints only |
| ----------------------- | -------------: | --------------: |
| `fib(35)`               | 1.30 to 1.36 s |         1.338 s |
| `work(20_000_000)`      | 2.36 to 2.37 s |         2.355 s |
| `count_primes(200_000)` | 0.49 to 0.50 s |         0.494 s |

Identical. All of the gain in the second scenario comes from the compilation that
uses the types.

## Why each benchmark gives a different result

Dividing the time by each algorithm's work makes the comparison clearer:

| cost per unit                    | Python |  mypyc | Cython |
| -------------------------------- | -----: | -----: | -----: |
| `fib`, per call                  |  45 ns | 2.4 ns | 0.5 ns |
| `work`, per iteration            | 118 ns | 4.4 ns | 2.9 ns |
| `count_primes`, per `while` turn |  69 ns | 4.8 ns | 4.9 ns |

(In `count_primes` the time includes the outer loop, which is about 3% of the
turns.)

### `fib`: Cython pulls almost 5× ahead of mypyc

Here the cost is almost entirely the function call. mypyc replaces the
interpreter's call with a native call, and that alone is worth 19×. But the C it
generates still uses Python integers (`CPyTagged_Add`, `CPyTagged_Subtract`...),
with the tag and overflow checks that requires on every operation.

In Cython, `fib` is a pure C function over `long long`, with nothing from Python
in between. To find out how much of that gain is the C compiler's doing, I
compiled the same `.pyx` with `CFLAGS=-O0`: `fib` went to **0.115 s**, slower than
mypyc. So most of the 0.016 s is gcc optimizing a recursion it can see in full. I
didn't read the assembly, so I can't say which exact optimization it applied.

### `work`: the gap drops to 1.5×

The loop is the same, but now there are no calls to save. mypyc generates
`CPyTagged_Multiply` and `CPyTagged_Remainder`, each with a fast path for small
integers and a way out for big ones. Cython generates plain C `int` arithmetic.

I suspected that the semantics of Python's `%` (the remainder takes the divisor's
sign) were part of the cost in Cython, which emits `__Pyx_mod_long` by default. I
tested with `# cython: cdivision=True`: 0.067 s against 0.057 s, no real
difference. `%` isn't the explanation.

### `count_primes`: a tie

Here both compiled versions land at around 4.8 ns per turn, and Cython gains
nothing over mypyc. My reading, which I **haven't verified** with a profiler or
disassembly: the loop's cost is dominated by `x % d`, where `d` varies and can't
be replaced by a multiplication. That becomes a hardware division, which costs the
same whatever the integer's representation. The extra work of declaring C types
bought nothing in this case, while mypyc delivered 15× without touching the
function's body.

## What C types cost

The comparison above is fair on speed, but the two `int`s aren't the same `int`. I
tested with a one-line function in each tool:

```python
# mypyc
def mul(a: int, b: int) -> int:
    return a * b
```

```cython
# cython
cpdef int mul(int a, int b):
    return a * b
```

| call                    |                    Python |                     mypyc |          Cython |
| ----------------------- | ------------------------: | ------------------------: | --------------: |
| `mul(100_000, 100_000)` |               10000000000 |               10000000000 |  **1410065408** |
| `mul(2**40, 2**40)`     | 1208925819614629174706176 | 1208925819614629174706176 | `OverflowError` |

mypyc's `int` is still Python's `int`, with arbitrary precision. Cython's `int` is
32 bits: it silently overflows inside the computation (the 1410065408 above) and
rejects arguments that are too big on the way in.

In the benchmark both agree because the values fit in 32 bits (the largest
intermediate in `work` stays around 2 million). But that's now an invariant you
have to guarantee, and the compiler won't check it for you.

There's also an ergonomic cost. The mypyc file is still valid Python, and the
control above shows it runs on CPython without compiling. A `.pyx` isn't Python:
without compiling, it doesn't run.

## What I'd do with this

- **Already have typed code checked with mypy?** Try mypyc first. The cost is
  close to zero and the semantics don't change.
- **Have a hot numeric loop, need C integers, typed arrays or calls into C
  libraries?** Then Cython pays for itself, and `fib` shows the ceiling.
- **Before either of them, measure.** And check `__file__`.

A note on how far this goes: integer arithmetic loops are the best possible case
for both. In code that spends its time on strings, lists and objects, the gain is
usually much smaller than the 14× to 86× in the table. This post shows what each
tool can do when the type is all that matters, not what you'll gain in your own
code.
