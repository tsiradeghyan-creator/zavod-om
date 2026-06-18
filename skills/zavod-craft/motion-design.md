# Motion Design — Շարժապատկեր և տիտր (FILM MODE)

Armenian kinetic typography is brand-critical and was previously owned by no one. This
station owns every word that moves on screen — captions, titles, episode cards, the
glyph gate, and the cover frame that wins the 0.25s scroll. The Unicode law is absolute:
proper Eastern Armenian only, never a Latin/Cyrillic lookalike.

## Caption kinetics

- **Burned-in Armenian primary + thin English underbar** (+15–25% retention) — never the
  platform auto-CC for the primary line.
- **Safe zone:** middle 65% of the 9:16 frame (top 15% / bottom 20% are UI graveyards).
- **Animation curves:** ease-out 200–300ms in, **no bounce**, no spin. One caption style
  per series — design it once, log it, reuse it.
- Fonts: **Noto Sans Armenian** (captions) / **GHEA** fonts (titles) — per `maghakian-brand`.

## Titles, episode & time cards

- Episode/part cards in her house pattern: «ՄԱՍ 1», «ՄԱՍ 2».
- Time-cards copied from her scripts: «ՄԵԿ ՇԱԲԱԹ ԱՆՑ», «ՀԱՋՈՐԴ ԱՌԱՎՈՏ»,
  «ԵՐԿՈՒ ՏԱՐԻ ԱՌԱՋ» (`style-profile.md` / `corpus-notes.md`).
- Chapter-title cards for the A6 register («Ճերմակ շապիկ» chapter heads).
- **Brand purple #6450D2 only as an accent** in UI/titles — never a wash over the image.

## Glyph gate (this station OWNS it)

Every burned-in line passes the **mixed-script homoglyph check BEFORE export** — AI
subtitle/title tools love sneaking Latin/Cyrillic lookalikes into Armenian words (wiki
rules #4). No frame ships with an unchecked glyph. EN/RU subtitle accuracy → `localization.md`.

## Spelling & canonical-phrase lock (beyond the glyph gate — The Absolute Spellchecker)

The glyph gate catches mixed scripts; this catches human typos and drift. Before ANY slide
or project publishes:
- **Armenian orthography pass:** spell-check every burned-in line (Armenian spell dictionary /
  Hunspell hy_AM). A real Armenian word with a typo passes the glyph gate but fails here.
- **Canonical-phrase lock:** the agency's signature lines are stored verbatim and matched
  EXACTLY — character + punctuation. e.g. «Սերը հասցե ուներ…» must render letter-for-letter,
  no `…`/`...` substitution, no comma drift, no synonym. Any deviation from the approved
  standard is rejected, not auto-corrected.
- **Punctuation discipline:** Armenian «», ՝ ։ — used correctly; no Latin quotes/periods inside
  Armenian text.

## Premium display typography (the aggressive brand face)

Captions use Noto/GHEA; CAMPAIGN key-art and logos may go heavier:
- **Aggressive editorial display faces** (THUNDER-class condensed/heavy) give cinematic weight
  to Instagram campaign covers and wordmarks — pairs with the monochrome protocol (`color-craft.md`)
  and the premium gate (`identity-guard.md`).
- **Armenian caveat (critical):** THUNDER and most Latin display faces have **no Armenian
  glyphs** — never set Armenian in them. For Armenian campaign display use a heavy Armenian
  face (GHEA Mariam/Grapalat bold, Arian AMU Bold, or a licensed Armenian display); reserve
  THUNDER-class for **Latin wordmarks / numbers only**. Mixed-face Armenian is a hard fail.
- Extreme high-resolution export; the type must stay razor-sharp at full size.

## Cover frame / thumbnail (the 0.25s scroll-death window)

- **Frame-1 / thumbnail rules:** mid-action CU, the strongest single visual, readable at
  thumbnail size; never an establishing wide.
- **Carousel coordination:** slide 1 = the poster hook; **slide 2 must also work as a
  standalone alternate hook** (second-chance delivery re-serves from slide 2 —
  `carousel-template.md`).
- One legible focal word maximum on a cover; the rest is image.

## Motion-design checklist
- [ ] Captions burned-in, Armenian primary + EN underbar, middle-65% safe zone.
- [ ] One logged caption style per series; ease-out, no bounce/spin.
- [ ] Episode/time/chapter cards in the house Armenian pattern; purple accent only.
- [ ] Glyph gate passed on every burned-in line before export.
- [ ] Cover frame: mid-action CU, thumbnail-legible; carousel slide-2 alt-hook ready.
