"""Checkpoint seam wiring for the full-bench standing order."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.bench_gate import RULING_MIN, required_bench  # noqa: E402
from lib.checkpoint import CheckpointValidationError, _enforce_zavod_gates  # noqa: E402


def _bench_report(stage: str, *, omit: str | None = None, thin: str | None = None) -> dict:
    bench = {}
    for role in required_bench(stage):
        if role == omit:
            continue
        bench[role] = {"ruling": "x" * (RULING_MIN + 5)}
    if thin:
        bench[thin] = {"ruling": "ok"}
    return {"stage": stage, "bench": bench}


def _checkpoint(stage: str, status: str, artifacts: dict) -> dict:
    return {"pipeline_type": "zavod-reel", "stage": stage, "status": status, "artifacts": artifacts}


def test_zavod_stage_without_bench_report_is_blocked_at_checkpoint_seam():
    with pytest.raises(CheckpointValidationError) as exc:
        _enforce_zavod_gates(_checkpoint("scene_plan", "completed", {"scene_plan": {}}))
    assert "bench_report" in str(exc.value)


def test_zavod_stage_with_missing_specialist_is_blocked_at_checkpoint_seam():
    artifacts = {"bench_report": _bench_report("scene", omit="costume-designer")}
    with pytest.raises(CheckpointValidationError) as exc:
        _enforce_zavod_gates(_checkpoint("scene_plan", "completed", artifacts))
    assert "costume-designer" in str(exc.value)


def test_zavod_stage_with_thin_specialist_ruling_is_blocked_even_while_awaiting_human():
    artifacts = {"bench_report": _bench_report("asset", thin="identity-guard")}
    with pytest.raises(CheckpointValidationError) as exc:
        _enforce_zavod_gates(_checkpoint("assets", "awaiting_human", artifacts))
    assert "rubber-stamp" in str(exc.value)


def test_zavod_stage_with_full_bench_report_passes_checkpoint_seam():
    artifacts = {"bench_report": _bench_report("scene")}
    _enforce_zavod_gates(_checkpoint("scene_plan", "completed", artifacts))
