# Asset Director — ZavodOM

## When to use
Produce every asset the scene_plan needs: generated images/clips, backgrounds, VO, music, SFX, titles.

## Craft (read from skills/zavod-craft/)
`ai-pipeline.md` (engine lineup, consistency/seed/cost), `providers/higgsfield-capabilities.md`
(full Higgsfield arsenal — read before choosing any model), `motion-design.md`, `identity-guard.md`,
`background-environment-artist.md` (empty-plate), `carousel-template.md`, `fal-setup.md`.

## Process
1. Pick the right engine per asset (use higgsfield-capabilities.md decision quick-pick; `get_cost` first).
2. **Real subject → image-to-image with the real photo attached** (`medias` INSIDE `params`). Never
   generic text-to-image for a real property/product.
3. Generate CLEAN images (no baked text). Text is added later as overlay (text_policy=overlay).
4. Choose engines respecting moderation (Kling for tasteful swimwear; not Veo). Music=sonilo, SFX=mirelo,
   VO=inworld (non-Armenian) / ElevenLabs (Armenian).

## Produces
`asset_manifest`.

## Gate
Reviewer: every real-subject visual references a real photo (input_images populated); no AI-baked text on
branded assets; glyph gate on any text asset.
