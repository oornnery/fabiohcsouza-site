---
title: Blog and portfolio
summary: This site. Posts, projects and résumé in Portuguese and English, served by
  a single Python process behind a Cloudflare Tunnel.
created: 2026-09-30
updated: 2026-09-30
status: published
type: project
topic: Python
tags:
- Python
- FastAPI
- Jinja
- Preact
- SQLite
- Docker
- Cloudflare
- Projetos
stage: Em andamento
tech:
- Python
- FastAPI
- Jinja
- Preact
- SQLite
- Docker
- Cloudflare
goal: A place to write, show projects and get in touch, simple to maintain and to
  run on a VPS.
---

## The project

Blog, projects and an About page in a single FastAPI app, with Jinja2 templates and a Preact admin to edit everything in Portuguese and English.

## How it works

- Every page is server-rendered HTML and works without JavaScript. The carousel, filters, reactions and contact form are islands loaded when they come into view.
- Content starts as Markdown with frontmatter, is imported into SQLite and can go back to Markdown with one command.
- Every page has a Markdown copy, and the site has an `llms.txt` for agents to read.
- The contact form saves to the database and sends a notification through Resend.

## In production

Docker on the VPS, with the app exposing no ports and `cloudflared` next to it. The container runs unprivileged, with a read-only file system and memory and CPU limits.

## Goal

A place to write, show projects and get in touch, simple to maintain and to run on a VPS.

## Decisions

- Server-rendered HTML; JavaScript only in Preact islands where the page needs interaction.
- SQLite on a Docker volume, with consistent backups made by the app itself.
- No published ports: traffic arrives through the Cloudflare Tunnel.
- Strict CSP, per-IP rate limiting and an admin session with a hashed password.
