---
title: Type hints não aceleram Python. Compilar com eles, sim
summary: Os mesmos três algoritmos em Python puro, Python tipado compilado com mypyc
  e Cython com tipos de C, medidos de verdade e explicados um a um.
---

Anotar `n: int` não deixa o CPython mais rápido. O interpretador lê a anotação e
a ignora. A pergunta útil é outra: o que muda quando uma ferramenta **usa** essa
informação para gerar código?

Montei um experimento com três versões dos mesmos algoritmos:

1. Python sem tipos.
2. Python com type hints, compilado com **mypyc**.
3. **Cython** com tipos de C (`cdef`, `cpdef`).

Todos os números deste post vêm de execuções minhas, descritas no final. Onde eu
só tenho uma hipótese, digo que é hipótese.

## Os três algoritmos

Cada um estressa uma coisa diferente, e é isso que torna a comparação
interessante:

- `fib(35)`: recursão pura, 29.860.703 chamadas de função. O custo é a chamada.
- `work(20_000_000)`: um laço de aritmética inteira, com multiplicação e módulo
  por constantes.
- `count_primes(200_000)`: um laço com divisão por um divisor que muda a cada
  volta, 7.167.463 iterações do `while`.

## O código

A versão sem tipos:

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

A versão do mypyc é uma cópia do arquivo acima, `mypyc_impl.py`, trocando apenas
as três linhas `def` (os corpos ficam idênticos):

```python
def fib(n: int) -> int:
def work(n: int) -> int:
def count_primes(n: int) -> int:
```

A do Cython troca os tipos Python por tipos de C:

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

E o benchmark. Cada função roda uma vez para aquecer e depois cinco vezes; vale a
mediana. A linha com `module.__file__` é minha e já explico por que ela existe.

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

## Montando o ambiente

Precisa de um compilador C (no Arch, `sudo pacman -S base-devel`).

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

### A armadilha que invalida o experimento

O `uv init` completo (sem `--bare`) cria um layout `src/`, e o mypyc deixa o `.so`
dentro de `src/`. Só que o `bench.py` roda com a pasta do projeto na frente do
`sys.path`, onde está o `mypyc_impl.py`. Resultado: o Python importa o **arquivo
`.py`**, e o benchmark chamado "mypyc" mede Python puro sem avisar nada. Foi
exatamente isso que aconteceu quando segui a receita original.

Só percebi porque imprimi `module.__file__`. A saída é deixar o `.so` ao lado do
`.py`: quando os dois estão na mesma pasta, o Python prefere a extensão
compilada ao código-fonte. Por isso o `--bare`. E o `py-modules = []` existe
porque, sem ele, o setuptools olha a pasta cheia de módulos soltos e aborta com
`Multiple top-level modules discovered in a flat-layout`.

Se o seu `__file__` terminar em `.py` no teste do mypyc, você ainda não está
medindo o mypyc.

## Resultados

Mediana de 5 execuções, mais um aquecimento. Os três módulos devolvem o mesmo
resultado (`9227465`, `717644` e `17984`), então estão calculando a mesma coisa.

|                         |  Python |             mypyc |            Cython |
| ----------------------- | ------: | ----------------: | ----------------: |
| `fib(35)`               | 1,356 s | 0,073 s (**19×**) | 0,016 s (**86×**) |
| `work(20_000_000)`      | 2,363 s | 0,088 s (**27×**) | 0,059 s (**40×**) |
| `count_primes(200_000)` | 0,496 s | 0,034 s (**15×**) | 0,035 s (**14×**) |

Ambiente: Ryzen 7 5700U num WSL2, Python 3.13.14, mypy 2.4.0 (compilado),
Cython 3.3.0, gcc do sistema. Uma segunda rodada na mesma sessão ficou a até 7%
da primeira. Uma terceira, mais tarde, saiu entre 25% e 55% mais lenta nas
versões compiladas (não repeti o Python puro nela). É um notebook: trate os
valores absolutos como ordem de grandeza e olhe as proporções.

### Controle: só os type hints

Para separar "ter tipos" de "compilar com tipos", rodei o arquivo anotado como
Python comum, sem compilar:

|                         |        Python | só type hints |
| ----------------------- | ------------: | ------------: |
| `fib(35)`               | 1,30 a 1,36 s |       1,338 s |
| `work(20_000_000)`      | 2,36 a 2,37 s |       2,355 s |
| `count_primes(200_000)` | 0,49 a 0,50 s |       0,494 s |

Idêntico. Todo o ganho do segundo cenário vem da compilação que usa os tipos.

## Por que cada benchmark dá um resultado

