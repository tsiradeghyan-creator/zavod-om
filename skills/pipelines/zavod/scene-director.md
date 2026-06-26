# Scene Director — ZavodOM

## When to use
Turn the `script` into a `scene_plan`: what the viewer sees each beat, the camera, the staging, and
how text appears. This is where taste + craft become an enforceable structure.

## Craft (read from skills/zavod-craft/)
`director-craft.md` (shot grammar, blocking, AI-scene directing), `cinematography.md` (lens/light/
move + DoP→AI prompt table), `storyboard.md` (per-frame card), `art-department.md` (mise-en-scène,
prop registry), `color-craft.md`, `shotdeck-reference-lab.md`.

## Process — every scene MUST specify (schema-enforced)
1. `shot_language`: shot_size, camera_movement, lens_mm, lighting_key, depth_of_field, color_temperature.
2. `staging`: blocking, **in_hand_objects** (any held prop — this feeds the continuity gate so the
   06-18 disappearing-glass class is caught), props, set_dressing, wardrobe.
3. `text_policy`: mode=overlay (default; brand font, never AI-baked), language (hy→glyph gate), text.
4. Vary shot sizes/movement across scenes (anti-slideshow). For real-subject promo, map each shot to a
   real source photo and design AROUND model limits (e.g. no one holds a glass mid-jump).

`zavod-promo` pre-production lock, before any render:
1. Owner-approved source frame for every shot.
2. Owner-approved visual style and color grade.
3. Owner-approved font pair and overlay hierarchy.
4. Owner-approved character/people policy: none, hands, backs, silhouettes, or licensed faces.
5. Technical storyboard for every shot: camera body/format, lens mm, aperture/DoF, camera move/rig,
   lighting recipe, color grade, duration, audio bed, source media, and overlay text.

Hard stop: a storyboard/scene_plan may contain prompt drafts, but no final prompt is sent to generation
until the asset stage emits the prompt pack and the owner approves it.

## Creative-language council — named style per role (not "a vibe")
Before technical prep, the council locks a **named** Style Radar pick for every craft role. Use
`lib/style_selection.candidate_styles(role)` to surface 2-3 named options per role and present them as
a choice with a one-line rationale each:
- director ← `directors`, cinematographer ← `cinematographers`, editor ← `montage`,
  production_designer ← `production_designers`, costume_designer ← `costume_designers`,
  colorist ← `color_luts`.
The owner picks one per role; record them under
`production_ladder.sub_stages[creative_language_council].style_selections`. A completed `scene_plan`
whose council left any role unchosen is rejected at the checkpoint seam — the locked picks then drive
the shot cards, color grade, wardrobe, and prompt pack.

## Produces
`scene_plan` (schema includes shot_language + staging + text_policy).
The stage checkpoint also carries `production_ladder` recording each owner-gated sub-stage
(creative_language_council → technical_preparation → storyboard_shot_cards → preproduction_plan) so
the specialist chain is provably non-collapsible.

## Gate
Reviewer + `variation_checker` (shot variety, no generic phrasing). Vague shots fail schema/review.
