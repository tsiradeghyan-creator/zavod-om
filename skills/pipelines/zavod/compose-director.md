# Compose Director — ZavodOM

## When to use
Render the final deliverable: stitch clips/slides, apply brand-font overlays, mix VO/music/SFX, master.

## Craft (read from skills/zavod-craft/)
`sound-craft.md` (4-layer build, loudness), `voice-director.md` (VO performance/pronunciation),
`composer-music-supervisor.md`, `final-mixer.md`, `mastering-delivery-qc.md`, `localization.md`,
`vfx-render-supervisor.md`, `compositor.md`.

## Process
1. Route by the locked lane (`engine_lock`) — never silently pick an engine. The seam rejects a compose
   checkpoint whose `engine_lock.compose_runtime` does not match the lane:
   - **Remotion lane** → `compose_runtime` follows the locked `render_runtime`: `remotion` (React
     composition pass) or `hyperframes` (HTML/CSS/GSAP kinetic cards & carousels; `hyperframes lint` +
     `hyperframes validate` must pass first). The `render_runtime` choice is locked at the idea stage.
   - **Higgsfield lane** → `compose_runtime` is **`ffmpeg`** only. **Zero Remotion** — stitch the approved
     Higgsfield clips and burn Armenian brand-font overlays via ffmpeg. Portable ffmpeg discovery (system
     ffmpeg / @ffmpeg-installer) — never depend on a specific OS.
   `delivery_promise.motion_required=true` makes the locked lane a commitment: a silent cross-lane swap
   (including an FFmpeg Ken Burns standing in for motion) is a CRITICAL governance violation. If the locked
   runtime fails, escalate — don't swap lanes.
2. Overlay brand-font text (never AI-baked). Mix VO over ducked ambient/music; target loudness (e.g. -14 LUFS).
3. Produce `render_report` + `final_review`, and carry `engine_lock` (with `compose_runtime`) on the checkpoint.

## Gate (HARD)
- **`continuity_checker`** runs on EVERY generated clip — sample dense frames, verify each
  `staging.in_hand_objects` + identity + architecture persists. A dropped object (the 06-18 glass) = fail.
- **`delivery_promise`** — a motion-led promise must not silently become a slideshow.
- ffprobe validates the output (resolution/aspect/streams); audio levels checked.
