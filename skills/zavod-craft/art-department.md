# Art Department — Գեղարվեստական բաժին (FILM MODE)

The physical world of the story: design, props, costume, and the object photography the
brand lives on. The art department is where Maghakian **subtext becomes a thing you can
point a camera at** — her meaning is carried by objects, so this is not decoration, it is
dramaturgy. Director: `director-craft.md`. Look/grade: `cinematography.md` · `color-craft.md`.

## Production designer — Բեմադրող նկարիչ

Owns the world per register (A1 war-drama grit → A3 Glendale gloss → A6 thriller cool).
The heart of the job is the **subtext-object registry**:

| Symbol (from «Տակնուվրա» + scripts) | Means | Physical spec to lock |
|---|---|---|
| Anchor («խարիսխը արմատ չէ, հույս է») | the wish to be held / rooted | object, where it sits in frame, who touches it |
| The saved last cigarette | postponed surrender / dignity | unsmoked, specific brand-less pack |
| Frozen laundry line | home, shrinking family | the «Բլոկադա» motif — cold, stiff, fewer items each scene |
| Fish / aquarium | loneliness | glass + negative space (`cinematography.md` composition) |
| Dim cheap-glass lamp | flickering hope | one warm practical (lighting motivation) |
| Marionette / mask | being played / hidden identity | the «Խաղալիք» carousel props |

- Per production, spec each live symbol: **what it looks like, where it lives in frame,
  who is allowed to touch it.** Plant the cliffhanger object early, ignored, so the
  payoff lands (`director-craft.md` blocking).
- Palette discipline: the set dressing serves the show palette (black #0D0D0D, gold,
  per-show accent) — never fights the grade.

## Costume — Կոստյումներ

- **Silhouette-first design:** must read in 9:16 and in no-faces AI shots (the body
  carries the performance — `director-craft.md`). Shape and posture before fabric detail.
- **Anthology costume-continuity trick** (e.g. «84 ամառ»): same actor, different
  characters — lock costume + posture notes so the recurrence reads as intentional.
- Wardrobe palette tied to the show palette; the cold protagonist dresses in control
  (centered, symmetrical), breaks it visually when she breaks emotionally.

## Props & set decoration — Ռեկվիզիտ

- **Practicals are lighting** — every lamp/screen/fridge is a motivated source; coordinate
  placement with `cinematography.md` (practical-driven night).
- **Sponsor-prop integration** must pass the scene test (objective/turn) or it dies in the
  edit — coordinate tiers with `producer-craft.md` (ՌԵԿԼԱՄ scenes).

## Poster-prop & object stills — Պաստառ-ռեկվիզիտ և առարկայական լուսանկար

The brand shoots **posters-as-props and object photography instead of faces** (brand rule;
`carousel-template.md`). The art department preps these:
- Builds the still-life: the symbol object on the show-palette surface, lit per the DoP
  kit, framed with negative space for typography overlay.
- Treats the show's own poster as a prop (the «Խաղալիք» cracked-marble set) — outpaint /
  extend in `ai-pipeline.md`, never redraw faces.

## Print pre-press (CMYK — physical posters & living posters)

Her theatre plays («Պատերազմից հետո կյանք կա», «Բլոկադա» — `filmography.md`) and premium
promo need posters that leave the screen. Digital is RGB; print is CMYK — convert properly:
- **RGB → CMYK with a profile** (ISO Coated v2 / GRACoL), not a naive flatten — soft-proof
  first; deep blacks become **rich black** (e.g. C40 M30 Y30 K100), never single-channel K
  (looks washed on paper).
- **Spec for the press:** 300 DPI at final size · 3mm bleed · safe margin · crop marks ·
  embedded ICC profile · PDF/X-1a or X-4 export.
- **Protect the look on paper:** the monochrome aesthetic (`color-craft.md`) and aggressive
  display type (`motion-design.md`) must survive the conversion — re-check black depth and
  highlight roll-off after CMYK; gradients banding is a hard fail.
- For a 500-copy run, supply a print-ready PDF/X + a low-res preview; vector elements stay
  vector (`identity-guard.md` SVG), only photographic layers raster.
- **Living poster** (animated promo): export the still as CMYK for print AND a 9:16 motion
  version (`motion-design.md`) for screen — one art direction, two masters.

## Art-department checklist
- [ ] Subtext-object registry filled for this production (look / position / who touches).
- [ ] Cliffhanger object planted in an early frame.
- [ ] Costumes read in silhouette (9:16 + no-faces AI); anthology continuity logged.
- [ ] Every practical is a motivated light source (synced with `cinematography.md`).
- [ ] Sponsor props pass the scene test (`producer-craft.md`).
- [ ] Poster-prop / object stills prepped with negative space for Canva text.
