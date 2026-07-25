from __future__ import annotations

import copy
import json

import pytest

from lib.agent_registry import AgentRegistry, content_hash, task_contract_hash
from lib.agent_runtime import AgentRuntimeError, TaskLedger

from .conftest import (
    approval_for,
    complete_plan,
    complete_task,
    executor_for,
    plan_for,
    task_for,
)


def strict_plan(registry: AgentRegistry, *, request_id: str) -> dict:
    return plan_for(
        registry,
        "Գրիր Մաղակյանի հայկական սցենարային ձեռագրով երկխոսություն։ Գույները հետաքրքիր չեն։",
        request_id=request_id,
    )


def test_ledger_submission_order_and_hash_chain_match_the_plan(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = strict_plan(registry, request_id="ledger-order")
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)

    assert [event["task_id"] for event in ledger.data["events"]] == [
        task["task_id"] for task in plan["tasks"]
    ]
    previous = None
    for sequence, event in enumerate(ledger.data["events"]):
        assert event["sequence"] == sequence
        assert event["previous_event_hash"] == previous
        assert event["event_hash"] == content_hash(
            {key: value for key, value in event.items() if key != "event_hash"}
        )
        previous = event["event_hash"]
    assert ledger.data["head_hash"] == previous


def test_dependency_wave_blocks_early_start_and_allows_parallel_peers(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = strict_plan(registry, request_id="runtime-waves")
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)
    route = task_for(plan, phase="route")
    voice = task_for(plan, agent_id="authorial-voice-guardian")
    story = task_for(plan, agent_id="story-architect")
    script = task_for(plan, agent_id="scriptwriter")

    with pytest.raises(AgentRuntimeError, match="dependencies finish"):
        ledger.transition(voice["task_id"], "working", executor=executor_for(voice))

    complete_task(ledger, route)
    ledger.transition(voice["task_id"], "working", executor=executor_for(voice))
    ledger.transition(story["task_id"], "working", executor=executor_for(story))
    assert ledger.state(voice["task_id"]) == "working"
    assert ledger.state(story["task_id"]) == "working"

    with pytest.raises(AgentRuntimeError, match="dependencies finish"):
        ledger.transition(script["task_id"], "working", executor=executor_for(script))


def test_terminal_task_is_immutable(registry: AgentRegistry, tmp_path) -> None:
    plan = strict_plan(registry, request_id="terminal-immutable")
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)
    route = task_for(plan, phase="route")
    complete_task(ledger, route)

    with pytest.raises(AgentRuntimeError, match="Illegal task transition"):
        ledger.transition(route["task_id"], "working", executor=executor_for(route))


def _complete_through_synthesis(ledger: TaskLedger, plan: dict) -> list[str]:
    producer_runs: list[str] = []
    for wave in plan["waves"]:
        for task_id in wave["task_ids"]:
            task = next(task for task in plan["tasks"] if task["task_id"] == task_id)
            if task["phase"] == "verify":
                return producer_runs
            run_id = f"isolated:{task['task_id']}"
            complete_task(ledger, task, run_id=run_id)
            if task["phase"] == "specialist":
                producer_runs.append(run_id)
    raise AssertionError("Plan did not contain an independent verifier")


def test_independent_verifier_cannot_reuse_a_specialist_run(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = strict_plan(registry, request_id="verifier-isolation")
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)
    producer_runs = _complete_through_synthesis(ledger, plan)
    verifier = task_for(plan, phase="verify")
    reused = executor_for(verifier, run_id=producer_runs[0])

    ledger.transition(verifier["task_id"], "working", executor=reused)
    with pytest.raises(AgentRuntimeError, match="matches a producer or synthesizer run"):
        ledger.transition(
            verifier["task_id"],
            "completed",
            output_hash=content_hash({"verdict": "pass"}),
            evidence=["adversarial verification"],
            verdict="pass",
        )


