"""Minimal production orchestrator — the executable runtime that drives a pipeline through
its stages, wiring get_next_stage -> write_checkpoint -> resume_checkpoint into a real run.

Until this module existed, every gate in lib/checkpoint.py was an *enforceable library* with
no production caller: nothing sequenced an actual run, so the gates were only ever exercised
by tests. This is that spine — deliberately thin. It does NOT generate creative content
(agents/skills do that); it decides which stage runs next, gates each stage completion through
write_checkpoint (so every contract — ordering, referential integrity, glyph, continuity,
ladder — fires on the real path), stops at owner checkpoints, and resumes fail-closed.

Owner law (Mozg): the orchestrator advances one stage at a time and never skips ahead. A
stage may pause the run for the owner by completing as ``awaiting_human`` instead of
``completed``; the run does not proceed past it until the owner supplies the completed write.
"""
from __future__ import annotations

import copy
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Optional

import jsonschema

from lib.checkpoint import (
    CheckpointValidationError,
    _canonical_pipeline_type,
    get_completed_stages,
    get_next_stage,
    get_pipeline_stages,
    read_checkpoint,
    resume_checkpoint,
    write_checkpoint,
)
from lib.agent_registry import content_hash, load_agent_registry
from lib.agent_router import (
    normalize_agent_request,
    replan_with_fallback,
    route_agents,
)
from lib.agent_runtime import AgentRuntimeError, TaskLedger


class OrchestratorError(RuntimeError):
    """Raised when a run is driven incorrectly — e.g. an out-of-order advance."""


AGENT_RUNTIME_DIRECTORY = "agent_runtime"
AGENT_RESULT_SCHEMA = (
    Path(__file__).resolve().parent.parent / "schemas" / "agents" / "agent_result.schema.json"
)


