---
name: gpt-image-prompting
description: >-
  Best-practice prompting and API patterns for OpenAI's GPT image generation
  models (gpt-image-2, gpt-image-1.5, gpt-image-1, gpt-image-1-mini). Use this
  skill whenever the user wants to generate or edit an image with an OpenAI /
  gpt-image model, write or improve an image-generation prompt, build an
  image-gen or image-editing workflow, or asks how to get better results
  (photorealism, in-image text, infographics, logos, ads, UI mockups, style
  transfer, virtual try-on, compositing, object removal, lighting/weather
  changes, product mockups, character consistency). Trigger it even when the
  user doesn't name the model explicitly — e.g. "make an image of...",
  "generate a logo for...", "edit this photo to...", "why does the text in my
  generated image come out garbled", or "help me write a prompt for an
  infographic". Prefer this skill over ad-hoc prompting for any gpt-image work.
---

# GPT Image Prompting

Write effective prompts and API calls for OpenAI's `gpt-image` models. The
goal is production-quality, controllable output with fewer retries — by being
explicit about structure, constraints, and what must change vs. stay the same.

## How to use this skill

1. **Identify the job**: generation (text → image) or edit (text + image →
   image), and the use case (infographic, logo, ad, photorealism, UI mockup,
   translation, style transfer, try-on, compositing, object removal, lighting
   change, product mockup, character consistency, slide/chart).
2. **Pick a model + quality** using the rules below (default `gpt-image-2`).
3. **Write the prompt** following the fundamentals below. For a specific use
   case, read `references/use-cases.md` for a matching template.
4. **Emit runnable code** using the setup helper in
   `references/api-reference.md`, unless the user only wants the prompt text.
5. **Iterate small**: change one thing at a time and re-state the invariants
   so the image doesn't drift.

## Model selection (quick rules)

- **Default to `gpt-image-2`** for new work — strongest generation + editing,
  text-heavy images, photorealism, compositing, identity-sensitive edits, and
  flexible sizing. `input_fidelity` is not used on `gpt-image-2` (output is
  already high fidelity); it *does* apply to the older models.
- **`quality="low"`** on `gpt-image-2` when speed / cost dominate (high-volume
  generation, ideation, previews). It's often good enough. `gpt-image-1-mini`
  is an alternative for cheap batches.
- **`quality="medium"` / `"high"`** for small or dense text, detailed
  infographics, close-up portraits, identity-sensitive edits, slides/charts,
  and high-resolution outputs.
- **Legacy (`gpt-image-1.5`, `gpt-image-1`)**: only for backward compatibility
  while migrating validated workflows. See the full table in
  `references/api-reference.md`.

Common `gpt-image-2` sizes: `1024x1024` (square default), `1024x1536`
(portrait), `1536x1024` (landscape), `1536x864` (deck slide), `2560x1440`
(2K, upper reliability boundary). Full size constraints live in
`references/api-reference.md`.

## Prompting fundamentals

These are the levers that most reliably improve results. Apply the ones the
task needs — don't pile on all of them.

- **Structure + intended use.** Write in a consistent order:
  background/scene → subject → key details → constraints. Name the intended
  use (ad, UI mock, infographic) so the model sets the right "mode" and polish
  level. For complex requests, use short labeled segments or line breaks
  instead of one dense paragraph.
- **Specificity + quality cues.** Be concrete about materials, shapes,
  textures, and medium (photo, watercolor, 3D render). Add targeted levers
  only when needed (*film grain*, *textured brushstrokes*, *macro detail*).
  For photorealism, put the word **"photorealistic"** directly in the prompt;
  phrases like "real photograph," "professional photography," or "iPhone
  photo" also help. Treat camera specs as look/composition hints, not exact
  physical simulation.
- **Composition.** Specify framing/viewpoint (close-up, wide, top-down),
  angle (eye-level, low-angle), and lighting/mood (soft diffuse, golden hour,
  high-contrast). If layout matters, call out placement ("logo top-right,"
  "subject centered with negative space on the left").
- **People, pose, action.** Describe scale, body framing, gaze, and object
  interaction: "full body visible, feet included," "looking down at the book,
  not the camera," "hands gripping the handlebars." This fixes proportion,
  action geometry, and gaze.
- **Constraints — change vs. preserve.** State exclusions and invariants
  explicitly ("no watermark," "no extra text," "no logos/trademarks,"
  "preserve identity / geometry / layout / brand elements"). For edits, use
  **"change only X" + "keep everything else the same,"** and **repeat the
  preserve-list on every iteration** to reduce drift. For surgical edits, also
  say not to alter saturation, contrast, layout, arrows, labels, camera angle,
  or surrounding objects.
- **Text in images.** Put literal copy in **"quotes"** or **ALL CAPS** and
  specify typography (font style, size, color, placement). Spell tricky words
  (brand names, uncommon spellings) letter-by-letter. Use `medium`/`high`
  quality for small text, dense panels, or multi-font layouts.
- **Multi-image inputs.** Reference each input by **index + description**
  ("Image 1: product photo… Image 2: style reference…") and describe how they
  interact ("apply Image 2's style to Image 1"). When compositing, be explicit
  about what moves where.
- **Iterate, don't overload.** Start from a clean base prompt and refine with
  small single-change follow-ups ("make lighting warmer," "remove the extra
  tree"). Use references like "same style as before," but re-specify critical
  details if they start to drift.

## Reference files

- `references/api-reference.md` — Python setup helper (`client`,
  `save_image`), `images.generate` / `images.edit` call shapes, the full model
  comparison table, size constraints, and the `quality` / `input_fidelity` /
  `background` / `n` parameters. Read this before writing runnable code.
- `references/use-cases.md` — Copy-ready prompt templates and worked examples
  for each use case (infographics, translation-in-image, photorealism, world
  knowledge, logos, ads, comics, UI mockups, scientific/educational visuals,
  slides & charts, style transfer, virtual try-on, sketch→render, product
  mockups, in-image marketing text, lighting/weather, object removal,
  person-into-scene, multi-image compositing, interior swaps, holiday cards,
  merch concepts, and children's-book character consistency). Read the section
  matching the user's task and adapt the template.
