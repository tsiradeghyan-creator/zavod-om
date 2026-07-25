# Carousel Template — Maghakian Editorial Carousel

The agency's proven carousel system. Use for any Instagram/Telegram carousel.
Pairs with `style-profile.md` (voice) and `playbook.md` (algorithm).

## Format
- **1080 × 1350 px (4:5 portrait).**
- **Slide count: 6–10 is optimum — do NOT default to 10 by reflex.**
  - **6–8 slides** = opinion / quick-tip / single-show post.
  - **13–15 slides** (max 20) = serial scene-breakdown ONLY (reach plateaus ~slide 13).
- Slide 1 carries ~80% of the weight (0.25s scroll-death window). Make it stop the thumb.
- **Slide 2 must work as a STANDALONE ALTERNATE HOOK** — IG second-chance delivery re-serves
  the carousel starting from slide 2, so it can't assume slide 1 was seen.
- Slide 3 is an algorithm checkpoint (swipe-through rate). Put a question/payoff there.
- Include ≥1 save-worthy slide (facts summary). Last slide = **dual CTA** (comment + "save this").
- _Stats provenance: 2026 audit ([[zavod-craft-audit-2026-06]]) + `playbook.md`;
  re-validate periodically — platform numbers drift._

## 8-slide skeleton (the default)

| # | Role | Job |
|---|------|-----|
| 01 | **Poster Hook** | Poster-as-prop + bold nostalgic hook + scale stat row. Stop the scroll. |
| 02 | **Alt-hook / what it was** | A second standalone hook (works if shown first) + identify the show; key data point; emotional truth line. |
| 03 | **Swipe trigger** | A question answered with anaphora ("որովհետև… / որովհետև…"). Retention. |
| 04 | **Characters / core** | Four centers, one story — archetypes, not actor names. |
| 05 | **Scale** | Numbers as standalone lines (episodes, seasons, rating). |
| 06 | **Fan demand / turn** | The cultural aftershock — flashmobs, demand, legacy. |
| 07 | **Facts summary** | Save-worthy quick recap (the "screenshot this" slide). |
| 08 | **Dual CTA** | Specific comment question + "պահպանի՛ր սա" (save) — top answer seeds the next carousel. |

For 13–15 serial version: split slides 03–06 into "Part 1/5… 5/5" beats, each a scene.

## Per-slide captions (IG feature, late June 2026 — write them, most rivals still ignore this)

IG now lets every slide carry its own caption, swapping as the viewer swipes. This is a second
text layer under the carousel — use it, don't echo:
- **Slide 1 caption = the master caption** (`style-profile.md` formula: hook → truth → numbers →
  comment CTA). It's what feed shows before any swipe; hashtags live here.
- **Slides 2+: 1–2 lines each, doing THAT slide's job** — alt-hook line under 02, the question's
  tease under 03, a numbers line under 05, «պահպանի՛ր սա» under the last. Each swipe reveals a
  new line = extra dwell, and dwell + swipe are what carousels get ranked on.
- **Never duplicate the on-image text.** The slide states; the caption adds the subtext — a
  detail, a source, a question. If caption = image text, delete the caption line.
- **Distribute caption-SEO:** one real search phrase per slide caption (show name, «հայկական
  սերիալ», "Armenian screenwriter") instead of stuffing them all into one master block.
- Provenance: IG rollout late June 2026, live by July (platform features drift — re-verify).

## Visual recipe (the look)

- **Aesthetic:** editorial magazine — Apartamento × Kinfolk × New York Magazine. Sharp grid,
  generous white space, bold sans + serif mix, numbered slides ("01 / 08 ●"), geometric
  colour blocks, thin/thick dividers.
- **Subject:** object / symbol / poster-as-prop photography. **No actor faces, no copyrighted
  stills** — բացառություն՝ licensed/owned poster-as-prop-ը (օր. «Խաղալիք» պաստառը), որտեղ
  պաստառի սեփական դեմքերը մնում են անփոփոխ (`ai-pipeline.md` Identity-lock; AI-ն նոր դեմք
  երբեք չի ստեղծում)։
