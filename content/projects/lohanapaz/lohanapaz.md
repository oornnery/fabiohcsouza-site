---
title: Lohana Paz website
kind: work
summary: Landing page that presents Lohana Paz's advertising work and brings clients to WhatsApp. Static Astro on Cloudflare.
tags: [astro, typescript, cloudflare, web]
site: https://lohanapaz.com
year: 2026
updated: 2026-10-23
---

The website of Lohana Paz, who works in advertising: a single page in Portuguese with who she is, her services, her
work, how a project goes and a way to talk to her on WhatsApp.

![The home page](assets/home.png)

## How it is built

Astro renders the whole page to HTML at build time. Each section is a component with its own CSS and a small
TypeScript script for what moves: the menu, the work carousel, the project modal and the animations. The copy and the
projects are JSON files in content collections, checked with zod, and the images are resized and hashed at build.

Cloudflare serves the files from a Worker's static assets. The only code that runs on the server is one route that
records clicks in Analytics Engine, with an origin check and a rate limit. Visits come from Cloudflare Web Analytics,
and Google Ads only loads after the visitor accepts cookies.

Each push runs type checks, tests and the build on GitHub Actions, and Cloudflare deploys the Worker.

![The page on a phone](assets/mobile.png)
