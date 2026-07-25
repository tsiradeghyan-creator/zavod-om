# OpenMontage - Shared Project Context

This is the single source of truth for project architecture and conventions. All platform-specific agent files (CLAUDE.md, CODEX.md, CURSOR.md, COPILOT.md) should point here instead of duplicating this content.

## Identity

OpenMontage is an open-source, AI-orchestrated media-production platform. ZavodOM is its universal
content-production layer: a brand-neutral craft brain plus code-enforced routing, artifacts, gates,
and owner checkpoints. The bundled Maghakian authorial profile is optional and remains separate from
visual identity.

## Architecture: Hybrid Agent Control Plane

Creative judgment remains in model agents instructed by pipeline manifests and Markdown craft
skills. Python is the deterministic control plane: it validates content routing, discovers typed
agent capabilities, plans dependency-aware dispatch waves, records task receipts, enforces
approvals/checkpoints, drives those waves through a native host adapter, and refuses unsupported
claims of completion.

```text
request → typed agent route → isolated specialist dispatch waves
        → hash-linked execution receipts → hash-bound synthesis candidate
        → exact owner gate where required → independent final verification → pipeline artifacts/checkpoints
        → owner-gated external action
```

This distinction is contractual:

- A file in `skills/` is a **role playbook**: knowledge and acceptance rules for a worker.
- An entry in `agents/registry.yaml` is a **dispatchable agent card**: capabilities, triggers,
  permissions, budget, evidence duties, failure policy, and instruction hashes.
- A card counts as a **real agent execution** only when a host launches an isolated worker and the
  execution ledger records its executor/run identity, output hash, and evidence. Merely reading
  several role playbooks in one context is simulation, not multi-agent execution.
- `lib/agent_router.py` plans work; `lib.orchestrator.execute_agent_run(...)` executes the graph,
  parallel waves, receipts, owner pauses, and fallback replans. Claude, Codex, or an API host must
  provide the actual native worker adapter. A host without isolated workers may use explicitly labeled degraded
  `single_context_simulation`, but simulation cannot satisfy the independent-verifier task or a
  claim of complete multi-agent execution.

## Source of Truth

- **Agent guide & contract:** `AGENT_GUIDE.md` (tool inventory, pipeline selection, dispatch, stage playbooks, protocols)
- **Executable agent registry:** `agents/registry.yaml`
- **Agent control schemas:** `schemas/agents/`
- **Agent router/runtime:** `lib/agent_registry.py`, `lib/agent_router.py`, `lib/agent_runtime.py`,
  `lib/orchestrator.execute_agent_run(...)`
- **Host-neutral dispatch contract:** `skills/meta/agent-routing.md`
- **Skill index:** `skills/INDEX.md`
- **Tool registry:** `tools/tool_registry.py`
- **Pipeline manifests:** `pipeline_defs/`
- **Artifact schemas:** `schemas/artifacts/`
- **Style playbooks:** `styles/*.yaml` (schema: `schemas/styles/playbook.schema.json`)
- **Stage director skills:** `skills/pipelines/<pipeline>/<stage>-director.md`
- **Meta skills:** `skills/meta/*.md` (reviewer, checkpoint-protocol, skill-creator)
- **Architecture deep-dive:** `docs/ARCHITECTURE.md`

## Knowledge Architecture (3 Layers)

```
Layer 1: tools/tool_registry.py     → "What tools exist" (runtime capabilities, status, cost)
Layer 2: skills/                    → "How OpenMontage uses them" (project conventions)
Layer 3: .agents/skills/            → "How the technology works" (generic API rules, skills.sh)
```

Each tool's `agent_skills[]` field bridges Layer 1 → Layer 3. See `skills/INDEX.md` for the full mapping.

These are knowledge layers, not proof of process isolation. The agent control plane above them
selects the smallest sufficient specialist team and records which host workers actually executed it.

## Key Patterns

- **Pipeline state machines:** media routes use `idea -> script -> scene_plan -> assets -> edit -> compose -> publish`;
  the no-render `zavod-content` route uses `idea -> script -> quality -> publish`
- **Deterministic content routing:** a schema-valid `content_spec` maps each supported format/modality
  to a real pipeline or fails loudly (`lib/content_router.py`)
- **Automatic specialist activation:** `lib/agent_router.py` extracts declared request signals,
  scores every typed card, records selected and rejected agents with reasons, blocks unmatched
  required capabilities, and emits bounded dependency waves
- **Real execution receipts:** `lib/agent_runtime.py` maintains an append-only task lifecycle ledger.
  A completed task needs an executor identity, output hash, and evidence; terminal tasks are immutable
