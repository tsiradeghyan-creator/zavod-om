"""Coverage for the ZavodOM craft gates and their non-bypassable wiring.

Before this file the gates were proven only by each module's own __main__ self-test —
nothing in CI would catch a regression. These tests pin: the glyph gate (incl. the
homoglyph + mislabeled-language cases), continuity verdict tri-state, the brand-voice
heuristic, the gatechain dispatcher, and — most importantly — the checkpoint enforcement
seam that makes the gates impossible to skip for zavod pipelines while leaving upstream
OpenMontage behavior untouched.
"""

import json
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
    read_checkpoint,
    validate_checkpoint,
)
from lib.gatechain import (
    run_compose_gates,
    run_scene_plan_gates,
    run_script_gates,
)
from lib.pipeline_loader import load_pipeline, get_stage_order
from lib.style_selection import required_roles, validate_selections


def _scene_plan_ladder(style_overrides=None, approved=True):
    """A fully-walked scene_plan ladder: every owner-gated rung recorded, council
    carrying a named Style Radar pick per craft role. `approved=False` models an
    automatic run that walked the ladder without an owner freeze."""
    styles = {role: f"pick-{role}" for role in required_roles()}
    if style_overrides is not None:
        styles = style_overrides
    return {
        "sub_stages": [
            {"name": "creative_language_council", "produces": "creative_language",
             "owner_approved": approved, "style_selections": styles},
            {"name": "technical_preparation", "produces": "technical_plan", "owner_approved": approved},
            {"name": "storyboard_shot_cards", "produces": "shot_cards", "owner_approved": approved},
            {"name": "preproduction_plan", "produces": "preproduction_plan", "owner_approved": approved},
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
         "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
         "run_mode": "automatic"},
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


# ------------------------------------------------- run modes (supervised vs automatic)
def _publish_log():
    return {"version": "1.0", "entries": [
        {"platform": "instagram", "status": "draft", "timestamp": "2026-06-26T00:00:00Z"}]}


def _scene_plan():
    return _scene("Your desert weekend", language="en")


def test_idea_requires_run_mode_lock(tmp_path):
    # Same structure, but the run direction (supervised vs automatic) must be explicit.
    with pytest.raises(CheckpointValidationError) as exc:
        write_checkpoint(
            tmp_path, "p-nomode", "idea", "completed",
            {"brief": _brief(), "production_ladder": _ladder(_IDEA_SUBS),
             "engine_lock": {"engine": "remotion", "compose_runtime": "remotion"}},
            pipeline_type="zavod-reel",
        )
    assert "Run mode not locked" in str(exc.value)


def test_automatic_run_completes_without_per_rung_approval(tmp_path):
    # The new gates are structural, not approval-based: an automatic run walks the full
    # ladder and completes without any owner freeze. Proves automatic was not damaged.
    p = write_checkpoint(
        tmp_path, "p-auto", "scene_plan", "completed",
        {"scene_plan": _scene_plan(),
         "production_ladder": _scene_plan_ladder(approved=False),
         "run_mode": "automatic"},
        pipeline_type="zavod-reel",
    )
    assert p.exists()


def test_supervised_run_requires_rung_approval(tmp_path):
    with pytest.raises(CheckpointValidationError) as exc:
        write_checkpoint(
            tmp_path, "p-sup-bad", "scene_plan", "completed",
            {"scene_plan": _scene_plan(),
             "production_ladder": _scene_plan_ladder(approved=False),
             "run_mode": "supervised"},
            pipeline_type="zavod-reel",
        )
    assert "owner approval" in str(exc.value)


def test_supervised_run_with_approval_passes(tmp_path):
    p = write_checkpoint(
        tmp_path, "p-sup-ok", "scene_plan", "completed",
        {"scene_plan": _scene_plan(),
         "production_ladder": _scene_plan_ladder(approved=True),
         "run_mode": "supervised"},
        pipeline_type="zavod-reel",
    )
    assert p.exists()


def test_final_delivery_needs_owner_even_in_automatic(tmp_path):
    # Automatic still stops at the irreversible external gate (publish/delivery).
    ladder = {"sub_stages": [{"name": "presentation_route", "produces": "presentation_route",
                              "owner_approved": False}]}
    with pytest.raises(CheckpointValidationError) as exc:
        write_checkpoint(
            tmp_path, "p-pub", "publish", "completed",
            {"publish_log": _publish_log(), "production_ladder": ladder, "run_mode": "automatic"},
            pipeline_type="zavod-reel",
        )
    assert "Final delivery" in str(exc.value)


# ------------------------------------------------- backward-compat (legacy checkpoints)
def _legacy_checkpoint(scene):
    # A completed zavod scene_plan as it was written BEFORE the ladder/engine/run_mode rules:
    # schema-valid, clean payload, but none of the new structural artifacts.
    return {
        "version": "1.0", "project_id": "legacy", "pipeline_type": "zavod-reel",
        "stage": "scene_plan", "status": "completed",
        "timestamp": "2026-06-01T00:00:00Z",
        "checkpoint_policy": "guided", "human_approval_required": False,
        "human_approved": True, "artifacts": {"scene_plan": scene},
    }


def test_legacy_checkpoint_validates_on_read(tmp_path):
    # Re-reading an old checkpoint must NOT be retroactively rejected for missing the
    # ladder/engine/run_mode that did not exist when it was written.
    cp = _legacy_checkpoint(_scene("Your desert weekend", language="en"))
    validate_checkpoint(cp)  # must not raise

    proj = tmp_path / "legacy"
    proj.mkdir(parents=True)
    (proj / "checkpoint_scene_plan.json").write_text(json.dumps(cp))
    loaded = read_checkpoint(tmp_path, "legacy", "scene_plan")
    assert loaded is not None and loaded["stage"] == "scene_plan"


def test_legacy_dirty_checkpoint_still_blocked_on_read():
    # Content gates are NOT relaxed by backward-compat: a dirty legacy payload still fails.
    cp = _legacy_checkpoint(_scene("Vanը Հայկական", language="en"))  # mislabeled, mixed-script
    with pytest.raises(CheckpointValidationError):
        validate_checkpoint(cp)


def test_write_still_enforces_structure_even_though_read_does_not(tmp_path):
    # The contracts are write-time: writing the same legacy-shaped checkpoint is rejected.
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(
            tmp_path, "legacy2", "scene_plan", "completed",
            {"scene_plan": _scene("Your desert weekend", language="en")},
            pipeline_type="zavod-reel",
        )


def test_upstream_pipeline_is_not_gated():
    # Same dirty artifact under a non-zavod pipeline must NOT trip the zavod gate
    # (upstream OpenMontage behavior is unchanged).
    cp = {
        "pipeline_type": "cinematic", "stage": "scene_plan", "status": "completed",
        "artifacts": {"scene_plan": _scene("Vanը Հայկական", language="en")},
    }
    _enforce_zavod_gates(cp)  # must not raise


def _rr_with_reports(reports):
    """Reports ride the ONE valid route: render_report.continuity_reports (schema field)."""
    return {"version": "1.0",
            "outputs": [{"path": "/tmp/c.mp4", "format": "mp4",
                         "resolution": "1080x1920", "duration_seconds": 5.0}],
            "continuity_reports": reports}


def test_needs_human_blocks_completed_but_allows_awaiting(tmp_path):
    art = {"render_report": _rr_with_reports([{
        "clip": "c.mp4", "anchors": [{"name": "glass", "kind": "object", "persists": None}]}])}
    completed = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "completed", "artifacts": art}
    awaiting = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "awaiting_human", "artifacts": art}
    with pytest.raises(CheckpointValidationError):
        _enforce_zavod_gates(completed)
    _enforce_zavod_gates(awaiting)  # must not raise — legitimate human-review pause


