"""Append-only execution ledger for routed ZavodOM agent tasks.

This module does not pretend to be an LLM. Platform adapters execute tasks; the ledger makes
their lifecycle auditable and fail-closed. Every event is hash-linked, terminal tasks are
immutable, dependencies must be satisfied, approval is bound to the task idempotency hash,
and an independent verifier cannot share the producer's isolated run or use the single-context
simulation fallback.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

import jsonschema

from lib.agent_registry import content_hash, file_hash, task_contract_hash


ROOT = Path(__file__).resolve().parent.parent
PLAN_SCHEMA = ROOT / "schemas" / "agents" / "activation_plan.schema.json"
LEDGER_SCHEMA = ROOT / "schemas" / "agents" / "execution_ledger.schema.json"

TERMINAL_STATES = frozenset({"completed", "failed", "cancelled", "rejected"})
ALLOWED_TRANSITIONS: dict[str | None, frozenset[str]] = {
    None: frozenset({"submitted"}),
    "submitted": frozenset({"working", "approval_required", "failed", "cancelled", "rejected"}),
    "working": frozenset({"input_required", "approval_required", "completed", "failed", "cancelled"}),
    "input_required": frozenset({"working", "failed", "cancelled"}),
    "approval_required": frozenset({"working", "failed", "cancelled", "rejected"}),
    "completed": frozenset(),
    "failed": frozenset(),
    "cancelled": frozenset(),
    "rejected": frozenset(),
}


class AgentRuntimeError(RuntimeError):
    """Raised when task execution would violate routing, provenance, or approval law."""


def _schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_schema(instance: dict[str, Any], path: Path, label: str) -> None:
    try:
        jsonschema.Draft202012Validator(
            _schema(path), format_checker=jsonschema.FormatChecker()
        ).validate(instance)
    except jsonschema.ValidationError as exc:
        where = ".".join(str(part) for part in exc.absolute_path) or "<root>"
        raise AgentRuntimeError(f"Invalid {label} at {where}: {exc.message}") from exc


def _contract_path(relative_path: str) -> Path:
    candidate = (ROOT / relative_path).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError as exc:
        raise AgentRuntimeError(
            f"Task contract path escapes the repository: {relative_path!r}"
        ) from exc
    return candidate


def _verify_contract_files(task: dict[str, Any], executor_type: str) -> None:
    snapshots = dict(task["instruction_hashes"])
    if executor_type == "claude_subagent":
        snapshots.update(task["platform_adapter_hashes"])
    for relative_path, expected_hash in snapshots.items():
        path = _contract_path(relative_path)
        if not path.is_file() or file_hash(path) != expected_hash:
            raise AgentRuntimeError(
                f"Task {task['task_id']!r} instruction snapshot is missing or stale: "
                f"{relative_path!r}. Create a new activation plan."
            )


def _validate_executor_receipt(task: dict[str, Any], executor: dict[str, Any]) -> None:
    executor_type = executor.get("type")
    if executor.get("prompt_version") != task["prompt_version"]:
        raise AgentRuntimeError(
            f"Task {task['task_id']!r} executor used a different prompt version."
        )
    isolated = {"claude_subagent", "codex_subagent", "api_agent"}
    if task["phase"] == "owner_gate":
        if executor_type != "owner_approval":
            raise AgentRuntimeError(
                f"Owner gate task {task['task_id']!r} requires an owner approval executor."
            )
    elif task["phase"] == "verify":
        if executor_type == "single_context_simulation":
            raise AgentRuntimeError(
                "A simulated role cannot satisfy independent verification."
            )
        if executor_type not in isolated:
            raise AgentRuntimeError(
                "Independent verification requires an isolated host agent executor."
            )
    elif executor_type not in isolated | {"single_context_simulation"}:
        raise AgentRuntimeError(
            f"Task {task['task_id']!r} has an executor incompatible with its phase."
        )


def validate_activation_plan(plan: dict[str, Any]) -> None:
    """Validate graph, routing, and approval semantics beyond JSON shape."""
    _validate_schema(plan, PLAN_SCHEMA, "activation plan")
    if plan["routing_status"] != "ready":
        raise AgentRuntimeError(
            f"Activation plan is {plan['routing_status']!r} and cannot create an execution ledger."
        )
    if plan["unmatched_capabilities"]:
        raise AgentRuntimeError("A ready activation plan cannot have unmatched capabilities.")
    if (plan["supersedes_plan_hash"] is None) != (plan["replan_reason"] is None):
        raise AgentRuntimeError(
            "Activation plan supersession hash and replan reason must be declared together."
        )
    tasks = plan["tasks"]
    if any(not task["required"] for task in tasks):
        raise AgentRuntimeError(
            "Every routed task is mandatory; irrelevant agents must be rejected, not optional."
        )
    task_ids = [task["task_id"] for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        raise AgentRuntimeError("Activation plan contains duplicate task IDs.")
    by_id = {task["task_id"]: task for task in tasks}
    for task in tasks:
        if task["input_hash"] != plan["request_hash"]:
            raise AgentRuntimeError(
                f"Task {task['task_id']!r} is not bound to the activation request hash."
            )
        if task["idempotency_key"] != task_contract_hash(task):
            raise AgentRuntimeError(
                f"Task {task['task_id']!r} idempotency hash does not match its full contract."
            )
        lineage = task["lineage"]
        if lineage is not None and lineage["supersedes_plan_hash"] != plan["supersedes_plan_hash"]:
            raise AgentRuntimeError(
                f"Task {task['task_id']!r} lineage does not match the superseded plan."
            )
        if task["fallback_for_task"] is not None:
            if (
                lineage is None
                or lineage.get("primary_task") != task["fallback_for_task"]
                or task["failure_policy"] != "fail_closed"
                or task["fallback_agent"] is not None
            ):
                raise AgentRuntimeError(
                    f"Fallback task {task['task_id']!r} has incomplete fail-closed lineage."
                )
        for relative_path in [
            *task["instruction_hashes"],
            *task["platform_adapter_hashes"],
        ]:
            _contract_path(relative_path)
        unknown = sorted(set(task["depends_on"]) - set(by_id))
        if unknown:
            raise AgentRuntimeError(
                f"Task {task['task_id']!r} has unknown dependencies: {unknown}"
            )
        if any(by_id[item]["wave"] >= task["wave"] for item in task["depends_on"]):
            raise AgentRuntimeError(
                f"Task {task['task_id']!r} has a cyclic or non-prior-wave dependency."
            )

    wave_numbers = [wave["wave"] for wave in plan["waves"]]
    if wave_numbers != list(range(len(wave_numbers))):
        raise AgentRuntimeError("Activation plan waves must be contiguous and ordered from zero.")
    scheduled = [task_id for wave in plan["waves"] for task_id in wave["task_ids"]]
    if len(scheduled) != len(set(scheduled)) or set(scheduled) != set(task_ids):
        raise AgentRuntimeError("Every planned task must appear in exactly one execution wave.")
    for wave in plan["waves"]:
        if len(wave["task_ids"]) > plan["policy"]["max_parallel"]:
            raise AgentRuntimeError("An execution wave exceeds policy.max_parallel.")
        if any(by_id[task_id]["wave"] != wave["wave"] for task_id in wave["task_ids"]):
            raise AgentRuntimeError("Task wave metadata does not match the wave schedule.")
        if wave["parallel"] and len(wave["task_ids"]) < 2:
            raise AgentRuntimeError("A one-task execution wave cannot claim parallel execution.")

    phases = {phase: [task for task in tasks if task["phase"] == phase] for phase in {
        "route", "synthesize", "verify"
    }}
    if any(len(phases[phase]) != 1 for phase in phases):
        raise AgentRuntimeError("Activation plan needs exactly one route, synthesis, and verifier task.")
    route = phases["route"][0]
    synthesis = phases["synthesize"][0]
    verifier = phases["verify"][0]
    if not all(task["required"] for task in (route, synthesis, verifier)):
        raise AgentRuntimeError("Routing, synthesis, and independent verification are mandatory.")
    if any(
        task["external_side_effects"] != "forbidden"
        for task in (route, synthesis, verifier)
    ):
        raise AgentRuntimeError("Control and verification tasks cannot perform external actions.")
    if (
        route["wave"] != 0
        or route["depends_on"]
        or plan["waves"][0]["task_ids"] != [route["task_id"]]
        or verifier["wave"] != plan["waves"][-1]["wave"]
    ):
        raise AgentRuntimeError("Route must start the graph and independent verification must end it.")
    specialists = [task for task in tasks if task["phase"] == "specialist"]
    specialist_ids = {task["task_id"] for task in specialists}
    expected_synthesis_dependencies = specialist_ids or {route["task_id"]}
    if set(synthesis["depends_on"]) != expected_synthesis_dependencies:
        raise AgentRuntimeError("Synthesis must wait for every selected specialist exactly once.")
    if synthesis["agent_id"] != route["agent_id"] or verifier["agent_id"] == route["agent_id"]:
        raise AgentRuntimeError(
            "Routing and synthesis need one coordinator, plus a distinct independent verifier."
        )
    if any(
        task["wave"] <= route["wave"] or task["wave"] >= synthesis["wave"]
        for task in specialists
    ):
        raise AgentRuntimeError("Every specialist must run after routing and before synthesis.")

    def ancestors(task_id: str) -> set[str]:
        result: set[str] = set()
        pending = list(by_id[task_id]["depends_on"])
        while pending:
            dependency_id = pending.pop()
            if dependency_id in result:
                continue
            result.add(dependency_id)
            pending.extend(by_id[dependency_id]["depends_on"])
        return result

    if any(route["task_id"] not in ancestors(task["task_id"]) for task in tasks if task is not route):
        raise AgentRuntimeError("Every planned task must descend from the locked routing task.")

    selected = [item["agent_id"] for item in plan["selected_agents"]]
    rejected = [item["agent_id"] for item in plan["rejected_agents"]]
    if len(selected) != len(set(selected)) or len(rejected) != len(set(rejected)):
        raise AgentRuntimeError("Agent selection lists contain duplicate identities.")
    if set(selected) & set(rejected):
        raise AgentRuntimeError("An agent cannot be both selected and rejected.")
    if len(selected) > plan["policy"]["max_agents"]:
        raise AgentRuntimeError("Selected agent count exceeds policy.max_agents.")
    if any(task["agent_id"] not in selected for task in tasks):
        raise AgentRuntimeError("Activation plan schedules an agent that was not selected.")
    if set(selected) != {task["agent_id"] for task in tasks}:
        raise AgentRuntimeError("Every selected agent must own at least one planned task.")
    selection_required = {
        item["agent_id"]: item["required"] for item in plan["selected_agents"]
    }
    if any(task["required"] != selection_required[task["agent_id"]] for task in specialists):
        raise AgentRuntimeError("Specialist task criticality does not match agent selection.")
    specialist_agents = [task["agent_id"] for task in specialists]
    if len(specialist_agents) != len(set(specialist_agents)):
        raise AgentRuntimeError("A specialist agent may own only one task in an activation plan.")

    gates = plan["owner_gates"]
    gate_ids = [gate["gate_id"] for gate in gates]
    if len(gate_ids) != len(set(gate_ids)):
        raise AgentRuntimeError("Activation plan contains duplicate owner gates.")
    gate_by_id = {gate["gate_id"]: gate for gate in gates}
    approval_tasks = [
        task for task in tasks if task["external_side_effects"] == "approval_required"
    ]
    for task in tasks:
        if task in approval_tasks:
            if not task["approval_gate"] or task["approval_binding"] not in {
                "idempotency_key", "dependency_output_hash"
            }:
                raise AgentRuntimeError(
                    f"Approval task {task['task_id']!r} lacks an exact action binding."
                )
        elif task["approval_gate"] is not None or task["approval_binding"] is not None:
            raise AgentRuntimeError(
                f"Non-external task {task['task_id']!r} declares an owner gate."
            )
    for task in approval_tasks:
        if task["approval_gate"] not in gate_by_id:
            raise AgentRuntimeError(
                f"Approval task {task['task_id']!r} has no matching plan owner gate."
            )
    for gate in gates:
        binding = by_id.get(gate["binding_task_id"])
        if binding is None:
            raise AgentRuntimeError(f"Owner gate {gate['gate_id']!r} binds an unknown task.")
        matching = [task for task in approval_tasks if task["approval_gate"] == gate["gate_id"]]
        if len(matching) != 1:
            raise AgentRuntimeError(
                f"Owner gate {gate['gate_id']!r} needs exactly one approval task."
            )
        approval_task = matching[0]
        if gate["binding_source"] == "idempotency_key":
            if approval_task["task_id"] != binding["task_id"] or approval_task["approval_binding"] != "idempotency_key":
                raise AgentRuntimeError(
                    f"Owner gate {gate['gate_id']!r} has inconsistent task-action binding."
                )
        elif (
            approval_task["phase"] != "owner_gate"
            or approval_task["approval_binding"] != "dependency_output_hash"
            or binding["task_id"] != synthesis["task_id"]
            or approval_task["depends_on"] != [synthesis["task_id"]]
            or approval_task["agent_id"] != route["agent_id"]
            or not synthesis["wave"] < approval_task["wave"] < verifier["wave"]
        ):
            raise AgentRuntimeError(
                f"Owner gate {gate['gate_id']!r} has inconsistent output-hash binding."
            )

    owner_task_ids = {task["task_id"] for task in tasks if task["phase"] == "owner_gate"}
    if any(not by_id[task_id]["required"] for task_id in owner_task_ids):
        raise AgentRuntimeError("A deferred owner gate cannot be optional.")
    expected_verifier_dependencies = owner_task_ids or {synthesis["task_id"]}
    if set(verifier["depends_on"]) != expected_verifier_dependencies:
        raise AgentRuntimeError(
            "Independent verifier does not wait for synthesis and every deferred owner gate."
        )


def _write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


class TaskLedger:
    """Validated append-only state machine for one activation plan."""

    def __init__(self, path: str | Path, plan: dict[str, Any], data: dict[str, Any]):
        self.path = Path(path)
        self.plan = plan
        self.data = data
        self._tasks = {task["task_id"]: task for task in plan["tasks"]}

    @classmethod
    def create(cls, path: str | Path, plan: dict[str, Any]) -> "TaskLedger":
        validate_activation_plan(plan)
        path = Path(path)
        if path.exists():
            raise AgentRuntimeError(f"Execution ledger already exists: {path}")
        data: dict[str, Any] = {
            "version": "1.0",
            "request_id": plan["request_id"],
            "plan_hash": content_hash(plan),
            "registry_hash": plan["registry_hash"],
            "events": [],
            "head_hash": "0" * 64,
        }
        ledger = cls(path, plan, data)
        for task in plan["tasks"]:
            ledger._append_event(
                task,
                from_state=None,
                to_state="submitted",
                executor=None,
                output_hash=None,
                evidence=[],
                verdict=None,
                reason="Task submitted from activation plan.",
                approval=None,
            )
        ledger.verify()
        ledger.save()
        return ledger

    @classmethod
    def load(cls, path: str | Path, plan: dict[str, Any]) -> "TaskLedger":
        validate_activation_plan(plan)
        path = Path(path)
        if not path.is_file():
            raise AgentRuntimeError(f"Execution ledger not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        ledger = cls(path, plan, data)
        ledger.verify()
        return ledger

    def save(self) -> None:
        self.verify()
        _write_atomic(self.path, self.data)

    def _events_for(self, task_id: str) -> list[dict[str, Any]]:
        return [event for event in self.data["events"] if event["task_id"] == task_id]

    def state(self, task_id: str) -> str:
        if task_id not in self._tasks:
            raise AgentRuntimeError(f"Unknown task id: {task_id!r}")
        events = self._events_for(task_id)
        if not events:
            raise AgentRuntimeError(f"Task {task_id!r} has no submitted event.")
        return str(events[-1]["to_state"])

    def _last_executor(self, task_id: str) -> dict[str, Any] | None:
        for event in reversed(self._events_for(task_id)):
            if event["executor"] is not None:
                return dict(event["executor"])
        return None

    def _last_approval(self, task_id: str) -> dict[str, Any] | None:
        for event in reversed(self._events_for(task_id)):
            if event["approval"] is not None:
                return dict(event["approval"])
        return None

    def _dependency_receipts(self, task: dict[str, Any]) -> list[dict[str, str]]:
        receipts: list[dict[str, str]] = []
        for dependency_id in task["depends_on"]:
            event = next(
                (
                    item for item in reversed(self._events_for(dependency_id))
                    if item["to_state"] == "completed"
                ),
                None,
            )
            if event is None or event["output_hash"] is None:
                raise AgentRuntimeError(
                    f"Task {task['task_id']!r} has no completed receipt for {dependency_id!r}."
                )
            receipts.append({
                "task_id": dependency_id,
                "event_hash": event["event_hash"],
                "output_hash": event["output_hash"],
            })
        return receipts

    def _dependency_ready(self, dependency_id: str) -> bool:
        dependency = self._tasks[dependency_id]
        state = self.state(dependency_id)
        if dependency["required"]:
            return state == "completed"
        return state in TERMINAL_STATES

    def expected_approval_hash(self, task_id: str) -> str:
        """Return the exact action hash an approval receipt must authorize."""
        if task_id not in self._tasks:
            raise AgentRuntimeError(f"Unknown task id: {task_id!r}")
        task = self._tasks[task_id]
        binding = task["approval_binding"]
        if binding == "idempotency_key":
            return str(task["idempotency_key"])
        if binding == "dependency_output_hash":
            if len(task["depends_on"]) != 1:
                raise AgentRuntimeError(
                    f"Task {task_id!r} needs exactly one dependency for output-hash approval."
                )
            dependency_id = task["depends_on"][0]
            event = next(
                (
                    item for item in reversed(self._events_for(dependency_id))
                    if item["to_state"] == "completed"
                ),
                None,
            )
            if event is None or event["output_hash"] is None:
                raise AgentRuntimeError(
                    f"Task {task_id!r} cannot be approved before {dependency_id!r} completes."
                )
            return str(event["output_hash"])
        raise AgentRuntimeError(f"Task {task_id!r} has no approval binding.")

    def transition(
        self,
        task_id: str,
        to_state: str,
        *,
        executor: dict[str, Any] | None = None,
        output_hash: str | None = None,
        evidence: Iterable[str] = (),
        verdict: str | None = None,
        reason: str = "",
        approval: dict[str, Any] | None = None,
        save: bool = True,
    ) -> dict[str, Any]:
        if task_id not in self._tasks:
            raise AgentRuntimeError(f"Unknown task id: {task_id!r}")
        task = self._tasks[task_id]
        current = self.state(task_id)
        if to_state not in ALLOWED_TRANSITIONS.get(current, frozenset()):
            raise AgentRuntimeError(
                f"Illegal task transition for {task_id!r}: {current!r} -> {to_state!r}."
            )
        if task["required"] and to_state in {"cancelled", "rejected"}:
            raise AgentRuntimeError(f"Required task {task_id!r} cannot be {to_state}.")
        if to_state == "failed" and not reason.strip():
            raise AgentRuntimeError(f"Failed task {task_id!r} needs a concrete reason.")

        if to_state == "approval_required":
            if task["external_side_effects"] != "approval_required":
                raise AgentRuntimeError(
                    f"Task {task_id!r} has no planned owner gate and cannot request approval."
                )
            unmet = [
                dependency for dependency in task["depends_on"]
                if not self._dependency_ready(dependency)
            ]
            if unmet:
                raise AgentRuntimeError(
                    f"Task {task_id!r} cannot request approval before dependencies finish: {unmet}"
                )

        effective_approval = approval
        if to_state == "working":
            unmet = [
                dependency for dependency in task["depends_on"]
                if not self._dependency_ready(dependency)
            ]
            if unmet:
                raise AgentRuntimeError(
                    f"Task {task_id!r} cannot start before dependencies finish: {unmet}"
                )
            if task["external_side_effects"] == "approval_required":
                if current not in {"approval_required", "input_required"}:
                    raise AgentRuntimeError(
                        f"Task {task_id!r} requires approval_required before working."
                    )
                if current == "input_required" and effective_approval is None:
                    effective_approval = self._last_approval(task_id)
                if not effective_approval:
                    raise AgentRuntimeError(f"Task {task_id!r} requires an exact approval receipt.")
                if effective_approval.get("gate_id") != task["approval_gate"]:
                    raise AgentRuntimeError(f"Task {task_id!r} approval gate does not match the plan.")
                if effective_approval.get("action_hash") != self.expected_approval_hash(task_id):
                    raise AgentRuntimeError(
                        f"Task {task_id!r} approval is stale or bound to another action."
                    )
            elif approval is not None:
                raise AgentRuntimeError(
                    f"Task {task_id!r} cannot record an unplanned approval receipt."
                )

        effective_executor = executor or self._last_executor(task_id)
        if to_state in {"working", "completed"}:
            if effective_executor is None:
                raise AgentRuntimeError(f"Task {task_id!r} needs an executor receipt.")
            _validate_executor_receipt(task, effective_executor)
            _verify_contract_files(task, str(effective_executor["type"]))
        evidence_list = list(dict.fromkeys(item for item in evidence if item))
        if to_state == "completed":
            if not output_hash:
                raise AgentRuntimeError(f"Completed task {task_id!r} needs an output hash.")
            if not evidence_list:
                raise AgentRuntimeError(f"Completed task {task_id!r} needs evidence.")
            if task["phase"] == "verify" and verdict not in {"pass", "revise", "reject"}:
                raise AgentRuntimeError(
                    f"Independent verifier task {task_id!r} requires pass, revise, or reject."
                )
            if task["phase"] != "verify":
                if verdict not in {None, "pass"}:
                    raise AgentRuntimeError(
                        f"Only the independent verifier may return {verdict!r}."
                    )
                verdict = "pass"
            if task["phase"] == "owner_gate":
                expected_hash = self.expected_approval_hash(task_id)
                if output_hash != expected_hash:
                    raise AgentRuntimeError(
                        f"Owner gate task {task_id!r} output must equal the approved action hash."
                    )
            if task["phase"] == "verify":
                producer_runs = {
                    event["executor"]["run_id"]
                    for event in self.data["events"]
                    if event["to_state"] == "completed"
                    and self._tasks[event["task_id"]]["phase"] in {"specialist", "synthesize"}
                    and event["executor"] is not None
                }
                if effective_executor.get("run_id") in producer_runs:
                    raise AgentRuntimeError(
                        "Independent verifier run_id matches a producer or synthesizer run."
                    )

        previous_head = self.data["head_hash"]
        event = self._append_event(
            task,
            from_state=current,
            to_state=to_state,
            executor=effective_executor if to_state in {"working", "completed"} else executor,
            output_hash=output_hash,
            evidence=evidence_list,
            verdict=verdict,
            reason=reason,
            approval=effective_approval,
        )
        try:
            self.verify()
        except Exception:
            self.data["events"].pop()
            self.data["head_hash"] = previous_head
            raise
        if save:
            self.save()
        return event

    def _append_event(
        self,
        task: dict[str, Any],
        *,
        from_state: str | None,
        to_state: str,
        executor: dict[str, Any] | None,
        output_hash: str | None,
        evidence: list[str],
        verdict: str | None,
        reason: str,
        approval: dict[str, Any] | None,
    ) -> dict[str, Any]:
        sequence = len(self.data["events"])
        previous = self.data["events"][-1]["event_hash"] if self.data["events"] else None
        event = {
            "event_id": f"evt-{sequence:06d}",
            "task_id": task["task_id"],
            "agent_id": task["agent_id"],
            "sequence": sequence,
            "attempt": 1,
            "from_state": from_state,
            "to_state": to_state,
            "input_hash": task["input_hash"],
            "output_hash": output_hash,
            "executor": executor,
            "evidence": evidence,
            "dependency_receipts": (
                self._dependency_receipts(task) if to_state == "completed" else []
            ),
            "verdict": verdict,
            "reason": reason,
            "approval": approval,
            "previous_event_hash": previous,
            "event_hash": "",
        }
        event["event_hash"] = content_hash({key: value for key, value in event.items() if key != "event_hash"})
        self.data["events"].append(event)
        self.data["head_hash"] = event["event_hash"]
        return event

    def verify(self) -> None:
        validate_activation_plan(self.plan)
        _validate_schema(self.data, LEDGER_SCHEMA, "execution ledger")
        if self.data["request_id"] != self.plan["request_id"]:
            raise AgentRuntimeError("Execution ledger request_id does not match activation plan.")
        if self.data["plan_hash"] != content_hash(self.plan):
            raise AgentRuntimeError("Execution ledger activation plan hash mismatch.")
        if self.data["registry_hash"] != self.plan["registry_hash"]:
            raise AgentRuntimeError("Execution ledger registry hash mismatch.")

        states: dict[str, str | None] = {task_id: None for task_id in self._tasks}
        for task in self._tasks.values():
            if task["external_side_effects"] == "approval_required":
                if not task["approval_gate"] or task["approval_binding"] not in {
                    "idempotency_key", "dependency_output_hash"
                }:
                    raise AgentRuntimeError(
                        f"Approval-required task {task['task_id']!r} lacks an exact binding."
                    )
            elif task["approval_gate"] is not None or task["approval_binding"] is not None:
                raise AgentRuntimeError(
                    f"Non-external task {task['task_id']!r} declares an approval gate."
                )
        terminal: set[str] = set()
        completed_sequence: dict[str, int] = {}
        completed_receipts: dict[str, dict[str, str]] = {}
        previous_hash: str | None = None
        seen_events: set[str] = set()
        for index, event in enumerate(self.data["events"]):
            if event["sequence"] != index or event["event_id"] in seen_events:
                raise AgentRuntimeError("Execution ledger event order or identity is invalid.")
            seen_events.add(event["event_id"])
            if event["previous_event_hash"] != previous_hash:
                raise AgentRuntimeError("Execution ledger hash chain is broken.")
            expected_hash = content_hash({
                key: value for key, value in event.items() if key != "event_hash"
            })
            if event["event_hash"] != expected_hash:
                raise AgentRuntimeError("Execution ledger event was modified after recording.")
            previous_hash = event["event_hash"]

            task = self._tasks.get(event["task_id"])
            if task is None:
                raise AgentRuntimeError(f"Ledger contains unplanned task {event['task_id']!r}.")
            if event["agent_id"] != task["agent_id"] or event["input_hash"] != task["input_hash"]:
                raise AgentRuntimeError("Ledger agent or input hash does not match the plan.")
            if event["executor"] is not None:
                _validate_executor_receipt(task, event["executor"])
            current = states[event["task_id"]]
            if event["task_id"] in terminal:
                raise AgentRuntimeError(f"Terminal task {event['task_id']!r} was mutated.")
            if event["from_state"] != current:
                raise AgentRuntimeError(f"Ledger from_state mismatch for {event['task_id']!r}.")
            if event["to_state"] not in ALLOWED_TRANSITIONS.get(current, frozenset()):
                raise AgentRuntimeError(f"Illegal recorded transition for {event['task_id']!r}.")
            if task["required"] and event["to_state"] in {"cancelled", "rejected"}:
                raise AgentRuntimeError(
                    f"Required task {event['task_id']!r} cannot be {event['to_state']}."
                )
            if event["to_state"] == "failed" and not event["reason"].strip():
                raise AgentRuntimeError(
                    f"Failed task {event['task_id']!r} has no concrete reason."
                )
            if event["to_state"] == "approval_required":
                if task["external_side_effects"] != "approval_required":
                    raise AgentRuntimeError(
                        f"Task {event['task_id']!r} recorded an unplanned owner gate."
                    )
                for dependency_id in task["depends_on"]:
                    dependency = self._tasks[dependency_id]
                    dependency_state = states[dependency_id]
                    ready = (
                        dependency_state == "completed"
                        if dependency["required"]
                        else dependency_state in TERMINAL_STATES
                    )
                    if not ready:
                        raise AgentRuntimeError(
                            f"Task {event['task_id']!r} requested approval before "
                            f"{dependency_id!r} completed."
                        )
            if event["to_state"] == "working":
                if event["executor"] is None:
                    raise AgentRuntimeError(
                        f"Task {event['task_id']!r} entered working without an executor."
                    )
                for dependency_id in task["depends_on"]:
                    dependency = self._tasks[dependency_id]
                    dependency_state = states[dependency_id]
                    ready = (
                        dependency_state == "completed"
                        if dependency["required"]
                        else dependency_state in TERMINAL_STATES
                    )
                    if not ready:
                        raise AgentRuntimeError(
                            f"Task {event['task_id']!r} started before {dependency_id!r}."
                        )
                if task["external_side_effects"] == "approval_required":
                    approval = event["approval"]
                    if current not in {"approval_required", "input_required"} or approval is None:
                        raise AgentRuntimeError(
                            f"Task {event['task_id']!r} started without its approval pause."
                        )
                    if approval.get("gate_id") != task["approval_gate"]:
                        raise AgentRuntimeError(
                            f"Task {event['task_id']!r} approval gate does not match the plan."
                        )
                    expected_action_hash = task["idempotency_key"]
                    if task["approval_binding"] == "dependency_output_hash":
                        if len(task["depends_on"]) != 1:
                            raise AgentRuntimeError(
                                f"Task {event['task_id']!r} has ambiguous approval dependencies."
                            )
                        dependency_id = task["depends_on"][0]
                        dependency_receipt = completed_receipts.get(dependency_id)
                        if dependency_receipt is None:
                            raise AgentRuntimeError(
                                f"Task {event['task_id']!r} approval precedes its bound output."
                            )
                        expected_action_hash = dependency_receipt["output_hash"]
                    if approval.get("action_hash") != expected_action_hash:
                        raise AgentRuntimeError(
                            f"Task {event['task_id']!r} approval is bound to another action."
                        )
                elif event["approval"] is not None:
                    raise AgentRuntimeError(
                        f"Task {event['task_id']!r} recorded an unplanned approval receipt."
                    )
            elif event["approval"] is not None:
                raise AgentRuntimeError("Approval receipts belong only to approved working events.")
            if event["to_state"] == "completed":
                if event["executor"] is None or not event["output_hash"] or not event["evidence"]:
                    raise AgentRuntimeError("Completed task lacks executor, output hash, or evidence.")
                if task["phase"] == "verify":
                    if event["verdict"] not in {"pass", "revise", "reject"}:
                        raise AgentRuntimeError(
                            f"Independent verifier task {event['task_id']!r} has no verdict."
                        )
                    producer_runs = {
                        prior["executor"]["run_id"]
                        for prior in self.data["events"][:index]
                        if prior["to_state"] == "completed"
                        and self._tasks[prior["task_id"]]["phase"] in {"specialist", "synthesize"}
                        and prior["executor"] is not None
                    }
                    if event["executor"].get("run_id") in producer_runs:
                        raise AgentRuntimeError(
                            "Independent verifier run_id matches a producer or synthesizer run."
                        )
                if task["phase"] == "owner_gate":
                    expected_hash = completed_receipts[task["depends_on"][0]]["output_hash"]
                    if event["output_hash"] != expected_hash:
                        raise AgentRuntimeError(
                            f"Owner gate task {event['task_id']!r} does not preserve the approved hash."
                        )
                if task["phase"] != "verify" and event["verdict"] != "pass":
                    raise AgentRuntimeError(
                        "Only the independent verifier may record revise or reject."
                    )
                expected_dependencies = [completed_receipts[item] for item in task["depends_on"]]
                if event["dependency_receipts"] != expected_dependencies:
                    raise AgentRuntimeError(
                        f"Completed task {event['task_id']!r} is not bound to its exact "
                        "dependency receipts."
                    )
                completed_sequence[event["task_id"]] = index
                completed_receipts[event["task_id"]] = {
                    "task_id": event["task_id"],
                    "event_hash": event["event_hash"],
                    "output_hash": event["output_hash"],
                }
            elif event["verdict"] is not None:
                raise AgentRuntimeError("Only completed task events may carry a verdict.")
            states[event["task_id"]] = event["to_state"]
            if event["to_state"] in TERMINAL_STATES:
                terminal.add(event["task_id"])

        if set(states) != {event["task_id"] for event in self.data["events"]}:
            raise AgentRuntimeError("Every planned task must have a submitted ledger event.")
        if self.data["head_hash"] != previous_hash:
            raise AgentRuntimeError("Execution ledger head hash is stale.")

    def completion_report(self) -> dict[str, Any]:
        self.verify()
        states = {task_id: self.state(task_id) for task_id in self._tasks}
        required_incomplete = sorted(
            task_id for task_id, task in self._tasks.items()
            if task["required"] and states[task_id] != "completed"
        )
        approval_waiting = sorted(
            task_id for task_id, state in states.items() if state == "approval_required"
        )
        fail_closed = sorted(
            task_id for task_id, task in self._tasks.items()
            if task["failure_policy"] == "fail_closed" and states[task_id] == "failed"
        )
        fallback_required = sorted(
            task_id for task_id, task in self._tasks.items()
            if task["required"]
            and task["failure_policy"] == "fallback"
            and states[task_id] == "failed"
        )
        completed_verdicts = {
            event["task_id"]: event["verdict"]
            for event in self.data["events"]
            if event["to_state"] == "completed"
            and self._tasks[event["task_id"]]["phase"] == "verify"
        }
        revise_required = sorted(
            task_id for task_id, verdict in completed_verdicts.items() if verdict == "revise"
        )
        rejected_results = sorted(
            task_id for task_id, verdict in completed_verdicts.items() if verdict == "reject"
        )
        if approval_waiting:
            status = "owner_required"
        elif fail_closed:
            status = "failed"
        elif rejected_results:
            status = "failed"
        elif revise_required:
            status = "revision_required"
        elif fallback_required:
            status = "fallback_required"
        elif required_incomplete:
            status = "running"
        else:
            status = "complete"
        return {
            "status": status,
            "states": states,
            "required_incomplete": required_incomplete,
            "approval_waiting": approval_waiting,
            "fail_closed": fail_closed,
            "fallback_required": fallback_required,
            "revise_required": revise_required,
            "rejected_results": rejected_results,
            "head_hash": self.data["head_hash"],
        }


__all__ = [
    "ALLOWED_TRANSITIONS",
    "AgentRuntimeError",
    "TERMINAL_STATES",
    "TaskLedger",
    "validate_activation_plan",
]
