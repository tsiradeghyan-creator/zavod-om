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

The recipes above are the decisions; these tools do the labor. **DaVinci Resolve 21** (free)
is the spine: **AI Color Match** (auto-balance a shot to a hero still — feed it the
`grade-refs/` still), **Magic Mask + CineFocus** (skin/face isolation for the skin-protection
qualifier), **Face Refinement**. **Colourlab.ai** for show-LUT building from references at
scale. AI matches and isolates; the creative grade (register look, halation, day-for-night)
stays human — never ship an auto-grade unexamined.

## Colorist checklist
- [ ] Show-LUT built from 3 hero stills; applied as the last node; never bent per shot.
- [ ] Skin hue qualified and protected before any look; no purple spill on faces.
- [ ] AI shots normalized per engine → show-LUT → shared grain on top.
- [ ] Register look + contrast ratio match `cinematography.md` grade intention.
- [ ] Halation on highlights only; day-for-night reads as night, not murk.
- [ ] Delivered SDR Rec.709; reference stills filed in `exports/<series>/grade-refs/`.
