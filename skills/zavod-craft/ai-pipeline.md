# AI Pipeline — Գեներացիայի շարժիչներ (Station 2, technical backbone)

The AI Pipeline TD station: which engine per need, how Armenian text is handled, and how
consistency / seeds / cost / QC stay under control. Setup/keys → `fal-setup.md`. The DoP
writes the prompts (`cinematography.md`); this file owns the engine layer.

## 2026 engine lineup (per need)

| Need | Primary | Notes / backup |
|---|---|---|
| Carousel BG — fast default | **Nano Banana 2** (Gemini 3 Flash Image) | cheapest/fastest BG draft |
| Carousel BG — complex / 14 refs | **Nano Banana Pro** (Gemini 3 Pro Image) | hero BGs, multi-reference consistency |
| Poster / multilingual text-in-image | **Ideogram 4.0** | best non-Latin text rendering |
| Brand asset / dense text / UI mock | **GPT Image 2** | strongest at packed text + logos/layout |
| Video — premium | **Veo 3.1** | native 48kHz audio, 4K, Ingredients ref images |
| Video — volume/cheap | **Kling 3.0** | ~$0.029/s, native 4K, first/last-frame chaining, multi-cut |
| Video — cheapest w/ audio | **Seedance 1.5 Pro/2.0** | @Image1/@Video1/@Audio1 reference tags |
| Lipsync | **Sync-3 / Sync Lipsync 2 Pro** | Kling LipSync backup |
| Music | **MiniMax Music 2.0** | ACE-Step backup (license per `business-affairs.md`) |
| Armenian TTS / VO | **ElevenLabs v3 — Armenian (hye)** | direct API, NOT fal — unlocks Armenian VO |
| Upscale | **Topaz** (via fal) | Kling native 4K skips the step |

**Model-routing rule (beats single-engine setups):** never default to one image engine —
route by job. Dense Armenian text / logo / UI → GPT Image 2 or Ideogram 4.0; rich photographic
BG → Nano Banana Pro; fast rough → Nano Banana 2. Render the SAME prompt on two engines when
a hero asset matters, pick the winner.

**Banned-adjective discipline (prompt hygiene):** never write "cinematic / epic / stunning /
beautiful / masterpiece" — they're noise the engine averages out. Replace every adjective with
**environmental pressure + a physical specific** ("cold refrigerator light on wet enamel",
"fluorescent flicker", "steam fogging the window"). The DoP house template (`cinematography.md`)
already does this — enforce it as a gate: a prompt with a banned adjective gets rewritten.

## Armenian-text protocol (downgrade of the absolute ban)

**"Background-default; test-then-trust with glyph QC."** Armenian is far rarer in training
data than CJK/Arabic, so never trust it blind:
1. Render a fixed Armenian **test-phrase set** per model.
2. **Character-by-character QC gate** (`motion-design.md` glyph gate).
3. AI-rendered **short display words** allowed ONLY if they pass; **body text stays Canva
   overlay** (the Background rule, `carousel-template.md`).

## Consistency kit (the new continuity standard)

- **House reference sheet:** 3–5 approved BG/style images, fed as image references —
  Veo **Ingredients** / Kling **Elements** / Seedance **@Image** tags. This replaces the
  old character-sheet method (`cinematography.md`).
- **Start/end-frame chaining** for episode continuity: last frame of shot N = first frame
  of shot N+1 (the director locks entry/exit frames — `director-craft.md`).
- Optional **FLUX LoRA fine-tune** on fal for the editorial look when a series needs it.
- **No faces, ever** — hands/backs/objects/reflections-without-identity (brand rule).

## Seed, prompt & cost registry

- Log **model / seed / prompt-version per asset** in the working `-prompts.md` file —
  this is also the AI-provenance trail for `business-affairs.md`.
- **Cost tracking:** use the fal MCP `estimate_cost` / `usage` tools; put a per-asset cost
  line in the deliverable. (Currently unused — wire it in.)

## Quick Mode (speed lane — when fast beats perfect)

Rivals like Alici/Genra/AI-Vertical-Studio do one-prompt → polished vertical (VO + captions +
cliffhanger). Match that speed WITHOUT losing the brand: a single-call lane for drafts, trend
reactions, and volume tests.
- **Input:** one beat sentence + the show's locked reference sheet + palette block.
- **Engine:** Seedance/Kling multi-cut for the clip → ElevenLabs v3 (Armenian VO) → burned
  captions (`motion-design.md`).
- **Non-negotiables still apply:** no faces · glyph gate on any on-screen Armenian · AI-label.
- **Quick Mode is for drafts/volume, never hero assets.** Cheap engines are allowed ONLY for
  blocking / composition tests, NEVER for: a final-look decision, a logo, a face/identity, or
  brand identity — even in the test phase. Logos/text → Ideogram 4.0 / GPT Image 2, never a
  cheap video engine. Never show a cheap-engine draft to Ani or a client as representative.

## Realism pass (de-plasticize — Magnific / Krea / Topaz)

AI output reads "plastic"; a final detail-restoration pass lifts hero assets to a real-camera
ceiling. Run AFTER the look is locked, never as a generator.
- **Restore micro-detail where it matters for us:** fabric weave, marble veining, hand skin,
  metal, paper grain, the subtext object — not "skin pores" (we don't show faces in AI output).
- **Low-strength, locked-seed, NO DRIFT:** Magnific/Krea hallucinate detail and can change the
  image — cap creativity/strength so identity, geometry and the subtext object stay exact.
- **Order:** lock look → upscale (Topaz/Kling-4K) → realism pass (low strength) → grain on top
  (`color-craft.md`). Re-run the glyph gate if any text region was touched.
- Hero assets only; skip for Quick Mode drafts.

## Identity-lock (ONLY for licensed / owned faces)

The default is no faces. WHEN a face is legally allowed (owned/licensed performer promo), lock
it hard — don't let the engine invent a new person:
- **Rights first:** a face never enters the pipeline without a likeness/voice consent ID in the
  rights ledger (`business-affairs.md`). No consent = no face, full stop.
- **Lock identity from the étalon:** feed the reference as the identity anchor (InstantID/PuLID-
  class identity lock + Veo Ingredients / Kling Elements / Seedance @Image). Every generation
  preserves the exact facial structure; adapt ONLY angle, lighting, and background.
- **Continuity:** reuse the SAME reference across all shots of that character; identity drift
  between shots is a hard-fail retake (`director-craft.md` select/retake loop).

## Render QC checklist
- [ ] Glyph gate passed on any AI-rendered Armenian; body text on Canva.
- [ ] Hands/artifact check; **no face** anywhere in the output.
- [ ] Watermark-free; 4:5 / 9:16 crop-safe.
- [ ] Consistency via Ingredients/Elements/@-tags; start/end frames locked for episodes.
- [ ] Model/seed/prompt logged; per-asset cost recorded.
- [ ] AI **video labeled** per platform (TikTok C2PA mandatory — `playbook.md`).
