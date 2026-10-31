# Storyboard — Ռասկադրովկա (UNIVERSAL production board)

The shot-by-shot visual plan a real crew (or an AI pipeline) shoots from. This is the single
most attended station: nothing reaches the set or the render without a board. It UNIONS the
professional shot-list rigor of StudioBinder, the look-bible discipline of the best AI storyboard
skills, **and** a register system that adapts the board to ANY production — ad / commercial,
film, series, animation, social short, music video — then annotates every frame with the full
technical card (camera · lens · light · color gradient). No rival combines all three; that is our edge.

This is a **universal production zavod**, not one brand's tool. Maghakian's quiet restraint is ONE
register preset (see *Register presets* below), not the global law — a soda splash ad and a
mythic animated series get their own register, sheet type, cut-arc, and identity policy.

Owned by the storyboard / previz artist (`production-team.md`). Inputs: the director's
objective/turn (`director-craft.md`). Lens/light recipes: `cinematography.md`. Grade/gradient:
`color-craft.md`. Sound: `sound-craft.md`. AI-render bridge: `ai-pipeline.md`.

## Board mode — pick the REGISTER first (sets everything downstream)
Choose the register before the look bible; it decides the reference-sheet type, the cut-arc, and
the identity/face policy. Don't force a narrative-drama template onto a product spot.
| Register | Reference sheet | Cut-arc (Section "Narrative progression") | Identity / face policy |
|---|---|---|---|
| **Character drama** (film, series, micro-drama) | Subject sheet | establishment → development → intensification → peak → payoff | per brand preset (Maghakian = no actor face) |
| **Product / commercial** (ads) | **Hero-Object sheet** | reveal → material macro → motion/energy → beauty payoff | n/a — hero is the object; people are context |
| **Action / sports** | Hero-Object + subject | build → impact → kinetic peak → settle | generic athletes/faces OK unless brand-locked |
| **Animation / mult** | Model sheet + style frames | per story (drama or product arc) | designed characters, not photo identity |
| **Social / marketing short** | Subject or Hero-Object | hook (first 1s) → proof → turn → CTA frame | per brand preset; vertical safe-zones always |

## The look bible (lock ONCE per production — keeps the board consistent)
Before any frame, lock the shared block every panel inherits:
- **Palette + grade:** black #0D0D0D, gold accents, show accent; the gradient logic
  (e.g. warm tungsten foreground → cold window background = past vs present).
- **Contrast ratio by register:** comedy 2:1 · daily drama 4:1 · thriller/«Ճերմակ շապիկ» 8:1+.
- **Lens set:** 35 documentary spine · 50 dialogue · 85–100 the turn (`cinematography.md`).
- **Grain stock:** ONE per series, logged · **movement default:** static tripod (restraint).

## Board header — shared choices (lock once, print across the top)
One narrow full-width strip every panel inherits — the board's contract:
- **Cut count · total duration · frame format** (default 2.39:1 anamorphic; 9:16 for Reels).
- **Color palette** strip + **show-LUT** note (`color-craft.md`) — name each swatch with its role
  (e.g. SUNSET ORANGE = warm key · NEON CYAN = accent · CHARCOAL = ground), not just an unlabeled strip.
- **Mood keywords:** 4–6 words that fix the emotional register for the whole board (e.g.
  *vigilant · athletic · cinematic* / *refreshing · premium · crisp* / *EXPLOSIVE · ELITE · KINETIC*).
  Every panel's lighting + action must read back to these.
