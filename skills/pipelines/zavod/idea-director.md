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
3. For `zavod-promo`, present a choice board before any visual is made: source-frame candidates,
   visual-style options, typography options, and character/people policy. Stop for owner approval.
4. Write the `brief` (audience, hook, format, duration, platform, voice register, success metric).

Hard stop: do not create a polished visual, screenshot, image edit, video clip, or prompt pack in the
idea stage. The idea stage proposes choices only.

## Production engine — ASK FIRST, lock the lane (HARD RULE)
Before any production, ask the owner the one upfront question: **Remotion թե՞ Higgsfield**. These are two
mutually-exclusive lanes (`metadata.production_engine`); they never mix.
- **`remotion`** — programmatic build: motion graphics, kinetic typography, brand-font overlays, carousels
  → video. **No AI footage.** Within this lane you still **present both `render_runtime` options** to the
  owner — `render_runtime="remotion"` (React) vs `render_runtime="hyperframes"` (HTML/CSS/GSAP; brand fonts
  pass the glyph gate natively) — and log a `render_runtime_selection` decision. See `skills/core/hyperframes.md`.
- **`higgsfield`** — AI footage: real-photo image-to-video and generative clips. **Zero Remotion** — overlay
  and assembly happen in **ffmpeg** (the Armenian brand-font overlay is burned via ffmpeg in this lane).

Record the locked choice in **`artifacts.engine_lock`** and carry it on every downstream stage:
```yaml
engine_lock:
  engine: higgsfield            # or: remotion
  compose_runtime: ffmpeg       # remotion lane → remotion|hyperframes ; higgsfield lane → ffmpeg
```
Also log an `engine_selection` decision in `decision_log` (`options_considered`, `chosen_because`). The
checkpoint seam **rejects an idea stage with no locked lane**, a Remotion-lane asset stage that used
Higgsfield, and a compose stage whose runtime does not match the lane. A fresh-session agent that does
not ask would silently default to Remotion — that is the exact failure this contract prevents.

## Produces
`brief` (canonical artifact) + `engine_lock` (the locked Remotion/Higgsfield lane). Schema-validated by
the reviewer; the seam blocks a completed idea stage without a locked lane.

## Gate
Reviewer checks: one hook is explicit, scope realistic, source media identified. Big bets also pass an
`llm-council` verdict before money moves (idea-lab).
