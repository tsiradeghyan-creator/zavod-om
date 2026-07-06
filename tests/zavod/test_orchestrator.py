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
from lib.orchestrator import (  # noqa: E402
    OrchestratorError,
    advance,
    resume,
    run_state,
)

PT = "zavod-reel"


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


def test_advance_in_progress_writes_without_ordering_check(tmp_path):
    # A non-completed (in_progress) write is allowed at any stage — the run is still on 'idea'.
    st = advance(tmp_path, "p", PT, stage="idea", status="in_progress", artifacts={})
    assert (tmp_path / "p" / "checkpoint_idea.json").exists()
    assert st["completed"] == []           # in_progress is not completion
    assert st["next_stage"] == "idea"


def test_advance_propagates_gate_violation(tmp_path):
    # Completing 'idea' (the expected stage) without its required brief artifact must surface
    # the gate failure through the orchestrator, not swallow it.
    with pytest.raises(CheckpointValidationError):
        advance(tmp_path, "p", PT, stage="idea", status="completed", artifacts={})


def test_resume_empty_project_returns_none(tmp_path):
    assert resume(tmp_path, "p") is None


def test_advance_when_finished_raises(tmp_path, monkeypatch):
    # When get_next_stage reports the run is finished, advancing further is a loud error.
    import lib.orchestrator as orch
    monkeypatch.setattr(orch, "get_next_stage", lambda *a, **k: None)
    with pytest.raises(OrchestratorError, match="already complete"):
        advance(tmp_path, "p", PT, stage="publish", artifacts={})
