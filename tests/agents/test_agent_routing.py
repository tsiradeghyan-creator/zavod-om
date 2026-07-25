from __future__ import annotations

import pytest

from lib.agent_registry import AgentRegistry, file_hash
from lib.agent_router import build_agent_request, route_agents

from .conftest import plan_for, task_for


CONTROL_AGENTS = {"executive-producer", "quality-auditor"}


def selected_ids(plan: dict) -> set[str]:
    return {item["agent_id"] for item in plan["selected_agents"]}


@pytest.mark.parametrize(
    ("request_id", "text", "expected"),
    [
        ("minimal", "Ասա մեկ պարզ պատասխան։", CONTROL_AGENTS),
        (
            "research",
            "Ստուգիր այս փաստը վերջին պաշտոնական աղբյուրներով։",
            CONTROL_AGENTS | {"research-accuracy"},
        ),
        (
            "rights",
            "Ստուգիր իրավունքներն ու լիցենզիան։",
            CONTROL_AGENTS | {"rights-provenance"},
        ),
        (
            "publish",
            "Հրապարակիր արդեն հաստատված նյութը։",
            CONTROL_AGENTS | {"rights-provenance", "distribution-growth"},
        ),
        (
            "system",
            "Կատարիր գործակալ համակարգի ճարտարապետական թեստ և աուդիտ։",
            CONTROL_AGENTS | {"system-architect"},
        ),
    ],
)
def test_exact_agent_set_is_routed(
    registry: AgentRegistry,
    request_id: str,
    text: str,
    expected: set[str],
) -> None:
    plan = plan_for(registry, text, request_id=f"routing-{request_id}")

    assert plan["routing_status"] == "ready"
    assert plan["unmatched_capabilities"] == []
    assert selected_ids(plan) == expected
    assert {task["agent_id"] for task in plan["tasks"]} == expected


@pytest.mark.parametrize(
    "visual_exclusion",
    ["Գույները հետաքրքիր չեն։", "Տեսողականը կարևոր չէ։"],
)
def test_strict_armenian_screenplay_activates_voice_but_not_visuals(
    registry: AgentRegistry,
    visual_exclusion: str,
) -> None:
    plan = plan_for(
        registry,
        "Գրիր Մաղակյանի հայկական սցենարային ձեռագրով երկխոսություն։ "
        + visual_exclusion,
        request_id=f"strict-screenplay-{len(visual_exclusion)}",
    )

    assert plan["routing_status"] == "ready"
    assert plan["unmatched_capabilities"] == []
    assert selected_ids(plan) == CONTROL_AGENTS | {
        "authorial-voice-guardian",
        "story-architect",
        "scriptwriter",
    }
    for irrelevant in {
        "visual-director",
        "media-producer",
        "rights-provenance",
        "distribution-growth",
        "localization-director",
        "system-architect",
        "research-accuracy",
        "resilience-generalist",
    }:
        assert irrelevant not in {task["agent_id"] for task in plan["tasks"]}
        rejection = next(
            item for item in plan["rejected_agents"] if item["agent_id"] == irrelevant
        )
        assert rejection["required"] is False


@pytest.mark.parametrize(
    ("risk", "required_capability", "agent_id"),
    [
        ("factual_claims", "factual_accuracy", "research-accuracy"),
        ("rights", "rights_clearance", "rights-provenance"),
        ("publication", "publishing", "distribution-growth"),
    ],
)
def test_high_risk_signals_force_the_mandatory_specialist(
    registry: AgentRegistry,
    risk: str,
    required_capability: str,
    agent_id: str,
) -> None:
    request = build_agent_request(
        "Կատարիր պարտադիր վերահսկվող ստուգումը։",
        request_id=f"hard-trigger-{risk}",
        risks=[risk],
        required_capabilities=[required_capability],
    )
    plan = route_agents(request, registry=registry)

    selection = next(item for item in plan["selected_agents"] if item["agent_id"] == agent_id)
    assert selection["required"] is True
    assert task_for(plan, agent_id=agent_id)["failure_policy"] == "fail_closed"


def test_publication_trigger_carries_exact_owner_gate(registry: AgentRegistry) -> None:
    plan = plan_for(
        registry,
        "Հրապարակիր արդեն հաստատված նյութը։",
        request_id="publication-gate",
    )
    distribution = task_for(plan, agent_id="distribution-growth")
    owner_gate = task_for(plan, phase="owner_gate")
    synthesis = task_for(plan, phase="synthesize")

    assert distribution["external_side_effects"] == "forbidden"
    assert distribution["approval_gate"] is None
    assert owner_gate["external_side_effects"] == "approval_required"
    assert owner_gate["approval_gate"] == "publication"
    assert owner_gate["approval_binding"] == "dependency_output_hash"
    assert owner_gate["depends_on"] == [synthesis["task_id"]]
    assert {gate["gate_id"] for gate in plan["owner_gates"]} == {"publication"}
    assert all(gate["action_hash_required"] is True for gate in plan["owner_gates"])
    assert plan["owner_gates"][0]["binding_task_id"] == synthesis["task_id"]
    assert plan["owner_gates"][0]["binding_source"] == "output_hash"


