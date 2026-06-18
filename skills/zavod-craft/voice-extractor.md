# Voice Extractor — Ձայնի ավտո-վերլուծաբան (the living-voice feeder)

Keeps `style-profile.md` + `corpus-notes.md` learning Ani's NEWEST writing without a manual
read. A weekly scan of her script corpus surfaces new characters, aphorisms, and devices and
proposes updates — so the factory sharpens in step with how she writes in real time.

> **Hard rule — propose, don't pollute.** The voice files are curated. The extractor writes
> a **draft delta** (`voice-deltas/<date>.md`), never edits `style-profile.md` directly. A
> human (or the Maghakian veto in `world-benchmark.md`) accepts the delta into the canon. New
> material is **PROVISIONAL** until confirmed (`style-profile.md` confidence flag).

## What it scans
`~/Documents/Maghakian-Scripts/docx/` (+ `txt/`). Tracks which files were already read (a
`voice-deltas/seen.json` ledger of filename + mtime) so each run only processes NEW or CHANGED
scripts.

## What it extracts per new script
- **New characters:** name, series, want / wound / secret, verbal tic, register (A1–A6/B/C).
- **New aphorisms / signature lines:** verbatim Armenian, with the source file + a note whether
  it echoes an existing one (feeds the aphorism usage ledger, `style-profile.md`).
- **New devices / structure:** any cue, transition, framing trick not yet in the registers.
- **Register confirmation:** which existing register it belongs to, or a candidate new one.
- **Dialect/idiolect notes:** new slang, code-switch patterns, `,,,` density.

## Output — the weekly delta
`voice-deltas/<YYYY-MM-DD>.md`:
```md
# Voice delta — <date>
## New scripts read: <files>
## New characters: <name · series · want/wound/secret · tic · register>
## New aphorisms (verbatim): «…» (source: <file>)  [echo of: <existing?>]
## New devices: …
## Proposed edits: style-profile.md §<section> / corpus-notes.md §<series>
## Confidence: provisional until human-confirmed
```
Glyph-gate every extracted Armenian string before writing the delta (no homoglyphs).

## How it runs
- **Cadence:** weekly. Implemented as a `python-docx` scan; runnable by the `zavod-scout`
  loop or its own cron (mirror the launchd pattern of `zavod-scout`). It only WRITES the delta
  file — accepting into the canon stays a human step.
- **No invention:** it reports what's in the scripts; it never fabricates a character or
  aphorism. Empty week → empty delta, that's fine.

## Voice-Extractor checklist
- [ ] Only NEW/changed `.docx` processed (seen.json ledger current).
- [ ] Delta written to `voice-deltas/<date>.md`; canon files untouched.
- [ ] Every extracted Armenian string glyph-gated.
- [ ] Aphorisms flagged as new vs. echo; characters carry want/wound/secret + register.
- [ ] Human-confirm step pending before anything enters `style-profile.md`.
