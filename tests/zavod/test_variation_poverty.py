"""#9 — single-scene semantic-poverty blind spot.

Most variation checks only fire at 4+ scenes, so a 1-3 scene plan that leans on generic
phrasing used to score 'strong' and close silently. It must instead escalate to a
needs_human owner decision — unless the maker marked it an intentional beat — and must NOT
false-flag a specific, deliberately minimal scene.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.variation_checker import check_scene_variation  # noqa: E402
from lib.gatechain import run_scene_plan_gates  # noqa: E402


def _scene(**kw):
    base = {"id": "s1", "type": "generated", "start_seconds": 0, "end_seconds": 5,
            "shot_language": {"shot_size": "wide", "camera_movement": "static"}}
    base.update(kw)
    return base


def test_generic_single_scene_escalates_to_needs_human():
    scenes = [_scene(description="a beautiful modern room, sleek design")]
    assert check_scene_variation(scenes)["verdict"] == "needs_human"


def test_generic_single_scene_with_shot_intent_stays_strong():
    scenes = [_scene(description="a beautiful modern room",
                     shot_intent="a deliberately still master to hold the silence")]
    assert check_scene_variation(scenes)["verdict"] == "strong"


def test_generic_single_scene_marked_hero_stays_strong():
    scenes = [_scene(description="a beautiful modern room", hero_moment=True)]
    assert check_scene_variation(scenes)["verdict"] == "strong"


def test_specific_minimal_scene_is_not_flagged():
    # A concrete, non-generic single scene (e.g. a real establisher) must stay 'strong' —
    # minimalism alone is not poverty. Protects legitimate short plans from false positives.
    scenes = [_scene(description="rain-slicked Yerevan crossing at dawn, tram cables overhead")]
    assert check_scene_variation(scenes)["verdict"] == "strong"


def test_many_generic_scenes_still_revise_or_fail():
    scenes = [_scene(id=f"s{i}", description="a beautiful modern dynamic vibrant stunning scene")
              for i in range(6)]
    assert check_scene_variation(scenes)["verdict"] in ("revise", "fail")


def test_gatechain_surfaces_needs_human_non_silently():
    plan = {"version": "1.0", "scenes": [_scene(
        description="a beautiful modern room, sleek design",
        text_policy={"mode": "overlay", "language": "en", "text": "Your weekend"})]}
    out = run_scene_plan_gates(plan)
    assert out["variation"] == "needs_human"
    assert not out["ok"]  # must not auto-pass a short/generic plan
    assert any("owner decision" in v for v in out["violations"])


def test_gatechain_passes_specific_single_scene():
    plan = {"version": "1.0", "scenes": [_scene(
        description="rain-slicked Yerevan crossing at dawn, tram cables overhead",
        text_policy={"mode": "overlay", "language": "en", "text": "Your weekend"})]}
    out = run_scene_plan_gates(plan)
    assert out["ok"], out["violations"]
