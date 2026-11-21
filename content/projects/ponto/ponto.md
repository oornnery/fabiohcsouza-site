---
title: ponto
kind: open_source
year: 2026
summary: A CLI for Secullum Ponto Web, a time-tracking system.
tags: [python, cli, typer, automation]
repo: https://github.com/oornnery/ponto
updated: 2026-09-11
---

Uses the Secullum employee portal (Central do Funcionário) from the terminal: the timesheet, adjustments and
justifications, without opening the browser.

## Commands

- `ponto status` shows the timesheet for a period. Times still waiting for approval are marked, so they don't pass
  for real punches.
- `ponto adjust` fills the days that need an adjustment. With `--dry-run` it shows the plan first; weekends,
  holidays, days off and days with a pending request are skipped.
- `ponto justify` lists the reasons and files a justification for a day.
- `ponto requests` shows the requests already sent.
- `--json` writes only JSON, for scripts.

## How it is built

Python with Typer for the commands, Rich for the tables and httpx for the portal's API. The settings come from flags,
the environment, a `.env` or a TOML file that `ponto setup` writes. The tests run against a fake of the API.