def test_single_context_simulation_cannot_verify(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = plan_for(
        registry,
        "Ասա մեկ պարզ պատասխան։",
        request_id="simulation-not-verification",
    )
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)
    for task in plan["tasks"]:
        if task["phase"] == "verify":
            verifier = task
            break
        complete_task(ledger, task)
    else:
        raise AssertionError("Missing verifier task")

    with pytest.raises(AgentRuntimeError, match="cannot satisfy independent verification"):
        ledger.transition(
            verifier["task_id"],
            "working",
            executor=executor_for(verifier, executor_type="single_context_simulation"),
        )


def test_independent_verifier_requires_a_structured_verdict(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = strict_plan(registry, request_id="verifier-verdict-required")
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)
    _complete_through_synthesis(ledger, plan)
    verifier = task_for(plan, phase="verify")
    ledger.transition(verifier["task_id"], "working", executor=executor_for(verifier))

    with pytest.raises(AgentRuntimeError, match="requires pass, revise, or reject"):
        ledger.transition(
            verifier["task_id"],
            "completed",
            output_hash=content_hash({"verdict": "missing"}),
            evidence=["review output without a verdict"],
        )
    assert ledger.state(verifier["task_id"]) == "working"


@pytest.mark.parametrize(
    ("verdict", "expected_status"),
    [("revise", "revision_required"), ("reject", "failed")],
)
def test_negative_verifier_verdict_prevents_completion(
    registry: AgentRegistry,
    tmp_path,
    verdict: str,
    expected_status: str,
) -> None:
    plan = strict_plan(registry, request_id=f"verifier-{verdict}")
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)
    _complete_through_synthesis(ledger, plan)
    verifier = task_for(plan, phase="verify")
    executor = executor_for(verifier)
    ledger.transition(verifier["task_id"], "working", executor=executor)
    ledger.transition(
        verifier["task_id"],
        "completed",
        executor=executor,
        output_hash=content_hash({"verdict": verdict}),
        evidence=[f"independent verdict:{verdict}"],
        verdict=verdict,
    )

    report = ledger.completion_report()
    assert report["status"] == expected_status
    bucket = "revise_required" if verdict == "revise" else "rejected_results"
    assert report[bucket] == [verifier["task_id"]]


def test_external_action_requires_exact_approval_hash(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = plan_for(
        registry,
        "Հրապարակիր արդեն հաստատված նյութը։",
        request_id="approval-hash",
    )
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)
    route = task_for(plan, phase="route")
    rights = task_for(plan, agent_id="rights-provenance")
    distribution = task_for(plan, agent_id="distribution-growth")
    synthesis = task_for(plan, phase="synthesize")
    owner_gate = task_for(plan, phase="owner_gate")
    complete_task(ledger, route)
    complete_task(ledger, rights)
    complete_task(ledger, distribution)
    complete_task(ledger, synthesis)

    with pytest.raises(AgentRuntimeError, match="requires approval_required"):
        ledger.transition(
            owner_gate["task_id"],
            "working",
            executor=executor_for(owner_gate, executor_type="owner_approval"),
        )
    ledger.transition(
        owner_gate["task_id"],
        "approval_required",
        reason="Publication is an irreversible external action.",
    )
    with pytest.raises(AgentRuntimeError, match="stale or bound to another action"):
        ledger.transition(
            owner_gate["task_id"],
            "working",
            executor=executor_for(owner_gate, executor_type="owner_approval"),
            approval=approval_for(owner_gate, action_hash="0" * 64),
        )

    expected_hash = ledger.expected_approval_hash(owner_gate["task_id"])
    assert expected_hash != owner_gate["idempotency_key"]
    receipt = approval_for(owner_gate, action_hash=expected_hash)
    event = ledger.transition(
        owner_gate["task_id"],
        "working",
        executor=executor_for(owner_gate, executor_type="owner_approval"),
        approval=receipt,
    )
    assert event["approval"] == receipt
    assert event["approval"]["action_hash"] == expected_hash
    with pytest.raises(AgentRuntimeError, match="output must equal the approved action hash"):
        ledger.transition(
            owner_gate["task_id"],
            "completed",
            output_hash="0" * 64,
            evidence=["owner approval"],
        )
    ledger.transition(
        owner_gate["task_id"],
        "completed",
        output_hash=expected_hash,
        evidence=["owner approval bound to final payload"],
    )


