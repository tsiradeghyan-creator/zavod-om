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


_RUBRIC_OK = {"first_3_seconds_promise": 4, "brand_specificity": 4,
              "emotional_charge": 4, "clarity": 4, "share_or_save_reason": 4}


def _fast_bench(stage_roles):
    bench = {}
    for r in stage_roles:
        entry = {"ruling": f"The {r} examined its own {r} domain thoroughly and "
                           f"reached a specific, well-supported conclusion here.",
                 "verdict": "approve"}
        if r == "story-hook":
            entry["rubric"] = dict(_RUBRIC_OK)
        bench[r] = entry
    return {"bench": bench}


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


# ── Hook rubric (strategy audit): the reviewer judges, the code demands structure ──
from lib.bench_gate import run_bench_gates  # noqa: E402


def _idea_report(rubric):
    entry = {"ruling": "The story-hook reviewer weighed the opening promise, tension and "
                       "save-worthiness of this hook against the brand pack in detail.",
             "verdict": "approve"}
    if rubric is not None:
        entry["rubric"] = rubric
    other = {"ruling": "The brand-voice-guard checked register, vocabulary and visual "
                       "identity against the loaded brand pack and found them consistent.",
             "verdict": "approve"}
    return {"stage": "idea", "bench": {"story-hook": entry, "brand-voice-guard": other}}


def test_story_hook_without_rubric_blocks():
    r = run_bench_gates("idea", _idea_report(None), pipeline_type="zavod-reel-fast")
    assert not r["ok"] and any("rubric" in v for v in r["violations"])


def test_low_rubric_total_blocks():
    weak = dict(_RUBRIC_OK, first_3_seconds_promise=1, emotional_charge=1, clarity=1)  # 14
    r = run_bench_gates("idea", _idea_report(weak), pipeline_type="zavod-reel-fast")
    assert not r["ok"] and any("not strong enough" in v for v in r["violations"])


def test_invalid_rubric_score_blocks():
    r = run_bench_gates("idea", _idea_report(dict(_RUBRIC_OK, clarity=7)),
                        pipeline_type="zavod-reel-fast")
    assert not r["ok"] and any("1-5" in v for v in r["violations"])


def test_passing_rubric_closes():
    r = run_bench_gates("idea", _idea_report(dict(_RUBRIC_OK)),
                        pipeline_type="zavod-reel-fast")
    assert r["ok"], r["violations"]


# ── Round 7.1 (2026-07-08 re-audit №5, MERJEL): owner_override_required_if now enforced ──
# The manifest documented risk categories that require owner override, but nothing read
# the list — a paid_client_delivery reel under 45s sailed through unnoticed.
def _brief_with(risk_flags=None, owner_override=None, duration=30):
    b = {"version": "1.0", "title": "T", "hook": "H", "key_points": ["a"],
         "tone": "warm", "style": "clean", "target_platform": "instagram",
         "target_duration_seconds": duration}
    if risk_flags is not None:
        b["risk_flags"] = risk_flags
    if owner_override is not None:
        b["owner_override"] = owner_override
    return b


def test_flagged_risk_without_override_blocks(tmp_path):
    with pytest.raises(CheckpointValidationError, match="owner_override"):
        write_checkpoint(
            tmp_path, "p", "idea", "completed",
            {"brief": _brief_with(risk_flags=["paid_client_delivery"]),
             "bench_report": {"stage": "idea", **_fast_bench(["story-hook", "brand-voice-guard"])},
             "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
             "run_mode": "automatic",
             "decision_log": _concept_log("p")},
            pipeline_type="zavod-reel-fast",
        )


def test_flagged_risk_with_partial_override_still_blocks(tmp_path):
    with pytest.raises(CheckpointValidationError, match="owner_override"):
        write_checkpoint(
            tmp_path, "p", "idea", "completed",
            {"brief": _brief_with(
                risk_flags=["paid_client_delivery", "legal_or_sensitive_topic"],
                owner_override={"approved_by": "ani", "reason": "client ok",
                                "covers": ["paid_client_delivery"]}),  # legal_ flag not covered
             "bench_report": {"stage": "idea", **_fast_bench(["story-hook", "brand-voice-guard"])},
             "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
             "run_mode": "automatic",
             "decision_log": _concept_log("p")},
            pipeline_type="zavod-reel-fast",
        )


def test_flagged_risk_with_full_override_passes(tmp_path):
    p = write_checkpoint(
        tmp_path, "p", "idea", "completed",
        {"brief": _brief_with(
            risk_flags=["paid_client_delivery"],
            owner_override={"approved_by": "ani", "reason": "client approved fast-lane use",
                            "covers": ["paid_client_delivery"]}),
         "bench_report": {"stage": "idea", **_fast_bench(["story-hook", "brand-voice-guard"])},
         "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
         "run_mode": "automatic",
         "decision_log": _concept_log("p")},
        pipeline_type="zavod-reel-fast",
    )
    assert p.exists()


def test_no_risk_flags_unaffected(tmp_path):
    p = write_checkpoint(
        tmp_path, "p", "idea", "completed",
        {"brief": _brief_with(),  # no risk_flags at all
         "bench_report": {"stage": "idea", **_fast_bench(["story-hook", "brand-voice-guard"])},
         "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
         "run_mode": "automatic",
         "decision_log": _concept_log("p")},
        pipeline_type="zavod-reel-fast",
    )
    assert p.exists()


def test_unflagged_risk_category_ignored(tmp_path):
    # A risk_flag NOT in the manifest's owner_override_required_if list doesn't gate.
    p = write_checkpoint(
        tmp_path, "p", "idea", "completed",
        {"brief": _brief_with(risk_flags=["minor_stylistic_experiment"]),
         "bench_report": {"stage": "idea", **_fast_bench(["story-hook", "brand-voice-guard"])},
         "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
         "run_mode": "automatic",
         "decision_log": _concept_log("p")},
        pipeline_type="zavod-reel-fast",
    )
    assert p.exists()