- **Environment fingerprint:** one dense running sentence of 3–5 distinctive features that must stay
  recognizable in EVERY relevant shot (e.g. "cracked archway · gold samovar · north-window light ·
  wet cobblestone" — the prompt-ready format the reference sheets use).
- **Subject continuity anchors:** the immutable identity facts — wardrobe construction, footwear,
  accessories, props, distinguishing wear (NOT faces for AI frames — see hard rule).
- **Primary screen direction** (L→R / R→L) + the locked **180° axis**.
- Board labels may be **EN or RU** (owner's call); Armenian glyphs never go INSIDE an AI cinematic
  frame — only on the overlay/caption layer.

## Reference sheets (lock the WHAT before the HOW)
Before the panels, build the locked reference blocks the whole board inherits. Build the **Subject
sheet** for character registers, the **Hero-Object sheet** for product/commercial registers (often
both for action/sports), plus the environment plan always:
- **Subject sheet** *(character registers)* — front / side / back / three-quarter + 3–4 macro detail
  crops (fabric, tool, accessory, wear) + extracted palette strip, in neutral reference light that
  reveals construction (don't beautify or simplify). **Brand face rule (preset-conditional):** when a
  face-restricted preset is active (e.g. Maghakian) the sheet shows hands / back / silhouette /
  costume / subtext object — NOT the actor's face (faces only from licensed/owned material). Other
  registers may show faces; designed/animated characters use a full model sheet with expression row.
- **Hero-Object sheet** *(product / commercial registers)* — the product IS the hero, not a person:
  - **Hero views:** front · ¾ · side (· rear if it reads differently) in clean studio light.
  - **2+ material macros:** the surfaces that sell it — condensation & texture, cap threads / ridges,
    water beading, stitching, grain, specular edge. Macro is where premium lives.
  - **In-context / lifestyle frame:** the object in its real use/environment, once.
  - **Object classification + notes:** label it *HERO PRODUCT (not a character)* and lock the
    immutable facts — silhouette, proportions, material, **branding policy** (e.g. "no label / no
    logo"), grip/indent details. These are the continuity anchors for every panel.
- **Environment hero + top-down SET PLAN** — the single biggest upgrade to our board:
  - **Hero frame:** one wide establishing view preserving the reference's architecture, landmarks,
    terrain, weather, light (no new buildings / no redesign).
  - **Overhead plan** (readable, to rough scale): set geometry · subject start position + movement
    path · **numbered camera positions C1…Cn matching the cuts** · camera viewing directions ·
    camera move paths (start→end) · subject arrows · the **180° action axis** · primary screen
    direction · **key-light direction** · obstacles / doors / edges / landmarks.
  - Every camera position + move must be **physically possible** inside the mapped space.

### Inheritance ladder (absorbed 2026-08-25 — RainLib/RedBox/Seedance parity, with our gates)

Rival storyboard skills now win on context persistence: a core environment frame, stable anchor
phrases, and per-shot deltas. We keep that, then add the full card, Armenian/no-faces policy and
approval gates:

1. **Environment master first:** build the wide/core environment reference before any close-up.
   It must show layout, major props, light direction and the camera worldview for the whole
   sequence.
2. **Subject/object anchor block:** one exact phrase for the subject or hero object; for
   Maghakian/no-faces boards this phrase describes hands, silhouette, wardrobe construction,
   accessories and subtext object, never a generated actor face.
3. **Panel prompts inherit, then differ:** every panel repeats the same environment anchor and
   subject/object anchor, then changes ONLY the shot-specific delta: size, angle, action phase,
   pose, camera move, light change, duration.
4. **Transition pair field:** each card states how it exits and how the next panel enters —
   motion match, shape match, color match, action match, scale match, or hard cut. This is written
   on the board before editing so AI clips do not become isolated pretty shots.
5. **Dossier handoff:** once the board is approved, `ai-pipeline.md` receives a render dossier
   with `shot-table.md`, refs, keyframes, sealed prompts and QC receipts. The board is the brief;
   the dossier is the execution memory.

## The maximal shot card (under EVERY frame)

For each frame, the board carries this card — the world's-best annotation set:

| Field | What goes here |
|---|---|
| **Frame #** | scene.shot (e.g. 14.3) + the sketch/photo thumbnail |
| **The turn / beat** | why this frame exists — objective or turn (`director-craft.md`) |
| **Size** | EWS · WS · MS · MCU · CU · ECU (size = emotional job) |
| **Angle** | eye / low (power) / high (lost) / OTS / top / dutch (only at a flip) |
| **Lens (mm) + why** | 35 honest · 50 neutral · 85 isolate the turn — name the reason |
| **Aperture / DoF** | f/1.8 isolate inner state · f/5.6+ when the WORLD is the point |
| **Camera move + rig** | static / push-in ≤8% / handheld / gimbal float + tripod·slider·gimbal·crane |
| **Lighting recipe** | key (motivated source) · ratio · practical · rim color (coral/steel) · Kelvin (3200K warm / 5600K cool) |
| **Color gradient / grade** | palette + gradient direction + show-LUT note (`color-craft.md`) |
| **Subtext object** | the ECU symbol in frame — anchor, cigarette, laundry line (`art-department.md`) |
| **Action (verbs only)** | behaviour, never stated emotion: «fingers tighten on the cup» |
| **Pose / body blocking** | explicit body position per frame (Katalist-posing parity): posture · weight · hand placement · head turn / look-away · breath. In no-faces registers the pose IS the performance — script the reaction beat (what the hands do, not the face) |
| **Sound / audio bed** | ambience + sync FX + the silence beat (`sound-craft.md`) |
| **Continuity** | eyeline · screen-direction (L→R/R→L) · wardrobe/prop (`production-team.md`) |
| **Duration / fps** | seconds + 24/25fps (120fps overcrank only for the object insert) |
| **AI-prompt line** *(if rendered)* | the house render template (`cinematography.md` · `ai-pipeline.md`); build it off the Composition×Lighting×Pose menu in `prompt-axes.md` |
| **Transition pair** | exit/entry glue to the next panel: motion · shape · color · action · scale · hard cut; name the continuity anchor that survives |

## Coverage minimum per scene (what the board must contain)
Master · OTS pair (or singles for 9:16) · **the turn's CU** (held 2s longer) · **one subtext
insert**. One insert earns meaning; three make a commercial. Plant the cliffhanger object in an
early frame, ignored, so the payoff lands.

## Progression / cut-arc (each panel = a distinct job, never an angle variant)
The chronological row must move through beats, not repeat compositions. Use the arc that matches the
register (see *Board mode*):

**Character drama** (film, series, micro-drama):
1. **Establishment** — location, scale, subject position, the dramatic situation.
2. **Development** — push closer; the main action begins/continues.
3. **Intensification** — the face/hand/prop/reaction/decision that raises tension (the turn).
4. **Peak action** — the clearest, most dynamic readable moment.
5. **Payoff** — landing, reaction, reveal, consequence, or a strong final composition.

**Product / commercial** (no emotional turn — the object is the protagonist):
1. **Reveal** — establishing hero shot, the object readable in its space (often a crane/overhead in).
2. **Material macro** — push to the surface detail that sells it (texture, droplets, threads).
3. **Motion / energy** — the dynamic beat (splash, arc-around, kinetic launch) that gives life.
4. **Beauty payoff** — slow final hero hold, the clean composed packshot the viewer remembers.
(Action/sports = build → impact → kinetic peak → settle; same no-repeat-framing law.)

More than the base count → insert connective beats, never a duplicate framing.

## Panel caption (printed under each board frame)
One compact line, then one sentence:
`CUT N | focal length | duration | camera movement | shot size`
→ then a single sentence covering: visible action · camera behaviour · composition ·
**continuity link to the previous shot** (action phase + screen direction preserved).

## Lens & movement logic (pick by purpose, hold ONE family across the board)
| Focal (FF-equiv) | Use for |
|---|---|
| 18–24mm | extreme scale, strong environmental perspective |
| 28–35mm | wide action, spatial movement (the documentary spine) |
| 40–50mm | natural medium coverage, dialogue |
| 75–100mm | emotional compression, isolate the turn |
| 100mm macro | the subtext-object / material insert |

Moves allowed: locked-off · pan · tilt · dolly in/out · crane up/down · side-track · arc ·
handheld · controlled pull-out · crash-zoom (energy registers only) · rack-focus (focus pull, not a
move). Default still tripod for the quiet preset (restraint); commercial/action registers earn more
movement. Hold one coherent lens family + photographic character across the whole board.

## Register presets — house disciplines (apply the one the project selects)
A preset is a coherent bundle of taste rules a brand/register turns on. Maghakian-quiet is the
flagship preset, not the universal default; other clients/registers run different (or no) presets.

**Maghakian-quiet preset** (drama, the agency's own work — what makes a board *hers*, not generic):
- **Restraint:** hold the frame, cut late; melodrama is shot loud, Maghakian is shot quiet —
  when in doubt, wider, longer, stiller.
- **Behaviour over statement:** the card's Action field is verbs; emotion lives in the
  blocking and the subtext object, never in a caption.
- **The shield:** block the activity first (cooking, pottery, cleaning a wound); dialogue
  rides on it — board the hands, not just the face.
- **Face/text lock:** no actor faces in AI-rendered frames — hands, backs, silhouettes, objects,
  reflections without identity; Armenian text never inside the frame (`ai-pipeline.md` · `motion-design.md`).

**Product / commercial preset:** high-key clean studio or location, premium specular & material
truth, the object framed as protagonist; energy from the move and the splash/impact, not a face.

**Always-on (every register, not preset-specific):**
- **Vertical 9:16 board:** hero subject/object in the middle 65% (top 15% / bottom 20% are UI
  graveyards); depth not width (FG object / midground hero / BG context).
- **No AI text inside the frame** unless it passes the glyph gate (`motion-design.md`); brand
  copy and any non-Latin script ride the overlay layer, not the render.
- **Identity/rights:** use real faces only from licensed/owned material in ANY register.

## Continuity — non-negotiable (the drift killers)
Same subjects in every relevant panel — no duplicated/missing person, no face/age/hair/anatomy
or body-proportion drift, no costume/footwear/accessory/prop swap, no unexplained pose jump
between connected cuts. Preserve action phase + momentum, travel direction + screen direction,
environment geography + landmark positions, time of day/weather/light direction, and material
wear/dirt/damage. Never mirror asymmetric details (logos, text, weapons, costume). No extra/
fused limbs, no impossible camera placement, no repeated framing sold as a new cut.

## Workflow (real shoot)
1. Director marks objective / obstacle / turn / subtext-image per scene (`director-craft.md`).
2. Storyboard artist draws/photos each frame + fills the maximal card above.
3. DoP turns the lighting-recipe fields into a lighting plot + gear list (`cinematography.md`).
4. 1st AD breaks the boarded shots into the schedule, grouped by location; TURN scenes early
   in the day (`production-team.md`).
5. On set the board is the source of truth; the script supervisor logs continuity against it.
6. If AI-rendered: each frame's AI-prompt line + start/end-frame chaining drives the engine.

## Previz → start-frame (kill AI's spatial/light hallucination — CineTracer / Blender logic)

AI engines misread space and light when given only words. Ground them with a real reference:
- Build a fast **3D previz** of the key frame (CineTracer / Blender / UE5) with **physically
  accurate** light falloff, shadow depth, and object distance for the chosen lens (35/50/85mm).
- Render that previz frame and feed it as the **start frame** to Seedance/Kling/Veo — the engine
  inherits correct geometry and lighting instead of inventing them (`ai-pipeline.md` consistency).
- **Lean version (80% of the value, near-zero cost):** a single CineTracer/Blender still as the
  start frame beats a full UE5 pipeline — phase the heavy 3D only for complex hero scenes.

**In-engine whitebox previz (Seedance 2.5, official launch 2026-07-31 — the previz step moved inside the model):**
2.5 ships **3D white-model previz**: it locks space, composition and motion *before* style is
applied. That is the same job as our CineTracer/Blender start frame, one call earlier and at no
extra tooling cost — so it becomes the default previz lane for AI-rendered boards, with the
external 3D path kept for complex hero scenes and for anything that must be physically surveyed.
Our gates do not move:
- The whitebox is checked against the **top-down SET PLAN** (camera positions C1…Cn, 180° axis,
  key-light direction) — the engine proposing a camera does not make the camera *possible*. A
  whitebox that contradicts the set plan is rejected, not adopted.
- Whitebox → approved → THEN style. Never let the styled render be the first time the space is
  seen; that is how geometry drift enters a board.
- The whitebox is **planning scaffolding, never final pixels** — same law as the motion-animatic.

**30-second single-pass changes the panel math (read this before celebrating it):** with a full
beat renderable in one call, the temptation is to stop boarding and let the engine improvise the
middle. Don't. The board still specifies every cut, and **finals still render one panel at a
time with seed + start-frame chaining** — the long window is spent on the HOLD (restraint: the
frame that stays), not on unboarded coverage. Where a 30s pass genuinely serves a continuous
oner, the board carries it as ONE panel with internal beats marked on the Duration field, and
the animatic gate still locks tempo first.

## Timing pass — the board's Duration column is executable (animatic gate)
The per-frame **Duration/fps** fields are not notes; they are the cut. String the accepted
panels into a timed animatic (`animatic-editor.md`) BEFORE any expensive final render — the
same job Katalist's Premiere-timeline export does, but ours runs through the pacing gate:
hook lands? turn holds? any panel over/under? Adjusted durations flow BACK into the board's
cards, so the board and the animatic never disagree. No final motion render until the
animatic locks the tempo.

**Motion-animatic option (Katalist 2026 parity — their image-to-video animatics, our gates):**
for movement-critical boards (action beat, product splash, camera-move-heavy cuts), draft-render
individual panels image-to-video at the CHEAP tier (Seedance/Kling via fal, low res, panel's
AI-prompt line + start frame) and cut those clips into the animatic instead of stills — it
tests real motion + camera-move tempo, not just durations. Same laws: it runs through the
pacing gate, adjusted durations write back into the cards, and draft clips are throwaway
scaffolding — never final pixels (finals still render ONE panel at a time with seed +
start-frame chaining, `ai-pipeline.md`).

## Board review & versioning (sign-off discipline — Boords parity, run through our gates)
Boords made frame-level review its whole product (versioned boards, per-frame comments,
no-signup client links); we fold the discipline into the gate chain instead of a separate app:
- **Version the board** v1, v2 — never "final" (same law as `post-production.md`). Each
  version keeps its full card set, so a reverted panel restores its whole card, not just
  the image.
- **Frame-level notes:** review comments attach to the frame's card (a NOTES line), not to
  chat. Every note is either RESOLVED (card updated) or REJECTED (reason logged) — and
  unresolved notes BLOCK the animatic gate, not the other way round.
- **Owner sign-off is recorded against the board version** the owner actually saw; an
  approved v2 does not carry approval to v3 (matches the zavod hash-bound approval law).

## Two ways to output the board
- **One-shot AI board** (fast): `nano_banana_pro` can render the WHOLE A3 bible — header, subject
  ref, environment + top-down plan w/ camera map, the 5 caption-lined panels, lighting/mood — in a
  SINGLE generation with legible text (give it one detailed prompt + the real-property reference).
  Best for internal planning boards. Watch for minor label dupes; not for PUBLISHED brand posts
  (where fonts are locked → use HTML overlay). Proven 2026-06-27 (desert-owl).
- **HTML-assembled board** (precise): AI for imagery only + HTML/CSS for all layout & exact brand
  fonts, Chrome-rendered. Use when font/precision/brand-lock matters.

## Storyboard checklist
- [ ] Register chosen (character / product / action / animation / social) — it sets the sheet type,
      cut-arc, and identity policy below.
- [ ] Board header locked (cut count/duration/format, named palette, **mood keywords**, environment
      fingerprint, continuity anchors, primary screen direction + 180° axis).
- [ ] Reference sheet built for the register (Subject sheet / **Hero-Object sheet** / model sheet) +
      environment plan; the sheet's anchors match every panel.
- [ ] Inheritance ladder followed: environment master first, stable subject/object anchor block,
      panel-specific deltas only, and transition pair named on every connected cut.
- [ ] Top-down set plan drawn; camera numbers C1…Cn match the panel cuts; every path physically possible.
- [ ] Look bible locked (palette/gradient, contrast ratio, lens set, grain, default move).
- [ ] Every frame carries the full card — incl. lens(mm)+reason, lighting recipe, color gradient,
      pose/body blocking (the no-faces performance line).
- [ ] Timing pass run: Duration fields strung into the animatic (`animatic-editor.md`); tempo
      locked before any final motion render; adjusted durations written back into the cards.
- [ ] Board versioned (v1/v2, never "final"); all frame notes RESOLVED/REJECTED before the
      animatic gate; owner sign-off tied to the exact approved version.
- [ ] Each cut has a distinct function along the register's cut-arc (drama establishment→payoff, or
      product reveal→beauty payoff); continuity readable WITHOUT the captions.
- [ ] Coverage minimum present; cliffhanger object planted early; turn's CU boarded.
- [ ] Continuity drift-killers pass (no face/anatomy/costume/prop drift, screen direction held).
- [ ] Vertical safe zones respected; no AI text inside the frame (unless glyph-gate passed); the
      active brand preset's rules applied (Maghakian = no actor face / Armenian on overlay only).
- [ ] Previz done before style: whitebox (in-engine 2.5) or CineTracer/Blender still, checked
      against the top-down set plan; contradictions rejected, not adopted.
- [ ] Board = planning doc; final cinematic frames are rendered ONE panel at a time with seed +
      start-frame chaining (`ai-pipeline.md`), NOT as a single megaboard — a 30s single-pass
      window is not permission to leave a cut unboarded.
- [ ] Approved board handed to the `ai-pipeline.md` render dossier; paid generation / likeness /
      publishing / account or tool migration remains owner-approved only.
- [ ] AI frames carry the house prompt line + start/end chaining for continuity.
