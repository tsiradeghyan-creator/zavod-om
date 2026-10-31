# Cinematography — Օպերատոր-պաստանովշիկի վարպետություն (FILM MODE)

World-class DoP craft + the translation layer that turns it into AI-video prompts
(Kling/Veo/Seedance via fal-ai) and into real smartphone/DSLR setups. The director
(`director-craft.md`) says what to feel; this file makes the light and lens say it;
`color-craft.md` keeps it consistent in the grade.

## Lighting (the mood engine)

- **Motivated low-key = the house drama look** (the «Խաղալիք» palette: black #0D0D0D,
  gold veining, one warm practical). Every light needs an excuse in the world: window,
  lamp, fridge, phone screen.
- **Contrast ratio by register:** comedy (A3) 2:1 flat & bright · daily drama 4:1 ·
  thriller/«Ճերմակ շապիկ» mood 8:1+, single hard source, deep falloff. Metering: ratio =
  meter key vs fill at the face, or eyeball on waveform — drama side sits 2–3 stops
  under key.
- **Three-point baseline, then subtract:** key (motivated) → fill (bounce, NOT a lamp —
  use negative fill to deepen drama) → rim/hair (separates from dark backgrounds; coral
  or steel-blue rim = the brand's accent trick).
- **Book light:** bounce the COB into polyboard, then THROUGH diffusion (shower
  curtain/half-grid) — the wrap-around interview key; use for confession-register
  face-to-camera pieces.
- **Window discipline:** never raw window — tape diffusion (216/250) on the glass or net
  curtain; key from the short side (far cheek) for drama, broad side for warmth.
- **Mixed-Kelvin as subtext:** warm 3200K inside / cool 5600–7000K window, 1–2 stops
  apart, cool side always dimmer = the past vs the present in one frame; mixed light =
  a character torn (use sparingly, on turns).
- **Atmosphere:** haze before beauty — light haze makes the practical-deep-in-background
  read as volume rays; AI prompt words: "volumetric haze, atmospheric depth".
- **Practical-driven night:** night = pools of motivated warm practicals + one
  steel-blue ambient base 2 stops under; never an even "night wash".
- **Golden hour & day-for-night:** golden hour = 25 min — block and rehearse before
  sun; day-for-night: underexpose 2 stops, kill the sky, blue-shift in grade
  (`color-craft.md`), rim with hard "moon" source.
- **Ani face-to-camera kit (the workhorse):** big soft key 45° off-lens at window side,
  negative fill opposite, warm practical deep in background, camera at eye level.

## Lens language (focal length = psychological distance)

| mm (FF) | Feel | Use |
|---|---|---|
| 24–28 | space distorts, world presses in | panic, wards, crowds — rare, on turns |
| 35 | honest, documentary | daily-series spine, walk-and-talks |
| 50 | neutral human eye | dialogue masters |
| 85–100 | compressed, intimate, isolating | the turn's CU, longing, portraits |
| **macro / probe** | extreme detail, world dissolves to one object | **"legacy mood"** — the writer's desk, the saved cigarette, the anchor; the subtext object alone |

**Legacy-mood macro:** when the target is the screenwriter's workspace or a key subtext object,
go aggressively to a **macro/probe lens** alongside the 35/50mm — the detail fills the frame and
the world falls away, building deep memory/mood. Pairs with the 120fps overcrank + probe-lens
prompt language below. (Spatial/light accuracy on these comes from the previz start-frame —
`storyboard.md`.)

Depth of field = attention: f/1.8 isolation for inner states; f/5.6+ when the WORLD is
the point (her EWS of ruins/village). Rack focus only with a story reason (the object
behind the lie comes sharp).

## Composition (her visual symbols built into frames)

- **Negative space = loneliness** (the fish/aquarium motif) — put the character at a
  third, give the emptiness the rest.
- **Frame-within-frame = entrapment** — doorways, windows, the ward's glass.
- **Centered symmetry = control/coldness** (the cold protagonist's frames center her;
  the moment she breaks, break the symmetry).
- **Headroom tight on power, loose on lost souls; leadroom toward the unsaid.**
- **9:16 vertical zones:** top 15% and bottom 20% are UI graveyards — eyes and the
  subtext object live in the middle 65%; compose depth (FG object / face / BG context).

## Movement (the camera is the narrator's breath)

Static tripod = her default restraint · slow push-in (5–10%) = realization · handheld
(subtle) = the world destabilizes · gimbal float = dream/memory (selavi sequences) ·
whip/snap = comedy only. NEVER move without a narrative verb. One move per scene max
in drama registers.

## Modern camera FX (2026 toolkit, restraint-filtered)

| ALLOWED (with discipline) | FORBIDDEN (trend-bait vs restraint brand) |
|---|---|
| Halation + Black Pro-Mist 1/4–1/2 look — "filmic halation, gentle bloom on practicals": gold practicals bloom on #0D0D0D | FPV drone language |
| Subtle anamorphic texture, memory/dream register ONLY — "subtle anamorphic character, oval bokeh"; NOT streak flares | Snorricam |
| Parallax foreground occlusion — "shot through a doorframe/foreground object": extends frame-within-frame, hides faces | Whip-pan transitions |
| Speed ramp ONLY as 60→24fps settle INTO stillness on the turn | Infinite/AI-zoom transitions |
| 120fps overcrank for single ECU subtext objects (smoke, fabric, pouring coffee) | Tilt-shift miniaturization |
| Probe-lens macro language in AI prompts — "extreme macro, probe lens perspective" | Lens whacking |
| Mirror/prism only as reflection-without-identity | — |

## → AI-PROMPT TRANSLATION TABLE (DoP language → engines, verified July 2026)

**Vocabulary law (beats every generic prompt skill):** ban "cinematic / epic / stunning /
beautiful / dramatic / masterpiece" — engines average them to mush. Every adjective is replaced
by **environmental pressure + a physical specific**: not "moody lighting" but "cold refrigerator
light on wet enamel"; not "tense" but "fluorescent flicker, a fly on the glass". The world does
the emotion. (`ai-pipeline.md` enforces this as a prompt gate.)

**Grade words are banned too (flat-source law, `color-craft.md`):** the palette line is **art
direction, not a grade** — name what is physically in frame (the gold practical, the wet enamel,
the tungsten bulb, the wardrobe). Never "teal-and-orange grade / heavily graded / LUT applied /
colour-graded look": a baked-in look leaves the colourist no headroom, and cross-engine matching
dies with it. The engine lights the scene; `color-craft.md` grades it.

Build every video prompt as: **[shot size + lens feel] + [subject & action] + [lighting
recipe] + [movement] + [palette/grade] + [texture] + [audio bed]**. House template:

> "Cinematic {ECU|close-up|medium|wide} shot, {85mm portrait compression, shallow depth
> of field f/1.8 | 35mm documentary feel}, {subject + ONE action}, motivated low-key
> lighting from {a warm practical lamp | a cold window}, deep shadows, negative fill,
> {coral|steel-blue} rim light, {static tripod | slow 8% push-in | subtle handheld},
> palette: black #0D0D0D with gold accents, filmic grain, 4K, {audio bed: ambient
> written out — "distant traffic, clock ticking"}, {start frame: <image>}"