def test_unknown_capability_blocks_instead_of_guessing(registry: AgentRegistry) -> None:
    request = build_agent_request(
        "Կատարիր փակ հատուկ կարողությունը։",
        request_id="unknown-capability",
        required_capabilities=["capability-that-does-not-exist"],
    )
    plan = route_agents(request, registry=registry)

    assert plan["routing_status"] == "blocked"
    assert plan["unmatched_capabilities"] == ["capability-that-does-not-exist"]
    assert selected_ids(plan) == CONTROL_AGENTS
    assert all(task["phase"] != "specialist" for task in plan["tasks"])


def test_world_best_agent_system_request_routes_architecture_and_benchmark(
    registry: AgentRegistry,
) -> None:
    plan = plan_for(
        registry,
        "Ուզում եմ, որ գործակալները հարցին առնչվելիս սկսեն աշխատել, իսկ համակարգը "
        "աշխարհում իր հավասարը չունենա և լինի ամենալավը։",
        request_id="owner-agent-system-request",
    )

    assert plan["routing_status"] == "ready"
    assert selected_ids(plan) == CONTROL_AGENTS | {
        "system-architect",
        "research-accuracy",
    }


def test_dependency_waves_are_parallel_then_synthesize_then_verify(
    registry: AgentRegistry,
) -> None:
    plan = plan_for(
        registry,
        "Գրիր Մաղակյանի հայկական սցենարային ձեռագրով երկխոսություն։ Գույները հետաքրքիր չեն։",
        request_id="dependency-waves",
    )
    tasks = {task["task_id"]: task for task in plan["tasks"]}
    route = task_for(plan, phase="route")
    voice = task_for(plan, agent_id="authorial-voice-guardian")
    story = task_for(plan, agent_id="story-architect")
    script = task_for(plan, agent_id="scriptwriter")
    synth = task_for(plan, phase="synthesize")
    verify = task_for(plan, phase="verify")

    assert voice["depends_on"] == [route["task_id"]]
    assert story["depends_on"] == [route["task_id"]]
    assert voice["wave"] == story["wave"]
    parallel_wave = next(wave for wave in plan["waves"] if wave["wave"] == voice["wave"])
    assert parallel_wave == {
        "wave": voice["wave"],
        "task_ids": [voice["task_id"], story["task_id"]],
        "parallel": True,
    }
    assert set(script["depends_on"]) == {voice["task_id"], story["task_id"]}
    assert synth["depends_on"] == [voice["task_id"], story["task_id"], script["task_id"]]
    assert verify["depends_on"] == [synth["task_id"]]
    assert tasks[plan["waves"][-1]["task_ids"][0]]["phase"] == "verify"


def test_every_task_is_bound_to_registry_and_instruction_hashes(
    registry: AgentRegistry,
) -> None:
    plan = plan_for(
        registry,
        "Կատարիր գործակալ համակարգի ճարտարապետական թեստ և աուդիտ։",
        request_id="task-provenance",
    )

    assert plan["registry_hash"] == registry.registry_hash
    for task in plan["tasks"]:
        assert task["input_hash"] == plan["request_hash"]
        assert task["instruction_hashes"] == registry.instruction_hashes(task["agent_id"])
        assert task["platform_adapter_hashes"] == registry.platform_adapter_hashes(
            task["agent_id"]
        )
        for relative_path, digest in task["instruction_hashes"].items():
            assert file_hash(registry.path.parent.parent / relative_path) == digest
        for relative_path, digest in task["platform_adapter_hashes"].items():
            assert file_hash(registry.path.parent.parent / relative_path) == digest


def test_fallback_only_agent_is_never_proactively_routed(registry: AgentRegistry) -> None:
    assert registry.get("resilience-generalist")["activation_mode"] == "fallback_only"
    requests = [
        "Գրիր ամբողջական հայկական սցենար։",
        "Ստեղծիր և մոնտաժիր կարճ տեսանյութ։",
        "Կառուցիր պատմության ամբողջական կառուցվածքը։",
    ]
    for index, text in enumerate(requests):
        plan = plan_for(registry, text, request_id=f"no-proactive-fallback-{index}")
        assert "resilience-generalist" not in selected_ids(plan)
        assert all(task["agent_id"] != "resilience-generalist" for task in plan["tasks"])
