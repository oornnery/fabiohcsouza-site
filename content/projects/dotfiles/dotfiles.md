---
title: dotfiles
kind: open_source
year: 2023
summary: "My work environment: configs, scripts and the tools I use."
tags: [shell, linux, wsl, stow]
repo: https://github.com/oornnery/dotfiles
updated: 2026-11-11
---

My setup for Arch Linux on WSL, ready to go back to Arch on a desktop. Every script is safe to run again.

## How it works

A new machine is one line: clone the repo and run `bootstrap`, which installs git and GNU Stow and then applies the
machine's file. Each folder in `home/` is a config package linked into `$HOME` with Stow, and each machine has a file
that lists its tools, its config packages and its folders.

The `dots` command does the rest: `apply` makes the machine match its file, `status` shows what is missing, `doctor`
what is broken, and `migrate` runs one-time changes. It also saves package lists, switches themes and opens the
cheat sheets.

## What else is in it

The Windows side lives in the same repo: GlazeWM, YASB, Windows Terminal, PowerShell, the WSL settings and the winget
packages. There are also my AI agent configs and prompts, and compose files for the services I self-host. A test
script checks every script, also in CI.
