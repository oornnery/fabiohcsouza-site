---
title: Link or button? Start with what the person will do
summary: A practical review of semantics, focus and keyboard navigation in page components.
created: 2026-09-05
updated: 2026-09-05
status: published
type: tutorial
topic: HTML
tags:
- HTML
- Acessibilidade
- Componentes
read: 2
---

## The rule

If the action takes you somewhere else, it's a link. If it changes something on the page or sends data, it's a button. The looks come later, in CSS.

```html example.html
<a href="/posts">See all posts</a>
<button type="button" aria-expanded="false">Open menu</button>
```

## Test with the keyboard

- `Tab` has to reach both.
- `Enter` activates the link; `Enter` and `Space` activate the button.
- Focus has to stay visible in both cases.

A `div` with `onclick` fails every one of these tests. Starting with the right element solves it for free.
