from __future__ import annotations

import copy

import pytest

from lib.agent_registry import AgentRegistry, content_hash
from lib.agent_router import AgentRoutingError, build_agent_request, replan_with_fallback, route_agents

from .conftest import task_for


FALLBACK_CASES = [
    ("story-architect", "story_structure"),
    ("scriptwriter", "screenwriting"),
    ("visual-director", "visual_language"),
    ("media-producer", "video_generation"),
]


def capability_plan(
    registry: AgentRegistry,
    agent_id: str,
    capability: str,
) -> dict:
    request = build_agent_request(
        "Կատարիր ճշգրիտ սահմանված մասնագիտական առաջադրանքը։",
        request_id=f"fallback-{agent_id}",
        required_capabilities=[capability],
    )
    plan = route_agents(request, registry=registry)
    assert task_for(plan, agent_id=agent_id)
    return plan


@pytest.mark.parametrize(("agent_id", "capability"), FALLBACK_CASES)
def test_allowlisted_fallback_preserves_the_exact_task_contract(
    registry: AgentRegistry,
    agent_id: str,
    capability: str,
) -> None:
    plan = capability_plan(registry, agent_id, capability)
    original = copy.deepcopy(plan)
    primary = task_for(plan, agent_id=agent_id)

    replacement_plan = replan_with_fallback(plan, primary["task_id"], registry=registry)
    replacement = next(
        task for task in replacement_plan["tasks"] if task["fallback_for_task"] == primary["task_id"]
    )

    assert plan == original
    assert replacement_plan["supersedes_plan_hash"] == content_hash(plan)
    assert replacement["agent_id"] == primary["fallback_agent"] == "resilience-generalist"
    assert replacement["input_hash"] == primary["input_hash"]
    assert replacement["input_artifacts"] == primary["input_artifacts"]
    assert replacement["output_artifact"] == primary["output_artifact"]
    assert set(replacement["allowed_tools"]) == set(primary["allowed_tools"])
    assert replacement["external_side_effects"] == primary["external_side_effects"]
    assert replacement["approval_gate"] == primary["approval_gate"]
    assert replacement["required"] == primary["required"]
    assert replacement["evidence_required"] == primary["evidence_required"]
    assert replacement["stop_conditions"] == primary["stop_conditions"]
    assert replacement["failure_policy"] == "fail_closed"
    assert replacement["fallback_agent"] is None
    assert primary["task_id"] not in {task["task_id"] for task in replacement_plan["tasks"]}
    assert all(
        primary["task_id"] not in task["depends_on"]
        for task in replacement_plan["tasks"]
    )


@pytest.mark.parametrize(
    ("agent_id", "capability"),
    [
        ("authorial-voice-guardian", "maghakian_script_dna"),
        ("research-accuracy", "factual_accuracy"),
        ("rights-provenance", "rights_clearance"),
        ("distribution-growth", "publishing"),
        ("system-architect", "system_architecture"),
    ],
)
def test_critical_specialists_never_fall_back(
    registry: AgentRegistry,
    agent_id: str,
    capability: str,
) -> None:
    request = build_agent_request(
        "Կատարիր պարտադիր մասնագիտական ստուգումը։",
        request_id=f"critical-{agent_id}",
        required_capabilities=[capability],
    )
    plan = route_agents(request, registry=registry)
    critical = task_for(plan, agent_id=agent_id)

    assert critical["failure_policy"] == "fail_closed"
    assert critical["fallback_agent"] is None
    with pytest.raises(AgentRoutingError, match="not fallback-eligible"):
        replan_with_fallback(plan, critical["task_id"], registry=registry)


@pytest.mark.parametrize("phase", ["route", "synthesize", "verify"])
def test_control_tasks_cannot_fall_back(registry: AgentRegistry, phase: str) -> None:
    request = build_agent_request("Ասա մեկ պարզ պատասխան։", request_id=f"control-{phase}")
    plan = route_agents(request, registry=registry)
    control = task_for(plan, phase=phase)

    with pytest.raises(AgentRoutingError, match="cannot fall back"):
        replan_with_fallback(plan, control["task_id"], registry=registry)


def test_fallback_refuses_a_stale_registry_hash(registry: AgentRegistry) -> None:
    plan = capability_plan(registry, "scriptwriter", "screenwriting")
    plan["registry_hash"] = "0" * 64
    primary = task_for(plan, agent_id="scriptwriter")

    with pytest.raises(AgentRoutingError, match="registry hash is stale"):
        replan_with_fallback(plan, primary["task_id"], registry=registry)


def test_every_declared_fallback_target_is_fallback_only(registry: AgentRegistry) -> None:
    for card in registry.cards():
        fallback_id = card["fallback_agent"]
        if fallback_id is None:
            continue
        fallback = registry.get(fallback_id)
        assert fallback["activation_mode"] == "fallback_only"
        assert fallback["failure_policy"] == "fail_closed"