Dividir o tempo pelo trabalho de cada algoritmo deixa a comparação mais clara:

| custo por unidade                    | Python |  mypyc | Cython |
| ------------------------------------ | -----: | -----: | -----: |
| `fib`, por chamada                   |  45 ns | 2,4 ns | 0,5 ns |
| `work`, por iteração                 | 118 ns | 4,4 ns | 2,9 ns |
| `count_primes`, por volta do `while` |  69 ns | 4,8 ns | 4,9 ns |

(No `count_primes` o tempo inclui o laço externo, que é cerca de 3% das voltas.)

### `fib`: o Cython abre quase 5× sobre o mypyc

Aqui o custo é quase só a chamada de função. O mypyc troca a chamada do
interpretador por uma chamada nativa, e isso já vale 19×. Mas o C que ele gera
continua usando inteiros do Python (`CPyTagged_Add`, `CPyTagged_Subtract`...),
com a checagem de tag e de overflow que isso exige a cada operação.

No Cython, `fib` é uma função C pura sobre `long long`, sem nada de Python no
meio. Para saber quanto desse ganho é mérito do compilador C, compilei o mesmo
`.pyx` com `CFLAGS=-O0`: o `fib` foi para **0,115 s**, mais lento que o mypyc.
Ou seja, a maior parte dos 0,016 s é o gcc otimizando uma recursão que ele
consegue enxergar por inteiro. Não li o assembly, então não sei dizer qual
otimização exata ele aplicou.

### `work`: a diferença cai para 1,5×

O laço é o mesmo, mas agora não há chamadas para economizar. O mypyc gera
`CPyTagged_Multiply` e `CPyTagged_Remainder`, cada um com um caminho rápido para
inteiros pequenos e uma saída para inteiros grandes. O Cython gera aritmética de
`int` de C direto.

Eu suspeitava que a semântica do `%` do Python (resto com sinal de divisor) fosse
parte do custo no Cython, que por padrão emite `__Pyx_mod_long`. Testei com
`# cython: cdivision=True`: 0,067 s contra 0,057 s, sem diferença real. O `%` não
é a explicação.

### `count_primes`: empate

Aqui os dois compilados cravam em torno de 4,8 ns por volta e o Cython não
ganha nada sobre o mypyc. Minha leitura, que **não verifiquei** com profiler nem
com disassembly: o custo do laço é dominado pelo `x % d`, em que `d` varia e não
dá para trocar por multiplicação. Isso vira uma divisão de hardware, que custa o
mesmo qualquer que seja a representação do inteiro. O trabalho extra de declarar
tipos de C não comprou nada neste caso, enquanto o mypyc entregou 15× sem tocar
no corpo da função.

## O que os tipos de C custam

A comparação acima é justa em velocidade, mas os dois `int` não são o mesmo `int`.
Testei com uma função de uma linha em cada ferramenta:

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

| chamada                 |                    Python |                     mypyc |          Cython |
| ----------------------- | ------------------------: | ------------------------: | --------------: |
| `mul(100_000, 100_000)` |               10000000000 |               10000000000 |  **1410065408** |
| `mul(2**40, 2**40)`     | 1208925819614629174706176 | 1208925819614629174706176 | `OverflowError` |

O `int` do mypyc continua sendo o `int` do Python, de precisão arbitrária. O `int`
do Cython tem 32 bits: estoura em silêncio dentro da conta (o 1410065408 acima) e
recusa argumentos grandes demais na entrada.

No benchmark os dois concordam porque os valores cabem em 32 bits (o maior
intermediário do `work` fica perto de 2 milhões). Só que isso agora é um
invariante que você precisa garantir, e que o compilador não vai checar por você.

Há ainda um custo de ergonomia. O arquivo do mypyc continua sendo Python válido, e
o controle acima mostra que ele roda no CPython sem compilar. Um `.pyx` não é
Python: sem compilar, não roda.

## O que eu faria com isso

- **Já tem código tipado e checado com mypy?** Tente o mypyc primeiro. O custo é
  quase nulo e a semântica não muda.
- **Tem um laço numérico quente, precisa de inteiros de C, de arrays tipados ou de
  chamar bibliotecas em C?** Aí o Cython se paga, e o `fib` mostra o teto.
- **Antes de qualquer um dos dois, meça.** E confira o `__file__`.

Um aviso sobre o alcance disso: laços de aritmética inteira são o melhor caso
possível para os dois. Em código que gasta o tempo com strings, listas e objetos,
o ganho costuma ser bem menor do que os 14× a 86× da tabela. Este post mostra o
que cada ferramenta consegue fazer quando o tipo é tudo o que importa, e não o
que você vai ganhar no seu código.
