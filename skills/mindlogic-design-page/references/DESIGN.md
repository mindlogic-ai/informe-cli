# DESIGN.md

Visual rules for anything MindLogic's agent renders for a person to look at: 구성도와
아키텍처 다이어그램, 지표·리포트 페이지, 내부 대시보드, 그리고 고객에게 나가는 안내물.
Supersedes `DIAGRAM.md`, which covered only the first of those and therefore missed most
of what actually gets requested (30일 실측: 구성도 7건 대 HTML·대시보드 32건, 고객
안내물 7건).

An agent reading this file should produce something that reads as a *deliverable* —
something with presence that a director would put on screen — not a generated
illustration and not a terminal dump.

Scope: static HTML/SVG rendered by us. Charts follow `dataviz`; customer document
furniture (대외비 푸터, 브랜드 규칙) follows `customer_doc_confidential_footer`.

Reference systems studied: IBM Carbon, Stripe, Linear (via `voltagent/awesome-design-md`).

---

## 0. Pick the lane first

Three lanes. They share §1–§6 and diverge after that. Choosing wrong is the most
expensive mistake on this page, so choose explicitly before writing any CSS.

| Lane | What it is | Reader | Section |
|---|---|---|---|
| **A · 구성도** | components, boundaries, edges | 우리 팀 | §7 |
| **B · 지표 페이지** | stat rows, ranked tables, weekly bars, dashboards | 우리 팀 | §8 |
| **C · 안내물** | 고객이 보는 설명서·안내 이미지·제안서 삽입물 | 고객 | §9 |

Lane C is not "lane A with a footer bolted on". It is read once by someone who does not
work here, often at phone size or inside a slide, and it is allowed warmth the other two
are not. §9 says exactly how much.

---

## 1. The two failure modes

A page fails in one of two directions, and the fix for one is not the fix for the other.

**Generated look** — four pastel zones, one hue per zone, 16px radii, coloured dots,
emoji, soft shadows, every box the same size. Everything is decorated equally, so
nothing is emphasised. Fixed by *removing*: one accent, square corners, no shadows.

**Nerdy look** — the overcorrection. Everything neutral, everything monospaced,
everything the same size. Reads as a config dump. It is not that it lacks colour; it is
that it lacks **scale contrast** and a **focal point**. Fixed by *adding* those two
things, and only those two.

The rest of this file is how to get impact without going back to mess.

---

## 2. Impact — the three moves

All three reference systems (IBM, Stripe, Linear) build presence the same way, and none
of them use colour to do it.

**2.1 Scale contrast, carried by the title rule.** Display type to body type must span
a wide interval — Stripe runs 56px against 15px, IBM 76px against 16px. But a 구성도 is
not a landing page: a 40px headline eats vertical space the page needs, and it competes
with the zones. Get the same presence for less height by pairing a compact title with
**a full-width accent rule running from the end of the title to the right edge**. The
rule does the work the oversized type would have done, and it frames the page as a
drafted document rather than a slide.

```
title      26px / weight 700 / -0.02em, with a 2px accent rule to the right edge
subtitle   13px / weight 500 / ink-3, on the title's baseline
zone title 15px / weight 700 / -0.012em
node       13px / weight 600
metadata   11px / weight 500
eyebrow    10.5px / weight 700 / +0.08em
```

Ratio here is ~2.4×, below the landing-page figure, and that is correct — the accent
rule supplies the missing contrast. Where a page genuinely needs a display headline
(a cover page, a single-slide summary, lane C), set it at **weight 300, never bold**:
40px bold is loud, 40px light is confident. Lane C overrides this scale — see §9.

**2.2 Emphasis is a line and the accent, never an inverted block.** A solid black bar
inside a hairline layout reads as a foreign object dropped on the page — it outweighs
everything including the thing it sits on, and it kills the greyscale balance the rest
of the rules build.

Emphasise the focal element with **a mark plus weight** instead:

- a 2px accent tick on the leading edge, inset from the top and bottom edges so it
  reads as a mark rather than a border,
- the label in **ink**, one weight heavier than its neighbours — not in the accent,
- a 1px hairline separating it from what it introduces.

**One signal, not three.** The accent tick already says "this one"; setting the label in
the accent as well, at a larger size, on top of the tick, triples the signal and the
element starts shouting — the same failure as the black block, in colour instead of
value. The accent marks; the type carries the weight.

