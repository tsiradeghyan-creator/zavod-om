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

## Produces
`scene_plan` (schema includes shot_language + staging + text_policy).

## Gate
Reviewer + `variation_checker` (shot variety, no generic phrasing). Vague shots fail schema/review.
