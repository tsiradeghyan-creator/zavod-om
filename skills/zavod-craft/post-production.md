# Post-Production — Մոնտաժ, գույն, ձայն, թողարկում (FILM MODE)

World-class post craft: the edit is where Maghakian restraint becomes rhythm. Load for
any cut — Reel, micro-drama episode, sizzle, or carousel-video hybrid.

## Edit grammar (the invisible art)

- **Cut on motion, look, or sound bridge** — never on stillness unless the stillness IS
  the point (her held CUs at the turn: let them sit 2 extra seconds).
- **J/L cuts are her dialogue style in edit form:** the next line starts under the
  current face (subtext = we watch the listener, not the speaker). Default to L-cuts on
  every emotional exchange.
- **Scene compression:** enter late, leave early — but never cut the activity (the
  "shield" business carries the subtext; trim words, keep hands).
- **Montage + voiceover = her signature turn:** silent behaviour shots under
  «արտակադրային ձայն» — build as: 1 wide (world) → 2–3 behaviour mids → the object
  insert → return to the face. Music swells AFTER the last line, not under it.
- **End-revealed framing in edit:** keep the "unclear-location" shots visually
  consistent (same grade/lens) so the finale recontextualization lands («Ճերմակ շապիկ»).
- **Cliffhanger cut:** end ON the turn frame (door opens / body falls) — no reaction
  shot, no resolution. The reaction is the next episode's first frame.
- **Murch's Rule of Six:** when two cuts both "work," rank by emotion (51%) > story >
  rhythm > eye-trace > 2D plane > 3D space. **Emotion always wins the tie.**
- **Eye-trace (critical at 9:16 phone distance):** note where the viewer's eyes sit at
  the outgoing frame; place the incoming point of interest within ~10% of that spot — or
  deliberately violate it ONLY on turns (the jolt is the point).
- **Match-on-action:** cut mid-gesture; the incoming shot continues the same gesture from
  a new angle / punch-in — hides the cut even between two AI takes.
- **Rhythm mapping (montage):** lock the music FIRST, place cuts on the grid (downbeats),
  then displace 1–2 cuts OFF the grid — perfect quantization reads as template, not drama.

## Reels / vertical rhythm (the algorithm layer, from `playbook.md`)

- Frame 1 = the strongest visual (mid-action CU). Hook ≤3s. Jump-cut every 3–5s.
- **Retention typology:** a pattern interrupt every 3–5s is the FLOOR; vary the TYPE —
  cut / insert / caption-style change / sound drop / speed shift. A 1s full-silence hold
  IS a pattern interrupt — use it once per Reel, at the turn.
- **Invisible-cut whitelist:** whip-pan wipe · object wipe (hand/door crosses lens) ·
  2-frame blur-dissolve. These are the ONLY "transitions" allowed — never preset
  spins/glitches.
- **Tension-curve pass (retention edit):** lay the episode's writing-stage tension curve
  (`serial-structure.md`) over the timeline; at every dip apply a fix — a J/L cut, a sound
  drop/sweetener (`sound-craft.md`), a punch-in, or a subtext-object insert — so no flat
  stretch runs >10–15s and the curve rises into the paywall. Confirm against the real
  drop-off data from `growth-analytics.md`; a dip the data flags but the rubric missed
  becomes a new rule.
- **Clip-mining pass (long master → shorts):** when a long master exists (episode, windows
  video), mine candidate clips before designing new ones — score each candidate 1–5 on:
  hook-in-first-frame · self-contained turn · loop potential · plays-silent readability.
  This is OpusClip-class "virality scoring" rebuilt on house taste: an AI ranker
  (OpusClip / Vizard tier) may PROPOSE candidates, but the rubric + tension-curve pass
  decide — never ship a ranker's cut uncut.
- 30–60s sweet spot; retention loop: last shot flows back into the first.
- AI footage = b-roll/teaser support only; Ani face-to-camera leads.
- No foreign watermarks. Punch-ins (4K→1080) replace second angles in vertical.

## Modern FX (2026 — restraint-filtered)