**2.3 Numbers are typographic events.** Any figure the page exists to communicate —
counts, capacities, throughput — is set one step larger and one weight heavier than its
surrounding label, in the sans face with `tabular-nums`. `메모리 271건` becomes 271 at
14px/700 next to 11px/500. Free impact, zero mess.

There is an editorial half to this and it matters more than the typographic one: **the
figure has to be an actual count.** `46개 운영 중`, never "several", never "다수". A vague
quantifier is the fastest way to tell the reader nobody counted, and it survives every
other rule on this page.

---

## 3. Colour

**One accent. Everything else is neutral.** Impact comes from §2, not from here.

```
--accent      #1F65FF   MindLogic signature blue — the ONLY chromatic colour
--accent-soft #EDF2FF   accent at ~8% — fills only, never text
--ink         #0F1115   primary text
--ink-2       #3F4552
--ink-3       #767D8D   labels, metadata
--rule        #E1E4EA   borders
--rule-2      #EFF1F5   inner dividers
--surface     #FFFFFF
--surface-2   #F7F8FA   recessed ground
```

- Hierarchy is value and weight, never hue.
- **Accent budget: five *placements*, not five pixels.** One repeating structural
  element counts once no matter how many times the grid repeats it — four zone numerals
  are one placement, not four. The five: the title rule, the zone numerals, the focal
  element's tick, the focal element's own label if it needs one, and one inline
  identifier. A sixth *kind* of accent use means one is decorative — cut it.
- **No inverted surfaces.** No black bars, no dark panels, no white-on-dark blocks
  inside the body.
- **Inline bars stay on this palette.** A 5-row bar next to a label is furniture, not a
  chart: track `--rule-2`, fill `--ink-2`, never a hue, never one hue per row. Hand off
  to `dataviz` only when the thing is a real chart — axes, a legend, series that must be
  told apart by colour.
- Semantic colour (red/amber) only when the subject is *state*. A component map has no
  states, so it has no red. **One exception, lane C only:** a pointer colour marking
  "여기를 누르세요" on a screenshot or mockup. It is instruction, not decoration, and it
  may appear as many times as there are steps.

**Never:** one hue per zone · gradients · coloured shadows · pastel fills behind body
text · a colour used exactly once for decoration.

---

## 4. Typography

```
sans   "Pretendard", "Apple SD Gothic Neo", "Noto Sans KR", -apple-system, sans-serif
mono   ui-monospace, "SF Mono", Menlo, monospace
```

**Load the display face.** Do not rely on the reader having Pretendard — link it. A page
that falls back to a system Korean face loses its tracking and its 300 weight, which is
where the impact lived.

**Monospace is a scalpel, not a paintbrush.** This is the rule that separates
professional from nerdy. Mono is for text the reader might *copy*: a hostname, a path,
a table name, an env var. It is **not** for service names, product names, counts, or
metadata generally. Set those in the sans face with `font-variant-numeric: tabular-nums`
and tight tracking — that is what Stripe does for money, and money is as technical as
it gets. If more than ~5% of the page is monospaced, the page is a terminal.

Korean text: 한글 only, no 한자. Line-height 1.5 minimum on anything that wraps.
Sentence case headings; no ALL CAPS on Korean.

**Never:** emoji anywhere (lane C included — a 🍎 in a section heading is the single
loudest "generated" tell) · icons standing in for words · more than three type sizes
inside one zone · type below 10.5px (lane C: 13px).

---

## 5. Line breaking — the detail that gives it away

An identifier broken across a line — `backend-` / `weekly` — undoes every other
decision on the page. Nothing signals "nobody looked at this" faster.

- **Never** set `overflow-wrap: anywhere` or `word-break: break-all` on a container
  holding identifiers. It is the direct cause.
- Hyphenated tokens break at the hyphen under normal wrapping too. Wrap each token in
  `white-space: nowrap` — split delimiter-separated lists (` · `) into per-token spans
  at render time so the line breaks *between* tokens and never inside one.
- If a list still cannot fit, the layout is wrong, not the text: give the column more
  width, or move the list to its own line. Never solve it by shrinking type below
  10.5px or by letting it break.
- Korean: `word-break: keep-all` so 어절 stay whole.

