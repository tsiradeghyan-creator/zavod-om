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
from lib.pipeline_loader import load_pipeline, get_stage_order
from lib.style_selection import required_roles, validate_selections


def _scene_plan_ladder(style_overrides=None):
    """A fully-walked scene_plan ladder: every owner-gated rung recorded, council
    carrying a named Style Radar pick per craft role."""
    styles = {role: f"pick-{role}" for role in required_roles()}
    if style_overrides is not None:
        styles = style_overrides
    return {
        "sub_stages": [
            {"name": "creative_language_council", "produces": "creative_language",
             "owner_approved": True, "style_selections": styles},
            {"name": "technical_preparation", "produces": "technical_plan", "owner_approved": True},
            {"name": "storyboard_shot_cards", "produces": "shot_cards", "owner_approved": True},
            {"name": "preproduction_plan", "produces": "preproduction_plan", "owner_approved": True},
        ]
    }


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
        {"scene_plan": good, "production_ladder": _scene_plan_ladder()},
        pipeline_type="zavod-reel",
    )
    assert path.exists()


# ------------------------------------------------- production ladder (no-collapse)
def test_completed_scene_plan_without_ladder_is_blocked(tmp_path):
    # A clean artifact is not enough: a completed stage that skipped its specialist
    # sub-stages must be rejected — this is the non-collapse guarantee.
    good = _scene("Your desert weekend", language="en")
    with pytest.raises(CheckpointValidationError) as exc:
        write_checkpoint(
            tmp_path, "proj-collapse", "scene_plan", "completed",
            {"scene_plan": good}, pipeline_type="zavod-reel",
        )
    assert "ladder collapsed" in str(exc.value)


def test_completed_scene_plan_missing_one_rung_is_blocked(tmp_path):
    good = _scene("Your desert weekend", language="en")
    ladder = _scene_plan_ladder()
    ladder["sub_stages"] = ladder["sub_stages"][:-1]  # drop preproduction_plan
    with pytest.raises(CheckpointValidationError) as exc:
        write_checkpoint(
            tmp_path, "proj-rung", "scene_plan", "completed",
            {"scene_plan": good, "production_ladder": ladder},
            pipeline_type="zavod-reel",
        )
    assert "preproduction_plan" in str(exc.value)


def test_full_ladder_with_per_role_styles_passes(tmp_path):
    good = _scene("Your desert weekend", language="en")
    path = write_checkpoint(
        tmp_path, "proj-full", "scene_plan", "completed",
        {"scene_plan": good, "production_ladder": _scene_plan_ladder()},
        pipeline_type="zavod-reel",
    )
    assert path.exists()


def test_creative_council_missing_a_style_pick_is_blocked(tmp_path):
    good = _scene("Your desert weekend", language="en")
    partial = {r: f"pick-{r}" for r in required_roles() if r != "costume_designer"}
    ladder = _scene_plan_ladder(style_overrides=partial)
    with pytest.raises(CheckpointValidationError) as exc:
        write_checkpoint(
            tmp_path, "proj-style", "scene_plan", "completed",
            {"scene_plan": good, "production_ladder": ladder},
            pipeline_type="zavod-reel",
        )
    assert "costume_designer" in str(exc.value)


def test_awaiting_human_does_not_require_full_ladder(tmp_path):
    # Mid-ladder pause: a not-yet-completed scene_plan must be writable without the
    # whole specialist chain present.
    good = _scene("Your desert weekend", language="en")
    path = write_checkpoint(
        tmp_path, "proj-pause", "scene_plan", "awaiting_human",
        {"scene_plan": good}, pipeline_type="zavod-reel",
    )
    assert path.exists()


def test_style_selection_validate_unit():
    assert validate_selections({})["ok"] is False
    full = {r: f"x-{r}" for r in required_roles()}
    assert validate_selections(full)["ok"] is True
    blank = dict(full, director="   ")
    v = validate_selections(blank)
    assert v["ok"] is False and "director" in v["empty"]


# ------------------------------------------------- engine lanes (Remotion vs Higgsfield)
def _ladder(names):
    subs = []
    for n in names:
        e = {"name": n, "produces": n, "owner_approved": True}
        if n == "creative_language_council":
            e["style_selections"] = {r: f"pick-{r}" for r in required_roles()}
        subs.append(e)
    return {"sub_stages": subs}


def _brief():
    return {"version": "1.0", "title": "T", "hook": "H", "key_points": ["a"],
            "tone": "warm", "style": "clean", "target_platform": "instagram",
            "target_duration_seconds": 30}


def _asset_manifest(source_tool):
    return {"version": "1.0", "assets": [
        {"id": "a1", "type": "video", "path": "a.mp4", "source_tool": source_tool, "scene_id": "s1"}]}


def _render_report():
    return {"version": "1.0", "outputs": [
        {"path": "o.mp4", "format": "mp4", "resolution": "1080x1920", "duration_seconds": 30}]}


