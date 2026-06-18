# Storyboard — Ռասկադրովկա (FILM MODE, real-shoot first)

The shot-by-shot visual plan a real crew shoots from. This is the single most attended
station: nothing reaches the set or the render without a board. It UNIONS the professional
shot-list rigor of StudioBinder, the look-bible discipline of the best AI storyboard skills,
**and** Ani's restraint dramaturgy — then annotates every frame with the full technical card
(camera · lens · light · color gradient). No rival combines all three; that is our edge.

Owned by the storyboard / previz artist (`production-team.md`). Inputs: the director's
objective/turn (`director-craft.md`). Lens/light recipes: `cinematography.md`. Grade/gradient:
`color-craft.md`. Sound: `sound-craft.md`. AI-render bridge: `ai-pipeline.md`.

## The look bible (lock ONCE per production — keeps the board consistent)
Before any frame, lock the shared block every panel inherits:
- **Palette + grade:** black #0D0D0D, gold accents, show accent; the gradient logic
  (e.g. warm tungsten foreground → cold window background = past vs present).
- **Contrast ratio by register:** comedy 2:1 · daily drama 4:1 · thriller/«Ճերմակ շապիկ» 8:1+.
- **Lens set:** 35 documentary spine · 50 dialogue · 85–100 the turn (`cinematography.md`).
- **Grain stock:** ONE per series, logged · **movement default:** static tripod (restraint).

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
| **Sound / audio bed** | ambience + sync FX + the silence beat (`sound-craft.md`) |
| **Continuity** | eyeline · screen-direction (L→R/R→L) · wardrobe/prop (`production-team.md`) |
| **Duration / fps** | seconds + 24/25fps (120fps overcrank only for the object insert) |
| **AI-prompt line** *(if rendered)* | the house render template (`cinematography.md` · `ai-pipeline.md`) |

## Coverage minimum per scene (what the board must contain)
Master · OTS pair (or singles for 9:16) · **the turn's CU** (held 2s longer) · **one subtext
insert**. One insert earns meaning; three make a commercial. Plant the cliffhanger object in an
early frame, ignored, so the payoff lands.

## The Maghakian discipline (what makes the board hers, not generic)
- **Restraint:** hold the frame, cut late; melodrama is shot loud, Maghakian is shot quiet —
  when in doubt, wider, longer, stiller.
- **Behaviour over statement:** the card's Action field is verbs; emotion lives in the
  blocking and the subtext object, never in a caption.
- **The shield:** block the activity first (cooking, pottery, cleaning a wound); dialogue
  rides on it — board the hands, not just the face.
- **Vertical 9:16 board:** subject + subtext object in the middle 65% (top 15% / bottom 20%
  are UI graveyards); depth not width (FG object / face / BG context).
- **No actor faces in AI-rendered frames** — hands, backs, silhouettes, objects, reflections
  without identity; Armenian text never inside the frame (`ai-pipeline.md` · `motion-design.md`).

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

## Storyboard checklist
- [ ] Look bible locked (palette/gradient, contrast ratio, lens set, grain, default move).
- [ ] Every frame carries the full card — incl. lens(mm)+reason, lighting recipe, color gradient.
- [ ] Coverage minimum present; cliffhanger object planted early; turn's CU boarded.
- [ ] Continuity fields filled (eyeline, screen-direction, wardrobe/prop).
- [ ] Vertical safe zones respected; no face / no Armenian text in any AI-rendered frame.
- [ ] AI frames carry the house prompt line + start/end chaining for continuity.
