# Color Craft — Գունային մշակում (FILM MODE)

The colorist station, split out of post so the grade is owned, not improvised. The DoP
lights it (`cinematography.md`); this file keeps it consistent across episodes, engines
and time. Grade AFTER picture lock; **skin first, mood second, brand third.**

## Show-LUT workflow (consistency engine)

- **Per series:** grade 3 hero stills → bake a **show-LUT** → apply it as the LAST node.
- Per-shot balancing happens UNDER the LUT, **never by bending the LUT** — if a shot
  fights the LUT, fix exposure/WB beneath it.
- Keep a **reference-still library** per series in `exports/<series>/grade-refs/` — match
  new episodes to the stills, not to memory.

### Show-LUT BUILD PATH — doctrine → an actual `.cube` file (2026-07-31)

"Bake a show-LUT" was a decision with no execution path; rival colour skills
(`isaacrowntree/color-grade-ai` — analyse frames → emit correction `.cube`) ship the path but
have no register doctrine. Take the path, keep our doctrine on top:

1. **Extract the anchors:** pull the 3 hero stills as PNG (`ffmpeg -ss <t> -i <src> -frames:v 1`)
   into `grade-refs/`. Flat/log source only — see the flat-source law below.
2. **Analyse → per-node recommendation:** read each still for cast, black point, skin excursion
   and highlight roll-off; write the fix as an ordered **node chain**, not one blob.
3. **Chain the nodes in this order** (order is the whole craft — later nodes inherit earlier
   error): `balance/WB → skin qualifier (protect) → black point → register look → accent/halation`.
   Creative presets stack with **weighted intensity** (e.g. `drama_crush@0.8, warm_shift@0.3`)
   so a look can be dialled, not re-cut.
4. **Emit the `.cube`** and apply it as the LAST node; use **tetrahedral interpolation** on
   apply (Resolve LUT settings / `ffmpeg lut3d=interp=tetrahedral`) — trilinear banding shows
   up exactly in our crushed #0D0D0D shadows.
5. **Version the LUT with the series** (`showlut_v1.cube`, never "final") and log which stills
   built it — a LUT whose anchors aren't recorded cannot be rebuilt next episode.

**Our edge over the LUT generators:** the machine proposes the correction, it never picks the
**register**. A generated LUT that neutralises a shot is a *starting node*, not the look —
drama still lands at 8:1 with lifted-then-crushed blacks, comedy still stays 2:1 flat. Any
auto-LUT that flattens the register or lifts skin out of the qualifier is rejected, not tuned.

### Flat-source law (AI footage: never let the engine bake the grade)

Auto-balance and shot-match both degrade when the source already carries a baked look — the
tool has no headroom left to correct. So the palette line in a generation prompt
(`cinematography.md`) is **art direction, not a grade**: name what is physically in frame —
the gold practical, the wet enamel, the tungsten bulb, the wardrobe — and never a filter
("teal-and-orange grade", "heavily graded", "LUT applied", "colour-graded look"). The engine
lights the scene; **this file grades it.** Where an engine offers a flat/neutral or log-ish
output mode, take it — a flatter render is worth more than a pretty one straight out.

## Skin-tone protection (hard gate)

- Pin skin hue with a **vector / HSL qualifier BEFORE any look adjustment.**
- Brand purple **#6450D2 spill onto faces is a hard fail** — the accent is for UI/titles
  (`motion-design.md`), never a wash on skin.
- Protect skin first even when crushing to the 8:1 drama look below.

## House looks per register

| Register | Look | Contrast |
|---|---|---|
| Drama (A1/A2/A6) | lifted blacks #0D0D0D, warm golds, crushed | 8:1 |
| Comedy (A3) | bright, saturated, flat | 2:1 |
| Memory / dream (A5 selavi, flashbacks) | softened highlights, cooled shadows | gentle |

Brand purple #6450D2 only as accent (titles, UI), never a wash. (Mirrors the looks noted
in `post-production.md` — this file owns the recipes; post keeps a one-line summary.)

## Monochrome protocol (premium B&W — thriller / pitch design)

