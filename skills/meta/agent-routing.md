# Agent Routing and Execution Contract

This is the host-neutral execution contract for ZavodOM's specialist agents. The canonical
machine-readable sources are:

- `agents/registry.yaml` — identities, triggers, skills, permissions, budgets, and failure policy.
- `lib/agent_router.py` — deterministic request normalization and activation planning.
- `lib/orchestrator.execute_agent_run(...)` — dependency-wave dispatch, native host receipts,
  bounded fallback replan, and owner pauses.
- `schemas/agents/activation_plan.schema.json` — the immutable task graph contract.
- `lib/agent_runtime.py` and `schemas/agents/execution_ledger.schema.json` — lifecycle and receipts.

Platform files such as `.claude/agents/*.md` are adapters. They may narrow permissions, but they
must not broaden or replace the registry card.

## 1. Route before work

1. Normalize the request with `build_agent_request` or an equivalent schema-valid adapter.
2. Add inferred topics, formats, risks, or capabilities only when the request or locked artifacts
   provide evidence. Never remove a hard risk merely to obtain a smaller team.
3. Call `route_agents`; do not hand-pick a different team after seeing the result.
4. Persist the activation plan and its hash before any specialist starts. Production hosts call
   `lib.orchestrator.initialize_agent_run(pipeline_dir, project_id, request)`; a Zavod checkpoint
   cannot close through the production orchestrator until that run has completed independent review.
5. If `routing_status` is `ready`, call `lib.orchestrator.execute_agent_run(...)` with the native host
   executor. This is the canonical automatic wave loop; do not rebuild it ad hoc in a prompt.
6. If `routing_status` is not `ready`, stop. Missing capabilities and owner input are blockers, not
   permission to improvise.

## 2. Smallest sufficient team

Every run contains the registry coordinator and independent verifier. Between them, dispatch only
the specialists selected by the deterministic plan.

- A specialist below the route score floor stays rejected unless a new, evidence-backed request
  signal produces a hash-linked replan.
- Record every selected and rejected agent with reasons.
- Do not summon a full theatrical bench. Add a specialist only for a declared capability, hard
  risk, format, or explicit owner request.
- Never exceed `policy.max_agents`. Split a genuinely larger request into separately approved runs.
- `resilience-generalist` is dormant. It is never a normal team member and may run only through
  `replan_with_fallback` after an allowlisted primary task terminates as failed.

## 3. Deterministic hard triggers

The registry and router are authoritative. A host may improve signal extraction, but these risk
classes may not be suppressed by model judgment:

- current, factual, sourced, competitive, or benchmark claims require `research-accuracy`;
- strict authorial voice, Maghakian Script DNA, Armenian dialogue/register, or glyph risk requires
  `authorial-voice-guardian`;
- rights, licenses, consent, likeness, external assets, or final publication require
  `rights-provenance`;
- translation, localization, subtitles, dubbing, or synthetic-voice consent requires
  `localization-director`;
- media generation, editing, mastering, paid generation, or runtime changes require the planned
  visual/media specialists and their owner gates;
- external distribution, publication, analytics actions, or account changes require
  `distribution-growth`;
- agent architecture, routing, schemas, tests, or governance changes require `system-architect`.

Negative trigger phrases in the registry are binding. For example, an explicit instruction that
visuals or colors are out of scope prevents visual work unless another hard requirement makes it
unavoidable and the owner approves a replan.

## 4. Dependency waves and bounded parallelism

Execute only the `waves` written in the activation plan.

1. Wave 0 locks decomposition, constraints, and the input snapshot.
2. Specialist waves follow `execution_order`. A task starts only after all required dependencies
   have completed.
3. A wave may run concurrently only when `parallel: true` and every task card is `parallel_safe`.
4. Run at most **4 tasks in parallel**, even if the host supports more.
5. Non-parallel tasks run alone.
6. After every required specialist has a valid receipt, the coordinator synthesizes one locked
   candidate. The candidate records its exact input receipts and output hash and preserves every
   blocker and minority report.
7. When the plan contains `owner_gate` tasks, each waits for synthesis and accepts only an owner
   approval whose action hash equals the exact synthesized output hash. The receipt also carries the
   host-verified identity provider and identity-proof hash. Task-bound paid-generation or runtime
   approvals use the full task idempotency hash. Any changed contract or candidate makes the receipt
   stale.
8. Final verification runs only after synthesis and required owner gates, in a fresh isolated context, against that exact
   candidate hash and its supporting receipts. Do not overlap synthesis and verification.

The maximum delegation depth is the registry policy, currently 3. Platform limitations may reduce
depth but may never create hidden nested work. Claude subagents cannot dispatch sibling subagents;
the parent host executes the plan.

## 5. Task handoff