- **ALLOWED, with discipline:** speed ramps ("ramp INTO stillness, not out of it;
  pitch-correct or MUTE audio during ramps — chipmunk audio is an instant brand kill");
  one punch-in per beat ("max 30%, ease-out curve, never linear"); film emulation
  (halation on highlights only — `color-craft.md`; subtle gate weave on memory/dream
  register only; ONE grain stock per series, logged); AI upscale / frame interpolation
  ("24→30 only when the engine output stutters; **never 60fps** — soap-opera motion breaks
  the film register"); generative-fill outpainting 16:9→9:16 ("backgrounds only, never
  across faces/hands; glyph-check any regenerated region").
- **FORBIDDEN:** velocity-curve "TikTok ramps", beat-synced strobe zooms, glow/bloom
  washes, AI relight that shifts skin tone, auto-caption templates, 3D camera projections.
- One line: **if the effect announces itself, it's off-brand. Restraint is the look.**

## Color (one-line summary — full recipes in `color-craft.md`)

Grade after picture lock; skin first, mood second, brand third. House looks: drama
8:1 crushed warm golds on #0D0D0D · comedy (A3) 2:1 bright flat · memory/dream softened &
cooled. Purple #6450D2 is accent only, never a wash. AI shots: normalize per engine →
show-LUT → shared grain on top (grain is the unifier). Everything else → `color-craft.md`.

## Sound (AI footage arrives SILENT — build it)

- Every AI shot has NO production sound. The 4-layer build, dialogue chain, leitmotifs and
  cue sheets live in **`sound-craft.md`** — this file keeps only the house loudness law:
  dialogue intelligibility > everything; music ducks −6dB under VO; −14 LUFS integrated,
  true peak −1dB; cut all music 0.5s before the cliffhanger frame — silence is the sting;
  room tone under every cut, J/L the ambience or the edit "clicks".

## Captions & titles → `motion-design.md`

Burned-in Armenian primary + thin English underbar; Noto Sans Armenian (captions) / GHEA
(titles); the **glyph gate** (mixed-script homoglyph check before export) and all caption
kinetics / title cards / thumbnail craft are owned by `motion-design.md`. Subtitle
translation/QC for EN/RU → `localization.md`.

## Tools & pipeline

- **Free path:** CapCut (vertical speed) → DaVinci Resolve 21 (grade/sound polish;
  **IntelliSearch** finds any shot in the master library by content — use it to pull b-roll
  and clip-mining candidates instead of scrubbing).
- **AI post:** enhance speech (Adobe MCP) · fal-ai for music beds, upscales, cleanups ·
  auto-transcribe for captions, then HUMAN glyph pass.
- Project hygiene: `exports/<slug>/` per `carousel-template.md`; version as v1, v2 —
  never "final".

## Export specs (canonical table, 2026)

Codec baseline (all vertical): **H.264 High, 1080×1920, MP4/MOV, AAC 320kbps 48kHz.**

| Platform | Res | Target / limit | Bitrate | Notes |
|---|---|---|---|---|
| IG Reels | 1080×1920 | **target 30–60s** (limit ~15–20 min; >3 min distribution penalty) | ~10–12 Mbps | burned captions, loop ending |
| TikTok | 1080×1920 | **target 21–34s** (limit 10 min in-app / 60 min upload) | 6–8 Mbps floor | AI-label if AI video |
| YouTube Shorts | 1080×1920 | ≤3 min | ~10 Mbps | retention loop |
| IG carousel video slide | 1080×1350 | ≤15s | ~10 Mbps | silent-safe (captions carry it) |
| YouTube (windows) | 3840×2160 | full | high | −14 LUFS, chapters |
| ReelShort-style episode | 1080×1920 | 60–120s | ~10–12 Mbps | cliffhanger cut, ep number card |

- **HDR:** master **SDR Rec.709**. IG passes Dolby Vision through, but mixed-feed HDR
  grays out the #0D0D0D blacks on SDR screens — stay SDR until the pipeline is
  HDR-monitored (`color-craft.md`).

## QC gate (before anything leaves the building)
- [ ] Hook in ≤3s; loop or cliffhanger at the end; jump-cut rhythm holds.
- [ ] Dialogue clear; **final mix checked on a real phone speaker AND cheap earbuds**;
      −14 LUFS; music ducks under VO.
- [ ] Grade matches register; AI shots normalized + indistinguishable after grain pass.
- [ ] Captions: proper Armenian Unicode, glyph-checked (`motion-design.md`), in safe zones.
- [ ] FX from the ALLOWED set only; no effect "announces itself".
- [ ] Specs match the export table; AI video labeled per platform; filename versioned;
      masters + LUTs + cue sheets archived.
- [ ] **C2PA Content Credentials signed + invisible watermark stamped** on the final export
      (author/provenance/AI-label in one) — `business-affairs.md`.
