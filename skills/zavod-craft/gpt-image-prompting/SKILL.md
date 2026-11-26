---
name: gpt-image-prompting
description: >-
  OpenAI-specific GPT image prompting and API workflow skill. Use only when an
  OpenAI/gpt-image model is named or already chosen for generation, editing,
  image prompt repair, UI/infographic/logo/ad mockups, compositing, product
  mockups, or character-consistency image work.
metadata:
  version: 1.2.0
---

# GPT Image Prompting

Write effective prompts and API calls for OpenAI's `gpt-image` models. The
goal is production-quality, controllable output with fewer retries — by being
explicit about structure, constraints, and what must change vs. stay the same.

Scope gate: a bare "make an image" request is not enough. Route engine-neutral
still-image work to `banana-pro-director-2.0` (the studio default for stills),
Nano Banana/fal work to `fal-ai-media`, and Higgsfield platform work to
`higgsfield`.

Before writing a prompt, run `film-crew` (single-shot mode for one shot, full mode for several) per CLAUDE.md, and take its plan as input. If a film-crew plan already exists, use it.

## Safety Boundaries

- Verify current OpenAI image model names, parameters, prices, and policy
  constraints before presenting them as current or running paid generation.
- Do not spend credits, upload private/sensitive images, or publish outputs
  without explicit approval.
- Do not imitate private likenesses, voices, IDs, protected characters, logos,
  or brand assets without clear authorization.
- Do not overwrite source images or generated deliverables unless the user asks.
- For exact text, logos, UI, charts, and Armenian typography, prefer editable
  overlay or programmatic composition when image-model text may be unreliable.

## How to use this skill

1. **Identify the job**: generation (text → image) or edit (text + image →
   image), and the use case (infographic, logo, ad, photorealism, UI mockup,
   translation, style transfer, try-on, compositing, object removal, lighting
   change, product mockup, character consistency, slide/chart).
2. **Pick a model + quality** using the rules below (default `gpt-image-2.6-flare`, verify live).
3. **Write the prompt** following the fundamentals below. For a specific use
   case, read `references/use-cases.md` for a matching template.
4. **Emit runnable code** using the setup helper in
   `references/api-reference.md`, unless the user only wants the prompt text.
5. **Iterate small**: change one thing at a time and re-state the invariants
   so the image doesn't drift.

## Model selection (quick rules)

Checked against OpenAI's API reference and image guide on 2026-11-26 (model names move fast:
confirm with the live reference before a paid batch).

- **Current family (Sept 2026 onward):** GPT Image 2.5 shipped 2026-09-08 in two models,
  `gpt-image-2.5-flare` (fast, "higher-quality images than GPT-Image-2 at 50% lower
  latency") and `gpt-image-2.5-sunburst` (extra precision for detailed work, slower), with
  dated snapshots `-2026-09-08`. The image guide now names **GPT-Image-2.6 Sunburst / Flare**
  (`gpt-image-2.6-sunburst`, `gpt-image-2.6-flare`) for new integrations.
- **Default:** `gpt-image-2.6-flare` for most work; `-sunburst` for detailed creative work,
  dense text and identity-sensitive edits. If a 2.6 feature you need is not documented yet,
  use the 2.5 model of the same name, whose features are documented. Pin a dated snapshot
  for a production run that must not change.
- **`gpt-image-2`** stays valid (and is what Higgsfield's "GPT Image 2" exposes); use it when
  the user names it or a platform only offers it.
- **Quality:** `low` / `medium` / `high` on all GPT image models; the 2.5 models also take
  `xhigh` and `max`.
- **`input_fidelity`:** leave it out on `gpt-image-2` and newer; those models process every
  image input at high fidelity and the API does not let you change it.
- **Transparent backgrounds:** supported on the 2.5 models (and their snapshots); on
  `gpt-image-2` it is a **preview** feature. Use `png` or `webp` output with `transparent`.
  Developers report occasional grey edge halos and ignored requests, so check the alpha
  channel; the reliable fallback is a flat plain background plus a cutout.
- **Legacy:** `gpt-image-1` was shut down on 2026-10-23. `gpt-image-1.5` and
  `gpt-image-1-mini` remain for validated older workflows and cheap batches.

Common sizes (same rules on `gpt-image-2` and the 2.5 models): `1024x1024` (square default), `1024x1536`
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