def test_owner_gate_cannot_request_approval_before_synthesis(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = plan_for(
        registry,
        "Հրապարակիր արդեն հաստատված նյութը։",
        request_id="premature-owner-gate",
    )
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)
    owner_gate = task_for(plan, phase="owner_gate")

    with pytest.raises(AgentRuntimeError, match="dependencies finish"):
        ledger.transition(owner_gate["task_id"], "approval_required")


def test_tampered_plan_cannot_skip_specialists_or_owner_gate(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = plan_for(
        registry,
        "Հրապարակիր արդեն հաստատված նյութը։",
        request_id="plan-bypass",
    )
    synthesis = task_for(plan, phase="synthesize")
    route = task_for(plan, phase="route")
    synthesis["depends_on"] = [route["task_id"]]
    synthesis["idempotency_key"] = task_contract_hash(synthesis)

    with pytest.raises(AgentRuntimeError, match="every selected specialist"):
        TaskLedger.create(tmp_path / "skip-specialists.json", plan)

    plan = plan_for(
        registry,
        "Հրապարակիր արդեն հաստատված նյութը։",
        request_id="gate-bypass",
    )
    verifier = task_for(plan, phase="verify")
    synthesis = task_for(plan, phase="synthesize")
    verifier["depends_on"] = [synthesis["task_id"]]
    verifier["idempotency_key"] = task_contract_hash(verifier)

    with pytest.raises(AgentRuntimeError, match="does not wait"):
        TaskLedger.create(tmp_path / "skip-owner-gate.json", plan)

    plan = plan_for(
        registry,
        "Հրապարակիր արդեն հաստատված նյութը։",
        request_id="gate-rebinding",
    )
    owner_gate = task_for(plan, phase="owner_gate")
    route = task_for(plan, phase="route")
    owner_gate["depends_on"] = [route["task_id"]]
    owner_gate["idempotency_key"] = task_contract_hash(owner_gate)
    plan["owner_gates"][0]["binding_task_id"] = route["task_id"]

    with pytest.raises(AgentRuntimeError, match="output-hash binding"):
        TaskLedger.create(tmp_path / "rebind-owner-gate.json", plan)


def test_task_contract_tampering_invalidates_idempotency_hash(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = strict_plan(registry, request_id="contract-tamper")
    tampered = copy.deepcopy(plan)
    task_for(tampered, agent_id="scriptwriter")["allowed_tools"].append("undeclared_tool")

    with pytest.raises(AgentRuntimeError, match="full contract"):
        TaskLedger.create(tmp_path / "contract-tamper.json", tampered)


def test_only_independent_verifier_can_return_negative_verdict(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = strict_plan(registry, request_id="specialist-verdict-bypass")
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)
    route = task_for(plan, phase="route")
    complete_task(ledger, route)
    specialist = task_for(plan, agent_id="story-architect")
    executor = executor_for(specialist)
    ledger.transition(specialist["task_id"], "working", executor=executor)

    with pytest.raises(AgentRuntimeError, match="Only the independent verifier"):
        ledger.transition(
            specialist["task_id"],
            "completed",
            output_hash=content_hash({"specialist": "negative"}),
            evidence=["invalid specialist verdict"],
            verdict="revise",
        )


def test_executor_prompt_and_production_type_are_contract_bound(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = strict_plan(registry, request_id="executor-contract")
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)
    route = task_for(plan, phase="route")
    wrong_prompt = executor_for(route)
    wrong_prompt["prompt_version"] = "stale-prompt"
    with pytest.raises(AgentRuntimeError, match="different prompt version"):
        ledger.transition(route["task_id"], "working", executor=wrong_prompt)

    fake = executor_for(route)
    fake["type"] = "test_double"
    with pytest.raises(AgentRuntimeError, match="incompatible with its phase"):
        ledger.transition(route["task_id"], "working", executor=fake)


def test_event_tampering_is_detected_on_load(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = strict_plan(registry, request_id="ledger-tamper")
    path = tmp_path / "ledger.json"
    ledger = TaskLedger.create(path, plan)
    complete_task(ledger, task_for(plan, phase="route"))

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["events"][0]["reason"] = "tampered after persistence"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(AgentRuntimeError, match="modified after recording"):
        TaskLedger.load(path, plan)


def test_required_fail_closed_agent_makes_run_failed(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = plan_for(
        registry,
        "Ստուգիր այս փաստը վերջին պաշտոնական աղբյուրներով։",
        request_id="critical-failure",
    )
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)
    route = task_for(plan, phase="route")
    research = task_for(plan, agent_id="research-accuracy")
    complete_task(ledger, route)
    ledger.transition(research["task_id"], "working", executor=executor_for(research))
    ledger.transition(
        research["task_id"],
        "failed",
        reason="A high-impact claim could not be verified.",
    )

    report = ledger.completion_report()
    assert report["status"] == "failed"
    assert report["fail_closed"] == [research["task_id"]]
    assert research["task_id"] in report["required_incomplete"]


def test_complete_hash_bound_run_reports_complete(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = strict_plan(registry, request_id="complete-run")
    ledger = TaskLedger.create(tmp_path / "ledger.json", plan)
    complete_plan(ledger, plan)

    report = ledger.completion_report()
    assert report["status"] == "complete"
    assert report["required_incomplete"] == []
    assert report["approval_waiting"] == []
    assert report["fail_closed"] == []
    assert report["head_hash"] == ledger.data["head_hash"]
    assert all(state == "completed" for state in report["states"].values())
    completed_phases = [
        next(task["phase"] for task in plan["tasks"] if task["task_id"] == event["task_id"])
        for event in ledger.data["events"]
        if event["to_state"] == "completed"
    ]
    assert completed_phases[-2:] == ["synthesize", "verify"]

    completed_events = {
        event["task_id"]: event
        for event in ledger.data["events"]
        if event["to_state"] == "completed"
    }
    synthesis = task_for(plan, phase="synthesize")
    verifier = task_for(plan, phase="verify")
    assert [item["task_id"] for item in completed_events[synthesis["task_id"]]["dependency_receipts"]] == synthesis["depends_on"]
    assert completed_events[verifier["task_id"]]["dependency_receipts"] == [{
        "task_id": synthesis["task_id"],
        "event_hash": completed_events[synthesis["task_id"]]["event_hash"],
        "output_hash": completed_events[synthesis["task_id"]]["output_hash"],
    }]


def test_rehashed_dependency_receipt_tampering_is_detected(
    registry: AgentRegistry,
    tmp_path,
) -> None:
    plan = strict_plan(registry, request_id="dependency-receipt-tamper")
    path = tmp_path / "ledger.json"
    ledger = TaskLedger.create(path, plan)
    complete_plan(ledger, plan)

    payload = json.loads(path.read_text(encoding="utf-8"))
    synthesis = task_for(plan, phase="synthesize")
    changed = False
    for event in payload["events"]:
        if event["task_id"] == synthesis["task_id"] and event["to_state"] == "completed":
            event["dependency_receipts"][0]["output_hash"] = "0" * 64
            changed = True
        event["previous_event_hash"] = (
            payload["events"][event["sequence"] - 1]["event_hash"]
            if event["sequence"] else None
        )
        event["event_hash"] = content_hash(
            {key: value for key, value in event.items() if key != "event_hash"}
        )
    assert changed
    payload["head_hash"] = payload["events"][-1]["event_hash"]
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(AgentRuntimeError, match="exact dependency receipts"):
        TaskLedger.load(path, plan)