For «Ճերմակ շապիկ»-type thrillers (the title literally is "white shirt") and pitch/key-art:
- **Aggressive, high-acutance monochrome** — deep true blacks (#0D0D0D maps to pure black),
  controlled highlight roll-off, and **preserved micro-contrast** so the image stays
  hyperreal, never muddy or "flat phone B&W".
- Use a **channel-mixer / luminance-curve B&W** (not desaturation) — pick which colours become
  which greys; reds/skin to mid-grey, the practical to the brightest point.
- **Accents drop:** purple #6450D2 has no place in mono; the gold becomes a tonal value, not a
  hue. Texture and contrast carry the brand, not colour.
- Keep skin protection + grain discipline identical to the colour looks above.

## Cross-engine matching (AI footage is the new continuity problem)

When Kling, Veo and Seedance shots sit in one timeline:
1. **Normalize gamma/saturation per engine FIRST** — each engine has a signature; neutralize it.
2. **Then** apply the show-LUT.
3. **Then** lay **shared grain on top of everything** — grain is the great unifier of
   AI + shot footage (`post-production.md`).

## The STILL lane — carousels, posters and key art get graded too (2026-07-31)

The factory's blind spot: motion went through the show-LUT and the still lane never did.
Carousel BGs, posters and key art went engine → Canva ungraded, so the feed and the film
slowly drifted apart — two looks under one brand.

**Resolve 21 (shipped 2026-06-03) closes it: the Photo page brings the node graph, primaries,
curves, qualifiers and power windows to still images under the same colour science as the
timeline.** So:

- **Same show-LUT, both lanes.** A carousel BG or poster is graded on the Photo page with the
  series' `showlut_v1.cube` as the last node — identical LUT, identical register look, identical
  skin qualifier. The still is a frame of the same world, not a separate design.
- **Register applies to stills:** a drama carousel is 8:1 crushed, a comedy carousel is 2:1 flat.
  A still that grades brighter than its own series is a fail, not a "punchier thumbnail".
- **Order in the still lane:** engine render → realism/upscale pass (`ai-pipeline.md`) →
  **grade under the show-LUT** → grain → THEN text/overlay (`carousel-template.md`,
  `motion-design.md`). Grading after the Armenian text is burned in shifts the type colour —
  grade first, and if any text region was touched, re-run the glyph gate.
- **Feed the graded still back** into `grade-refs/` when it becomes a key art anchor.

No rival does this: colour tools grade footage, carousel generators make slides, and nobody
owns both lanes under one LUT. We do, because the same factory makes both.

## Halation & day-for-night recipes

- **Halation:** glow on **highlights only** (gold practicals bloom on #0D0D0D); subtle,
  filmic — pairs with the DoP Pro-Mist look (`cinematography.md`). Never a full-frame bloom.
- **Day-for-night:** underexpose 2 stops at the lens → in grade: blue-shift, kill the sky
  luminance, protect a hard "moon" rim, crush shadows but keep one readable highlight.

## HDR policy (2026)

- **Master SDR Rec.709.** IG now passes Dolby Vision/HDR through, but mixed-feed HDR
  **grays out the #0D0D0D blacks on SDR screens** — stay SDR until the whole pipeline is
  HDR-monitored. Revisit when the monitor chain is HDR end-to-end.

## Execution tools (our doctrine → their engine)

The recipes above are the decisions; these tools do the labor. **DaVinci Resolve 21**
(released 2026-06-03, free build + $295 Studio) is the spine:

- **AI Color Match** — auto-balance a shot to a hero still; feed it the `grade-refs/` anchor.
- **Magic Mask + CineFocus** — isolation for the skin/subject qualifier (CineFocus also does
  post-hoc refocus with real bokeh — useful when an engine renders the subtext object soft).
- **UltraSharpen** — high-fidelity sharpening for moving images; our use is rescuing a
  cheap-tier render's material detail, at low strength, never as a look.
- **Photo page** — the still lane above.
- *Not for us:* Face Age Transformer / Face Reshaper / Blemish Removal — face tools, dead on
  arrival under the no-faces rule. Listed so nobody re-discovers them as a "missing feature".

**Colourlab.ai** (paid) runs as an **OFX plugin inside Resolve** and batch-matches a whole
timeline to a reference — the fastest path when a series has hundreds of clips. **Imagen Video**
(NAB 2026) is the adaptive per-frame alternative. Both are *proposal engines*.

AI matches, isolates and proposes; the creative grade (register look, halation, day-for-night)
stays human — never ship an auto-grade unexamined.

## Colorist checklist
- [ ] Show-LUT built from 3 hero stills; applied as the last node; never bent per shot.
- [ ] LUT built through the node chain (balance → skin → black point → register → accent),
      emitted as a versioned `.cube`, applied with tetrahedral interpolation; anchor stills logged.
- [ ] Generation prompts carry palette as art direction only — no grade/filter words in the prompt.
- [ ] Still lane graded: carousel BG / poster / key art ran the same show-LUT BEFORE text overlay;
      glyph gate re-run if a text region was touched.
- [ ] Skin hue qualified and protected before any look; no purple spill on faces.
- [ ] AI shots normalized per engine → show-LUT → shared grain on top.
- [ ] Register look + contrast ratio match `cinematography.md` grade intention.
- [ ] Halation on highlights only; day-for-night reads as night, not murk.
- [ ] Delivered SDR Rec.709; reference stills filed in `exports/<series>/grade-refs/`.
