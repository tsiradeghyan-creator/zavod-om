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
| Video — dialogue/premium | **Veo 3.1** | the only engine with native 48kHz synced *dialogue*; 4K, Ingredients ref images |
| Video — volume/cheap | **Kling 3.0 Turbo** (Jun 2026) | faster/cheaper variant of 3.0; native 4K/60fps, 15s, first/last-frame chaining, multi-cut. Full 3.0 for heroes + phoneme-level lip-sync |
| Video — long beat / max refs | **Seedance 2.5** (official launch 2026-07-31) | 30s native single-pass · 4K route where available · audio alongside · **30 image + 10 video + 10 audio refs** · clay/white-model previz · timestamp-level controllable editing (fix one time range, keep motion/camera/light). 2.0 remains the fallback tier |
| ~~Video — Sora 2~~ | **deprecated 2026-04-26, API off 2026-09-24** | do not route here |
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

## Promo generation protocol (owner-approved only)

For `zavod-promo`, generated motion defaults to **Higgsfield** when the owner has that account/tooling
available. The pipeline must not silently substitute Remotion, Ken Burns, or another provider for the
approved video-generation route. In the Higgsfield lane composition/overlay is **ffmpeg only** (zero
Remotion); Remotion is a separate lane, never mixed in.

No image/video generation call is allowed until the owner has approved the exact prompt pack: prompt,
negative prompt, model, params, source media attachments, and cost estimate.

**"Background-default; test-then-trust with glyph QC."** Armenian is far rarer in training
data than CJK/Arabic, so never trust it blind:
1. Render a fixed Armenian **test-phrase set** per model.
2. **Character-by-character QC gate** (`motion-design.md` glyph gate).
3. AI-rendered **short display words** allowed ONLY if they pass; **body text stays Canva
   overlay** (the Background rule, `carousel-template.md`).

## Project pack / render dossier (absorbed 2026-08-25 — beat RedBox-style context persistence)

For any multi-shot, continuity-sensitive, or revision-prone asset, chat history is not the
production memory. Create or update a local render dossier before generation:

```text
media/video-projects/<project-id>/
  manifest.json        # model, duration, aspect, seed, cost, approval state
  brief.md             # owner-approved objective and constraints
  shot-table.md        # time | picture | sound | shot, copied from storyboard.md
  refs/                # approved subject/object/environment/audio refs only
  keyframes/           # accepted first/end frames by shot number
  prompts/             # sealed prompt per shot + negative constraints + prompt version
  clips/               # generated drafts/finals
  qc/                  # glyph gate, no-faces, continuity, artifact reports
```

- **Mode lock:** label each shot `text-to-video`, `reference-guided`, or `first-last-frame`.
  First/last-frame mode requires exactly two images with explicit start/end semantics; style
  references alone stay `reference-guided`.
- **Reference inheritance:** build the core environment master first, then generate later
  keyframes from the same environment anchor + the shot-specific delta. Do not rewrite the
  whole world for every frame.
- **Approval boundary:** no paid model run, likeness use, brand-identity change, publishing, or
  account/tool migration happens from the dossier without Ani's explicit approval.
- **Our edge:** generic video-director skills preserve context; this dossier also carries
  Armenian glyph QC, no-faces verification, rights state, cost state and Maghakian restraint.

## Consistency kit (the new continuity standard)

- **House reference sheet:** 3–5 approved BG/style images, fed as image references —
  Veo **Ingredients** / Kling **Elements** / Seedance **@Image** tags. This replaces the
  old character-sheet method (`cinematography.md`).
- **Seedance 2.5's 50-material ceiling — use it for coverage, not for clutter.** The whole
  shot-relevant look bible can fit in one call (environment hero, subject/object sheet, subtext
  object, palette plate, audio bed) across 30 image + 10 video + 10 audio refs. But @tag hygiene
  below still rules: **never pass a reference for something absent from the shot** — every slot is
  another chance to force an object into frame. Pass the shot's own anchors, not the series' whole
  library.
