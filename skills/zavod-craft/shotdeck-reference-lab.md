# ShotDeck Reference Lab — Վիզուալ հղումների կենդանի քարտեզ (FILM MODE)

External visual-reference research station. Use before `storyboard.md`, `cinematography.md`,
`art-department.md`, `color-craft.md`, `post-production.md`, and any pitch/look-book work. It
does **not** copy ShotDeck's article text, image library, stills, or paid database into our
files. It keeps a source map, extracts craft lessons in our own words, and routes those
lessons into Maghakian decisions.

## Legal / craft boundary

- **Never bulk-copy ShotDeck articles, images, stills, screenshots, contest entries, or
  paid-library data** into the zavod.
- Store only: source link, title, date, short paraphrased lesson, Maghakian application.
- Do not embed copyrighted stills in outputs unless licensed/cleared. For public posts,
  translate the lesson into our own object/silhouette/poster-prop visual system.
- ShotDeck is a reference source, not an aesthetic authority. Every borrowed principle passes
  the Maghakian filter: restraint, behaviour over statement, subtext object, Armenian Unicode,
  no actor faces in AI output.

## Public source map (SNAPSHOT 2026-06-13 — մի՛ մեջբերիր այս թվերը, դրանք հնանում են)

| Source | Public count | Use in zavod |
|---|---:|---|
| [Community home](https://community.shotdeck.com/) | hub | manual browsing start |
| News & Events ([posts API](https://community.shotdeck.com/wp-json/wp/v2/posts)) | 10 (News 7 · Events 3) | industry signals, festival/award coverage |
| [Articles](https://community.shotdeck.com/articles/) ([API](https://community.shotdeck.com/wp-json/wp/v2/articles)) | 26 | visual grammar, technical analysis, artist process |
| [Shot Talks](https://community.shotdeck.com/shot-talks/) ([API](https://community.shotdeck.com/wp-json/wp/v2/shot-talks)) | 38 | director/DP/editor/PD process interviews |
| [The Tuesday Drop](https://community.shotdeck.com/tuesday-drops/) ([API](https://community.shotdeck.com/wp-json/wp/v2/tuesday-drops)) | 150 | new reference-batch radar, trends, title discovery |
| [Recreations Contest](https://community.shotdeck.com/recreations-contest/) ([API](https://community.shotdeck.com/wp-json/wp/v2/winner)) | 237 | training drills: lighting/blocking/PD recreation |

Counts above are a one-day snapshot via `X-WP-Total` (2026-06-13) and drift weekly — ALWAYS
re-read the live headers before using any number. Treat the site as a **live source**:
read `X-WP-Total` / `X-WP-TotalPages`, page with `per_page=100&page=N`, store only `id, date,
link, title, excerpt` + taxonomy. Full bodies, images, stills, contest media stay on ShotDeck.

```text
https://community.shotdeck.com/wp-json/wp/v2/types
https://community.shotdeck.com/wp-json/wp/v2/articles?per_page=100&page=1&_fields=id,date,link,title,excerpt
https://community.shotdeck.com/wp-json/wp/v2/shot-talks?per_page=100&page=1&_fields=id,date,link,title,excerpt
https://community.shotdeck.com/wp-json/wp/v2/tuesday-drops?per_page=100&page=1&_fields=id,date,link,title,excerpt
https://community.shotdeck.com/wp-json/wp/v2/winner?per_page=100&page=1&_fields=id,date,link,title,excerpt
https://community.shotdeck.com/wp-json/wp/v2/article-topics?per_page=100&_fields=id,name,slug,count,link
```

## Article topics → craft routing

| Topic | Route |
|---|---|
| Film Movements | `idea-lab.md`, `brand-voice.md`, pitch comps |
| Artist Spotlights | `director-craft.md`, `cinematography.md`, collaboration models |
| Technical Analysis | `cinematography.md`, `color-craft.md`, `post-production.md` |
| Films in Focus | look bible, scene-study, visual-motif translation |

## ShotDeck → Maghakian translation protocol

1. **Pick the dramatic need first** (loneliness, withheld truth, power imbalance, memory,
   threat, false identity).
2. **Search references by need, not by prettiness** (composition, lens distance, colour
   contrast, lighting motivation, blocking geometry, object/hand behaviour, edit rhythm).
3. **Extract the principle, not the image** — one sentence: "what is the shot doing emotionally?"
4. **Translate into the Maghakian world** — replace famous faces/stills with Armenian objects,
   backs, hands, silhouettes, posters-as-props, or a subtext object from `art-department.md`.
5. **Board it with proof** — every borrowed principle lands in a `storyboard.md` shot card
   with lens, lighting, palette, action verb, sound bed, rights status.

## Shot-reference card (add to look bibles + key storyboard frames)

```md
### ShotDeck reference card
- Source: <link>      - Source type: Article / Shot Talk / Tuesday Drop / Recreation / search
- Dramatic need: <what the Maghakian scene must make us feel>
- Borrowed principle: <composition / light / lens / colour / movement / edit>
- Maghakian translation: <our object, room, body behaviour, palette, sound>
- Rights status: reference only / licensed / owned / public-source link only
- Do-not-copy note: <face, exact frame, copyrighted still, protected design>
```

## Department use

- **Director:** Articles + Shot Talks to ask "where is the turn, what behaviour reveals it,
  what frame should be held?" Never imitate a famous frame if the objective differs.
- **Storyboard:** one reference card only on key frames (opening image, the turn's CU, the
  subtext insert, the cliffhanger). More than four references per scene = no visual thesis.
- **DoP:** translate into measurable language — lens, height, contrast ratio, motivated
  source, movement, negative space, colour temperature.
- **Art department:** mine objects, wallpaper, costume silhouette, set texture, practicals —
  the object must mean something in the script; decoration dies.
- **Color:** build reference still sets by register, but grade for Maghakian skin/black/gold
  discipline first; brand purple stays accent only.
- **Post:** use edit/process interviews for rhythm — when to hold, when to cut on motion,
  when silence/room tone carries the turn.
- **Producer:** Shot Talks for schedule reality — days, multi-camera, location constraints,
  sunset windows, practical builds, VFX boundaries.

## Recreation drill (monthly, with a public-domain or self-made reference, never a copyrighted still)
1. Choose one emotional target: isolation, power, secrecy, memory, threat, surrender.
2. Build it with one light, one location, one object, one costume silhouette.
3. Shoot one wide, one MCU, one ECU object insert.
4. Log lens, distance, source, colour temperature, exposure, and the failure.
5. Feed the lesson into `cinematography.md`, `storyboard.md`, or `art-department.md`.

## Live refresh (before any big look-book, deck, or PD pass)

```bash
curl -L -s -I 'https://community.shotdeck.com/wp-json/wp/v2/articles?per_page=1'   # read X-WP-Total
curl -L -s 'https://community.shotdeck.com/wp-json/wp/v2/articles?per_page=100&page=1&_fields=id,date,link,title,excerpt'
curl -L -s 'https://community.shotdeck.com/wp-json/wp/v2/shot-talks?per_page=100&page=1&_fields=id,date,link,title,excerpt'
curl -L -s 'https://community.shotdeck.com/wp-json/wp/v2/tuesday-drops?per_page=100&page=1&_fields=id,date,link,title,excerpt'
```
If a new source changes doctrine, update only the relevant station with a one-line lesson +
source link. Do not paste full articles.

## ShotDeck Reference Lab checklist
- [ ] Source map refreshed for the project date (counts via X-WP-Total).
- [ ] Reference cards attached only to key shots, not every pretty frame.
- [ ] Each reference translated into Maghakian behaviour/object/light, not copied.
- [ ] Copyrighted stills/faces excluded from public outputs unless licensed.
- [ ] Lessons fed back into `storyboard.md`, `cinematography.md`, `art-department.md`,
      `color-craft.md`, or `post-production.md`.
