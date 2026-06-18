# Script Director — ZavodOM

## When to use
Turn the `brief` into a `script` in the zavod's voice (the brain's taste lives here).

## Craft (read from skills/zavod-craft/)
`style-profile.md` (Ani's screenwriting DNA — registers, beats, subtext) **read FIRST for Armenian**,
`brand-voice.md` (external/caption voice), `voice-extractor.md`, `corpus-notes.md`.

## Process
1. Read `style-profile.md` before writing any Armenian script. Match the target register.
2. Write the script / on-screen copy. Keep hooks in the first beat.
3. Tag every text element's language so downstream `text_policy.language` is correct.

## Produces
`script` (canonical artifact).

## Gate (HARD)
- `brand_voice_check` — drift vs style-profile/brand-voice scored.
- **`armenian_glyph_gate`** — any Armenian text MUST be pure Eastern Unicode (no Latin/Cyrillic
  lookalikes). Fail = fix before proceeding. This is non-negotiable ([[rules]]).