| Engine | State (verified 2026-07-31) | House rule |
|---|---|---|
| Veo 3.1 | the only model doing native 48kHz synced **dialogue** (not just SFX) · native 9:16 · true 4K · "Ingredients" = up to 3 ref images | write the ambient sound INTO the prompt ("distant traffic, clock ticking"); never leave audio unspecified or the engine invents it |
| Kling 3.0 (Feb 2026) · **3.0 Turbo** (Jun 2026) | Omni One multimodal base · native 4K/60fps · 15s clips · phoneme-level multi-character lip-sync (best in class) · first/last-frame control · Elements · multi-cut (≤6 shot changes/gen). **Turbo** = faster/cheaper variant of the same generation | chain shots: last frame of shot N = first frame of shot N+1. Turbo is the volume/draft lane, 3.0 proper for heroes |
| **Seedance 2.5** (official launch 2026-07-31) | **30s native single-pass** (2.0 capped at 15s) · native 4K route where available · audio generated alongside · **up to 30 images + 10 videos + 10 audio refs** in one request · **clay/white-model previz** to lock space + composition + motion before style · **timestamp-level controllable editing** — alter a time range / subject / camera while preserving approved motion, lighting and continuity | THE consistency standard. The 50-material ceiling means the whole shot-relevant look bible can ride in the call; the 30s window means a full beat is ONE generation, not four chained |
| ~~Sora 2~~ | **deprecated 2026-04-26; API shuts down 2026-09-24** | do not route here; do not cite it in a client deck |

