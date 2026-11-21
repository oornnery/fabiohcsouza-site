---
title: Python meets the web
summary: A lab of server-rendered pages with FastAPI and Jinja. Browser interactions
  come in as the page needs them.
created: 2026-09-01
updated: 2026-09-01
status: published
type: project
topic: Python
tags:
- Python
- FastAPI
- Jinja
- Web
- Projetos
stage: Exploração
tech:
- Python
- FastAPI
- Jinja
goal: Find out how far server HTML goes before a front-end framework is needed.
---

## The project

Simple server-rendered pages, starting with no JavaScript at all. Each new interaction comes in only when the page really needs it.

## How it works

- FastAPI routes return Jinja templates.
- Forms work with a plain POST before they become interactive.
- Each step becomes a post in this series.