def _validate_host_result(result: dict[str, Any]) -> None:
    try:
        schema = json.loads(AGENT_RESULT_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(result)
    except jsonschema.ValidationError as exc:
        where = ".".join(str(part) for part in exc.absolute_path) or "<root>"
        raise AgentRuntimeError(
            f"Invalid native host result at {where}: {exc.message}"
        ) from exc


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_immutable_json(path: Path, value: dict[str, Any], label: str) -> None:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise OrchestratorError(f"Existing {label} is unreadable: {path}") from exc
        if existing != value:
            raise OrchestratorError(f"Existing {label} is immutable and does not match: {path}")
        return
    _atomic_json(path, value)


def _agent_project_root(pipeline_dir: Path, project_id: str) -> Path:
    return Path(pipeline_dir) / project_id / AGENT_RUNTIME_DIRECTORY


def _agent_run_root(pipeline_dir: Path, project_id: str, request_id: str) -> Path:
    # request_id is schema-constrained to a single safe path component.
    return _agent_project_root(pipeline_dir, project_id) / request_id


def _agent_output_path(run_root: Path, task_id: str, output_hash: str) -> Path:
    return run_root / "outputs" / task_id / f"{output_hash}.json"


def _persist_agent_output(
    run_root: Path,
    task: dict[str, Any],
    output_hash: str,
    output: Any,
    *,
    hash_binding: str = "payload",
) -> dict[str, Any]:
    envelope = {
        "version": "1.0",
        "task_id": task["task_id"],
        "agent_id": task["agent_id"],
        "output_artifact": task["output_artifact"],
        "output_hash": output_hash,
        "hash_binding": hash_binding,
        "output": output,
    }
    _write_immutable_json(
        _agent_output_path(run_root, task["task_id"], output_hash),
        envelope,
        "agent task output",
    )
    return envelope


def _load_agent_output(run_root: Path, task_id: str, output_hash: str) -> dict[str, Any]:
    path = _agent_output_path(run_root, task_id, output_hash)
    if not path.is_file():
        raise OrchestratorError(
            f"Completed dependency {task_id!r} has no immutable output payload {output_hash}."
        )
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise OrchestratorError(f"Agent task output is unreadable: {path}") from exc
    if (
        envelope.get("task_id") != task_id
        or envelope.get("output_hash") != output_hash
    ):
        raise OrchestratorError(f"Agent task output identity does not match its receipt: {path}")
    binding = envelope.get("hash_binding")
    if binding == "payload":
        matches = content_hash(envelope.get("output")) == output_hash
    elif binding == "approved_action":
        output = envelope.get("output")
        matches = isinstance(output, dict) and output.get("approved_action_hash") == output_hash
    else:
        matches = False
    if not matches:
        raise OrchestratorError(f"Agent task output payload does not match its hash binding: {path}")
    return envelope


def _active_plan_hash(run_root: Path) -> str:
    pointer = run_root / "active_plan.json"
    if not pointer.is_file():
        raise OrchestratorError(f"Agent run has no active plan pointer: {pointer}")
    try:
        value = json.loads(pointer.read_text(encoding="utf-8"))
    except Exception as exc:
        raise OrchestratorError(f"Agent active plan pointer is unreadable: {pointer}") from exc
    plan_hash = value.get("plan_hash") if isinstance(value, dict) else None
    if (
        value.get("version") != "1.0"
        or not isinstance(plan_hash, str)
        or len(plan_hash) != 64
        or any(char not in "0123456789abcdef" for char in plan_hash)
    ):
        raise OrchestratorError(f"Agent active plan pointer is invalid: {pointer}")
    return plan_hash


def _load_agent_plan(run_root: Path, plan_hash: str) -> dict[str, Any]:
    path = run_root / "plans" / f"{plan_hash}.json"
    if not path.is_file():
        raise OrchestratorError(f"Active agent plan is missing: {path}")
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise OrchestratorError(f"Active agent plan is unreadable: {path}") from exc
    if content_hash(plan) != plan_hash:
        raise OrchestratorError(f"Active agent plan hash mismatch: {path}")
    return plan


def _agent_state_from_root(run_root: Path) -> dict[str, Any]:
    plan_hash = _active_plan_hash(run_root)
    plan = _load_agent_plan(run_root, plan_hash)
    ledger_path = run_root / "ledgers" / f"{plan_hash}.json"
    completion: dict[str, Any] | None = None
    if plan["routing_status"] == "ready":
        if not ledger_path.is_file():
            raise OrchestratorError(f"Ready agent plan has no execution ledger: {ledger_path}")
        try:
            ledger = TaskLedger.load(ledger_path, plan)
            tasks = {task["task_id"]: task for task in plan["tasks"]}
            for event in ledger.data["events"]:
                if event["to_state"] == "completed":
                    task = tasks[event["task_id"]]
                    envelope = _load_agent_output(
                        run_root,
                        event["task_id"],
                        event["output_hash"],
                    )
                    if (
                        envelope.get("agent_id") != task["agent_id"]
                        or envelope.get("output_artifact") != task["output_artifact"]
                    ):
                        raise OrchestratorError(
                            f"Agent output contract does not match task {event['task_id']!r}."
                        )
                    if task["phase"] == "owner_gate":
                        working = next(
                            item for item in reversed(ledger.data["events"])
                            if item["task_id"] == event["task_id"]
                            and item["to_state"] == "working"
                        )
                        if envelope["output"].get("approval") != working["approval"]:
                            raise OrchestratorError(
                                f"Owner output receipt does not match ledger task {event['task_id']!r}."
                            )
            completion = ledger.completion_report()
        except AgentRuntimeError as exc:
            raise OrchestratorError(f"Agent execution ledger failed verification: {exc}") from exc
    return {
        "request_id": plan["request_id"],
        "plan_hash": plan_hash,
        "supersedes_plan_hash": plan["supersedes_plan_hash"],
        "routing_status": plan["routing_status"],
        "selected_agents": [item["agent_id"] for item in plan["selected_agents"]],
        "unmatched_capabilities": list(plan["unmatched_capabilities"]),
        "completion": completion,
        "run_directory": str(run_root),
        "plan_path": str(run_root / "plans" / f"{plan_hash}.json"),
        "ledger_path": str(ledger_path) if ledger_path.is_file() else None,
    }


def initialize_agent_run(
    pipeline_dir: Path,
    project_id: str,
    request: str | dict[str, Any],
) -> dict[str, Any]:
    """Create an immutable activation plan and append-only execution ledger.

    This is the mandatory entry point for a new agent-backed request. It is idempotent for
    the exact same request, but it never replaces a plan after the registry or request changes.
    A blocked route is preserved for audit and receives no executable ledger.
    """
    normalized = normalize_agent_request(request)
    registry = load_agent_registry()
    plan = route_agents(normalized, registry=registry)
    return _persist_agent_run(pipeline_dir, project_id, normalized, plan)


def _persist_agent_run(
    pipeline_dir: Path,
    project_id: str,
    normalized: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, Any]:
    run_root = _agent_run_root(pipeline_dir, project_id, normalized["request_id"])
    _write_immutable_json(run_root / "request.json", normalized, "agent request")

    plan_hash = content_hash(plan)
    plan_path = run_root / "plans" / f"{plan_hash}.json"
    _write_immutable_json(plan_path, plan, "agent activation plan")
    pointer = run_root / "active_plan.json"
    if pointer.exists() and _active_plan_hash(run_root) != plan_hash:
        raise OrchestratorError(
            f"Agent request {normalized['request_id']!r} already has a different immutable "
            "active plan; use a new request id or an explicit hash-linked fallback replan."
        )

    if plan["routing_status"] == "ready":
        ledger_path = run_root / "ledgers" / f"{plan_hash}.json"
        if ledger_path.exists():
            TaskLedger.load(ledger_path, plan)
        else:
            TaskLedger.create(ledger_path, plan)
    _atomic_json(pointer, {"version": "1.0", "plan_hash": plan_hash})
    return _agent_state_from_root(run_root)


def initialize_revision_run(
    pipeline_dir: Path,
    project_id: str,
    prior_request_id: str,
    revised_request: str | dict[str, Any],
) -> dict[str, Any]:
    """Create a new hash-linked run after an independent revise/reject verdict.

    The revised request needs a new request ID and at least one explicit input-artifact reference
    to the revised candidate or correction packet. The previous plan and ledger stay immutable.
    """
    prior_root = _agent_run_root(pipeline_dir, project_id, prior_request_id)
    _agent_state_from_root(prior_root)
    prior_hash = _active_plan_hash(prior_root)
    prior_plan = _load_agent_plan(prior_root, prior_hash)
    prior_ledger_path = prior_root / "ledgers" / f"{prior_hash}.json"
    try:
        prior_report = TaskLedger.load(prior_ledger_path, prior_plan).completion_report()
    except AgentRuntimeError as exc:
        raise OrchestratorError(f"Cannot revise from an invalid agent ledger: {exc}") from exc
    negative_tasks = [
        *prior_report.get("revise_required", []),
        *prior_report.get("rejected_results", []),
    ]
    if not negative_tasks:
        raise OrchestratorError(
            f"Agent request {prior_request_id!r} has no terminal revise/reject verdict."
        )

    normalized = normalize_agent_request(revised_request)
    if normalized["request_id"] == prior_request_id:
        raise OrchestratorError("A revision run requires a new request_id.")
    if not normalized["input_artifacts"]:
        raise OrchestratorError(
            "A revision run requires an explicit revised candidate or correction artifact reference."
        )
    registry = load_agent_registry()
    plan = route_agents(normalized, registry=registry)
    plan["supersedes_plan_hash"] = prior_hash
    plan["replan_reason"] = (
        "Independent verdict requires a new candidate; superseded task verdicts: "
        + ", ".join(sorted(negative_tasks))
    )
    return _persist_agent_run(pipeline_dir, project_id, normalized, plan)


def load_agent_run(
    pipeline_dir: Path,
    project_id: str,
    request_id: str,
) -> dict[str, Any]:
    """Load and fully verify the active plan and ledger for one request."""
    return _agent_state_from_root(_agent_run_root(pipeline_dir, project_id, request_id))


def _project_agent_runs(pipeline_dir: Path, project_id: str) -> list[dict[str, Any]]:
    root = _agent_project_root(pipeline_dir, project_id)
    if not root.is_dir():
        return []
    states = [
        _agent_state_from_root(path)
        for path in sorted(root.iterdir(), key=lambda item: item.name)
        if path.is_dir()
    ]
    return states


def activate_agent_fallback(
    pipeline_dir: Path,
    project_id: str,
    request_id: str,
    failed_task_id: str,
) -> dict[str, Any]:
    """Activate one allowlisted fallback while preserving the superseded plan and ledger."""
    run_root = _agent_run_root(pipeline_dir, project_id, request_id)
    _agent_state_from_root(run_root)
    old_hash = _active_plan_hash(run_root)
    old_plan = _load_agent_plan(run_root, old_hash)
    old_ledger_path = run_root / "ledgers" / f"{old_hash}.json"
    try:
        old_ledger = TaskLedger.load(old_ledger_path, old_plan)
    except AgentRuntimeError as exc:
        raise OrchestratorError(f"Cannot replan from an invalid agent ledger: {exc}") from exc
    report = old_ledger.completion_report()
    if failed_task_id not in report.get("fallback_required", []):
        raise OrchestratorError(
            f"Task {failed_task_id!r} has no recorded fallback-eligible terminal failure."
        )

    new_plan = replan_with_fallback(old_plan, failed_task_id)
    new_hash = content_hash(new_plan)
    new_plan_path = run_root / "plans" / f"{new_hash}.json"
    _write_immutable_json(new_plan_path, new_plan, "fallback activation plan")
    new_ledger_path = run_root / "ledgers" / f"{new_hash}.json"
    if not new_ledger_path.exists():
        new_ledger = TaskLedger.create(new_ledger_path, new_plan)
        old_tasks = {task["task_id"]: task for task in old_plan["tasks"]}
        new_tasks = {task["task_id"]: task for task in new_plan["tasks"]}
        # Reuse only receipts whose complete task contract is byte-for-byte unchanged. Tasks
        # downstream of the failed primary receive a new dependency/idempotency key and must run
        # again; independent completed siblings are carried forward without paying twice.
        for wave in sorted(new_plan["waves"], key=lambda value: value["wave"]):
            for task_id in wave["task_ids"]:
                if task_id not in old_tasks or old_tasks[task_id] != new_tasks[task_id]:
                    continue
                old_state = old_ledger.state(task_id)
                if old_state == "failed":
                    failure_event = next(
                        event for event in reversed(old_ledger.data["events"])
                        if event["task_id"] == task_id and event["to_state"] == "failed"
                    )
                    new_ledger.transition(
                        task_id,
                        "failed",
                        evidence=[f"superseded-event:{failure_event['event_hash']}"],
                        reason=(
                            "Unchanged terminal failure carried from the superseded immutable "
                            f"plan: {failure_event['reason']}"
                        ),
                    )
                    continue
                if old_state != "completed":
                    continue
                completion_event = next(
                    event for event in reversed(old_ledger.data["events"])
                    if event["task_id"] == task_id and event["to_state"] == "completed"
                )
                executor = completion_event["executor"]
                if new_tasks[task_id]["external_side_effects"] == "approval_required":
                    working_event = next(
                        event for event in reversed(old_ledger.data["events"])
                        if event["task_id"] == task_id and event["to_state"] == "working"
                    )
                    new_ledger.transition(
                        task_id,
                        "approval_required",
                        reason="Approval state carried from the superseded immutable plan.",
                    )
                    new_ledger.transition(
                        task_id,
                        "working",
                        executor=executor,
                        approval=working_event["approval"],
                        reason="Unchanged completed task carried from the superseded plan.",
                    )
                else:
                    new_ledger.transition(
                        task_id,
                        "working",
                        executor=executor,
                        reason="Unchanged completed task carried from the superseded plan.",
                    )
                new_ledger.transition(
                    task_id,
                    "completed",
                    executor=executor,
                    output_hash=completion_event["output_hash"],
                    evidence=completion_event["evidence"],
                    verdict=completion_event["verdict"],
                    reason="Verified receipt carried from the superseded immutable plan.",
                )
    else:
        TaskLedger.load(new_ledger_path, new_plan)
    _atomic_json(run_root / "active_plan.json", {"version": "1.0", "plan_hash": new_hash})
    return _agent_state_from_root(run_root)


def execute_agent_run(
    pipeline_dir: Path,
    project_id: str,
    request_id: str,
    host_executor: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
    *,
    approval_provider: Callable[[dict[str, Any], str], dict[str, Any] | None] | None = None,
    auto_fallback: bool = True,
) -> dict[str, Any]:
    """Drive a routed request through native host workers, receipts, gates, and verification.

    ``host_executor`` is the platform boundary: Claude, Codex, or an API host must launch the
    isolated worker named by the task and return its executor/output/evidence receipt. Independent
    tasks in a parallel-safe wave are launched concurrently. The dispatcher never impersonates a
    model worker and never fabricates owner approval.
    """
    run_root = _agent_run_root(pipeline_dir, project_id, request_id)
    request_path = run_root / "request.json"
    if not request_path.is_file():
        raise OrchestratorError(f"Agent request is missing: {request_path}")
    request = json.loads(request_path.read_text(encoding="utf-8"))

    max_replans = 16
    for _ in range(max_replans):
        plan_hash = _active_plan_hash(run_root)
        plan = _load_agent_plan(run_root, plan_hash)
        if plan["routing_status"] != "ready":
            return _agent_state_from_root(run_root)
        ledger_path = run_root / "ledgers" / f"{plan_hash}.json"
        ledger = TaskLedger.load(ledger_path, plan)
        tasks = {task["task_id"]: task for task in plan["tasks"]}
        replanned = False

        for wave in sorted(plan["waves"], key=lambda item: item["wave"]):
            dispatchable: list[tuple[dict[str, Any], dict[str, Any] | None]] = []
            owner_waiting = False
            for task_id in wave["task_ids"]:
                task = tasks[task_id]
                state = ledger.state(task_id)
                if state == "completed":
                    continue
                if state in {"failed", "cancelled", "rejected"}:
                    continue
                if state == "working":
                    raise OrchestratorError(
                        f"Task {task_id!r} is already working; reconcile that host run before "
                        "automatic redispatch."
                    )

                approval: dict[str, Any] | None = None
                if task["external_side_effects"] == "approval_required" and state != "input_required":
                    if state == "submitted":
                        ledger.transition(
                            task_id,
                            "approval_required",
                            reason="The exact planned action requires verified owner approval.",
                        )
                    expected_hash = ledger.expected_approval_hash(task_id)
                    if approval_provider is None:
                        owner_waiting = True
                        continue
                    approval = approval_provider(copy.deepcopy(task), expected_hash)
                    if approval is None:
                        owner_waiting = True
                        continue

                if task["phase"] == "owner_gate":
                    if approval is None:
                        owner_waiting = True
                        continue
                    owner_executor = {
                        "type": "owner_approval",
                        "run_id": f"owner:{approval.get('identity_proof_hash', '')[:24]}",
                        "model": "verified-human-owner",
                        "prompt_version": task["prompt_version"],
                    }
                    ledger.transition(
                        task_id,
                        "working",
                        executor=owner_executor,
                        approval=approval,
                        reason="The host returned a verified owner identity and exact action hash.",
                    )
                    exact_hash = ledger.expected_approval_hash(task_id)
                    _persist_agent_output(
                        run_root,
                        task,
                        exact_hash,
                        {
                            "approved_action_hash": exact_hash,
                            "approval": approval,
                        },
                        hash_binding="approved_action",
                    )
                    ledger.transition(
                        task_id,
                        "completed",
                        output_hash=exact_hash,
                        evidence=[
                            f"identity-provider:{approval.get('identity_provider', '')}",
                            f"identity-proof:{approval.get('identity_proof_hash', '')}",
                            f"approved-action:{exact_hash}",
                        ],
                        reason="Owner approval is bound to the immutable candidate hash.",
                    )
                    continue
                dispatchable.append((task, approval))

            if owner_waiting:
                return _agent_state_from_root(run_root)
            if not dispatchable:
                report = ledger.completion_report()
                if report["fallback_required"]:
                    if auto_fallback:
                        activate_agent_fallback(
                            pipeline_dir,
                            project_id,
                            request_id,
                            report["fallback_required"][0],
                        )
                        replanned = True
                        break
                    return _agent_state_from_root(run_root)
                if report["status"] in {"failed", "revision_required", "complete"}:
                    return _agent_state_from_root(run_root)
                continue

            def invoke(item: tuple[dict[str, Any], dict[str, Any] | None]) -> tuple[str, Any]:
                task, _ = item
                ancestor_ids: set[str] = set()
                pending = list(task["depends_on"])
                while pending:
                    dependency_id = pending.pop()
                    if dependency_id in ancestor_ids:
                        continue
                    ancestor_ids.add(dependency_id)
                    pending.extend(tasks[dependency_id]["depends_on"])
                ancestor_outputs: dict[str, dict[str, Any]] = {}
                for dependency_id in sorted(ancestor_ids):
                    completion_event = next(
                        (
                            event for event in reversed(ledger.data["events"])
                            if event["task_id"] == dependency_id
                            and event["to_state"] == "completed"
                        ),
                        None,
                    )
                    if completion_event is not None:
                        ancestor_outputs[dependency_id] = _load_agent_output(
                            run_root,
                            dependency_id,
                            completion_event["output_hash"],
                        )
                context = {
                    "request": copy.deepcopy(request),
                    "plan_hash": plan_hash,
                    "dependency_receipts": ledger._dependency_receipts(task),
                    "ancestor_outputs": ancestor_outputs,
                }
                try:
                    result = host_executor(copy.deepcopy(task), context)
                    return (task["task_id"], result)
                except Exception as exc:  # host isolation boundary; record, then fail closed
                    return (task["task_id"], exc)

            results: dict[str, Any] = {}
            if wave["parallel"] and len(dispatchable) > 1:
                workers = min(plan["policy"]["max_parallel"], len(dispatchable))
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    futures = {pool.submit(invoke, item): item[0]["task_id"] for item in dispatchable}
                    for future in as_completed(futures):
                        task_id, result = future.result()
                        results[task_id] = result
            else:
                for item in dispatchable:
                    task_id, result = invoke(item)
                    results[task_id] = result

            approvals = {task["task_id"]: approval for task, approval in dispatchable}
            for task, _ in dispatchable:
                task_id = task["task_id"]
                result = results[task_id]
                if isinstance(result, Exception):
                    ledger.transition(
                        task_id,
                        "failed",
                        reason=f"Host launch failed closed: {type(result).__name__}: {result}",
                    )
                    continue
                if not isinstance(result, dict):
                    ledger.transition(
                        task_id,
                        "failed",
                        reason="Host returned a non-object task receipt.",
                    )
                    continue
                try:
                    _validate_host_result(result)
                except AgentRuntimeError as exc:
                    ledger.transition(
                        task_id,
                        "failed",
                        reason=f"Invalid host receipt failed closed: {exc}",
                    )
                    continue
                executor = result.get("executor")
                try:
                    ledger.transition(
                        task_id,
                        "working",
                        executor=executor,
                        approval=approvals[task_id],
                        reason="The native host returned an isolated executor receipt.",
                    )
                    status = result.get("status")
                    if status == "completed":
                        if result.get("output_artifact") != task["output_artifact"]:
                            raise AgentRuntimeError(
                                f"Host task {task_id!r} returned the wrong output artifact type."
                            )
                        if "output" not in result:
                            raise AgentRuntimeError(
                                f"Host task {task_id!r} returned no canonical output payload."
                            )
                        computed_output_hash = content_hash(result["output"])
                        if result.get("output_hash") != computed_output_hash:
                            raise AgentRuntimeError(
                                f"Host task {task_id!r} output hash does not match its payload."
                            )
                        _persist_agent_output(
                            run_root,
                            task,
                            computed_output_hash,
                            result["output"],
                        )
                        ledger.transition(
                            task_id,
                            "completed",
                            output_hash=computed_output_hash,
                            evidence=result.get("evidence", []),
                            verdict=result.get("verdict"),
                            reason=str(result.get("reason") or "Host task completed."),
                        )
                    elif status == "input_required":
                        ledger.transition(
                            task_id,
                            "input_required",
                            evidence=result.get("evidence", []),
                            reason=str(result.get("reason") or "Host task needs additional input."),
                        )
                    elif status == "failed":
                        ledger.transition(
                            task_id,
                            "failed",
                            evidence=result.get("evidence", []),
                            reason=str(result.get("reason") or "Host task failed."),
                        )
                    else:
                        raise AgentRuntimeError(
                            f"Host task {task_id!r} returned unsupported status {status!r}."
                        )
                except AgentRuntimeError as exc:
                    current = ledger.state(task_id)
                    if current not in {"failed", "completed", "cancelled", "rejected"}:
                        ledger.transition(
                            task_id,
                            "failed",
                            reason=f"Invalid host receipt failed closed: {exc}",
                        )

            report = ledger.completion_report()
            if report["fallback_required"] and auto_fallback:
                activate_agent_fallback(
                    pipeline_dir,
                    project_id,
                    request_id,
                    report["fallback_required"][0],
                )
                replanned = True
                break
            if report["status"] in {
                "failed", "revision_required", "complete"
            }:
                return _agent_state_from_root(run_root)
            if any(state == "input_required" for state in report["states"].values()):
                return _agent_state_from_root(run_root)

        if replanned:
            continue
        return _agent_state_from_root(run_root)
    raise OrchestratorError("Automatic agent execution exceeded the bounded fallback limit.")


def _require_agent_completion(
    pipeline_dir: Path,
    project_id: str,
    request_id: str | None,
    *,
    require_initialized: bool = False,
) -> None:
    all_states = _project_agent_runs(pipeline_dir, project_id)
    by_hash = {state["plan_hash"]: state for state in all_states}

    def ancestors(state: dict[str, Any]) -> set[str]:
        result: set[str] = set()
        prior_hash = state["supersedes_plan_hash"]
        while prior_hash is not None and prior_hash not in result:
            result.add(prior_hash)
            prior = by_hash.get(prior_hash)
            prior_hash = prior["supersedes_plan_hash"] if prior is not None else None
        return result

    complete_states = [
        state for state in all_states
        if state["completion"] is not None and state["completion"]["status"] == "complete"
    ]
    unresolved_negative: list[str] = []
    for state in all_states:
        completion = state["completion"] or {}
        has_negative_verifier = bool(
            completion.get("revise_required") or completion.get("rejected_results")
        )
        if has_negative_verifier and not any(
            state["plan_hash"] in ancestors(candidate) for candidate in complete_states
        ):
            unresolved_negative.append(state["request_id"])
    if unresolved_negative:
        raise OrchestratorError(
            "Checkpoint cannot bypass an unresolved independent revise/reject verdict. "
            "Create and complete a hash-linked revision run for: "
            + ", ".join(sorted(unresolved_negative))
        )

    states = all_states
    if request_id is not None:
        matches = [state for state in states if state["request_id"] == request_id]
        if len(matches) != 1:
            raise OrchestratorError(
                f"Checkpoint references unknown or ambiguous agent request {request_id!r}."
            )
        states = matches
    if not states:
        if require_initialized:
            raise OrchestratorError(
                "Zavod checkpoint cannot close before initialize_agent_run creates a typed "
                "activation plan and execution ledger."
            )
        return
    blocked = []
    for state in states:
        completion = state["completion"]
        status = completion["status"] if completion is not None else state["routing_status"]
        if status != "complete":
            blocked.append(f"{state['request_id']}={status}")
    if blocked:
        raise OrchestratorError(
            "Checkpoint cannot close before mandatory agent work and independent verification "
            f"complete: {', '.join(blocked)}"
        )


def run_state(pipeline_dir: Path, project_id: str, pipeline_type: str) -> dict[str, Any]:
    """The current state of a run.

    Returns the completed stages, the next stage to run (None when finished), whether the run
    is paused at an owner checkpoint, and a ``done`` flag.
    """
    # Canonicalize at the public boundary: a stray-cased/whitespace pipeline_type must resolve
    # to the real manifest, or get_pipeline_stages returns the generic order and the orchestrator
    # drives e.g. character-animation without its character_design/rig_plan stages (#round-5).
    pipeline_type = _canonical_pipeline_type(pipeline_type)
    completed = get_completed_stages(pipeline_dir, project_id, pipeline_type)
    next_stage = get_next_stage(pipeline_dir, project_id, pipeline_type)
    awaiting_human: Optional[str] = None
    for stage in get_pipeline_stages(pipeline_type):
        cp = read_checkpoint(pipeline_dir, project_id, stage)
        if cp and cp.get("status") == "awaiting_human":
            awaiting_human = stage
            break
    agent_runs = _project_agent_runs(pipeline_dir, project_id)
    superseded_hashes = {
        state["supersedes_plan_hash"]
        for state in agent_runs
        if state["supersedes_plan_hash"] is not None
    }
    lineage_heads = [
        state for state in agent_runs if state["plan_hash"] not in superseded_hashes
    ]
    agents_complete = all(
        state["completion"] is not None
        and state["completion"]["status"] == "complete"
        for state in lineage_heads
    )
    return {
        "pipeline_type": pipeline_type,
        "completed": completed,
        "next_stage": next_stage,
        "awaiting_human": awaiting_human,
        "agent_runs": agent_runs,
        "done": next_stage is None and awaiting_human is None and agents_complete,
    }


def advance(
    pipeline_dir: Path,
    project_id: str,
    pipeline_type: str,
    *,
    stage: str,
    artifacts: dict[str, Any],
    status: str = "completed",
    agent_request_id: str | None = None,
    **write_kwargs: Any,
) -> dict[str, Any]:
    """Advance the run by writing ``stage``'s checkpoint, and return the new run state.

    A ``completed`` write must target the next expected stage — no skipping ahead, no
    re-completing a finished stage. The ordering the checkpoint spine already enforces is
    surfaced here as a loud runtime error *before* anything is written, so a caller cannot
    drive the run out of order. Every gate runs inside write_checkpoint; a gate violation
    propagates as CheckpointValidationError.
    """
    pipeline_type = _canonical_pipeline_type(pipeline_type)  # resolve to the real manifest
    current = run_state(pipeline_dir, project_id, pipeline_type)
    awaiting = current["awaiting_human"]
    if awaiting is not None:
        if stage != awaiting or status != "completed":
            raise OrchestratorError(
                f"Run {project_id!r} is awaiting owner approval at stage {awaiting!r}; "
                "no downstream or parallel checkpoint may start."
            )
        if write_kwargs.get("human_approved") is not True:
            raise OrchestratorError(
                f"Stage {awaiting!r} can resume only with an explicit owner approval."
            )
        write_kwargs["human_approval_required"] = True

    expected = get_next_stage(pipeline_dir, project_id, pipeline_type)
    if expected is None:
        raise OrchestratorError(
            f"Run {project_id!r} is already complete — nothing left to advance."
        )
    if stage != expected:
        raise OrchestratorError(
            f"Out-of-order advance: run {project_id!r} expects stage {expected!r} next, "
            f"not {stage!r}."
        )

    if status == "awaiting_human":
        write_kwargs["human_approval_required"] = True
        write_kwargs["human_approved"] = False
    if (
        status == "completed"
        and write_kwargs.get("human_approval_required") is True
        and write_kwargs.get("human_approved") is not True
    ):
        raise OrchestratorError(
            f"Stage {stage!r} requires owner approval and cannot be marked completed without it."
        )
    if status == "completed":
        _require_agent_completion(
            pipeline_dir,
            project_id,
            agent_request_id,
            require_initialized=pipeline_type.startswith("zavod-"),
        )
    write_checkpoint(
        pipeline_dir, project_id, stage, status, artifacts,
        pipeline_type=pipeline_type, **write_kwargs,
    )
    return run_state(pipeline_dir, project_id, pipeline_type)


def resume(pipeline_dir: Path, project_id: str, stage: str | None = None) -> Optional[dict[str, Any]]:
    """Resume a run fail-closed.

    Delegates to resume_checkpoint, which re-runs the structural contracts, a read-only canon
    check, artifact existence/media validation, and referential integrity before handing back
    the state to continue from. A hand-edited, drifted, or dangling checkpoint is refused, not
    silently continued.
    """
    # Loading every active agent plan/ledger replays their schemas, hashes, dependency order,
    # approvals, and verifier isolation before a checkpoint is handed back to the host.
    _project_agent_runs(pipeline_dir, project_id)
    return resume_checkpoint(pipeline_dir, project_id, stage)
