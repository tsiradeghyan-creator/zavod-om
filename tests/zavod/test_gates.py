"""Coverage for the ZavodOM craft gates and their non-bypassable wiring.

Before this file the gates were proven only by each module's own __main__ self-test —
nothing in CI would catch a regression. These tests pin: the glyph gate (incl. the
homoglyph + mislabeled-language cases), continuity verdict tri-state, the brand-voice
heuristic, the gatechain dispatcher, and — most importantly — the checkpoint enforcement
seam that makes the gates impossible to skip for zavod pipelines while leaving upstream
OpenMontage behavior untouched.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.armenian_glyph_gate import gate as glyph_gate
from lib.brand_voice_check import check as brand_voice
from lib.continuity_checker import verdict as continuity_verdict
from lib.checkpoint import (
    CheckpointValidationError,
    _enforce_zavod_gates,
    write_checkpoint,
)
from lib.gatechain import (
    run_compose_gates,
    run_scene_plan_gates,
    run_script_gates,
)


# ---------------------------------------------------------------- glyph gate
def test_glyph_clean_armenian_passes():
    assert glyph_gate("Վանը Հայկական դարպասների հեղինակն է")["ok"] is True


def test_glyph_mixed_script_fails():
    r = glyph_gate("Vanը Հայկական")  # Latin spliced into an Armenian word
    assert r["ok"] is False
    assert any("Vanը" == v["text"] for v in r["violations"])


def test_glyph_english_brand_word_in_armenian_context_passes():
    # Pure-Latin brand words legitimately appear in Armenian copy.
    assert glyph_gate("Ամրագրիր հիմա Airbnb-ով")["ok"] is True


def test_glyph_cyrillic_homoglyph_in_armenian_context_fails():
    # No Armenian letters in the word, but Cyrillic look-alikes inside Armenian content.
    r = glyph_gate("Հայկական сезон")  # "сезон" is all-Cyrillic
    assert r["ok"] is False
    assert any("сезон" == v["text"] for v in r["violations"])


def test_glyph_pure_cyrillic_without_armenian_context_passes():
    # Outside Armenian context we do not police other scripts.
    assert glyph_gate("полный сезон")["ok"] is True


# --------------------------------------------------------- continuity verdict
@pytest.mark.parametrize(
    "persists,expected",
    [(True, "pass"), (False, "fail"), (None, "needs_human")],
)
def test_continuity_tristate(persists, expected):
    report = {"clip": "c.mp4", "anchors": [{"name": "glass", "kind": "object", "persists": persists}]}
    assert continuity_verdict(report)["verdict"] == expected


# ------------------------------------------------------------- brand voice
def test_brand_voice_clean_passes():
    assert brand_voice("Two acres of high desert. One private pool.")["ok"] is True


def test_brand_voice_tropes_revise():
    r = brand_voice("In today's world, unlock a revolutionary, seamless escape — elevate your stay!")
    assert r["ok"] is False and r["verdict"] == "revise"


# ------------------------------------------------------------- gatechain
def _scene(text, language="en", in_hand=None):
    sc = {
        "id": "s1", "type": "generated", "description": "x",
        "start_seconds": 0, "end_seconds": 5,
        "shot_language": {"shot_size": "wide", "camera_movement": "static"},
        "text_policy": {"mode": "overlay", "language": language, "text": text},
    }
    if in_hand:
        sc["staging"] = {"in_hand_objects": in_hand}
    return {"version": "1.0", "scenes": [sc]}


def test_run_script_gates_rejects_tropes_and_mixed_script():
    r = run_script_gates("In today's world, unlock Vanը")
    assert r["ok"] is False


def test_scene_plan_glyph_bypass_is_closed():
    # Armenian dirty text MISLABELED as english must still be caught (the old bypass).
    r = run_scene_plan_gates(_scene("Vanը Հայկական", language="en"))
    assert r["ok"] is False
    assert any("Van" in v for v in r["violations"])


def test_scene_plan_clean_passes():
    assert run_scene_plan_gates(_scene("Your desert weekend", language="en"))["ok"] is True


def test_compose_gates_separate_fail_from_needs_human():
    fail = run_compose_gates([{"clip": "a.mp4", "anchors": [{"name": "g", "kind": "object", "persists": False}]}])
    pend = run_compose_gates([{"clip": "a.mp4", "anchors": [{"name": "g", "kind": "object", "persists": None}]}])
    ok = run_compose_gates([{"clip": "a.mp4", "anchors": [{"name": "g", "kind": "object", "persists": True}]}])
    assert fail["verdict"] == "fail" and fail["ok"] is False
    assert pend["verdict"] == "needs_human" and pend["ok"] is False
    assert ok["verdict"] == "pass" and ok["ok"] is True


# ------------------------------------------------- checkpoint enforcement seam
def test_zavod_checkpoint_blocks_dirty_scene_plan(tmp_path):
    bad = _scene("Vanը Հայկական", language="en")  # mislabeled, mixed-script
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(
            tmp_path, "proj1", "scene_plan", "completed",
            {"scene_plan": bad}, pipeline_type="zavod-reel",
        )


def test_zavod_checkpoint_allows_clean_scene_plan(tmp_path):
    good = _scene("Your desert weekend", language="en")
    path = write_checkpoint(
        tmp_path, "proj2", "scene_plan", "completed",
        {"scene_plan": good}, pipeline_type="zavod-reel",
    )
    assert path.exists()


def test_upstream_pipeline_is_not_gated():
    # Same dirty artifact under a non-zavod pipeline must NOT trip the zavod gate
    # (upstream OpenMontage behavior is unchanged).
    cp = {
        "pipeline_type": "cinematic", "stage": "scene_plan", "status": "completed",
        "artifacts": {"scene_plan": _scene("Vanը Հայկական", language="en")},
    }
    _enforce_zavod_gates(cp)  # must not raise


def test_needs_human_blocks_completed_but_allows_awaiting(tmp_path):
    art = {"render_report": {}, "continuity_report": {
        "clip": "c.mp4", "anchors": [{"name": "glass", "kind": "object", "persists": None}]}}
    completed = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "completed", "artifacts": art}
    awaiting = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "awaiting_human", "artifacts": art}
    with pytest.raises(CheckpointValidationError):
        _enforce_zavod_gates(completed)
    _enforce_zavod_gates(awaiting)  # must not raise — legitimate human-review pause


def test_compose_hard_fail_blocks_even_awaiting(tmp_path):
    art = {"continuity_report": {
        "clip": "c.mp4", "anchors": [{"name": "glass", "kind": "object", "persists": False}]}}
    awaiting = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "awaiting_human", "artifacts": art}
    with pytest.raises(CheckpointValidationError):
        _enforce_zavod_gates(awaiting)