**A sentence is the smallest unit a line may break on.** A line that ends mid-clause
— `담당자가 바뀌어도` / `조직이 쌓은 기준은 남습니다` — reads as a typo of the layout:
the reader parses half a thought, drops to the next line, and starts again. The fix is
never to accept it; it is to make the break land *between* sentences, or to remove the
break entirely.

In priority order:

1. **Make it one line.** Widen the column, shorten the sentence, or drop the
   `max-width` that is forcing the wrap. Most two-line ledes are one sentence too long.
2. **Break between sentences.** Wrap each sentence in `<span class="s">` with
   `.s { display:inline-block }`. An inline-block sentence moves to the next line whole
   instead of splitting, so the break lands at a full stop. Do it at render time —
   split only at sentence ends that sit outside a tag, and only when both sides keep
   their inline tags balanced. A sentence still longer than its container wraps
   internally; that is the one case you accept.
3. **Balance what is left.** `text-wrap: pretty` on prose (kills the one-word last
   line), `text-wrap: balance` on short blocks — list items, card subtitles, figure
   labels — so a two-line item splits evenly instead of leaving an orphan.

Never fix it by hyphenating, by shrinking type, or by hand-inserting `<br>` at the one
width you happened to be looking at — that `<br>` is wrong at every other width and in
print.

---

## 6. Shape, line and grid

```
radius        3px    every box, no exceptions (lane C: 8px, see §9)
border        1px solid var(--rule)
inner divider 1px solid var(--rule-2)
edge stroke   1.25px
arrowhead     7×7px solid triangle
row height    36px for repeated rows
inner gutter  12px
zone gutter   28px
```

- **The grid is the design.** One row height, one inner gutter, one gutter between
  zones. Ragged stacks are the clearest tell.
- Zone headings sit on **one baseline across all columns**, with a hairline running from
  the end of each heading to the edge of its column. Cheap, and it makes the page look
  drafted rather than assembled.
- **Density is a feature *inside* a zone; air belongs between them.** Tighten rows,
  gutters and padding as much as legibility allows, then spend the saved space on the
  seams. The gap between the title block and the first zone heading is the one that gets
  noticed when it is missing — **56px minimum**, never the same as the gap between two
  zones.
- The title block sits on the same ground as the body, separated by its accent rule and
  a hairline — not on a contrasting band. A band turns the page into a slide.
- Metadata separators (` · `) are set in `--ink-3`, not `--rule`. At 11px a `--rule`
  separator is invisible and the list reads as one run-on string.

**Never:** `box-shadow` · `filter` · mixed radii · borders thicker than 1px as
decoration · centring everything · a legend for colours you did not use semantically ·
background patterns · anything stretched past 1600px.

---

## 7. Lane A — 구성도

- Node shape encodes type: rectangle = component · dashed rectangle = boundary ·
  stadium = external system · cylinder = datastore. More than three shapes means the
  diagram is doing two jobs and should be two diagrams.
- **Edges are orthogonal**, 4px corner arcs, no diagonals, no avoidable crossings.
- Draw edges from **measured geometry at render time**, never hand-tuned offsets. A
  hard-coded `padding-top:183px` on a connector breaks silently the next time anyone
  edits a row.
- Reading order left→right, top→bottom. The primary path is the straightest line
  through the diagram; branches go below it, never above.
- Edge labels when the relation is not obvious: a verb or protocol, 10.5px,
  `var(--ink-3)`, on a page-coloured backing so the stroke does not run through it.
- No node label wraps to three lines. If it does, it is a sentence and belongs in a note.

## 8. Lane B — 지표 페이지와 대시보드

The most-requested shape, and the one `DIAGRAM.md` had nothing to say about.

- **Stat row.** One bordered strip divided by `--rule-2`, never separate floating cards.
  Label 11px/500 `--ink-3` above, figure 22px/700 `tabular-nums` below, unit as a 12px
  `<small>` in `--ink-2` — the unit must never be the same size as the figure.
- **Ranked table.** 36px rows, 10.5px eyebrow header in `--ink-3`, numeric columns right
  aligned with `tabular-nums`, the headline figure per row one step up in `--ink`. The
  top row is the focal element per §2.2 — accent tick, ink weight, nothing else.
- **Inline bars.** Per §3: neutral track, `--ink-2` fill, widths normalised to the max
  in the set. The number stays in text beside the bar; a bar alone is not a reading.
- **Derived figures are forbidden unless they are exact.** Do not subtract overlapping
  buckets to invent a remainder. If categories overlap, say `중복 집계` in the zone note.