_IDEA_SUBS = ["intake_or_writer_room", "concept_lock"]
_ASSET_SUBS = ["source_media_and_rights_lock", "prompt_pack_or_shoot_pack_approval", "asset_generation_or_shoot"]
_COMPOSE_SUBS = ["final_mix", "color_vfx_master_qc"]


def test_idea_without_engine_lock_is_blocked(tmp_path):
    # Forces the upfront Remotion-vs-Higgsfield question: a locked lane is mandatory.
    with pytest.raises(CheckpointValidationError) as exc:
        write_checkpoint(
            tmp_path, "p-noeng", "idea", "completed",
            {"brief": _brief(), "production_ladder": _ladder(_IDEA_SUBS)},
            pipeline_type="zavod-reel",
        )
    assert "Engine lane not locked" in str(exc.value)


def test_idea_with_engine_lock_passes(tmp_path):
    p = write_checkpoint(
        tmp_path, "p-eng", "idea", "completed",
        {"brief": _brief(), "production_ladder": _ladder(_IDEA_SUBS),
         "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"}},
        pipeline_type="zavod-reel",
    )
    assert p.exists()


def test_remotion_lane_rejects_higgsfield_asset(tmp_path):
    with pytest.raises(CheckpointValidationError) as exc:
        write_checkpoint(
            tmp_path, "p-mix", "assets", "completed",
            {"asset_manifest": _asset_manifest("higgsfield"),
             "engine_lock": {"engine": "remotion"},
             "production_ladder": _ladder(_ASSET_SUBS)},
            pipeline_type="zavod-reel",
        )
    assert "Higgsfield" in str(exc.value)


def test_remotion_lane_allows_designed_asset(tmp_path):
    p = write_checkpoint(
        tmp_path, "p-clean", "assets", "completed",
        {"asset_manifest": _asset_manifest("remotion"),
         "engine_lock": {"engine": "remotion"},
         "production_ladder": _ladder(_ASSET_SUBS)},
        pipeline_type="zavod-reel",
    )
    assert p.exists()


def test_higgsfield_lane_must_compose_via_ffmpeg_not_remotion(tmp_path):
    with pytest.raises(CheckpointValidationError) as exc:
        write_checkpoint(
            tmp_path, "p-cross", "compose", "completed",
            {"render_report": _render_report(),
             "engine_lock": {"engine": "higgsfield", "compose_runtime": "remotion"},
             "production_ladder": _ladder(_COMPOSE_SUBS)},
            pipeline_type="zavod-reel",
        )
    assert "lane" in str(exc.value)


def test_higgsfield_compose_via_ffmpeg_passes(tmp_path):
    p = write_checkpoint(
        tmp_path, "p-hf", "compose", "completed",
        {"render_report": _render_report(),
         "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
         "production_ladder": _ladder(_COMPOSE_SUBS)},
        pipeline_type="zavod-reel",
    )
    assert p.exists()


def test_remotion_compose_via_remotion_passes(tmp_path):
    p = write_checkpoint(
        tmp_path, "p-rem", "compose", "completed",
        {"render_report": _render_report(),
         "engine_lock": {"engine": "remotion", "compose_runtime": "remotion"},
         "production_ladder": _ladder(_COMPOSE_SUBS)},
        pipeline_type="zavod-reel",
    )
    assert p.exists()


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


def test_failed_checkpoint_does_not_write_decision_log(tmp_path):
    bad = _scene("Vanը Հայկական", language="en")
    decision_log = {
        "decisions": [
            {"decision_id": "d1", "stage": "scene_plan", "decision": "bad idea"},
        ],
    }
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(
            tmp_path, "proj-log", "scene_plan", "completed",
            {"scene_plan": bad, "decision_log": decision_log},
            pipeline_type="zavod-reel",
        )
    assert not (tmp_path / "proj-log" / "decision_log.json").exists()


def test_reel_and_promo_expose_owner_gated_specialist_ladders():
    expected = {
        "zavod-reel": {
            "idea.intake_or_writer_room",
            "script.expanded_story_structure",
            "scene_plan.creative_language_council",
            "scene_plan.technical_preparation",
            "scene_plan.preproduction_plan",
            "assets.prompt_pack_or_shoot_pack_approval",
            "edit.story_cut",
            "compose.color_vfx_master_qc",
        },
        "zavod-promo": {
            "idea.intake_or_writer_room",
            "script.expanded_story_structure",
            "scene_plan.creative_language_council",
            "scene_plan.source_frame_selection",
            "scene_plan.technical_preparation",
            "assets.prompt_pack_approval",
            "edit.story_cut",
            "compose.color_vfx_master_qc",
        },
    }
    for pipeline, required in expected.items():
        order = set(get_stage_order(load_pipeline(pipeline), include_sub_stages=True))
        assert required.issubset(order)