def test_compose_hard_fail_blocks_even_awaiting(tmp_path):
    art = {"render_report": _rr_with_reports([{
        "clip": "c.mp4", "anchors": [{"name": "glass", "kind": "object", "persists": False}]}])}
    awaiting = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "awaiting_human", "artifacts": art}
    with pytest.raises(CheckpointValidationError):
        _enforce_zavod_gates(awaiting)


def test_loose_continuity_keys_are_closed():
    # 2026-07-02: the loose artifacts.continuity_report(s) keys escaped schema validation
    # (not in ARTIFACT_NAMES → any garbage rode along). They are no longer read: a FAIL
    # report carried ONLY on a loose key must not fire the gate (i.e. the seam ignores it),
    # while the same report inside render_report.continuity_reports must block.
    fail_report = {"clip": "c.mp4",
                   "anchors": [{"name": "glass", "kind": "object", "persists": False}]}
    for loose_key in ("continuity_report", "continuity_reports"):
        cp = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "completed",
              "artifacts": {"render_report": _rr_with_reports([]) | {"continuity_reports": []},
                            loose_key: fail_report}}
        _enforce_zavod_gates(cp)  # must NOT raise — loose route is dead
    valid = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "completed",
             "artifacts": {"render_report": _rr_with_reports([fail_report])}}
    with pytest.raises(CheckpointValidationError):
        _enforce_zavod_gates(valid)


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


# ============================================================================
# 2026-07-02 stress-test regressions (see tests/stress/STRESS-REPORT-2026-07-02.md)
# P0: seam↔schema contradiction on render_report.continuity_reports
# P1: Armenian brand-voice tropes | P1.5: pure-Latin transliterated Armenian
# Promise seam: delivery-promise gate wired into the edit checkpoint
# ============================================================================

def _cp(stage, status, artifacts):
    return {
        "version": "1.0", "project_id": "stress-regress", "pipeline_type": "zavod-reel",
        "stage": stage, "status": status, "timestamp": "2026-07-02T00:00:00+00:00",
        "checkpoint_policy": "guided", "human_approval_required": False,
        "human_approved": False, "artifacts": artifacts,
    }


