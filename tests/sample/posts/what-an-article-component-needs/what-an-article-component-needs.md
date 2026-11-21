---
title: What does an article component really need?
summary: Title, summary and link. An exercise in separating presentation, data and
  behavior without abstracting too early.
created: 2026-09-10
updated: 2026-09-10
status: published
type: article
topic: Web
tags:
- Web
- HTML
- Componentes
read: 2
---

## The minimum

A list of articles exists so the reader can decide what to read. Three things are enough for that: a title that is a link, a short summary and metadata that helps choose.

```html article.html
<article>
  <h3><a href="/posts/fastapi-route">A FastAPI route</a></h3>
  <p>From code to HTTP response.</p>
  <time datetime="2026-09-28">Sep 28, 2026</time>
</article>
```

## What stays out, for now

- A cover image, if no post has one.
- The author, while there is only one.
- Component variations that no page uses yet.

## Separate without abstracting

The data comes from one place, the presentation is the HTML above, and the behavior (like the hover highlight) lives in CSS. Extracting a generic component is only worth it when a second page needs it.