- **Independent acceptance:** the Executive Producer first builds one hash-bound candidate from
  receipt-backed specialist work while preserving blocking and minority findings. The verifier then
  evaluates that exact candidate in a different isolated run from every producer. A `revise` or
  `reject` verdict requires a new hash-linked plan; the producer cannot self-certify the same output
- **Instruction-driven stages:** Each stage has a director skill (MD) that teaches the agent HOW
- **Pipeline manifests:** Declarative YAML defining stages, skills, tools, review focus, approval gates
- **Capability-first tool design:** Each major family should expose a selector tool plus explicit provider tools
  - Example: `tts_selector` + `elevenlabs_tts` / `google_tts` / `openai_tts` / `piper_tts`
  - Example: `video_selector` + `heygen_video` / `wan_video` / `hunyuan_video` / `ltx_video_local` / `ltx_video_modal` / `cogvideo_video`
- **Style playbooks:** YAML defining visual language, typography, motion, audio, asset generation constraints
- **Artifacts are canonical:** the original media artifacts plus `content_spec`, `creative_identity`,
  `candidate_bakeoff`, `authorial_voice_report`, `content_quality_report`, and `rights_manifest`
  (32 artifact schemas total)
- **Alternatives are proven:** `zavod-content` scripts require 3–5 complete blind candidates with
  verified unique hashes, material differences across at least two creative axes, explicit rejection
  reasons, and canonical hash identity between the selected candidate and final script
- **Packages are exact:** a content script may hold one deliverable or a multi-deliverable package;
  IDs/kinds/languages must match the locked spec. Aggregate quality covers every promised item exactly
  once, runs all eight checks, and binds each review to the exact payload SHA-256.
- **Creative identity is split:** authorial voice may be neutral/reference/strict independently of
  optional visual identity. Strict Maghakian mode pins draft/profile hashes and evidence at the script seam.
- **Final rights/provenance:** export and publication require the exact local payload, passing rights,
  consent/disclosure, owner approval, and matching rights-row hash coverage; publication also needs
  the returned URL. Claimed signed/verified C2PA manifests are file/hash-checked, but SHA-256 evidence
  is not cryptographic C2PA signature verification.
- **Append-only approved history:** new Zavod checkpoints hash-link to the exact previous checkpoint.
  Resume fails if an earlier approval changed, and an earlier stage cannot be overwritten while later
  linked checkpoints exist. This is tamper-evident integrity, not a cryptographic signature.
- **Every tool inherits from `tools/base_tool.py`** (ToolContract)
- **Checkpoint policy** lives in pipeline manifest (`human_approval_default` per stage) + `skills/meta/checkpoint-protocol.md`
- **Stage self-review** via `skills/meta/reviewer.md` is advisory. A routed automatic-agent run also
  requires the registry's independent `quality-auditor`; same-context simulation cannot satisfy it
- **Evidence-bound superiority claims:** architecture, schemas, and green unit tests establish
  contract integrity, not market leadership. A "best in the world" claim requires a versioned blind
  evaluation against named current baselines on identical briefs, inputs, budgets, and rubrics,
  repeated runs, independent expert preference evidence, and disclosed failures and limitations
- **Cost tracker** (`tools/cost_tracker.py`) manages budget: estimate -> reserve -> reconcile
- **Canonical artifacts** validated against JSON schemas in `schemas/artifacts/`

## Key Files

