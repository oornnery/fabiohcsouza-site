# syntax=docker/dockerfile:1
# Two targets, built from the repository root:
#   prod (default)  the image CI publishes to ghcr.io: code and content inside, one site per container (SITE)
#   dev             the dependencies only; docker/compose.dev.yml mounts the code and runs both sites with --reload
# Only /data is written (the site's SQLite database). The user is not root.

FROM ghcr.io/astral-sh/uv:0.13.7 AS uv

FROM python:3.14.10-slim AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /srv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.14.10-slim AS base
RUN useradd --uid 10001 --home-dir /srv --no-create-home --shell /usr/sbin/nologin app \
 && mkdir -p /data && chown app:app /data
WORKDIR /srv
COPY --from=build /srv/.venv /srv/.venv
ENV PATH=/srv/.venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 PORT=8000 DATABASE_URL=sqlite:////data/app.sqlite
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]

FROM base AS dev
ENV ENVIRONMENT=development
CMD ["python", "-m", "app", "serve", "--reload"]

FROM base AS prod
COPY app ./app
COPY content ./content
ENV ENVIRONMENT=production
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--no-proxy-headers"]