Every handoff includes, without paraphrasing away constraints:

- `task_id`, `agent_id`, phase, objective, and dependency list;
- exact `input_hash` and input artifact references;
- registry hash, prompt version, and instruction-file hashes;
- allowed tools, evidence requirements, stop conditions, and budget;
- output artifact name, failure policy, fallback lineage, and external-side-effect policy;
- approval gate and idempotency/action hash when applicable.

The worker reads its exact registry card, this contract, and every skill listed by the card before
working. It returns only its bounded contribution with:

- status: `completed`, `input_required`, or `failed`;
- the exact declared output-artifact type, canonical JSON output payload, and matching SHA-256;
- concrete evidence satisfying the task card;
- blockers, dissent, assumptions, and unresolved questions;
- one safe next action or an explicit stop condition.

A worker does not edit another specialist's output, change the team, weaken a gate, or perform an
external action that was not approved in the plan.

## 6. Host adapters

### Claude Code

Use the matching file declared in `card.platform.claude_agent_file`. Descriptions support discovery,
but the parent supplies its native launch callback to `execute_agent_run(...)`, which dispatches the
exact planned task. Record executor type `claude_subagent`, the
actual run ID, model, and prompt version. Filesystem agents are loaded at session start; restart the
session after adding or changing an adapter.

### Codex

The parent wraps native collaboration/subagent tools as the `execute_agent_run(...)` callback with
the exact planned handoff. Record executor type `codex_subagent` and the returned run ID.
`.claude/agents` files do not cause Codex activation.

### API or another host

Start a fresh isolated context with only the planned instructions and allowed tools. Record executor
type `api_agent`, a stable run ID, model, and prompt version. The adapter must enforce the same task
graph, receipts, budgets, and owner gates.

### Single-context fallback

If no isolated worker exists, the main model may perform a bounded role only when the ledger labels
it `single_context_simulation`.

- Simulation is a continuity fallback, not a real specialist run.
- It must be disclosed in the final report.
- It cannot satisfy independent verification.
- It cannot claim cross-agent consensus or independence.
- When independent verification is required and no isolated verifier is available, the run pauses
  as incomplete instead of self-certifying success.

## 7. Receipts and append-only ledger

Create the ledger from the exact activation plan before dispatch. Every transition records the
planned agent, input hash, executor identity, evidence, reason, output hash, and previous-event hash.

- Follow the `TaskLedger` state machine; never rewrite a terminal event.
- A completed task needs an executor receipt, output hash, and non-empty evidence.
- `execute_agent_run(...)` independently hashes and immutably stores the canonical output payload;
  downstream workers receive the verified ancestor payloads, not only an uncheckable claimed hash.
- Verification must use a different isolated `run_id` from every producer and must not use
  `single_context_simulation`.
- Hidden retries are disabled (`policy.max_retries: 0`). A failed terminal task is never rerun under
  the same plan; only an allowlisted hash-linked fallback or a new revision plan may continue it.
- Fallback requires a hash-linked replacement plan. Never silently substitute an agent.
- Preserve the ledger head hash in the run's checkpoint/final report.

## 8. Owner gates

Automatic mode changes waiting behavior, not authority. Stop for explicit approval bound to the
exact action hash before:

- paid generation, spending, or a material provider/runtime change;
- publication, scheduling, messaging, account mutation, or another external action;
- rights, likeness, location, voice, or consent commitments;
- destructive repository or data changes;
- final delivery or release of the approved payload.

An approval for one hash does not authorize a changed prompt, file, provider, asset set, or payload.
Record a new plan/action hash and obtain new approval.

## 9. Verification, dissent, and completion

The verifier attacks the locked synthesis candidate, its receipts, and its evidence; it does not
manufacture missing producer evidence or edit the candidate it judges. Non-critical dissent remains
attached verbatim with its source agent and disposition. The coordinator may synthesize accepted
contributions before verification but cannot erase objections, relabel simulation as independent
work, or self-approve its candidate.

A `revise` or `reject` verdict blocks completion. It cannot be cleared by patching the candidate or
rerunning a task under the same activation plan. The coordinator must produce a new hash-linked
plan that records the verdict and superseded candidate, route the required work again, synthesize a
new hash-bound candidate, and obtain a new independent final-verification receipt. Use
`lib.orchestrator.initialize_revision_run(...)` with a new request ID and an explicit corrected
candidate or correction-packet artifact reference.

A routed run is complete only when:

- all required tasks have completed under legal transitions;
- all mandatory evidence and hashes match;
- the independent verifier passed the exact synthesis-candidate hash in a distinct isolated run;
- dissent and blockers are preserved and resolved or explicitly owner-accepted;
- every applicable owner gate has a matching approval receipt;
- the ledger verifies and its final head hash is reported.
