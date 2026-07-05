"""Proof that ZavodOM performs its function end-to-end under the new governance.

Walks a full zavod-reel run idea -> publish through the real checkpoint writer, in both
engine lanes and both run modes, asserting every stage is ACCEPTED when the specialist
ladder, engine lane, per-role styles, and run-mode contracts are satisfied. This is the
positive counterpart to test_gates.py (which proves the blocks): here nothing is blocked
because the run is done correctly.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.bench_gate import RULING_MIN, required_bench
from lib.checkpoint import write_checkpoint, get_completed_stages
from lib.style_selection import required_roles
from tests.zavod.media_helpers import tiny_mp4


# Owner-gated, produces-backed sub-stages per zavod-reel stage (the rungs the seam requires).
_STAGE_RUNGS = {
    "idea": ["intake_or_writer_room", "concept_lock"],
    "script": ["expanded_story_structure", "scene_outline", "dialogue_pass",
               "motivation_pass", "shooting_script_lock"],
    "scene_plan": ["creative_language_council", "technical_preparation",
                   "storyboard_shot_cards", "preproduction_plan"],
    "assets": ["source_media_and_rights_lock", "prompt_pack_or_shoot_pack_approval",
               "asset_generation_or_shoot"],
    "edit": ["story_cut", "rhythm_pass", "sound_music_color_vfx_plan"],
    "compose": ["final_mix", "color_vfx_master_qc"],
    "publish": ["presentation_route"],
}
_ORDER = ["idea", "script", "scene_plan", "assets", "edit", "compose", "publish"]


def _story_bible() -> dict:
    return {
        "premise": "A desert host discovers that the weekend escape is really a test of what home costs.",
        "controlling_idea": {
            "side_a": "A place becomes meaningful only when it asks for responsibility.",
            "side_b": "Freedom means leaving before responsibility turns into a trap.",
            "side_b_carrier": "Mara",
            "side_b_tragic_reason": "She has watched caretaking consume every adult around her, so refusal feels like survival rather than selfishness.",
        },
        "secret_chronology": {
            "file": "canon-secret.md",
            "what_happened": "Years before the shoot, the family kept the property by hiding the debt that forced their neighbor out of the valley.",
            "why_silent": "Naming the debt would expose the bargain that made the present comfort possible.",
            "why_now": "A guest recognizes the house and turns the old bargain into an immediate choice.",
            "who_knows_what_complete": True,
        },
        "characters": [
            {"name": "Host", "knows": "the house has a debt", "wrongly_believes": "beauty can cancel what happened", "cost": "keeping the house may cost the honest relationship she wants"},
            {"name": "Mara", "knows": "who paid for the silence", "wrongly_believes": "leaving is the only clean answer", "cost": "she risks turning grief into permanent exile"},
        ],
        "era": {"setting": "timeless desert present", "absorbed": True},
    }


def _delivery_promise() -> dict:
    return {"promise_type": "source_led", "motion_required": False,
            "source_required": False, "tone_mode": "cinematic",
            "quality_floor": "presentable"}


def _bench_stage(stage: str) -> str:
    return {"scene_plan": "scene", "assets": "asset"}.get(stage, stage)


def _full_bench_report(stage: str) -> dict:
    bench_stage = _bench_stage(stage)
    return {
        "stage": bench_stage,
        "bench": {role: {"ruling": f"The {role} reviewed this stage in depth and confirms craft quality across staging continuity and delivery.", "verdict": "approve"} for role in required_bench(bench_stage)},
    }


def _ladder(names, mode):
    subs = []
    for n in names:
        # automatic doesn't freeze per rung — except the irreversible final-delivery gate.
        approved = (mode == "supervised") or (n == "presentation_route")
        e = {"name": n, "produces": n, "owner_approved": approved}
        if n == "creative_language_council":
            e["style_selections"] = {r: f"pick-{r}" for r in required_roles()}
        subs.append(e)
    return {"sub_stages": subs}


def _artifact(stage, src_tool, compose_runtime):
    if stage == "idea":
        return "brief", {"version": "1.0", "title": "Desert weekend", "hook": "H",
                         "key_points": ["a"], "tone": "warm", "style": "clean",
                         "target_platform": "instagram", "target_duration_seconds": 30}
    if stage == "script":
        return "script", {"version": "1.0", "title": "Desert weekend",
                          "total_duration_seconds": 30,
                          "sections": [{"id": "s1", "text": "Your desert weekend",
                                        "start_seconds": 0, "end_seconds": 5}]}
    if stage == "scene_plan":
        return "scene_plan", {"version": "1.0", "scenes": [{
            "id": "s1", "type": "generated", "description": "wide establisher",
            "start_seconds": 0, "end_seconds": 5,
            "shot_language": {"shot_size": "wide", "camera_movement": "static"},
            "text_policy": {"mode": "overlay", "language": "en", "text": "Your desert weekend"}}]}
    if stage == "assets":
        return "asset_manifest", {"version": "1.0", "assets": [
            {"id": "a1", "type": "video", "path": "a.mp4", "source_tool": src_tool, "scene_id": "s1"}]}
    if stage == "edit":
        return "edit_decisions", {"version": "1.0", "render_runtime": compose_runtime,
                                  "cuts": [{"id": "c1", "source": "a.mp4",
                                            "in_seconds": 0, "out_seconds": 5}]}
    if stage == "compose":
        return "render_report", {"version": "1.0", "outputs": [
            {"path": "o.mp4", "format": "mp4", "resolution": "1080x1920", "duration_seconds": 30}]}
    if stage == "publish":
        return "publish_log", {"version": "1.0", "entries": [
            {"platform": "instagram", "status": "draft", "timestamp": "2026-06-26T00:00:00Z"}]}
    raise AssertionError(stage)


@pytest.mark.parametrize("engine,mode", [
    ("higgsfield", "automatic"),
    ("remotion", "supervised"),
])
def test_full_reel_run_is_accepted_end_to_end(tmp_path, engine, mode):
    compose_runtime = "ffmpeg" if engine == "higgsfield" else "remotion"
    src_tool = "higgsfield" if engine == "higgsfield" else "remotion"
    engine_lock = {"engine": engine, "compose_runtime": compose_runtime}

    for stage in _ORDER:
        project_dir = tmp_path / "ideal"
        if stage == "assets":
            project_dir.mkdir(exist_ok=True)
            tiny_mp4(project_dir / "a.mp4")
        if stage == "compose":
            project_dir.mkdir(exist_ok=True)
            tiny_mp4(project_dir / "o.mp4")
        key, art = _artifact(stage, src_tool, compose_runtime)
        artifacts = {
            key: art,
            "production_ladder": _ladder(_STAGE_RUNGS[stage], mode),
            "engine_lock": engine_lock,   # carried on every stage
            "run_mode": mode,
            "bench_report": _full_bench_report(stage),
        }
        if stage == "script":
            artifacts["story_bible"] = _story_bible()
        if stage == "edit":
            artifacts["delivery_promise"] = _delivery_promise()
        path = write_checkpoint(
            tmp_path, "ideal", stage, "completed", artifacts, pipeline_type="zavod-reel",
        )
        assert path.exists(), f"{stage} should be accepted in a correct {engine}/{mode} run"

    completed = get_completed_stages(tmp_path, "ideal", "zavod-reel")
    assert completed == _ORDER, f"all 7 stages complete in order, got {completed}"
