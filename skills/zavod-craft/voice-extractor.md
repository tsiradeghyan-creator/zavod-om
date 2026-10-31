# Voice Extractor — Ձայնի աճող ապացուցողական շերտ

`scripts/voice_extractor.py` is the live, incremental feeder for the curated authorial-voice
system. It turns eligible owner-supplied UTF-8 script text into a pinned corpus profile and
review-only change deltas. It does not decide whether new evidence belongs in the canon.

> **Evidence and update boundary.** The extractor never edits `style-profile.md`, `corpus-notes.md`,
> or another curated craft file. It updates machine evidence and writes a delta. The owner has
> authorized the script agents to keep the Ani profile current: after each new owner-supplied script
> or explicit project direction, agents apply `ani-evaluation-and-update.md`, record evidence and
> scope in `ani-profile-changelog.md` / `ani-project-directions.md`, and update the curated profile
> when the evidence thresholds in that protocol are met. A one-off direction applies immediately to
> its named project; it does not become historical authorial evidence. Preserve the original and a
> reversible prior profile snapshot.

## Current evidence plane

- Corpus: `~/Documents/Maghakian-Scripts/txt/*.txt`
- Pinned profile: `library/authorial_voice/maghakian-script-v1.json`
- Incremental hash ledger: `library/authorial_voice/.seen.json`
- Review deltas: `library/authorial_voice/deltas/<YYYY-MM-DD>.json` and `.md`
- Current profile snapshot: 40 glyph-clean eligible source files across nine corpus register buckets;
  register C is quarantined for strict automatic scoring until a clean source is available

The profile stores Unicode-safe source names or one-way filename evidence ids, exclusion evidence,
a corpus snapshot SHA-256, per-register source membership, and feature ranges. A filename containing
Latin/Cyrillic source text is never copied into generated profile or delta content. Visual colors,
fonts, logo, and layout are intentionally outside this profile.

## What each scan does

1. Discovers eligible `.txt` files and leaves the source corpus untouched.
2. Excludes contract/right files by filename, and also excludes person-named documents whose
   opening explicitly identifies them as contracts and contains multiple legal-party markers.
   It also excludes unstable mixed-script filenames and tiny files that cannot provide useful
   evidence. Original source files remain untouched.
3. Hashes every source file and compares it with `.seen.json`; only new or changed files enter
   the delta. Removed files are recorded explicitly.
4. Computes register candidates and objective feature signals.
5. Runs the authorial Armenian glyph gate. Legitimate pure Russian code-switching is preserved;
   Latin-script Armenian, mixed-script Armenian words, and invisible-character risks still fail.
6. Replaces unsafe or transliterated source filenames with stable one-way evidence ids.
7. Surfaces quoted-line and structural-device candidates as evidence for review. It never promotes
   an aphorism, device, register, or rule automatically.

Review tools can resolve an opaque id back to the local owner-supplied file with
`lib.authorial_voice.resolve_evidence_source`; the unsafe name still never enters a generated artifact.

## Run it

Create or deliberately rebuild the pinned aggregate profile, then record the current corpus as the
baseline:

```bash
./.venv/bin/python scripts/voice_extractor.py --baseline
```

Run the incremental scan:

```bash
./.venv/bin/python scripts/voice_extractor.py
```

Normal output reports the profile path, changed/removed counts, and whether a review delta was
written. A changed file with a glyph violation makes the command exit non-zero so corpus damage is
loud instead of silently absorbed.

## Relationship to strict Script DNA

The extractor creates evidence; it does not approve prose. When
`creative_identity.authorial_voice.mode` is `strict`, `lib/authorial_voice.py` and the script
checkpoint require an `authorial_voice_report` against the pinned profile. Code verifies:

- exact draft and profile hashes;
- all seven authorial criteria and score arithmetic;
- quoted evidence that truly exists in the draft;
- corpus references that belong to the pinned snapshot;
- Unicode, generic-trope, format, and register signals.

The reviewer supplies the literary judgment and rationale. If evidence is stale, invented, outside
the corpus snapshot, or below the locked score, the script stage cannot pass.

## Review checklist

- [ ] Only new, changed, and removed `.txt` files appear in the delta.
- [ ] `.seen.json` contains the current SHA-256 ledger.
- [ ] Source corpus and curated canon files remain untouched.
- [ ] Every surfaced Armenian string passes the authorial glyph gate.
- [ ] Candidates are treated as evidence, not approved canon.
- [ ] A human reviews the delta before changing a register, example, or craft rule.