| File | Purpose |
|------|---------|
| `config.yaml` | Global configuration |
| `lib/config_model.py` | Runtime config loader (Pydantic) |
| `lib/checkpoint.py` | Checkpoint writer/reader |
| `lib/pipeline_loader.py` | Pipeline manifest loader + helpers |
| `agents/registry.yaml` | Typed cards, triggers, permissions, budgets, fallbacks, and verifier policy |
| `lib/agent_registry.py` | Registry/schema/reference validation + exact instruction hashing |
| `lib/agent_router.py` | Request signals → selected/rejected agents → bounded dispatch waves |
| `lib/agent_runtime.py` | Immutable task states, dependency/approval enforcement, hash-linked receipts |
| `lib/orchestrator.py` | Native-host execution loop, safe parallel waves, fallback replan, pipeline checkpoints |
| `schemas/agents/` | Request, registry, activation-plan, and execution-ledger contracts |
| `skills/meta/agent-routing.md` | Cross-host dispatch, handoff, parallelism, receipt, verifier, and owner-gate law |
| `lib/content_router.py` | Validated format/modality → pipeline routing |
| `lib/candidate_bakeoff.py` | Blind full-draft comparison and selected/final identity proof |
| `lib/authorial_voice.py` | Pinned authorial profile signals and strict evidence validation |
| `lib/provenance.py` | Final local-file existence/hash/coverage verification |
| `lib/media_profiles.py` | Platform-specific render profiles |
| `styles/playbook_loader.py` | Style playbook loader + validator + design intelligence (color/type/a11y) |
| `tools/base_tool.py` | ToolContract base class |
| `tools/tool_registry.py` | Tool discovery and reporting |
| `tools/cost_tracker.py` | Budget governance |
| `tools/video/video_stitch.py` | Multi-clip assembly (stitch, spatial, validate, preview) |
| `tools/video/video_compose.py` | Runtime-aware composition orchestrator — routes to Remotion / HyperFrames / FFmpeg based on `edit_decisions.render_runtime` |
| `tools/video/hyperframes_compose.py` | HyperFrames runtime — workspace materialization, `hyperframes lint`/`validate`/`render`, FFmpeg floor check |
| `tools/character/character_animation.py` | Local character-animation tools — character specs, SVG rig plans, pose libraries, action timelines, HyperFrames packages, and QA reports |
| `lib/hyperframes_style_bridge.py` | Playbook → CSS custom properties + `DESIGN.md` bridge for HyperFrames workspaces |
| `remotion-composer/src/components/` | 8 Remotion components (TextCard, StatCard, ProgressBar, CalloutBox, ComparisonCard + charts/) |
| `.agents/skills/hyperframes*/` | Vendored HyperFrames Layer 3 skills (authoring contract, CLI, registry, website-to-video) |
| `skills/core/hyperframes.md` | Layer 2 — when OpenMontage should pick HyperFrames vs Remotion, artifact → workspace mapping |
| `schemas/styles/playbook.schema.json` | Playbook schema v2 with design tokens (chart_palette, scale_system, weight_matrix, color_rules) |
| `tests/qa/` | Quality validation test scripts for tool-by-tool output inspection |

## Available Pipelines

| Pipeline | Manifest | Type |
|----------|----------|------|
| `zavod-content` | `pipeline_defs/zavod-content.yaml` | Universal written/narrative, no render |
| `zavod-carousel` | `pipeline_defs/zavod-carousel.yaml` | Gated carousel production |
| `zavod-reel` | `pipeline_defs/zavod-reel.yaml` | Full gated short-video production |
| `zavod-reel-fast` | `pipeline_defs/zavod-reel-fast.yaml` | Audited short-video fast lane |
| `zavod-promo` | `pipeline_defs/zavod-promo.yaml` | Promotional image/video/mixed production |
| `talking-head` | `pipeline_defs/talking-head.yaml` | Footage-based |
| `animated-explainer` | `pipeline_defs/animated-explainer.yaml` | AI-generated |
| `screen-demo` | `pipeline_defs/screen-demo.yaml` | Screen-recording |
| `clip-factory` | `pipeline_defs/clip-factory.yaml` | Short-form batch extraction |
| `podcast-repurpose` | `pipeline_defs/podcast-repurpose.yaml` | Podcast repurposing |
| `cinematic` | `pipeline_defs/cinematic.yaml` | Cinematic edit |
| `animation` | `pipeline_defs/animation.yaml` | Animation-first |
| `character-animation` | `pipeline_defs/character-animation.yaml` | Local rigged character animation |
| `hybrid` | `pipeline_defs/hybrid.yaml` | Source-plus-support hybrid |
| `avatar-spokesperson` | `pipeline_defs/avatar-spokesperson.yaml` | Avatar presenter |
| `localization-dub` | `pipeline_defs/localization-dub.yaml` | Localization and dubbing |
| `framework-smoke` | `pipeline_defs/framework-smoke.yaml` | Test harness |

## When Building New Pipelines

1. Create a YAML manifest in `pipeline_defs/` (validated by `pipeline_manifest.schema.json`)
2. Create one stage director skill per manifest stage in `skills/pipelines/<pipeline-name>/`
3. Reference meta skills (reviewer, checkpoint-protocol) in the manifest
4. Add compatible playbooks to the manifest
5. Add contract tests in `tests/contracts/`
6. If the pipeline introduces a new specialist capability, add or update a typed card and routing
   tests; a director skill by itself does not create an executable agent

## When Building New Tools

1. Inherit from `tools/base_tool.py` `BaseTool`
2. Put the tool in the correct capability package (`tools/audio/`, `tools/video/`, `tools/enhancement/`, `tools/analysis/`, `tools/graphics/`, `tools/avatar/`, `tools/subtitle/`)
3. Prefer the selector-plus-provider pattern:
   - one capability router tool for agent convenience
   - one concrete tool per real provider/runtime path
4. Set all contract fields (name, version, tier, capability, provider, supports, fallback_tools, agent_skills, etc.)
5. Implement `execute()` returning a `ToolResult`
6. Let discovery happen through `tools/tool_registry.py`; do not depend on ad hoc imports
7. Add a JSON schema in `schemas/tools/` if the tool has complex I/O
8. Add tests only after the runtime path is correct