def _filled_continuity_report(clip, persists, note=""):
    """The build_review_request shape after the runtime VLM filled in the anchors."""
    return {"clip": clip, "frames": [], "anchors": [
        {"name": "drinking glass in hand", "kind": "object",
         "persists": persists, "note": note}]}


def _render_report_with(reports):
    return {"version": "1.0",
            "outputs": [{"path": "/tmp/out.mp4", "format": "mp4",
                         "resolution": "1080x1920", "duration_seconds": 10.0}],
            "continuity_reports": reports}


# ---------------------------------------------------------------- P0 (BROKEN fix)
def test_render_report_schema_accepts_continuity_reports():
    # Before the fix render_report.schema.json (additionalProperties: false) REJECTED the
    # very field the seam reads (checkpoint._continuity_reports) — the documented route
    # could never fire. The schema now validates it.
    from schemas.artifacts import validate_artifact
    validate_artifact("render_report",
                      _render_report_with([_filled_continuity_report("c.mp4", True)]))


def test_compose_seam_blocks_bad_clip_via_schema_valid_render_report():
    # The phase-3 negative test, made permanent: the 06-18 disappearing-glass report,
    # carried on the SCHEMA-VALID route, must reach the compose gate and block.
    rr = _render_report_with([_filled_continuity_report(
        "01-A-pooljump.mp4", False,
        "glass in jumper's hand f00-f04, both hands empty mid-air f06 — vanished")])
    with pytest.raises(CheckpointValidationError) as exc:
        validate_checkpoint(_cp("compose", "completed", {"render_report": rr}))
    msg = str(exc.value)
    assert "continuity fail" in msg and "drinking glass" in msg


def test_compose_seam_passes_clean_reports_via_schema_valid_render_report():
    rr = _render_report_with([_filled_continuity_report("01-A-pooljump-v2.mp4", True)])
    validate_checkpoint(_cp("compose", "completed", {"render_report": rr}))  # must not raise


# ---------------------------------------------------------------- P1 (hy tropes)
def test_brand_voice_armenian_tropes_revise():
    r = brand_voice("Բացահայտեք գաղտնիքները մեր հեղափոխական ծառայության։ "
                    "Բարձրացրեք ձեր բիզնեսը նոր մակարդակի։")
    assert r["ok"] is False and r["verdict"] == "revise"
    assert any("(hy)" in f for f in r["flags"])


def test_brand_voice_clean_armenian_passes():
    # Restrained, image-led Armenian in the house voice must NOT trip the trope list.
    r = brand_voice("Մի մարդ օվկիանոս անցավ սիրո համար, որը գոյություն չուներ։")
    assert r["ok"] is True


def test_brand_voice_armenian_exclamation_spam_flagged():
    r = brand_voice("Հրաշալի՜ Զարմանալի՜ Կարևոր՜ Անպայման դիտե՜ք")
    assert any("exclamation" in f for f in r["flags"])


# ---------------------------------------------------------------- P1.5 (translit)
def test_glyph_transliterated_armenian_fails():
    r = glyph_gate("barev dzez, es heghinak em u scenar em grum")
    assert r["ok"] is False
    assert any("Transliterated" in v["reason"] for v in r["violations"])


def test_glyph_single_translit_lookalike_does_not_fire():
    # One stray match is not enough — protects English copy with loan-like words.
    assert glyph_gate("The hima plant is native to the Andes.")["ok"] is True


def test_glyph_plain_english_still_passes():
    assert glyph_gate("Two acres of high desert. One private pool. Book your weekend.")["ok"] is True


# ------------------------------------------------- delivery-promise seam (gap closed)
def _slideshow_edit_decisions():
    return {"version": "1.0", "render_runtime": "remotion",
            "cuts": [{"id": f"c{i}", "source": f"slide{i}.png",
                      "in_seconds": 0, "out_seconds": 3} for i in range(6)]}


def _motion_led_promise():
    return {"promise_type": "motion_led", "motion_required": True,
            "source_required": False, "tone_mode": "cinematic",
            "quality_floor": "presentable"}


def test_edit_seam_blocks_motion_led_slideshow():
    # The stress test reproduced this exact silent downgrade passing the seam.
    cp = _cp("edit", "completed", {"edit_decisions": _slideshow_edit_decisions(),
                                   "delivery_promise": _motion_led_promise()})
    with pytest.raises(CheckpointValidationError) as exc:
        validate_checkpoint(cp)
    assert "delivery_promise" in str(exc.value)


def test_edit_seam_passes_when_promise_honored():
    ed = {"version": "1.0", "render_runtime": "ffmpeg",
          "cuts": [{"id": f"c{i}", "source": f"clip{i}.mp4",
                    "in_seconds": 0, "out_seconds": 3} for i in range(4)]}
    validate_checkpoint(_cp("edit", "completed",
                            {"edit_decisions": ed,
                             "delivery_promise": _motion_led_promise()}))  # must not raise


def test_edit_seam_without_promise_is_not_gated():
    # Legacy/upstream checkpoints without a locked promise stay valid (opt-in gate).
    validate_checkpoint(_cp("edit", "completed",
                            {"edit_decisions": _slideshow_edit_decisions()}))
