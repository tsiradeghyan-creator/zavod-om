from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from lib.agent_registry import content_hash
from lib.agent_router import build_agent_request
from lib.orchestrator import (
    OrchestratorError,
    execute_agent_run,
    initialize_agent_run,
    load_agent_run,
)


def _result(task: dict) -> dict:
    output = {"task": task["task_id"], "result": "complete"}
    return {
        "status": "completed",
        "executor": {
            "type": "api_agent",
            "run_id": f"native:{task['task_id']}",
            "model": "host-test-agent",
            "prompt_version": task["prompt_version"],
        },
        "output_artifact": task["output_artifact"],
        "output": output,
        "output_hash": content_hash(output),
        "evidence": [f"host-receipt:{task['task_id']}"],
        "verdict": "pass" if task["phase"] == "verify" else None,
        "reason": "Native host test worker completed the exact task contract.",
    }


def test_dispatcher_runs_relevant_agents_in_parallel_and_verifies(tmp_path) -> None:
    request = build_agent_request(
        "Գրիր Մաղակյանի հայկական սցենարային ձեռագրով երկխոսություն։ Գույները հետաքրքիր չեն։",
        request_id="dispatcher-screenplay",
    )
    initialize_agent_run(tmp_path, "project", request)
    parallel_pair = {"authorial-voice-guardian", "story-architect"}
    barrier = threading.Barrier(2)
    calls: list[str] = []
    lock = threading.Lock()

    def host(task: dict, context: dict) -> dict:
        assert context["request"]["request_id"] == request["request_id"]
        assert context["plan_hash"]
        if task["depends_on"]:
            assert set(task["depends_on"]) <= set(context["ancestor_outputs"])
        if task["agent_id"] in parallel_pair:
            barrier.wait(timeout=5)
        with lock:
            calls.append(task["agent_id"])
        return _result(task)

    state = execute_agent_run(tmp_path, "project", request["request_id"], host)

    assert state["completion"]["status"] == "complete"
    assert parallel_pair <= set(calls)
    assert "scriptwriter" in calls
    assert calls[-1] == "quality-auditor"
    assert "visual-director" not in calls
    assert "media-producer" not in calls


def test_dispatcher_pauses_for_verified_owner_identity_and_exact_hash(tmp_path) -> None:
    request = build_agent_request(
        "Հրապարակիր արդեն հաստատված նյութը։",
        request_id="dispatcher-owner-gate",
    )
    initialized = initialize_agent_run(tmp_path, "project", request)

    waiting = execute_agent_run(tmp_path, "project", request["request_id"], lambda task, _: _result(task))
    assert waiting["completion"]["status"] == "owner_required"

    approved_hashes: list[str] = []

    def approve(task: dict, expected_hash: str) -> dict:
        approved_hashes.append(expected_hash)
        return {
            "gate_id": task["approval_gate"],
            "action_hash": expected_hash,
            "approver": "verified-owner",
            "approved_at": "2026-07-13T12:00:00+04:00",
            "identity_provider": "host-signed-session",
            "identity_proof_hash": content_hash({"session": "verified-owner-session"}),
        }

    completed = execute_agent_run(
        tmp_path,
        "project",
        request["request_id"],
        lambda task, _: _result(task),
        approval_provider=approve,
    )

    assert completed["completion"]["status"] == "complete"
    assert len(approved_hashes) == 1
    plan = json.loads(Path(initialized["plan_path"]).read_text(encoding="utf-8"))
    synthesis_id = next(
        task["task_id"] for task in plan["tasks"] if task["phase"] == "synthesize"
    )
    ledger = json.loads(Path(completed["ledger_path"]).read_text(encoding="utf-8"))
    synthesis_output = next(
        event["output_hash"]
        for event in ledger["events"]
        if event["task_id"] == synthesis_id and event["to_state"] == "completed"
    )
    assert approved_hashes == [synthesis_output]


def test_dispatcher_automatically_activates_allowlisted_fallback_once(tmp_path) -> None:
    request = build_agent_request(
        "Գրիր հայկական սցենար իմ հեղինակային ձեռագրով։ Գույները կարևոր չեն։",
        request_id="dispatcher-fallback",
    )
    initialize_agent_run(tmp_path, "project", request)
    calls: list[str] = []

    def host(task: dict, context: dict) -> dict:
        calls.append(task["agent_id"])
        if task["agent_id"] == "story-architect":
            raise RuntimeError("primary host unavailable")
        return _result(task)

    state = execute_agent_run(tmp_path, "project", request["request_id"], host)

    assert state["completion"]["status"] == "complete"
    assert calls.count("story-architect") == 1
    assert calls.count("resilience-generalist") == 1
    assert state["supersedes_plan_hash"] is not None


def test_persisted_agent_output_tampering_blocks_completion(tmp_path) -> None:
    request = build_agent_request(
        "Ասա մեկ պարզ պատասխան։",
        request_id="dispatcher-output-tamper",
    )
    initialize_agent_run(tmp_path, "project", request)
    state = execute_agent_run(
        tmp_path,
        "project",
        request["request_id"],
        lambda task, _: _result(task),
    )
    assert state["completion"]["status"] == "complete"

    output_path = next(Path(state["run_directory"]).glob("outputs/*/*.json"))
    envelope = json.loads(output_path.read_text(encoding="utf-8"))
    envelope["output"] = {"tampered": True}
    output_path.write_text(json.dumps(envelope), encoding="utf-8")

    with pytest.raises(OrchestratorError, match="payload does not match"):
        load_agent_run(tmp_path, "project", request["request_id"])
