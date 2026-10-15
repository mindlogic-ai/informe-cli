---
name: mindlogic-design-page
description: Build a shareable page (doc, report, guide, prototype, mockup, dashboard, 구성도) and publish it behind the company login at docs.apps.mindlogic.tools. Use whenever the user asks for a page, doc, report or link to share — "docs에 올려줘", "페이지로 만들어줘", "링크로 줘", "공유해줘". "docs" means docs.apps.mindlogic.tools, not Google Docs or Notion. Plain .md for prose and tables, self-contained HTML only when it needs layout. NEVER publish claude.ai Artifacts.
---

# MindLogic Design Page

Build the page here, look at a screenshot of it, hand it to Informe to put behind the
company login, return the link. Never a claude.ai Artifact — not even "just to preview".
Installed by `inf setup`; the design standard in `references/` is the company's
`docs/DESIGN.md`, shipped with the CLI.

## 0. Destination

| Deliverable | Where |
|---|---|
| one-off doc — report, plan, guide, audit, handoff, spec, 구성도, prototype | **`docs.apps.mindlogic.tools`** (default) |
| dashboard, doc set with its own nav, scheduled refresh, running service | ask Informe for `apps publish` — needs a real reason |

Only `@mindlogic.ai` accounts can open these links. Something an outside reader must
open is a different request — say so instead of publishing.

**Ask whether it needs to be HTML at all.** The docs host renders Markdown (`name.md`
→ page, `?raw=1` for source). Prose + tables → ship a `.md`. Build HTML only when the
content needs layout: a timeline, a comparison grid, colour-coded lanes, a toggle, a 구성도.

No credentials, tokens, or customer personal data in a page.

## 1. Design standard — `references/DESIGN.md`, not your own palette

Read `references/DESIGN.md` before writing CSS, and start from the CSS in
`references/boilerplate.md` — add classes, don't replace the tokens. The short version:

- **Pick the lane first**: A 구성도 · B 지표/대시보드 · C 고객 안내물.
- **One accent, `#1F65FF`**, in ≤5 structural placements. Everything else is the neutral
  ramp. Light only: `<meta name="color-scheme" content="light">`, no dark mode.
- **Pretendard, linked** from jsdelivr. Body 13px, title 26px/700 with a 2px accent rule
  to the right edge, zone titles 15px with a hairline.
- **Mono only for strings someone would copy** (hostname, path, env var). Numbers are sans
  with `tabular-nums`.
- **Emphasis = accent tick + ink weight**, never filled blocks, a hue per zone, or
  coloured chips. Red/amber only for *state*.
- Radius 3px, 1px borders, no `box-shadow`, no gradient, no emoji.
- `word-break: keep-all`; identifiers `white-space: nowrap`.
- **Furniture**: title + subtitle + accent rule → meta line (문서 종류 · 날짜 · 작성자)
  → numbered zones (`요약`, `01`, `02`…) → 대외비 footer → `@page A4 landscape` print CSS.

Real content and real counts (`38대`, never "다수"). Korean body, identifiers as-is.

## 2. File

- One self-contained file: inline all CSS/JS/data (no `fetch`); images as data URIs.
  The Pretendard stylesheet link is the only external reference.
- Full document: `<!doctype html><html lang="ko"><head>` with charset, viewport,
  `color-scheme`, a real `<title>`.
- Name it `YYYY-MM-DD-<slug>.html` (or `.md`) so the docs listing sorts by date.

## 3. Look at it before sharing

Serve the folder (`python3 -m http.server 8765 --bind 127.0.0.1`), screenshot at 1280
wide with whatever browser tool you have, and read the image. Check: identifiers not
broken mid-token, no clipped table, footer present, only one chromatic colour.

## 4. Publish through Informe

```bash
inf -p "docs에 올려줘. 파일명 그대로, 링크만 줘." --attach ./2026-10-15-<slug>.html --json
```

Informe uploads the file as-is and answers with
`https://docs.apps.mindlogic.tools/<file>` in `text`. Give the user that link. Uploading
again with the same file name replaces your own page in place; if someone else already
has a page under that name, Informe adds `-2` and tells you.

Anyone with write access to `s3://mindlogic-apps` can skip Informe:
`aws s3 cp <file> s3://mindlogic-apps/apps/docs/v1/<file> --content-type "text/html; charset=utf-8"`
(served at `https://docs.apps.mindlogic.tools/<file>` — no `v1/` in the URL).

An unauthenticated `curl` on the link returns `302` to the company login — that is the
healthy answer. `403`/`404` after logging in is the failure.

If `inf` is missing or says to log in: `uv tool install "git+https://github.com/mindlogic-ai/informe-cli" && inf setup`,
then `cloudflared access login https://informe-agent.mindlogic.tools` (the login lasts 7 days).
