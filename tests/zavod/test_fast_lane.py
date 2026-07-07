"""zavod-reel-fast — the short-form fast lane (2026-07-07 strategy audit).

Same enforcement code as zavod-reel, lighter REQUIREMENTS declared in the manifest:
4 stages, a per-stage 3-role bench, no owner-gated ladder rungs. The invariant core
(glyph, artifacts, file reality, continuity, concept lock, identity lock) is untouched.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from lib.bench_gate import required_bench  # noqa: E402
from lib.checkpoint import (  # noqa: E402
    CheckpointValidationError, get_pipeline_stages, write_checkpoint,
    _required_ladder_sub_stages,
)
from tests.zavod.test_gates import _concept_log  # noqa: E402


def test_fast_lane_is_a_zavod_pipeline_with_four_stages():
    assert get_pipeline_stages("zavod-reel-fast") == ["idea", "scene_plan", "compose", "publish"]


def test_fast_lane_bench_is_manifest_declared():
    assert required_bench("idea", "zavod-reel-fast") == ["story-hook", "brand-voice-guard"]
    assert required_bench("compose", "zavod-reel-fast") == ["delivery-qc"]
    # the standard pipeline keeps its full default bench
    assert len(required_bench("idea", "zavod-reel")) >= 4
    # and an undeclared pipeline falls back to the full default too
    assert required_bench("idea", "animation") == required_bench("idea")


def test_fast_lane_has_no_ladder_rungs():
    for stage in ("idea", "scene_plan", "compose", "publish"):
        assert _required_ladder_sub_stages("zavod-reel-fast", stage) == []


def _fast_bench(stage_roles):
    return {"bench": {r: {"ruling": f"The {r} examined its own {r} domain thoroughly and "
                                    f"reached a specific, well-supported conclusion here.",
                          "verdict": "approve"} for r in stage_roles}}


def test_fast_lane_idea_closes_with_light_bench(tmp_path):
    p = write_checkpoint(
        tmp_path, "p", "idea", "completed",
        {"brief": {"version": "1.0", "title": "T", "hook": "H", "key_points": ["a"],
                   "tone": "warm", "style": "clean", "target_platform": "instagram",
                   "target_duration_seconds": 30},
         "bench_report": {"stage": "idea", **_fast_bench(["story-hook", "brand-voice-guard"])},
         "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
         "run_mode": "automatic",
         "decision_log": _concept_log("p")},
        pipeline_type="zavod-reel-fast",
    )
    assert p.exists()


def test_fast_lane_rejects_long_form_brief(tmp_path):
    with pytest.raises(CheckpointValidationError, match="eligibility"):
        write_checkpoint(
            tmp_path, "p", "idea", "completed",
            {"brief": {"version": "1.0", "title": "T", "hook": "H", "key_points": ["a"],
                       "tone": "warm", "style": "clean", "target_platform": "instagram",
                       "target_duration_seconds": 90},
             "bench_report": {"stage": "idea", **_fast_bench(["story-hook", "brand-voice-guard"])},
             "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
             "run_mode": "automatic",
             "decision_log": _concept_log("p")},
            pipeline_type="zavod-reel-fast",
        )


def test_fast_lane_missing_bench_role_still_blocks(tmp_path):
    # Lighter bench, same enforcement: the declared roles are still mandatory.
    with pytest.raises(CheckpointValidationError, match="bench"):
        write_checkpoint(
            tmp_path, "p", "idea", "completed",
            {"brief": {"version": "1.0", "title": "T", "hook": "H", "key_points": ["a"],
                       "tone": "warm", "style": "clean", "target_platform": "instagram",
                       "target_duration_seconds": 30},
             "bench_report": {"stage": "idea", **_fast_bench(["story-hook"])},  # brand-voice-guard missing
             "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
             "run_mode": "automatic",
             "decision_log": _concept_log("p")},
            pipeline_type="zavod-reel-fast",
        )
