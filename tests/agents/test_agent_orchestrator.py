from __future__ import annotations

import json
from pathlib import Path

import pytest

from lib.agent_registry import content_hash
from lib.agent_router import build_agent_request
from lib.agent_runtime import TaskLedger
from lib.orchestrator import (
    OrchestratorError,
    _require_agent_completion,
    _persist_agent_output,
    activate_agent_fallback,
    initialize_agent_run,
    initialize_revision_run,
)


def _executor(task: dict) -> dict[str, str]:
    return {
        "type": "api_agent",
        "run_id": f"isolated:{task['task_id']}",
        "model": "test",
        "prompt_version": task["prompt_version"],
    }


def _complete(ledger: TaskLedger, task: dict) -> None:
    executor = _executor(task)
    output = {"task": task["task_id"]}
    output_hash = content_hash(output)
    ledger.transition(task["task_id"], "working", executor=executor)
    _persist_agent_output(ledger.path.parent.parent, task, output_hash, output)
    ledger.transition(
        task["task_id"],
        "completed",
        executor=executor,
        output_hash=output_hash,
        evidence=[f"receipt:{task['task_id']}"],
        verdict="pass" if task["phase"] == "verify" else None,
    )


def test_fallback_replan_preserves_old_history_and_carries_unchanged_receipts(tmp_path) -> None:
    request = build_agent_request(
        "Գրիր հայկական սցենար իմ հեղինակային ձեռագրով։ Գույները կարևոր չեն։",
        request_id="fallback-resume",
    )
    initial = initialize_agent_run(tmp_path, "project", request)
    old_plan = json.loads(Path(initial["plan_path"]).read_text(encoding="utf-8"))
    old_ledger = TaskLedger.load(initial["ledger_path"], old_plan)
    by_agent = {task["agent_id"]: task for task in old_plan["tasks"] if task["phase"] == "specialist"}
    route = next(task for task in old_plan["tasks"] if task["phase"] == "route")

    _complete(old_ledger, route)
    _complete(old_ledger, by_agent["authorial-voice-guardian"])
    story = by_agent["story-architect"]
    old_ledger.transition(story["task_id"], "working", executor=_executor(story))
    old_ledger.transition(story["task_id"], "failed", reason="recoverable worker failure")
    assert old_ledger.completion_report()["status"] == "fallback_required"

    replanned = activate_agent_fallback(
        tmp_path,
        "project",
        request["request_id"],
        story["task_id"],
    )
    assert replanned["plan_hash"] != initial["plan_hash"]
    assert Path(initial["plan_path"]).is_file()
    assert Path(initial["ledger_path"]).is_file()

    new_plan = json.loads(Path(replanned["plan_path"]).read_text(encoding="utf-8"))
    new_ledger = TaskLedger.load(replanned["ledger_path"], new_plan)
    new_by_agent = {
        task["agent_id"]: task for task in new_plan["tasks"] if task["phase"] == "specialist"
    }
    new_route = next(task for task in new_plan["tasks"] if task["phase"] == "route")
    assert new_plan["supersedes_plan_hash"] == initial["plan_hash"]
    assert new_ledger.state(new_route["task_id"]) == "completed"
    assert new_ledger.state(new_by_agent["authorial-voice-guardian"]["task_id"]) == "completed"
    fallback = new_by_agent["resilience-generalist"]
    assert fallback["fallback_for_task"] == story["task_id"]
    assert new_ledger.state(fallback["task_id"]) == "submitted"
    assert new_ledger.completion_report()["status"] == "running"


def test_negative_final_review_requires_a_new_hash_linked_revision_run(tmp_path) -> None:
    initial_request = build_agent_request(
        "Գրիր հայկական սցենար իմ հեղինակային ձեռագրով։ Գույները կարևոր չեն։",
        request_id="reviewed-candidate-v1",
    )
    initial = initialize_agent_run(tmp_path, "project", initial_request)
    old_plan = json.loads(Path(initial["plan_path"]).read_text(encoding="utf-8"))
    old_ledger = TaskLedger.load(initial["ledger_path"], old_plan)
    verifier = next(task for task in old_plan["tasks"] if task["phase"] == "verify")
    for wave in old_plan["waves"]:
        for task_id in wave["task_ids"]:
            task = next(task for task in old_plan["tasks"] if task["task_id"] == task_id)
            if task["phase"] == "verify":
                break
            _complete(old_ledger, task)
        else:
            continue
        break

    executor = _executor(verifier)
    verifier_output = {"verdict": "revise"}
    verifier_output_hash = content_hash(verifier_output)
    old_ledger.transition(verifier["task_id"], "working", executor=executor)
    _persist_agent_output(
        old_ledger.path.parent.parent,
        verifier,
        verifier_output_hash,
        verifier_output,
    )
    old_ledger.transition(
        verifier["task_id"],
        "completed",
        executor=executor,
        output_hash=verifier_output_hash,
        evidence=["The final candidate needs one bounded correction."],
        verdict="revise",
    )
    assert old_ledger.completion_report()["status"] == "revision_required"

    revised_request = build_agent_request(
        "Վերամշակիր հայկական սցենարի անկախ ստուգմամբ նշված թերությունը։",
        request_id="reviewed-candidate-v2",
        input_artifacts=[f"candidate:{initial['plan_hash']}"],
    )
    revised = initialize_revision_run(
        tmp_path,
        "project",
        initial_request["request_id"],
        revised_request,
    )
    revised_plan = json.loads(Path(revised["plan_path"]).read_text(encoding="utf-8"))
    assert revised_plan["supersedes_plan_hash"] == initial["plan_hash"]
    assert revised_plan["request_id"] == revised_request["request_id"]
    assert Path(initial["plan_path"]).is_file()
    assert Path(initial["ledger_path"]).is_file()

    unrelated_request = build_agent_request(
        "Ասա մեկ պարզ պատասխան։",
        request_id="unrelated-complete-run",
    )
    unrelated = initialize_agent_run(tmp_path, "project", unrelated_request)
    unrelated_plan = json.loads(Path(unrelated["plan_path"]).read_text(encoding="utf-8"))
    unrelated_ledger = TaskLedger.load(unrelated["ledger_path"], unrelated_plan)
    for wave in unrelated_plan["waves"]:
        for task_id in wave["task_ids"]:
            _complete(
                unrelated_ledger,
                next(task for task in unrelated_plan["tasks"] if task["task_id"] == task_id),
            )

    with pytest.raises(OrchestratorError, match="cannot bypass"):
        _require_agent_completion(
            tmp_path,
            "project",
            unrelated_request["request_id"],
            require_initialized=True,
        )

    revised_ledger = TaskLedger.load(revised["ledger_path"], revised_plan)
    for wave in revised_plan["waves"]:
        for task_id in wave["task_ids"]:
            _complete(
                revised_ledger,
                next(task for task in revised_plan["tasks"] if task["task_id"] == task_id),
            )
    _require_agent_completion(
        tmp_path,
        "project",
        unrelated_request["request_id"],
        require_initialized=True,
    )
