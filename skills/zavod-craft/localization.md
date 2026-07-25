# Localization — Թարգմանություն և ենթագրեր (FILM MODE)

The translator-localizer + subtitle-QC station. The agency's audiences are tri-lingual
(Armenian primary, LA/Glendale English, Moscow Russian). Localization is a VOICE problem,
not a translation problem — `brand-voice.md` is one voice, but it does not transfer
literally across scripts.

## Voice transfer (her signature does NOT translate as-is)

| Her device | EN equivalent | RU equivalent |
|---|---|---|
| `,,,` trailing beat | em-dash trailing «—» or «…» | «…» |
| «»-quotes / ` — ` | "curly quotes" / em-dash | «ёлочки» / тире |
| Yerevan dialect | register-matched colloquial, NEVER literal | разговорный, не дословно |
| A2/A3 code-switch | keep the foreign words that were already foreign | то же |

- **Never translate dialect literally** — match the register (street stays street). A
  flat literary subtitle kills A1–A5 voice.
- Keep the words that were already English/Russian in her code-switching intact.

## Subtitle QC (the readable-speed law)

- **≤17 characters/second**, max 2 lines, ~42 chars/line.
- **Sync to the BEAT, not the word** — the subtitle in/out follows the cut and the breath.
- Glyph/homoglyph QC for all three scripts (Armenian / Latin / Cyrillic) — coordinate the
  Armenian gate with `motion-design.md`.

## AI dubbing workflow (the diaspora arbitrage engine)

- **ElevenLabs v3 supports Armenian (hye)** — confirmed current 2026-07: the v3 model
  covers 70+ languages incl. Armenian (direct API, not fal). **Know the product split:**
  the automated *Dubbing* product (voice-clone auto-dub) covers ~29 languages — RU and EN
  are both in, Armenian is on the wider v3 TTS list, not the auto-dub list. The arbitrage
  direction is unaffected: shoot once in Armenian, **AI-dub RU/EN** for Moscow +
  LA/Glendale (`producer-craft.md`).
- **Dub-tool routing (2026):**
  | Content | Route | Why |
  |---|---|---|
  | VO / off-screen narration | ElevenLabs Dubbing or v3 VO | best raw voice quality in class |
  | Ani on-camera (her real footage) | HeyGen video-translate (175+ langs, 2026 lip-sync leader) | lip-synced dub of her own delivery — likeness + paid tier = Ani's call, flag before use |
  | No budget / speed tier | subtitle-only path | the ≤17 CPS law above still applies |
- **Performer voice-consent is mandatory** before cloning/dubbing any real voice
  (`business-affairs.md`).
- Pipeline: lock Armenian master → script-adapt per language (voice transfer above) →
  AI-dub or AI-subtitle → human glyph + reading-speed pass → diaspora-windowed release.
- **Post-dub register QC:** machine dubbing flattens dialect — after ANY AI dub, re-run the
  voice-transfer table against the output (street must still be street); reject literary
  flattening like any other continuity error.

## Diaspora timing (works with `playbook.md`)

- Subtitled/dubbed versions post to the diaspora window: **19:00–21:00 Yerevan =
  08:00–10:00 LA + 18:00–20:00 Moscow.** RU cut to the Moscow evening, EN cut to the LA
  morning commute.

## Localization checklist
- [ ] Voice transferred, not translated literally; dialect register matched.
- [ ] Subtitles ≤17 CPS, ≤2 lines, synced to the beat; glyph-checked in all 3 scripts.
- [ ] AI dub uses a consented voice; Armenian master locked before dubbing; post-dub
      register QC passed (no dialect flattening).
- [ ] EN cut → LA morning, RU cut → Moscow evening, per the diaspora window.