- **Controllable editing (2.5) = the retake tool.** When a take is right but the subject is
  wrong, re-render with the subject replaced and the original's motion/camera/lighting preserved,
  instead of re-rolling the whole shot and losing the blocking. Under the no-faces rule this is
  for hands/objects/wardrobe continuity — it is NOT a face-swap path.
- **Start/end-frame chaining** for episode continuity: last frame of shot N = first frame
  of shot N+1 (the director locks entry/exit frames — `director-craft.md`).
- Optional **FLUX LoRA fine-tune** on fal for the editorial look when a series needs it.
- **No faces by default** — hands/backs/objects/reflections-without-identity (brand rule).
  ՄԻԱԿ բացառությունը՝ licensed/owned դեմքերը Identity-lock դարպասով (§ ներքևում) և licensed
  poster-as-prop outpaint-ը, որտեղ պաստառի սեփական դեմքերը մնում են 100% անփոփոխ
  (`carousel-khaghaliq-prompts.md`)։ Նոր դեմք AI-ով չի ստեղծվում երբեք։

## Seedance @tag & sealed-prompt discipline (absorbed from Higgsfield `seedance-clean`, 2026-07-04)

Engine-layer rules for reference-tagged generation (Seedance @Image/@Video/@Audio; same logic
for Kling Elements / Veo Ingredients). The DoP's block-prompt structure lives in
`cinematography.md`; these are the failure-mode laws the engine layer enforces:

- **Context isolation — every prompt is a sealed single-shot document.** The engine has no
  memory of previous shots. Never carry in: scene numbers, script headings, "as above /
  continues" phrasing, summaries of prior scenes, or unused tags/characters. Continuity is
  re-stated explicitly (or via start/end-frame chaining above), never implied.
- **@tag hygiene:** reference sets appearance, text sets action. Keep character text MINIMAL
  next to a reference — long appearance prose fights the image and degrades it. Format:
  `@TAG: age + role/build + current state + unique visible features + action-critical
  details (+ voice only if it has a line). 100% matches the reference.`
- **Restate critical smalls in words** even when they're on the reference — small text,
  logos, exact colors get dropped by the model unless written out.
- **Never place an @tag in a shot where that object is absent** — the model will force it
  into frame.
- **Failure-mode protocols (tested fixes):**
  - Whip-pan needs ≥0.8s for the blur phase (0.3s settle → 0.8s WHIP → settle) or it renders
    as a plain hard cut.
  - Mixed speeds: ONE speed per shot start-to-finish; hard cuts only between speed modes.
  - Cracks/breaks without an impact point: "crowd PRESSES, not strikes · fracture originates
    from edge stress · pressure-based crack, edge-to-center" — kills the fake radial-impact look.
  - Extreme-FOV multishot (8°/107°): all 4 mechanisms or it breaks after 2–3 beats —
    sequence-wide identity lock · LENS LOCK opener per beat · LENS CHECK closer per beat ·
    color via material+light (never a list).
  - Observation/hidden-camera pattern = all 3 at once: out-of-focus foreground occlusion
    (20–30% of frame) + atmospheric haze + 8–12° tele vantage anchored at distance.

## Seed, prompt & cost registry

- Log **model / seed / prompt-version per asset** in the working `-prompts.md` file —
  this is also the AI-provenance trail for `business-affairs.md`.
- **Cost tracking:** use the official fal MCP `get_pricing` before a run and record the quoted
  endpoint/params in `manifest.json`; use the installed legacy server's `estimate_cost` / `usage`
  only when that server is the active route. Put a per-asset cost line in the deliverable.

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
- **Order:** lock look → upscale (Topaz/Kling-4K) → realism pass (low strength) → **grade under
  the series show-LUT** (`color-craft.md` still lane — stills get graded too, on Resolve 21's
  Photo page, BEFORE any text overlay) → grain on top. Re-run the glyph gate if any text region
  was touched.
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