- Every zone carries a note line stating the basis (`기간 내 실사용 기준`, `주 시작일
  기준`). A dashboard without a stated basis will be read wrong within a week.
- A page that refreshes on a schedule earns `apps publish`; a one-off goes to the docs
  tier. That routing is the `publish` skill's, not this file's.

## 9. Lane C — 고객 안내물

Everything above still applies **except** the four things below. Lane C readers are
students, teachers, 행정 담당자 — on a phone, once, with no context. Density that reads
as confident internally reads as cold and unreadable here.

- **Scale goes up, not down.** Body 15–17px, step titles 19–21px, the page headline may
  be 34–40px — but at **weight 300**, per §2.1. Nothing below 13px anywhere.
- **Radius 8px** for content cards (not 3px, not 16px). 3px reads as a spreadsheet to a
  non-technical reader; 16px is the generated look.
- **Section headings get a hairline and an accent tick, not a filled pastel band.** The
  band is the single biggest generated tell in customer material we have shipped.
- **Step ordinals stay large.** In a procedure, the number is navigation, not metadata:
  19px/700 in the accent, above the step title. Demoting it to an 11px eyebrow (the
  lane A/B treatment) costs the reader the "따라 하는 순서" affordance — measured on the
  팩트챗 모바일 설정 안내 rebuild, 2026-08-28. Drop the filled circle, keep the size.
- **The pointer colour is allowed** (§3) — mark the exact tap target on every screenshot.
  A guide that says "공유 버튼을 눌러요" without marking it has failed at its one job.
- Product depictions — phone frames, UI mockups, screenshots — are the substance and are
  exempt from the palette. Style the *chrome around them*, never the artefact itself.
- 해요체, per `feedback_blog_korean_voice`. No 습니다체, no loanwords where a Korean word
  exists.
- Never name another customer, another institution, or an internal identifier. Aggregate
  or anonymise before it leaves.

## 10. Required furniture

1. Title + one-line subtitle sharing a baseline, closed by the accent rule.
2. Meta rule: document type · date · owner. Separators in `--ink-3`.
3. Footer per `customer_doc_confidential_footer`: 대외비 문장, left `Confidential
   기밀자료`, right `© 2026. Mindlogic Inc. All Rights Reserved.`
4. Print stylesheet: `@page { size: A4 landscape; margin: 12mm }` (lane C: `portrait`)
   with `print-color-adjust: exact`. A page that will not print to a clean PDF is not
   done.

## 11. Exporting to an image

Lane C artefacts usually leave as a PNG pasted into a mail, a 공지, or a slide — the
link is useless outside Cloudflare Access. So the HTML is the source, not the delivery.

- Render at **2× device scale** for a legible PNG; anything less and 13px Korean text
  furs at the edges.
- Fix the sheet width (1240px works for A4-ish portrait) and screenshot the sheet
  element, not the viewport — a viewport shot bakes in scroll position and cropped rows.
- The footer must survive the crop. A 대외비 footer cut off by the screenshot is the one
  failure mode that matters legally, so check the bottom of the PNG.
- Deliver PNG + the source HTML side by side on the docs tier, so the next person edits
  rather than redraws.
- PII or a 명단 in the image? It goes to Slack as a file attachment, never to S3.

## 12. Checklist

- [ ] Lane declared (A / B / C) before any CSS.
- [ ] Title carries a full-width accent rule; type ratio ≥ 2.4× without an oversized headline.
- [ ] Zero inverted/black-filled regions. Focal emphasis is an accent tick + ink weight.
- [ ] Every headline figure is one step larger and heavier than its label.
- [ ] Accent used in ≤ 5 *placements*, all structural (repeats count once).
- [ ] Monospace covers under ~5% of the page and only copyable strings.
- [ ] Exactly one chromatic hex in the CSS — plus the pointer colour in lane C.
- [ ] Zero `box-shadow`, zero gradient, zero emoji. Radii 3px (lane C: 8px).
- [ ] No identifier breaks mid-token at 1280px, 1600px, or in print.
- [ ] No line breaks mid-sentence: one line, or the break falls between sentences.
- [ ] Lane B: every zone states its basis; no derived figure from overlapping buckets.
- [ ] Lane C: nothing below 13px; every tap target marked; no other customer named.
- [ ] Greyscale test: hierarchy survives. If it collapses, it was carried by colour.
