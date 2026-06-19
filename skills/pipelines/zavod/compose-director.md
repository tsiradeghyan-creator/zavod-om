# Compose Director — ZavodOM

## When to use
Render the final deliverable: stitch clips/slides, apply brand-font overlays, mix VO/music/SFX, master.

## Craft (read from skills/zavod-craft/)
`sound-craft.md` (4-layer build, loudness), `voice-director.md` (VO performance/pronunciation),
`composer-music-supervisor.md`, `final-mixer.md`, `mastering-delivery-qc.md`, `localization.md`,
`vfx-render-supervisor.md`, `compositor.md`.

## Process
1. Route by `edit_decisions.render_runtime` — never silently pick an engine:
   - **`render_runtime="remotion"`** — clip-led reels/promos via the React composition pass.
   - **`render_runtime="hyperframes"`** — HTML/CSS/GSAP kinetic title cards & carousels; `hyperframes lint`
     and `hyperframes validate` must both pass before render. See `skills/core/hyperframes.md`.
   - **`render_runtime="ffmpeg"`** — bare stitch/mux. Portable ffmpeg discovery (system ffmpeg /
     @ffmpeg-installer) — never depend on a specific OS.
   `delivery_promise.motion_required=true` makes the locked runtime a commitment: a silent swap (including
   FFmpeg Ken Burns) is a CRITICAL governance violation. If the locked runtime fails, escalate — don't swap.
2. Overlay brand-font text (never AI-baked). Mix VO over ducked ambient/music; target loudness (e.g. -14 LUFS).
3. Produce `render_report` + `final_review`.

## Gate (HARD)
- **`continuity_checker`** runs on EVERY generated clip — sample dense frames, verify each
  `staging.in_hand_objects` + identity + architecture persists. A dropped object (the 06-18 glass) = fail.
- **`delivery_promise`** — a motion-led promise must not silently become a slideshow.
- ffprobe validates the output (resolution/aspect/streams); audio levels checked.
