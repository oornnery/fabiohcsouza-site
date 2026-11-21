# fabiohcsouza.dev

[English](README.md) · **Português**

Meu portfólio e posts do blog.

| Site | Domínio |
| --- | --- |
| Portfólio profissional | [fabiohcsouza.dev](https://fabiohcsouza.dev) |
| Blog: notas sobre assuntos que me interessam: VoIP, redes, automação, laboratórios, desenvolvimento e IA | [blog.fabiohcsouza.dev](https://blog.fabiohcsouza.dev) |

![A home do portfólio](docs/screenshots/home-light.png)

<p>
  <img src="docs/screenshots/projects-dark.png" alt="Projetos" width="49%">
  <img src="docs/screenshots/project-light.png" alt="A página de um projeto" width="49%">
</p>
<p>
  <img src="docs/screenshots/blog-home-dark.png" alt="A home do blog, com a newsletter" width="49%">
  <img src="docs/screenshots/blog-post-light.png" alt="Um post com sumário e série" width="49%">
</p>
<p>
  <img src="docs/screenshots/blog-post-mobile-dark.png" alt="Um post em português no celular" width="24%">
</p>

Os prints do blog usam os posts de exemplo de `tests/sample/`.

Python 3.14 e FastAPI geram todas as páginas no servidor com Jinja2. Páginas, projetos e posts são pastas de
Markdown em `content/`. O SQLite guarda as mensagens de contato e a newsletter, e os e-mails saem por SMTP.

## Rodar

```bash
uv sync
```

```bash
uv run task dev
```

Abra http://portfolio.localhost:8000 e http://blog.localhost:8000 (`*.localhost` aponta para a sua máquina); o
português fica em `/pt/`. Para mudar uma configuração, ponha essa linha num `.env` (o `.env.example` lista todas, com os valores de produção). Com Docker:
`docker compose -f docker/compose.dev.yml up --build`.

## Comandos

`uv run python -m app <comando>`

| Comando | O que faz |
| --- | --- |
| `serve [--reload]` | roda os sites |
| `leads [--last N]`, `stats` | mensagens de contato |
| `subscribers` | assinantes da newsletter |
| `send-post <slug> [--send]` | manda um post publicado para os assinantes (sem `--send`, só mostra o que sairia) |
| `projects-dates` | põe em cada projeto a data do último commit no GitHub (`updated`) |
| `images` | gera um WebP mais leve ao lado de cada PNG/JPEG em `content/` |
| `i18n` | junta os textos da interface no catálogo em português |
| `purge` | aplica agora as regras de retenção de dados |

## Tarefas

`uv run task <tarefa>` (taskipy; `uv run task --list` mostra todas)

| Tarefa | O que faz |
| --- | --- |
| `dev` | roda os dois sites com reload |
| `check` | tudo o que o CI confere: `lint`, `types`, `sec`, `templates`, `test` |
| `lint`, `types`, `sec`, `templates`, `test` | Ruff, ty, Bandit, djLint e pytest, um por vez |
| `audit` | vulnerabilidades conhecidas nos pacotes instalados |
| `i18n` | junta os textos da interface no catálogo em português |

## Estrutura

```
app/main.py     o app: middleware, um sub-app por site, a limpeza diária
app/api/        rotas (portfolio, blog, contact, newsletter, seo), dependências, o registro de páginas
app/core/       configuração, banco, segurança (middleware, limites, Turnstile), i18n
app/models.py   tabelas e entrada dos formulários        app/crud.py   leituras e gravações
app/content/    lê o content/: páginas, projetos, posts
app/utils/      Markdown, e-mail, renderização, JSON-LD
app/templates/  templates Jinja; app/locales/ o catálogo em português
content/        páginas, projetos e posts, uma pasta cada, imagens no assets/; site.yml
app/static/     CSS, JavaScript, fontes, ícones
docker/         Dockerfile, compose.yml (produção), compose.dev.yml
.env.example    todas as configurações, com os valores de produção
tests/          pytest, com posts de exemplo em tests/sample/
```

## Documentação

- [Content](docs/content.md): como escrever páginas, projetos e posts, com imagens
- [Deploy](docs/deploy.md): produção, um site ou os dois, atualizações, backup
- [Development](docs/development.md): testes, tradução, depuração
- [Architecture](docs/architecture.md): como uma requisição é atendida e onde fica cada parte do código
- [Rules](docs/business-rules.md): contato, newsletter, retenção de dados, limites
- [Security](docs/security.md) · [Design](docs/design.md)
- [TODO](TODO.md): o que pode vir depois (webhook, fila de envio, observabilidade)
