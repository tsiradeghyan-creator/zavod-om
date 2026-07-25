# ZavodOM — universal content production, with an enforcement spine

ZavodOM is a brand-neutral production system for supported written, narrative, image, audio,
video, and mixed deliverables. It is rebuilt on the OpenMontage spine as **craft brain +
enforcement**. The Maghakian authorial profile is bundled, but it is a selectable Script DNA
layer—not a global palette, logo, or visual-style requirement.

`README.md` contains the upstream OpenMontage documentation; this file is the ZavodOM entry point.

## Start every session here
```bash
./.venv/bin/python lib/healthcheck.py     # GREEN/RED signal (corpus, gates, manifests, render)
```

Then ask the owner before any production work:

```text
Ո՞ր ռեժիմով ենք աշխատում։
1. Քո հաստատումներով՝ փուլ առ փուլ։ Default. Ամեն փուլ ավարտվում է Agent Report-ով և կանգնում է մինչև «Անցիր առաջ»։
2. Ավտոմատ լրիվ սևագրային վազք։ Կարող եմ ներսում ստուգել, հետ ուղարկել ու սևագիր հավաքել, բայց չեմ հրապարակում, գումար չեմ ծախսում, իրավունք/դեմք/լոկացիա չեմ փակում և վերջնական չեմ հանձնում առանց քո հաստատման։

Գործակալներ՝ լռելյայն ավտոմատ երթուղում՝ հարցին առնչվող ամենափոքր բավարար իրական թիմը։
Ամբողջ բենչը միացրու միայն հստակ հրամանով։ `lib/bench_gate.py`-ը դեռ պարտադիր դերերի բովանդակային վճիռներն է պահանջում,
բայց մեկ համատեքստում դերի կատարումը իրական բազմագործակալային աշխատանք չի համարվում։
```

If the owner says the script already exists, do not rewrite it by default: start from the
next unlocked stage, produce that stage's report, and wait for approval.

## The three layers
- **Spine** (OpenMontage, AGPLv3): `pipeline_defs/*.yaml` (gated stage DAGs), `schemas/artifacts/*.json`
  (32 schema-validated artifact types), `lib/` (loader, checkpoint, routing, scoring, reviewer),
  `meta/reviewer` + `meta/checkpoint-protocol`.
