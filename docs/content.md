# Content

Everything the sites show lives in `content/`, one folder per page, project or post. English is the default
language; the Portuguese version sits next to it, and the images in the folder's `assets/`.

```
content/
  site.yml                    name, role, e-mail, socials, city
  pages/about/                about.md, about.pt.md
  pages/privacy/              privacy.md, privacy.pt.md
  projects/<slug>/            <slug>.md, <slug>.pt.md, assets/
  posts/<slug>/               <slug>.md, <slug>.pt.md, assets/
```

The folder name is the slug: the address of the page (`/projects/sipx`, `/posts/link-or-button`). Use `a-z`, `0-9`
and `-`. A broken front matter stops the app at start, and the error names the file.

## Images

Put the image in the item's `assets/` folder and write it with that path:

```markdown
![The ping view](assets/ping-tui.png)
```

It is served at `/media/projects/icmpx/ping-tui.png`, with its width and height. `python -m app images` writes a
WebP next to each PNG or JPEG, and the pages then use the WebP. The images of a draft post stay private in production.

## Projects

`content/projects/<slug>/<slug>.md`:

```markdown
---
title: sipx
summary: An async SIP library for Python, in the style of httpx.
kind: open_source            # or work (no public code)
updated: 2026-06-14          # the last commit; `python -m app projects-dates` reads it from GitHub
year: 2025                   # optional, shown when there is no updated
tags: [python, sip, voip]
repo: https://github.com/oornnery/sipx
site:                        # optional
---

The full description, shown on /projects/sipx. Markdown, with images.
```

`<slug>.pt.md` has `title`, `summary` and the Portuguese text. The summary is the short line in lists; the text below
the front matter is the project's page. Lists show Work, then Open Source, each newest first by `updated`.

## Posts

`content/posts/hello-world/` is the template: copy the folder and follow the comments in its front matter.
`content/posts/<slug>/<slug>.md`:

```markdown
---
title: A form with a plain POST
summary: One sentence for lists and the share card.
created: 2026-10-05
updated: 2026-10-20          # optional: shown as "Updated" when later than created
status: published            # without it, a draft: development only
tags: [python, fastapi]
image: assets/cover.png      # optional share image, 1200x630
series: python-meets-the-web # optional: this post is a part of that one
part: 2                      # its position in the series
project: sipx                # optional: the project it is about; both pages link to each other
---
```

`<slug>.pt.md` holds `title`, `summary` and `goal` in Portuguese, with the text. A post written only in Portuguese
has just `<slug>.pt.md`, with the whole front matter. A post shows on the portfolio only when `BLOG=true`.

## Pages

`content/pages/about/about.md` and `privacy/privacy.md`, with their `.pt.md`. In their text, `(/contact)` links to the
portfolio and `(blog:/posts)` to the blog, right in both languages.

## Interface text

Menus, buttons and messages are written in English in the templates (`{{ _("Posts") }}`) and translated in
`app/locales/pt_BR/LC_MESSAGES/messages.po`. After changing one, run `python -m app i18n`, fill in the empty
`msgstr` lines and restart the server. A test fails while a string has no translation.