**What the 2.5 jump actually changes for the DoP:** with 30s in one pass, the unit of generation
can become "a beat" — so the *lighting recipe must hold across an internal cut*, which is exactly
what the LOCATION MAP + POSITIVE LOCKS blocks below are for. Do not celebrate the long window by
writing a long scene: restraint still says hold the frame. Use the extra seconds on the hold, not
on more coverage.

**Timestamp-edit handoff (absorbed 2026-08-25 from Seedance 2.5's official editing path):**
when only one segment is wrong, do not reroll the whole take. Mark an edit window in the DoP
notes — `00:08-00:12 camera only`, `00:15-00:18 hand action only`, `00:20-00:23 light spill only`
— plus the continuity locks that must survive before/after the edit. This beats generic "fix it"
prompts because the cinematographer names the one variable allowed to change. Under the no-faces
rule, this is especially useful for hands, props, wardrobe, lighting direction and subtext objects;
faces/likeness remain rights-gated and normally absent.

- **Engines now parse real DoP grammar** — "dolly", "crane", "85mm", "rack focus" no
  longer drift on Veo 3.1/Seedance; the old "avoid pan/tilt" caution applies only to
  legacy Kling 2.1.
- **Consistency across shots:** reuse the exact lighting/palette block verbatim in every
  prompt of a scene; recurring subjects ride Seedance @Image tags / Kling Elements /
  Veo Ingredients; render variations of ONE master frame, not new worlds per shot.
- **No faces rule:** hands, backs, silhouettes, objects, reflections-without-identity —
  the DoP toolkit replaces faces with the subtext insert (her ECU objects).
- **Armenian text NEVER inside AI video** — Background rule applies to motion too;
  burn text in post (`post-production.md`).

## Seedance 2.0 LONG-PROMPT PROTOCOL (absorbed from Higgsfield `seedance-clean`, 2026-07-04)

The one-sentence house template above stays the default for SHORT prompts (≤1 shot, ≤10s).
For a long Seedance 2.0 multi-shot document, write a **block-structured prompt** instead —
blocks in this order, use only what the shot needs, drop the rest:

```
SCENE CONTEXT → ACTIVE REFERENCES (@tags) → LOCATION MAP (FG/MG/BG + camera + light + paths)
→ FIRST FRAME / BLOCKING → FORMAT MODE → OPTICS → CAMERA → ACTION → PERFORMANCE
→ PHYSICS → LIGHTING → [COLOR GRADE] → [WARDROBE] → AUDIO → STYLE + OUTPUT SETTINGS
(suffix) → POSITIVE LOCKS (last)
```

- **Style is distributed, never a prefix:** light→LIGHTING, color→COLOR GRADE or folded into
  LOCATION/LIGHTING, skin/acting→PERFORMANCE, format/grain→STYLE+OUTPUT suffix. The prompt
  opens on SCENE CONTEXT, never on a style block. (House palette/grade lines still come from
  the look bible — reuse verbatim across the scene as before.)
- **POSITIVE LOCKS block closes every long prompt:** short hard fixers in positive form
  ("headlights stay glowing in every shot"), continuity lives here. Positive phrasing only —
  state the target, never the prohibition ("stays upright, feet planted", not "does not fall").
- **FORMAT MODE picks cut precision:** oner ("one continuous shot, the camera does not cut on
  its own") · sequential CUT 1/CUT 2 (no timecodes) · timed multishot (HARD CUTs at stated
  seconds) · freestyle b-roll. When cuts are specified, always add the lock: *"cuts only at
  the specified points, the camera does not cut on its own."* Cut types: HARD / SMASH /
  MATCH / INSERT / REVERSE / WHIP.
- **Quantification laws:** speeds in km/h ("camera pans at 5 km/h", not "slow") · atmosphere
  in % and meters ("fog density 40%, haze visible at 15 m") · atmosphere builds in steps
  across shots (20% → 40% → 60%) · giant scale via human stacking ("as tall as four humans
  stacked"), never raw meters · WB in Kelvin fixed per scene (3200/4000/5600/8500K — already
  house law) · left/right always from the camera.
- **FOV° anchor table (Seedance dialect):** 180° fisheye · 107° ultra-wide · 84° wide ·
  63° observational · 47° neutral · 29° portrait-compress · 18° close-portrait · 12°
  tele-detail · 8° extreme-tele. Discrete steps only (no "23°"); multishot = FOV per segment
  + "no drift mid-segment"; CAMERA block sits 3rd in the core layer order (subject → action
  → camera → style → constraints) — at the end FOV gets ignored, at the front it fights identity.
- **✅ A/B RESOLVED (2026-07-31) — it was a false binary.** The open question was FOV° (per
  `seedance-clean`) vs named mm (per our table). ByteDance's own Seedance prompt guidance backs
  **neither extreme**: it treats lens as **buckets** — wide (24–28mm feel) · normal (35–50mm
  feel) · telephoto (85mm+ feel) — and advises against exact millimetres "unless necessary",
  because Seedance responds to human-rhythmic description, not photographic metadata
  (`f/2.8, ISO 800` is noise to it). Discrete FOV° was over-precision in the other direction.
  **House ruling:**
  - **Seedance dialect:** lead with the bucket, append the approximate focal only when the
    compression itself is the point — `[shot size] + [movement] + [angle], [bucket or ~focal]`.
    Keep the FOV° table above as a *reference for reading* other people's prompts, not as our
    output format.
  - **Veo / Kling:** keep naming real gear and mm — they parse "85mm / dolly / rack focus" fine.
  - **Universal:** *zoom ≠ dolly* — zoom changes focal length (the image compresses), dolly moves
    the camera (perspective shifts). Engines trained on real footage honour the distinction, so
    use the term you actually mean; this is where most "why did it look wrong" cases come from.
  - Our lens table (§ Lens language) stays the **decision** tool — it says WHY 85mm; the dialect
    only governs how that decision gets typed into a given engine.

## Real-set quick kits (when shooting, not rendering)

- **Phone kit ($0–20):** window key + white card fill + lamp in BG; lock exposure/WB;
  4K **25fps, 1/50** (50Hz region — 1/60 bands under local lighting); variable ND for
  outdoors; Blackmagic Camera app or Final Cut Camera (free, manual everything).
  iPhone 17 Pro: Apple Log 2 + ProRes RAW + open gate via Final Cut Camera 2.0 — log
  always for FILM MODE, grade to house palette (`color-craft.md`). A $20 lav into the
  phone beats any on-board mic. Vertical: shoot 4K wide, punch in post; wipe the lens.
- **One-light kit:** 60W COB through a softbox 45° (or lantern softbox = soft toplight
  for table scenes) + negative fill + practical — covers 90% of the agency's
  face-to-camera and product/poster-prop shots. Two RGB LED tubes (~$80/pair) = the
  coral/steel-blue rim engine. 5-in-1 reflector: the black side IS the negative fill.
- Slate every take (scene/take in frame 1 sec) — post thanks you.

## DoP pre-render/pre-shoot checklist
- [ ] Lighting recipe written per scene (key source, ratio, rim color) and reused verbatim.
- [ ] Lens/size chosen per the director's emotional map (not variety for its own sake).
- [ ] Vertical safe zones respected; subtext object planted in frame.
- [ ] AI prompts carry the full house template incl. {audio bed} + {start frame};
      consistency via @Image/Elements/Ingredients; no faces, no Armenian text.
- [ ] FX from the ALLOWED column only — nothing off the FORBIDDEN list.
- [ ] Grade intention noted for `color-craft.md` (register look + contrast ratio).
