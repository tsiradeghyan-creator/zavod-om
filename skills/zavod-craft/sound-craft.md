# Sound Craft — Ձայնային դիզայն (FILM MODE)

Sound is half the picture and all of the gut-punch. The biggest structural truth: **AI
footage arrives SILENT** — there is no production sound, so every shot's audio is built
from scratch. The edit grammar lives in `post-production.md`; this file builds the world.

## The 4-layer build (every AI shot, every scene)

1. **Ambience bed** — loopable, one per location (street, kitchen, ward). Lay it first.
2. **Spot FX** — sync points: doors, footsteps, cloth rustle, cup on table, the collapse.
3. **Sweeteners** — low-end under the turns; a sub hit on the cliffhanger frame.
4. **Room-tone glue** — one room-tone bed per scene, **J/L-ed across every cut**, or the
   timeline "clicks." Ambience continuity is what makes silent AI shots feel real.

## V2A first pass — the machine drafts the world, the ear keeps it (2026)

Video-to-audio models now watch a silent shot and generate frame-synced sound:
**ElevenLabs Video-to-Sound** (AI vision on the frames → matching SFX, 48kHz) and
**ThinkSound** (MMAudio + chain-of-thought; three stages: foundational foley →
object-centric refinement → natural-language editing). Use them as the DRAFT of layers 1–2:

- Run V2A on each AI shot → it proposes the ambience bed + sync spot FX in one pass.
- Keep what the ear accepts; replace what reads generic. **Layers 3–4 stay human** —
  sweeteners, room-tone glue, the leitmotif, and the cliffhanger silence are creative calls.
- **The subtext object is foleyed by hand.** V2A hears the scene, not the dramaturgy — it
  will never know the cup matters more than the street. If the ECU object isn't audible in
  the V2A pass, that sound is OURS to build, not the model's to guess.
- Log V2A prompts/edits like any music cue (`business-affairs.md`).
- Text-to-SFX for beds with no visual reference: `eleven_text_to_sound_v2` (48kHz, supports
  looping) — describe the room, not the emotion.

## Dialogue chain (order is non-negotiable)

**denoise → de-click → de-ess → high-pass 80Hz → subtractive EQ → compression (2:1–4:1,
slow attack) → limiter LAST.** Never limit before EQ. Adobe `media_enhance_speech` (MCP)
does the first cleanup pass on VO; the chain order still applies after.

## Music supervision

- **Only IG-monetization-safe sources:** Meta Sound Collection, a paid **sync license**,
  or fal-ai–generated cues with **logged prompts**. Social licenses do NOT cover
  sponsored/paid posts (`business-affairs.md`).
- **Cue sheet per episode:** cue / source / license / timecode — co-owned with
  `business-affairs.md`.
- **Leitmotif strategy:** each series («Վանը», «Ախրիման») gets ONE 3–5 note motif;
  restate it at every cliffhanger — sonic branding compounds across a season.

## House loudness & cliffhanger law (shared with `post-production.md`)

- Dialogue intelligibility > everything; music ducks **−6dB** under VO.
- **−14 LUFS** integrated for social; true peak **−1dB**.
- **Cut all music 0.5s before the cliffhanger frame — silence is the sting.**

## Foley priorities for AI shots

Hands and objects carry her subtext, so foley them first: footsteps, cloth, object
handling (the cup, the cigarette, the laundry line), the door, the breath that stops.
The ECU subtext object (`art-department.md`) must be AUDIBLE.

## Execution tools (our doctrine → their engine)

**DaVinci Resolve 21 Fairlight** (free) runs the whole 4-layer build + the dialogue chain +
−14 LUFS metering in one place; its **folder tracks** (new in 21) hold one collapsible
folder per scene — the 4 layers stay grouped and the big mix stays navigable. **Adobe `media_enhance_speech`** (MCP) for the VO denoise
pass; **fal-ai** music/SFX models for ambience beds and sweeteners (log prompts —
`business-affairs.md`). Auto-transcribe for captions, then the HUMAN glyph pass
(`motion-design.md`). Tools layer and clean; the leitmotif and the cliffhanger silence are
creative calls, kept human.

## Sound checklist
- [ ] 4 layers present on every AI shot; room tone J/L-ed across cuts.
- [ ] V2A draft (if used) reviewed by ear; layers 3–4 human; V2A prompts logged.
- [ ] Dialogue chain applied in order; intelligible on phone speaker + earbuds.
- [ ] −14 LUFS / −1dB TP; music −6dB under VO; silence 0.5s before the cliffhanger.
- [ ] Every music cue has a license; cue sheet filed; leitmotif restated at the turn.
- [ ] Subtext object foleyed; the collapse/door designed as a sonic event.
