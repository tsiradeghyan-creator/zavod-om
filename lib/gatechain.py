"""Gate-chain — the reviewer's hard-gate dispatcher, made concrete.

The Executive Producer / reviewer calls this at each stage. It runs the right code gates
for the artifact and returns a combined verdict. This is the spine's enforcement, proven
end-to-end (see __main__: a clean artifact passes; a deliberately-broken one is rejected
with specific violations — the P1 acceptance test).
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import jsonschema  # noqa: E402
from lib.armenian_glyph_gate import gate as glyph_gate  # noqa: E402
from lib.brand_voice_check import check as brand_voice  # noqa: E402
from lib.continuity_checker import verdict as continuity_verdict  # noqa: E402
from lib.variation_checker import check_scene_variation  # noqa: E402


def _schema(name: str) -> dict:
    return json.load(open(os.path.join(ROOT, "schemas/artifacts", f"{name}.schema.json")))


def run_script_gates(script_text: str) -> dict[str, Any]:
    g = glyph_gate(script_text)
    v = brand_voice(script_text)
    violations = list(g["violations"]) + (v["flags"] if not v["ok"] else [])
    return {"ok": g["ok"] and v["ok"], "glyph": g["verdict"], "brand_voice": v["verdict"], "violations": violations}


def run_scene_plan_gates(scene_plan: dict[str, Any]) -> dict[str, Any]:
    violations: list[str] = []
    # 1. schema
    try:
        jsonschema.validate(scene_plan, _schema("scene_plan"))
        schema_ok = True
    except jsonschema.ValidationError as e:
        schema_ok = False
        violations.append(f"schema: {e.message}")
    # 2. glyph gate on EVERY on-screen text, regardless of the declared language.
    #    The gate is a no-op on pure-Latin copy, so running it unconditionally is safe
    #    and closes the bypass where Armenian text was mislabeled language!=hy.
    for sc in scene_plan.get("scenes", []):
        tp = sc.get("text_policy") or {}
        if tp.get("text"):
            g = glyph_gate(tp["text"])
            if not g["ok"]:
                violations += [f"scene {sc.get('id')}: {x['reason']}" for x in g["violations"]]
    # 3. variation (anti-slideshow / generic)
    var = check_scene_variation(scene_plan.get("scenes", []))
    if var["verdict"] in ("revise", "fail"):
        violations += [f"variation: {x}" for x in var.get("violations", [])]
    return {"ok": schema_ok and not violations, "schema": schema_ok, "variation": var["verdict"], "violations": violations}


def declared_anchors(scene_plan: dict[str, Any]) -> dict[str, list[str]]:
    """Per-scene in_hand_objects the continuity gate must verify at compose time."""
    return {sc["id"]: (sc.get("staging", {}) or {}).get("in_hand_objects", [])
            for sc in scene_plan.get("scenes", []) if sc.get("staging", {}).get("in_hand_objects")}


def run_compose_gates(continuity_reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Compose-stage continuity gate.

    Keeps "fail" (a real continuity break — hard reject) distinct from "needs_human"
    (anchors not yet judged — pause at the human checkpoint, do NOT mark completed).
    Collapsing the two would either silently pass un-judged clips or block a legitimate
    human-review pause; the pipeline's whole premise is human checkpoints, so we surface both.
    """
    violations: list[str] = []
    pending: list[str] = []
    for r in continuity_reports:
        v = continuity_verdict(r)
        if v["verdict"] == "fail":
            violations.append(f"{r.get('clip','clip')}: continuity fail — {v['violations']}")
        elif v["verdict"] == "needs_human":
            pending.append(f"{r.get('clip','clip')}: continuity needs human judgment — {v['violations']}")
    verdict = "fail" if violations else ("needs_human" if pending else "pass")
    return {"ok": verdict == "pass", "verdict": verdict, "violations": violations, "pending": pending}


if __name__ == "__main__":
    # ---- P1 acceptance: good passes, broken is rejected ----
    good_script = "Two acres of high desert. One private pool. Ten minutes from Joshua Tree."
    good_scene = {"version": "1.0", "scenes": [
        {"id": "s1", "type": "generated", "description": "cheers at the pool", "start_seconds": 0, "end_seconds": 5,
         "shot_language": {"shot_size": "wide", "camera_movement": "dolly_in"},
         "staging": {"in_hand_objects": ["champagne glass"]}, "text_policy": {"mode": "overlay", "language": "en", "text": "Your weekend."}},
        {"id": "s2", "type": "generated", "description": "twilight spa", "start_seconds": 5, "end_seconds": 10,
         "shot_language": {"shot_size": "medium", "camera_movement": "crane_up"},
         "text_policy": {"mode": "overlay", "language": "en", "text": "Desert nights."}},
    ]}
    good_cont = [{"clip": "s1.mp4", "anchors": [{"name": "champagne glass", "kind": "object", "persists": True}]}]

    bad_script = "In today's world, unlock a revolutionary, seamless escape — elevate your stay!"
    bad_scene = {"version": "1.0", "scenes": [
        {"id": "s1", "type": "generated", "description": "x", "start_seconds": 0, "end_seconds": 5,
         "shot_language": {"shot_size": "wide", "camera_movement": "static"},
         "staging": {"in_hand_objects": ["բաժակ"]}, "text_policy": {"mode": "overlay", "language": "hy", "text": "Vanը Հայկական"}},
    ]}
    bad_cont = [{"clip": "s1.mp4", "anchors": [{"name": "բաժակ", "kind": "object", "persists": False, "note": "vanishes ~4s during the jump"}]}]

    print("=== GOOD ===")
    print(" script :", run_script_gates(good_script))
    print(" scene  :", run_scene_plan_gates(good_scene))
    print(" compose:", run_compose_gates(good_cont))
    print("=== BROKEN (must be rejected) ===")
    rs, rsc, rc = run_script_gates(bad_script), run_scene_plan_gates(bad_scene), run_compose_gates(bad_cont)
    print(" script :", rs["ok"], rs["violations"][:2])
    print(" scene  :", rsc["ok"], rsc["violations"][:2])
    print(" compose:", rc["ok"], rc["violations"][:1])

    assert run_script_gates(good_script)["ok"] and run_scene_plan_gates(good_scene)["ok"] and run_compose_gates(good_cont)["ok"]
    assert not rs["ok"] and not rsc["ok"] and not rc["ok"]
    print("\nP1 gate-chain acceptance: PASS (clean passes, broken rejected end-to-end)")
