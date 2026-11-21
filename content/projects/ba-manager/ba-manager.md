---
title: BA Manager
kind: work
year: 2026
updated: 2026-11-17
summary: A system I wrote from scratch to handle interconnection fault reports (BAs), integrated with Jira and e-mail.
tags: [python, fastapi, preact, jira, automation, telecom]
---

A BA (Boletim de Anormalidade) is how Brazilian carriers report a fault on the interconnection between their
networks, through the [ABR Telecom system](https://www.abrtelecom.com.br/servicos/outras-solucoes/ba%27s-de-interconexao). I wrote this system from scratch to handle those reports.

It stays in sync with ABR through its SOAP web service. BAs are opened, changed and closed from the platform, with
presets and message templates that fill in the text. Each BA that arrives opens an issue in Jira; the two stay linked
and share comments.

Automations are built in a drag-and-drop editor: a trigger, conditions and actions connected as a graph. A rule runs
on an event or on a schedule, can be previewed before it is saved and keeps the history of every run. A failed run
sends an alert. Escalation follows the SLA of each BA, and notices go out by e-mail and Slack.

The dashboard has charts of the BAs, the SLA and response times, and the lists export to reports. Admins manage users
and areas, which set the services each user can see, and have an audit log, the application logs and backups.

The backend is FastAPI with SQLModel and Alembic. The interface is Preact and TypeScript, with charts in ECharts and
the automation editor in React Flow.
