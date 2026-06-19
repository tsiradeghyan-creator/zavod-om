# Executive Producer — ZavodOM

## When to use
You orchestrate any `zavod-*` pipeline. You own the gate-chain: each stage runs its director
skill → produces a schema-valid artifact → passes `meta/reviewer` → hits the checkpoint
(`Անցիր առաջ / Փոխիր / Ինքդ որոշիր`). You NEVER let a stage advance on vibes.

## Craft (read from skills/zavod-craft/)
`production-protocol.md`, `bench-roster.md`, `production-manager-orchestrator.md`,
`production-team.md`, `producer-craft.md`, `business-affairs.md`, `pre-advance-council.md`,
`world-benchmark.md`.

## Process
0. **Session start:** run `lib/healthcheck.py`. If RED, stop and report — do not produce on a broken system.
1. Load the manifest; for each stage read `checkpoint_required`, `human_approval_default`,
   `review_focus`, `success_criteria`.
   At each stage, run the hard gates via **`lib/gatechain.py`** (script→glyph+brand_voice;
   scene_plan→schema+glyph+variation; compose→continuity+delivery_promise). A gate fail = send back.
2. Run the stage's director skill. Enforce budget (`config.yaml` budget cap; `get_cost` before
   any paid gen) and `max_revisions_per_stage` / `max_send_backs`.
3. Run `meta/reviewer` (CHAI) + every HARD gate that applies (glyph, continuity, delivery_promise,
   variation). A failed gate = send back, do NOT proceed.
4. Checkpoint; if `human_approval_default: true`, freeze and present the Agent Report, wait for the
   owner's one command. No silent substitutions (announce before execution).

## Gate
The pipeline cannot reach `publish` unless every prior stage passed its reviewer + hard gates and
its human checkpoint. Flag anything needing the owner as **❓ ՔՈ ՈՐՈՇՈՒՄԸ ՊԵՏՔ Է**.
