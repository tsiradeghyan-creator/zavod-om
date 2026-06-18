# Compose Director — ZavodOM

## When to use
Render the final deliverable: stitch clips/slides, apply brand-font overlays, mix VO/music/SFX, master.

## Craft (read from skills/zavod-craft/)
`sound-craft.md` (4-layer build, loudness), `voice-director.md` (VO performance/pronunciation),
`composer-music-supervisor.md`, `final-mixer.md`, `mastering-delivery-qc.md`, `localization.md`,
`vfx-render-supervisor.md`, `compositor.md`.

## Process
1. Render via the composition runtime (Remotion/HTML overlay; FFmpeg for stitch/mux). Portable ffmpeg
   discovery (system ffmpeg / @ffmpeg-installer) — never depend on a specific OS.
2. Overlay brand-font text (never AI-baked). Mix VO over ducked ambient/music; target loudness (e.g. -14 LUFS).
3. Produce `render_report` + `final_review`.

## Gate (HARD)
- **`continuity_checker`** runs on EVERY generated clip — sample dense frames, verify each
  `staging.in_hand_objects` + identity + architecture persists. A dropped object (the 06-18 glass) = fail.
- **`delivery_promise`** — a motion-led promise must not silently become a slideshow.
- ffprobe validates the output (resolution/aspect/streams); audio levels checked.
