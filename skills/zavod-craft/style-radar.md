# Style Radar — Ապրող, ինքնաթարմացվող ճաշակ (LIVING)

> The self-updating heart of the zavod's VISUAL taste — the look twin of `style-profile.md`
> (which owns the writing voice). It keeps a dated map of in-demand, current styles across four
> axes and pulls fresh signal from the internet on a schedule. **Read before any scene/asset/
> design/overlay/grade/montage decision.** Mature entries graduate to a card in `style-library/`.
>
> **Mechanism:** registry = `library/style_radar.json` · driver = `lib/style_radar.py` (wake-safe,
> health-gated, GATED — nothing self-adds) · cards = `skills/zavod-craft/style-library/`.
> Same contract as `meta/scout.md`: the agent web-scans → drops findings in
> `library/style_inbox.json` → driver dedups/scores → a card-proposal memo → **owner approves**
> → a card is written. Nothing enters the taste automatically.

## The four axes
1. **Design / visual** — overlay, title, carousel, thumbnail, motion-graphics (the design layer).
2. **Cinema / DP** — named directors & cinematographers as look references (incl. Armenian masters).
3. **Color / LUT** — grade looks, film-stock emulation, emotional palettes.
4. **Montage** — transition & editing grammar (named editors/directors).

## Cadence & sources (owner-approved 2026-06-25)
Weekly via the launchd job (reuse the Scout plist pattern; run `lib/style_radar.py`).
Scan targets (`SCAN_SOURCES` in `lib/style_radar.py`):
- **Reddit** — r/cinematography, r/colorists, r/graphic_design, r/editors, r/motiondesign
- **Design blogs** — Creative Bloq, It's Nice That, Behance, Adobe Express Learn
- **Cinema** — ShotDeck community, Oscar best-cinematography shortlist, festival coverage
- **Creator trends** — X (edit/transition/look virality), TikTok creator trends

## Protocol (per pass)
1. Scan the four source groups for what's **in demand THIS year**, by axis.
2. For each candidate, capture: `id`, `axis`, `essence`, `markers`, `source`, and 0-1 inputs
   `demand` / `recency` / `fit` (Maghakian register) / `durability` / `fad_risk`.
3. Drop them into `library/style_inbox.json`; run `lib/style_radar.py` → it health-gates,
   dedups against the registry, scores (`score_style_finding`), emits a GATED memo.
4. **Owner approves** → write a card in `style-library/` + add the id to `style_radar.json`.
5. Log the pass; update the trend-map below with the date.

## Scoring (taste-tuned, not capability-tuned)
`1.5·demand + 1.0·recency + 1.0·fit + 0.5·durability − 0.5·fad_risk`.
Reward what's requested, current, on-brand, and lasting; penalize disposable trend-bait.

## Routing into production (how taste reaches a frame)
- **scene-director** (`cinematography.md`, `color-craft.md`, `art-department.md`) pulls **cinema_dp**
  + **color_luts** cards → `scene_plan.shot_language` + grade.
- **asset-director** (`motion-design.md`, `carousel-template.md`) pulls **design_styles** cards →
  overlays/titles/carousels + `shot_prompt_builder` Layer 5 keywords.
- **edit-director** (`post-production.md`) pulls **montage** cards → transition choices.
- (Planned) a **taste-gate** scores a frame against the active card's markers and rejects slop.

---

## Trend-map — 2026-06-25 (first pass, web-verified)
Two live design lanes — keep BOTH; pick per project, never blend by accident:
- **Lane A — Apple-polish:** liquid glass, bento box, lightweight 3D, oversized type, minimalism.
- **Lane B — tactile-human (2026 anti-AI backlash):** naive/hand-drawn, texture+warmth, mixed-media
  collage, bright saturated color, retro-futurism. *This is the rising wave — "sameness is out."*

| Axis | In demand 2026 | Note for us |
|---|---|---|
| Design | tactile/human, mixed-media collage, oversized type, bento, liquid glass | editorial + minimalism = our spine; collage/tactile for warmth |
| Color/LUT | **analog nostalgia (Kodachrome/Fuji emulation)** #1, emotional desat, warm-intimate, teal&orange (deliberate) | analog-grain + emotional palette fit Maghakian's memory theme |
| Montage | **minimalist "barely-edited"**, retro-film effect, glitch (edgy) | restraint matches her register; PCW/Peleshyan for the turns |
| Cinema/DP | Deakins, Lubezki, Khondji, Laustsen; **+ Parajanov, Peleshyan, Egoyan (Armenian)** | Armenian masters = signature differentiator |

Sources (2026-06-25): Creative Bloq "texture/warmth/tactile rebellion 2026" · Digital Synopsis
top-20 2026 · AAA Presets "2026 LUT forecast" · Increditors "editing trends 2026" · StudioBinder
"best cinematographers". Re-verify each pass — treat as a live signal, not a fixed truth.

## Changelog
- 2026-06-25 — created; seeded registry (11 design · 9 DP · 7 color · 8 montage) from first web pass.
