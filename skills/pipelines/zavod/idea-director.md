# Idea Director — ZavodOM

## When to use
First stage. Turn the request into a `brief`: one segment + one hook, format, duration, platform,
and (for promo) the real source media to use.

## Craft (read from skills/zavod-craft/)
`idea-lab.md` (G1–G4 gates, route-weighted scoring), `serial-structure.md` (if part of a series),
`research-accuracy-consultant.md` (canon/fact check).

## Process
1. Run idea-lab's gates; pick ONE segment + ONE hook (offer 3 hooks if unclear).
2. For promo/real-subject work, name the exact real photo(s) the asset stage will edit.
3. Write the `brief` (audience, hook, format, duration, platform, voice register, success metric).

## Render runtime — decide here, present both (HARD RULE)
Per AGENT_GUIDE.md → "Present Both Composition Runtimes": do NOT silently default to Remotion.
At planning, pick `render_runtime` and record the choice:
- **`render_runtime="remotion"`** — default for clip-led reels/promos that stitch generated video with
  brand-font overlays in one React pass.
- **`render_runtime="hyperframes"`** — strong fit for carousels and kinetic title-card reels whose visual
  grammar is HTML/CSS/GSAP text (brand-font overlays are HTML anyway). See `skills/core/hyperframes.md`.
- **`render_runtime="ffmpeg"`** — bare stitch/mux with no composition.

Present both viable runtimes to the user with brief-specific pros/cons, then log a
`render_runtime_selection` decision in `decision_log` with both in `options_considered` and a
`chosen_because` / `rejected_because`. A fresh-session agent that finds no runtime guidance here would
silently default to Remotion — that is the exact failure this contract prevents.

## Produces
`brief` (canonical artifact, carrying the chosen `render_runtime`). Schema-validated by the reviewer.

## Gate
Reviewer checks: one hook is explicit, scope realistic, source media identified. Big bets also pass an
`llm-council` verdict before money moves (idea-lab).
