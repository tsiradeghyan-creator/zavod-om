# Proposal Director - Character Animation Pipeline

## Goal

Present character-animation concepts that are honest about local rigged motion,
reuse, cost, and runtime choice.

## Required Proposal Elements

Each option must include:

- characters and roles,
- visual style,
- action complexity,
- rig reuse strategy,
- sample plan,
- audio architecture,
- music plan,
- render runtime options,
- cost estimate,
- honest limitation note.

## Runtime Selection (required field — `render_runtime`)

Character-animation proposals must lock a `render_runtime` (technical engine) as a
separate field from the creative grammar. Read `skills/meta/animation-runtime-selector.md`
and `skills/core/hyperframes.md` for the decision matrix, and `AGENT_GUIDE.md` →
"Present Both Composition Runtimes (HARD RULE)" for the governance contract.

**MANDATORY workflow — present both runtimes, don't silently default:**

1. Query `video_compose.get_info()["render_engines"]`. If both `remotion` and
   `hyperframes` are `True`, proceed to step 2. If only one is available, go to
   step 4 with just that one.
2. Present both runtimes to the user with brief-specific analysis:
   - **Remotion** (`remotion`) — best when the final composition needs deterministic
     React-rendered video, captions, audio, scene JSON, and final MP4 governance.
   - **HyperFrames** (`hyperframes`) — best when the character scene is HTML/SVG/GSAP-heavy
     and benefits from web-native authoring, lint, validate, and registry blocks.
3. FFmpeg (`ffmpeg`) is post-processing only — never the primary runtime for character acting.
4. Wait for explicit user approval. Do NOT write `render_runtime` into
   `proposal_packet.production_plan` before approval.
5. Log a `render_runtime_selection` decision in `decision_log` with BOTH runtimes in
   `options_considered`, the user's pick as `selected`, and the rationale as `reason`.
   If a runtime was unavailable, record it as rejected with
   `rejected_because: "runtime not available on this machine"`.

A `render_runtime_selection` decision with only one option considered when both were
available is a CRITICAL reviewer finding — that is exactly how a fresh-session agent
silently defaults to Remotion.

## Sample-First Rule

Before full production, propose a 10-15 second sample containing:

- one main character,
- one expression change,
- one body action,
- one camera/background treatment,
- one audio/music cue if relevant.

Do not batch-generate all assets until this sample is approved.

## Cost Honesty

Local rigging is cheap at render time but expensive in authoring complexity.
Report the difference:

- asset generation cost,
- TTS/music cost,
- local render cost,
- manual complexity risk.
