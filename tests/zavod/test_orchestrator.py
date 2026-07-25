"""The minimal production orchestrator — the runtime that wires get_next_stage ->
write_checkpoint -> resume_checkpoint into a real run. These tests pin its control logic:
sequencing, out-of-order refusal, gate propagation, and fail-closed resume. The stage gates
themselves are covered by test_gates / test_ideal_run; here we prove the orchestrator drives
them on the real path (closing the 'no production caller' gap from the dry re-probes).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from lib.checkpoint import CheckpointValidationError  # noqa: E402
from lib.agent_registry import content_hash  # noqa: E402
from lib.orchestrator import (  # noqa: E402
    OrchestratorError,
    advance,
    execute_agent_run,
    initialize_agent_run,
    load_agent_run,
    resume,
    run_state,
)

PT = "zavod-reel"


def _complete_agent_runtime(state):
    import json

    plan = json.loads(Path(state["plan_path"]).read_text(encoding="utf-8"))
    run_root = Path(state["run_directory"])

    def host(task, _context):
        output = {"task": task["task_id"], "result": "complete"}
        return {
            "status": "completed",
            "executor": {
                "type": "api_agent",
                "run_id": f"isolated-{task['task_id']}",
                "model": "test",
                "prompt_version": task["prompt_version"],
            },
            "output_artifact": task["output_artifact"],
            "output": output,
            "output_hash": content_hash(output),
            "evidence": [f"receipt:{task['task_id']}"],
            "verdict": "pass" if task["phase"] == "verify" else None,
            "reason": "Production orchestrator test host completed the task.",
        }

    execute_agent_run(
        run_root.parents[2],
        run_root.parents[1].name,
        plan["request_id"],
        host,
    )
    return plan


def test_run_state_on_empty_project_points_at_first_stage(tmp_path):
    st = run_state(tmp_path, "p", PT)
    assert st["completed"] == []
    assert st["next_stage"] == "idea"      # first stage of the zavod-reel manifest
    assert st["awaiting_human"] is None
    assert st["done"] is False


def test_advance_out_of_order_is_refused_before_any_write(tmp_path):
    # The run expects 'idea' first; trying to complete 'compose' must loud-fail, and nothing
    # is written (no checkpoint file appears).
    with pytest.raises(OrchestratorError, match="Out-of-order"):
        advance(tmp_path, "p", PT, stage="compose", artifacts={"render_report": {}})
    assert not (tmp_path / "p" / "checkpoint_compose.json").exists()


def test_advance_in_progress_writes_only_for_current_stage(tmp_path):
    st = advance(tmp_path, "p", PT, stage="idea", status="in_progress", artifacts={})
    assert (tmp_path / "p" / "checkpoint_idea.json").exists()
    assert st["completed"] == []           # in_progress is not completion
    assert st["next_stage"] == "idea"


def test_advance_in_progress_cannot_start_a_downstream_stage(tmp_path):
    with pytest.raises(OrchestratorError, match="Out-of-order"):
        advance(tmp_path, "p", PT, stage="compose", status="in_progress", artifacts={})
    assert not (tmp_path / "p" / "checkpoint_compose.json").exists()


def test_owner_required_completion_cannot_be_written_unapproved(tmp_path):
    with pytest.raises(CheckpointValidationError, match="requires human approval"):
        from lib.checkpoint import write_checkpoint
        write_checkpoint(
            tmp_path,
            "p-owner",
            "idea",
            "completed",
            {},
            pipeline_type=PT,
            human_approval_required=True,
            human_approved=False,
        )
    assert not (tmp_path / "p-owner" / "checkpoint_idea.json").exists()


def test_awaiting_owner_blocks_every_downstream_status(tmp_path, monkeypatch):
    import lib.orchestrator as orch

    monkeypatch.setattr(
        orch,
        "run_state",
        lambda *args, **kwargs: {
            "awaiting_human": "idea",
            "completed": [],
            "next_stage": "idea",
            "agent_runs": [],
            "done": False,
        },
    )
    with pytest.raises(OrchestratorError, match="awaiting owner approval"):
        advance(tmp_path, "p", PT, stage="script", status="in_progress", artifacts={})


def test_agent_run_is_immutable_and_blocks_checkpoint_until_verified(tmp_path):
    state = initialize_agent_run(
        tmp_path,
        "p-agents",
        "Ստուգիր և ամրացրու գործակալների համակարգը",
    )
    assert state["routing_status"] == "ready"
    assert state["completion"]["status"] == "running"
    with pytest.raises(OrchestratorError, match="mandatory agent work"):
        advance(tmp_path, "p-agents", PT, stage="idea", artifacts={})

    plan = _complete_agent_runtime(state)

    finished = load_agent_run(tmp_path, "p-agents", plan["request_id"])
    assert finished["completion"]["status"] == "complete"
    assert finished["plan_hash"] == state["plan_hash"]


def test_advance_propagates_gate_violation(tmp_path):
    # Completing 'idea' (the expected stage) without its required brief artifact must surface
    # the gate failure through the orchestrator, not swallow it.
    state = initialize_agent_run(tmp_path, "p", "Ստուգիր գործակալների համակարգը։")
    _complete_agent_runtime(state)
    with pytest.raises(CheckpointValidationError):
        advance(tmp_path, "p", PT, stage="idea", status="completed", artifacts={})


def test_zavod_completion_requires_initialized_agent_runtime(tmp_path):
    with pytest.raises(OrchestratorError, match="initialize_agent_run"):
        advance(tmp_path, "p-no-agents", PT, stage="idea", status="completed", artifacts={})


def test_resume_empty_project_returns_none(tmp_path):
    assert resume(tmp_path, "p") is None


def test_advance_when_finished_raises(tmp_path, monkeypatch):
    # When get_next_stage reports the run is finished, advancing further is a loud error.
    import lib.orchestrator as orch
    monkeypatch.setattr(orch, "get_next_stage", lambda *a, **k: None)
    with pytest.raises(OrchestratorError, match="already complete"):
        advance(tmp_path, "p", PT, stage="publish", artifacts={})