- **Brain** (the zavod's 52 craft files + `SKILL.md` + `INDEX.md`): `skills/zavod-craft/` wires each craft file
  to a pipeline stage/role/gate. The pinned Maghakian authorial profile derives from the private
  owner-supplied corpus; visual identity remains a separate, optional lock.
- **Arsenal**: `skills/providers/higgsfield-capabilities.md` — every agent knows the full Higgsfield toolset.

## Automatic agent activation

The executable roster lives in `agents/registry.yaml`. Each card declares capabilities, multilingual
triggers and exclusions, input/output contracts, allowed tools, evidence, stop conditions, budget,
failure policy, and exact instruction files. `skills/meta/agent-routing.md` is the host-neutral
dispatch and receipt contract. The required flow for non-trivial work is:

```text
route → dispatch dependency waves → ledger receipts → hash-bound synthesis candidate
→ exact owner gate where required → independent final verification
```

Production starts with
`lib.orchestrator.initialize_agent_run(pipeline_dir, project_id, request)`, then
`lib.orchestrator.execute_agent_run(...)` drives the selected waves through the host's native agent
adapter. The first call writes the immutable request, plan, and ledger; the second launches safe
parallel work, records receipts, pauses for exact owner approval, performs the one-time allowlisted
fallback when necessary, and reaches the independent verifier. The production orchestrator refuses
to close a Zavod checkpoint until the run and its independent final verification are complete.

1. `lib/agent_router.py` records request signals plus every selected and rejected agent with reasons.
   Missing required capability blocks the plan.
2. `execute_agent_run(...)` dispatches each planned task through the supplied native host adapter.
   Independent tasks run in parallel; later waves wait for their declared dependencies.
3. `lib/agent_runtime.py` records an append-only receipt chain. Completion requires executor/run
   identity, exact output hash, and evidence; terminal tasks cannot be rewritten.
4. The Executive Producer synthesizes one hash-bound candidate from receipt-backed work and preserves
   objections and blockers.
5. Rights/likeness, publication, and destructive-change approvals bind to the exact synthesized
   output hash and host-verified owner identity proof; paid generation/runtime approval binds to the
   exact planned task contract.
6. `quality-auditor` must evaluate that exact approved candidate in a different isolated execution from every
   producing specialist. A `revise` or `reject` verdict requires a new hash-linked plan; the producer
   cannot self-certify or rewrite the terminal result in place. The corrected run starts through
   `lib.orchestrator.initialize_revision_run(...)` with a new request ID and a correction artifact.

Craft files in `skills/zavod-craft/` and stage director files are **role playbooks**, not processes.
They become real agent work only when a host launches an isolated worker and the ledger records its
receipt. The router itself never calls a model; `execute_agent_run(...)` owns the real execution loop,
while Claude, Codex, or an API deployment supplies the native worker adapter. Claude filesystem
adapters load at session start and therefore require a restart after they
change; `.claude/agents` files do not activate Codex workers. If isolated workers are unavailable, the
run must be labeled degraded `single_context_simulation`; it may produce a draft but cannot count as
independent verification or a complete multi-agent run.

Owner gates remain stronger than automation. Publication, paid generation or a material runtime
change, rights/likeness decisions, destructive changes, and final delivery require explicit approval
bound to the exact planned action hash.

## Pipelines (general; projects/styles sit on top)
Five Zavod manifests are currently audited: `zavod-content`, `zavod-carousel`, `zavod-reel`,
`zavod-reel-fast`, and `zavod-promo`. `lib/content_router.py` validates `content_spec` and maps
each supported format to a real pipeline or fails loudly; a campaign package expands into an explicit
bundle instead of being squeezed through a video workflow.

`zavod-content` is the no-render lane for social posts, captions, articles, newsletters,
screenplays, series episodes, and stage plays. One run may carry one deliverable or an exact
multi-deliverable package:

```text
idea → script → quality → publish
```

Media pipelines keep the full director bench in `skills/pipelines/zavod/*-director.md`:

```text
idea → script → scene → asset → edit → compose → publish
```

## Creative identity: handwriting first

`creative_identity` locks authorial voice independently from `visual_identity`. In strict Maghakian
mode, the script seam requires the pinned `maghakian-script-v1` profile and an
`authorial_voice_report`. Code verifies the draft/profile hashes, exact draft excerpts, corpus
references, seven criterion scores, score math, Unicode, format, register signal, and generic-trope
checks. A reviewer still makes the literary judgment; the evidence cannot be fabricated or bypassed.

The script stage also requires a blind `candidate_bakeoff`: three to five complete schema-valid
drafts, hidden generator/system preference, at least two creative difference axes, unique hashes and
materially different text, an explicit reason for every rejection, and exact canonical hash identity
between the selected candidate and the submitted final script.

`scripts/voice_extractor.py` incrementally scans new or changed UTF-8 corpus text, updates a hash
ledger, and writes review-only deltas. It never edits the curated authorial canon automatically.

## Gate coverage
| Gate | Status | File | Catches |
|---|---|---|---|
| Armenian glyph | checkpoint-enforced | `lib/armenian_glyph_gate.py` | Latin/Cyrillic inside Armenian words |
| Blind candidate bake-off | checkpoint-enforced for `zavod-content` | `lib/candidate_bakeoff.py` | cosmetic variants, revealed system preference, fake hashes, missing rejection reasons, final draft changed after selection |
| Authorial Script DNA | checkpoint-enforced in strict mode | `lib/authorial_voice.py` | wrong profile/register, stale hashes, invented excerpts/corpus refs, weak score |
| Continuity | checkpoint-enforced | `lib/continuity_checker.py` | disappearing in-hand object / identity / architecture |
| Brand voice | checkpoint-enforced | `lib/brand_voice_check.py` | generic-AI tropes / drift |
| Variation | checkpoint-enforced | `lib/variation_checker.py` | slideshow / generic scene plans |
| Schema | checkpoint-enforced | `schemas/artifacts/*.json` | malformed/vague artifacts (incl. scene_plan.staging/text_policy) |
| Delivery promise | checkpoint-enforced, required at edit seam | `lib/delivery_promise.py` | motion-led silently downgraded to slideshow or bypassed by missing promise |
| Universal content contract | checkpoint-enforced for `zavod-content` | `lib/content_router.py` + `lib/checkpoint.py` | wrong route, mutated spec/identity, run-mode mismatch, missing package item, incomplete/duplicate QC, QC bound to wrong draft hash |
| Checkpoint history integrity | checkpoint-enforced for new Zavod runs | `lib/checkpoint.py` | an earlier approved checkpoint changed after the next stage linked to its SHA-256; earlier-stage overwrite while later approvals exist |
| Rights + local provenance | checkpoint-enforced at final export/publish | `lib/gatechain.py` + `lib/provenance.py` | unresolved rights/consent/disclosure, missing exact local payload, hash mismatch, uncovered final file, missing returned URL, invalid claimed C2PA-manifest file/hash |
| Gate-chain | dispatcher | `lib/gatechain.py` | runs the right gates per stage |

## Self-improvement (Scout) — wake-safe
`skills/meta/scout.md` + `lib/scout.py` + `library/known_capabilities.json` + `tools/com.zavodom.scout.plist`
(launchd, runs healthcheck first). Weekly: web-scan → dedup → score → gated upgrade memo → (on approval)
skill-creator drafts a skill / provider. Nothing auto-installs.

## Quality claim law

"Best in the world" is a target, not a status emitted by the system. It may be claimed only after a
versioned blind evaluation compares ZavodOM with named current baselines on the same briefs, inputs,
budgets, and acceptance rubric; repeats runs to expose variance; includes expert human preference
review; and publishes failures and limitations. Green unit tests prove contract integrity, not global
creative superiority.

## Rules
Rule Zero: every production runs a routed pipeline (no ad-hoc prompt-and-pray). Armenian = Eastern Unicode
only (glyph gate). On-image text = overlay (AI-baked only for short display words that pass the glyph gate).
Strict authorial voice and optional visual identity are separate decisions. An aggregate
`content_quality_report` is written-content post-production, not decorative review: it covers every
promised deliverable exactly once, runs all eight checks, and binds each result to the exact draft
payload SHA-256. A draft may carry unresolved rights, but a final export or publication may not.
Both final states require the exact local payload; publication also requires its returned URL. A
claimed signed/verified C2PA manifest must exist and match its declared hash, but that hash check does
not itself create or cryptographically verify a C2PA signature.
Default mode: no stage advances without its gate + the owner's checkpoint (Անցիր առաջ / Փոխիր / Ինքդ որոշիր).
Autonomous mode may draft, retake, and verify internally, but publish/spend/rights-lock/final delivery still
require the owner's explicit approval.

## Run (portable, any OS)
```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt   # spine deps
cd remotion-composer && npm install                                     # render runtime
# rendering uses portable ffmpeg discovery: system ffmpeg or @ffmpeg-installer
```
