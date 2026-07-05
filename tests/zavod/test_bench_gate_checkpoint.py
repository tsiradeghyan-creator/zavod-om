"""Checkpoint seam wiring for the full-bench standing order."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.bench_gate import RULING_MIN, required_bench  # noqa: E402
from lib.checkpoint import CheckpointValidationError, _enforce_zavod_gates  # noqa: E402


def _story_bible() -> dict:
    return {
        "premise": "A village doctor must expose the buried lie that saved one family and ruined another.",
        "controlling_idea": {
            "side_a": "Truth heals only when it is spoken before power rewrites it.",
            "side_b": "Silence can be mercy when truth would destroy the innocent.",
            "side_b_carrier": "Nare",
            "side_b_tragic_reason": "She watched a public confession turn into punishment once before, so concealment feels like the only protection left.",
        },
        "secret_chronology": {
            "file": "canon-secret.md",
            "what_happened": "Twenty five years earlier the wrong witness was protected after the fire, because the real witness was a child and every adult chose reputation over repair.",
            "why_silent": "The families survived by trading public peace for private shame.",
            "why_now": "A returned letter names the child witness and forces every old alibi into the present.",
            "who_knows_what_complete": True,
        },
        "characters": [
            {"name": "Ani", "knows": "the letter is real", "wrongly_believes": "her mother hid it from cowardice", "cost": "she risks losing the only family tie she still trusts"},
            {"name": "Nare", "knows": "who moved the witness", "wrongly_believes": "silence is still saving the child", "cost": "she must choose between protection and becoming the lie's author"},
        ],
        "era": {"setting": "1920s border town", "absorbed": True},
    }


def _bench_report(stage: str, *, omit: str | None = None, thin: str | None = None) -> dict:
    bench = {}
    for role in required_bench(stage):
        if role == omit:
            continue
        bench[role] = {"ruling": (
            f"The {role} reviewed this stage in depth and confirms the craft bar is met "
            f"across staging, continuity, palette, and delivery quality."
        ), "verdict": "approve"}
    if thin:
        bench[thin] = {"ruling": "ok", "verdict": "approve"}
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


def test_script_stage_without_story_bible_is_blocked_at_checkpoint_seam():
    artifacts = {"bench_report": _bench_report("script")}
    with pytest.raises(CheckpointValidationError) as exc:
        _enforce_zavod_gates(_checkpoint("script", "completed", artifacts))
    assert "story_bible" in str(exc.value)


def test_script_stage_with_valid_story_bible_passes_checkpoint_seam():
    artifacts = {"bench_report": _bench_report("script"), "story_bible": _story_bible()}
    _enforce_zavod_gates(_checkpoint("script", "completed", artifacts))