- **Palette:** pick a per-topic palette (poster colors of the show). Keep the agency wordmark
  bottom-corner + `@maghakianscripts`. Brand purple `#6450D2` is the house accent when no
  topic palette dominates.
- **Type:** Noto Serif/Sans Armenian for body; bold display for headline. One yellow/accent
  highlight behind the key phrase, rotated ~-1.5°.

## CRITICAL — how to generate the images

AI image models render Armenian text badly. **Always generate the Background only** (the
layout, blocks, dividers, colour — NO Armenian text), then **add the Armenian text** on top.
This is the brand "Background" rule.

**Auto-text (skip the manual Canva pass):** `scripts/carousel_text.py` takes the clean
Background + a JSON text spec and renders proper Eastern Armenian (Noto Serif/Sans Armenian
or GHEA) with safe-zone-aware placement + an in-code glyph gate (refuses any homoglyph) →
one command = a publish-ready slide, not a semi-finished file. Use Canva only for bespoke
art-direction; for templated slides, automate.
```bash
# from the canonical working dir ~/zavod-om/
python3 skills/zavod-craft/scripts/carousel_text.py --bg slide-bg.png --spec slide.json --out exports/<slug>/slide-01.png
```
The script also enforces layout in code: blocks in the same zone stack (no overlap), any block
leaving the safe area or a word wider than `max_width` fails the render, `rotate` is applied,
and a font-coverage gate rejects Latin/Cyrillic text sent to an Armenian-only font (tofu guard).

Each slide gets two prompt options in the working file:
- **Prompt A** (with text) — only if a quick rough is fine; expect to fix text in Canva.
- **Prompt B (Background only)** — RECOMMENDED. Clean layout, empty spaces for typography.

### Engines for the backgrounds
- **Canva** or **Adobe Firefly** (live now) — fastest for editorial layouts.
- **Nano Banana via fal.ai** — for richer generated backgrounds (needs `FAL_KEY`).

## Deliverables for a finished carousel
1. `carousel-NN-<slug>.html` — the visual preview / Canva placement guide (slide text baked in).
2. `carousel-NN-<slug>-prompts.md` — per-slide Background prompts (A + B) + palette block.
3. `carousel-NN-<slug>-caption-and-sources.md` — caption with 3-5 hashtags + posting
   notes + sources.
4. Exported slide PNGs in `exports/<slug>/slide-NN.png`.

(Working folder pattern lives at `~/insta ej scripts/`.)

## Instagram Story campaign (9:16, daily automation)

Aggressive launches need constant Story visibility, not just feed posts. Auto-generate a
daily Story series for a new serial from its design code:
- **Format:** 1080×1920 (9:16); safe zones top 250px / bottom 250px (UI + interactive sticker
  room); brand palette + approved type (`motion-design.md`).
- **Inputs:** lead-character descriptions + the setting + the design code (colour, fonts, logo
  from `identity-guard.md`).
- **Daily interactive series:** polls («Ո՞ւմ կողմն ես»), countdown stickers (premiere/episode
  drop), quote cards (a signature line — canonical-phrase locked), "this/that" character cards,
  question boxes. One premium look even in 24h-life content.
- **Render path:** reuse `scripts/carousel_text.py` on a 9:16 Background (set `size`:[1080,1920])
  → text + glyph gate baked in; interactive stickers added natively at upload.
- Strategy/cadence (when, how many, retention) → `playbook.md` + `growth-analytics.md`.

## Quality gate before delivery
- [ ] Slide 1 hook is nostalgic + has a scale stat, readable at thumbnail size.
- [ ] Slide 3 has a question/anaphora payoff.
- [ ] ≥1 save-worthy slide; last slide = specific comment CTA.
- [ ] All Armenian in proper Unicode; no faces/stills; wordmark + handle present.
- [ ] Caption follows `style-profile.md` formula; 3-5 hashtags are in the caption, not first comment.
- [ ] Per-slide captions written: master on slide 1; one job + one search phrase per slide;
      no caption echoes its slide's on-image text.
