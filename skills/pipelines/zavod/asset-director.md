# Asset Director — ZavodOM

## When to use
Produce every asset the scene_plan needs: generated images/clips, backgrounds, VO, music, SFX, titles.

## Craft (read from skills/zavod-craft/)
`ai-pipeline.md` (engine lineup, consistency/seed/cost), `providers/higgsfield-capabilities.md`
(full Higgsfield arsenal under `skills/providers/` — read before choosing any model), `motion-design.md`, `identity-guard.md`,
`background-environment-artist.md` (empty-plate), `carousel-template.md`, `fal-setup.md`.

## Lane first (read `engine_lock`)
Route by the locked lane — the two lanes never mix:
- **`engine_lock.engine == "remotion"`** → build assets programmatically (motion graphics, designed plates,
  brand-font cards). **Do NOT call Higgsfield.** The seam rejects an `asset_manifest` that contains any
  Higgsfield-sourced asset on the Remotion lane.
- **`engine_lock.engine == "higgsfield"`** → the Higgsfield prompt-gate path below.

## Process
1. Pick the right engine per asset (use higgsfield-capabilities.md decision quick-pick; `get_cost` first).
2. **Real subject → image-to-image with the real photo attached** (`medias` INSIDE `params`). Never
   generic text-to-image for a real property/product.
3. Generate CLEAN images (no baked text). Text is added later as overlay (text_policy=overlay).
4. Choose engines respecting moderation (Kling for tasteful swimwear; not Veo). Music=sonilo, SFX=mirelo,
   VO=inworld (non-Armenian) / ElevenLabs (Armenian).

`zavod-promo` prompt gate:
1. First produce a prompt pack only: per-shot prompt, negative prompt, model, params, source media
   attachment plan, cost estimate, and expected failure modes.
2. Freeze and get owner approval for every prompt.
3. Only after approval call Higgsfield for generated motion (`generate_video`) or real-photo edits
   (`generate_image`) with the approved source media attached.
4. Never use Remotion in the Higgsfield lane — generation is Higgsfield, assembly/overlay is ffmpeg.

## Produces
`asset_manifest`.

## Gate
Reviewer: every real-subject visual references a real photo (input_images populated); no AI-baked text on
branded assets; glyph gate on any text asset.
