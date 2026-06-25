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

## Canon + axes
The OWNER-CURATED canon is **`style-rider.md`** — this file (`style-radar.md`) is the
self-updating loop that keeps it current; it proposes GATED additions, never overwrites the canon.
Eight taste axes (rider sections 1–7 + grading), mirrored in `library/style_radar.json`:
**directors · cinematographers · montage · animators · design_styles · production_designers ·
costume_designers · color_luts** (151 entries).

## Cadence & sources — the owner's pages ONLY (style-rider.md §8–11)
Weekly via the launchd job (`com.zavodom.style-radar`, Thu 09:00; runs `lib/style_radar.py`).
Taste updates come from THESE tastemakers and nothing else (`SCAN_SOURCES` in `lib/style_radar.py`):
- **LinkedIn** — Chris Do, Debbie Millman, Jessica Walsh, Brian Collins, Paula Scher, Pentagram,
  The Futur, AIGA, It's Nice That, Brand New/UnderConsideration, Andy Budd, Julie Zhuo
- **X** — @chrisdo, @jessicahische, @brad_frost, @maggieappleton, @vanschneider, @joulee,
  @davidhoang, @rachelnabors, @awwwards, @motionographer, @letterboxd, @criterion, @A24, @shotdeck
- **Instagram** — @thebrandidentity, @itsnicethat, @aigaeyeondesign, @bpando, @designmilk, @awwwards,
  @motionographer, @typewolf, @thedesignkids, @worldbranddesignsociety, @posteritati,
  @criterioncollection, @mubi, @shotdeck, @letterboxd
- **Reddit** — r/graphic_design, r/Design, r/typography, r/logodesign, r/branding, r/web_design,
  r/UI_Design, r/cinematography, r/Filmmakers, r/editors, r/colorists, r/MotionDesign, r/animation,
  r/AfterEffects, r/ObscureMedia

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
| Cinema/DP | **GLOBAL-first**: Deakins, Lubezki, Morano, Young, Khondji, Laustsen (+ scan world DPs) | Armenian (Parajanov/Peleshyan/Egoyan) = a few anchors only, occasional signature accent — not the focus |

Sources (2026-06-25): Creative Bloq "texture/warmth/tactile rebellion 2026" · Digital Synopsis
top-20 2026 · AAA Presets "2026 LUT forecast" · Increditors "editing trends 2026" · StudioBinder
"best cinematographers". Re-verify each pass — treat as a live signal, not a fixed truth.

## Changelog
- 2026-06-25 — created; seeded registry (11 design · 9 DP · 7 color · 8 montage) from first web pass.
- 2026-06-25 — adopted owner-curated `style-rider.md` as canon: registry expanded to **151 entries
  across 8 axes** (directors / cinematographers / montage / animators / design / production / costume
  / color); SCAN_SOURCES repointed to the owner's exact LinkedIn/X/Instagram/Reddit pages (§8–11).
