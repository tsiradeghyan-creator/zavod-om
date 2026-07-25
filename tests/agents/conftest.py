from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from lib.agent_registry import AgentRegistry, content_hash, load_agent_registry
from lib.agent_router import build_agent_request, route_agents
from lib.agent_runtime import TaskLedger


@pytest.fixture(scope="session")
def registry() -> AgentRegistry:
    """Load the real registry, including every declared platform adapter."""
    return load_agent_registry()


def plan_for(
    registry: AgentRegistry,
    text: str,
    *,
    request_id: str,
    **request_overrides: Any,
) -> dict[str, Any]:
    request = build_agent_request(
        text,
        request_id=request_id,
        **request_overrides,
    )
    return route_agents(request, registry=registry)


def task_for(plan: dict[str, Any], *, agent_id: str | None = None, phase: str | None = None) -> dict[str, Any]:
    matches = [
        task
        for task in plan["tasks"]
        if (agent_id is None or task["agent_id"] == agent_id)
        and (phase is None or task["phase"] == phase)
    ]
    assert len(matches) == 1, (agent_id, phase, matches)
    return matches[0]


def executor_for(
    task: dict[str, Any],
    *,
    run_id: str | None = None,
    executor_type: str = "api_agent",
) -> dict[str, str]:
    return {
        "type": executor_type,
        "run_id": run_id or f"run:{task['task_id']}",
        "model": "deterministic-test-double",
        "prompt_version": task["prompt_version"],
    }


def approval_for(task: dict[str, Any], *, action_hash: str | None = None) -> dict[str, str]:
    return {
        "gate_id": task["approval_gate"],
        "action_hash": action_hash or task["idempotency_key"],
        "approver": "owner-test-fixture",
        "approved_at": "2026-07-13T00:00:00+00:00",
        "identity_provider": "signed-test-identity",
        "identity_proof_hash": content_hash({"owner": "owner-test-fixture"}),
    }


def complete_task(
    ledger: TaskLedger,
    task: dict[str, Any],
    *,
    run_id: str | None = None,
    executor_type: str = "api_agent",
) -> None:
    if task["phase"] == "owner_gate" and executor_type == "api_agent":
        executor_type = "owner_approval"
    executor = executor_for(task, run_id=run_id, executor_type=executor_type)
    if task["external_side_effects"] == "approval_required":
        action_hash = ledger.expected_approval_hash(task["task_id"])
        ledger.transition(
            task["task_id"],
            "approval_required",
            reason="Exact owner approval is required before the external action.",
        )
        ledger.transition(
            task["task_id"],
            "working",
            executor=executor,
            approval=approval_for(task, action_hash=action_hash),
            reason="Owner approval matches the planned action hash.",
        )
    else:
        ledger.transition(
            task["task_id"],
            "working",
            executor=executor,
            reason="Dependencies are complete; deterministic test execution begins.",
        )
    output_hash = (
        ledger.expected_approval_hash(task["task_id"])
        if task["phase"] == "owner_gate"
        else content_hash({"task_id": task["task_id"], "fixture": "output"})
    )
    ledger.transition(
        task["task_id"],
        "completed",
        output_hash=output_hash,
        evidence=[f"evidence:{task['task_id']}"],
        verdict="pass" if task["phase"] == "verify" else None,
        reason="The test double returned a hash-bound contribution.",
    )


def tasks_in_wave_order(plan: dict[str, Any]) -> Iterator[dict[str, Any]]:
    tasks = {task["task_id"]: task for task in plan["tasks"]}
    for wave in sorted(plan["waves"], key=lambda item: item["wave"]):
        for task_id in wave["task_ids"]:
            yield tasks[task_id]


def complete_plan(ledger: TaskLedger, plan: dict[str, Any]) -> None:
    for task in tasks_in_wave_order(plan):
        complete_task(ledger, task)
