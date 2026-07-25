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


def run_bench_gates(stage: str, bench_report: dict[str, Any],
                    pipeline_type: str | None = None) -> dict[str, Any]:
    """Full-bench gate (owner standing order 2026-07-03): no zavod stage closes until every
    required specialist for that stage has left a substantive ruling. See lib/bench_gate.py.
    ``pipeline_type`` lets a manifest declare its own (lighter) bench — fast lanes."""
    from lib.bench_gate import run_bench_gates as _rb
    return _rb(stage, bench_report, pipeline_type)


def run_story_gates(story_bible: dict[str, Any]) -> dict[str, Any]:
    """Dramaturgy gate (2026-07-03): a serial/film production cannot pass the script stage
    without a complete story bible — full secret chronology, a defensible counter-idea
    carrier, a personal cost per character, and an era decision absorbed upstream."""
    try:
        jsonschema.validate(story_bible, _schema("story_bible"))
        return {"ok": True, "verdict": "pass", "violations": []}
    except jsonschema.ValidationError as e:
        path = ".".join(str(p) for p in e.absolute_path) or "(root)"
        return {"ok": False, "verdict": "fail", "violations": [f"story_bible.{path}: {e.message}"]}


def run_canon_guard(project_dir: str, stage: str) -> dict[str, Any]:
    """Mid-pipeline canon-change check (see lib/canon_guard.py)."""
    from lib.canon_guard import check as canon_check
    r = canon_check(project_dir, stage)
    return {"ok": r["ok"], "verdict": "pass" if r["ok"] else "fail",
            "violations": [] if r["ok"] else [r["action"]]}


def run_script_gates(script_text: str, *, allow_cyrillic_code_switch: bool = False) -> dict[str, Any]:
    if allow_cyrillic_code_switch:
        from lib.authorial_voice import authorial_glyph_gate
        g = authorial_glyph_gate(script_text)
    else:
        g = glyph_gate(script_text)
    v = brand_voice(script_text)
    violations = list(g["violations"]) + (v["flags"] if not v["ok"] else [])
    return {"ok": g["ok"] and v["ok"], "glyph": g["verdict"], "brand_voice": v["verdict"], "violations": violations}


def run_rights_gates(rights_manifest: dict[str, Any],
                     publish_log: dict[str, Any] | None = None) -> dict[str, Any]:
    """Final-delivery rights and provenance gate.

    Draft/pending-review exports may exist without this gate.  Once a publish log declares
    a real publish or final export, every rights row must be usable, consent-sensitive assets
    need evidence, and the AI disclosure decision must be closed.
    """
    violations: list[str] = []
    try:
        jsonschema.validate(rights_manifest, _schema("rights_manifest"))
    except jsonschema.ValidationError as exc:
        path = ".".join(str(p) for p in exc.absolute_path) or "(root)"
        return {
            "ok": False,
            "verdict": "fail",
            "violations": [f"rights_manifest.{path}: {exc.message}"],
        }

    entries = rights_manifest.get("entries") or []
    if not entries:
        violations.append("rights_manifest.entries is empty — final delivery has no chain-of-title evidence")
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        asset_id = entry.get("asset_id", "asset")
        status = entry.get("status")
        if status in {"unknown", "blocked", "legal_review"}:
            violations.append(f"rights {asset_id!r}: status {status!r} cannot reach final delivery")
        if status == "limited" and not (entry.get("constraints") or []):
            violations.append(f"rights {asset_id!r}: limited status must name its constraints")
        if entry.get("asset_type") == "likeness" and not entry.get("likeness_consent_id"):
            violations.append(f"rights {asset_id!r}: likeness has no consent id")
        if entry.get("asset_type") == "voice" and not entry.get("voice_consent_id"):
            violations.append(f"rights {asset_id!r}: voice has no consent id")
        if entry.get("model"):
            if not entry.get("model_terms_url"):
                violations.append(f"rights {asset_id!r}: AI model use has no terms source URL")
            if not entry.get("model_terms_snapshot_sha256"):
                violations.append(
                    f"rights {asset_id!r}: AI model use has no pinned terms snapshot hash"
                )

    disclosure = rights_manifest.get("ai_disclosure") or {}
    if disclosure.get("decision") == "pending":
        violations.append("AI disclosure decision is still pending")
    if disclosure.get("required") and disclosure.get("decision") != "label":
        violations.append("AI disclosure is required but the decision is not 'label'")
    if disclosure.get("decision") == "label" and not str(disclosure.get("label_text") or "").strip():
        violations.append("AI disclosure decision is 'label' but label_text is empty")

    if publish_log:
        final_entries = [
            item for item in publish_log.get("entries") or []
            if isinstance(item, dict) and item.get("status") in {"published", "exported"}
        ]
        if final_entries:
            if not rights_manifest.get("approved_by"):
                violations.append("final publish/export has no rights_manifest.approved_by")
            if not rights_manifest.get("approved_at"):
                violations.append("final publish/export has no rights_manifest.approved_at")

    return {
        "ok": not violations,
        "verdict": "pass" if not violations else "fail",
        "violations": violations,
    }


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
    elif var["verdict"] == "needs_human":
        # #9: a short/generic plan must not auto-close 'strong' — surface it for an owner
        # decision (not a silent pass, not a permanent hard reject).
        violations += ["variation: short/generic plan needs an owner decision — "
                       + "; ".join(var.get("suggestions", [])[-1:])]
    return {"ok": schema_ok and not violations, "schema": schema_ok, "variation": var["verdict"], "violations": violations}


def run_edit_gates(edit_decisions: dict[str, Any],
                   delivery_promise: dict[str, Any] | None = None) -> dict[str, Any]:
    """Edit-stage gate: delivery-promise preservation.

    The most damaging silent failure after 06-18 is a motion-led promise quietly becoming
    a slideshow. The locked promise (DeliveryPromise.to_dict()) travels in
    ``artifacts.delivery_promise``; Zavod edit-stage checkpoints must carry that
    artifact, and the cuts must honor it.
    """
    violations: list[str] = []
    if delivery_promise:
        from lib.delivery_promise import DeliveryPromise
        try:
            promise = DeliveryPromise.from_dict(delivery_promise)
        except Exception as exc:
            violations.append(f"delivery_promise: invalid promise artifact ({exc})")
        else:
            res = promise.validate_cuts((edit_decisions or {}).get("cuts", []))
            if not res["valid"]:
                violations += [f"delivery_promise: {v}" for v in res["violations"]]
    return {"ok": not violations,
            "verdict": "pass" if not violations else "fail",
            "violations": violations}


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

    Round-6 #2 (external audit №7): presence of a report is not proof of a check. A report
    with zero anchors "passed" trivially (nothing judged → no violations), and a report
    missing the identity anchor never looked at the one dimension every clip has. Both are
    structural inadequacy of the REPORT — a hard fail, not a pending human judgment — so a
    hollow report blocks awaiting_human too. The documented builder
    (continuity_checker.build_review_request) always emits the identity anchor.
    """
    violations: list[str] = []
    pending: list[str] = []
    for r in continuity_reports:
        clip = r.get("clip", "clip")
        anchors = [a for a in (r.get("anchors") or []) if isinstance(a, dict)]
        if not anchors:
            violations.append(f"{clip}: continuity report carries no anchors — nothing was actually checked")
            continue
        if not any(a.get("kind") == "identity" for a in anchors):
            violations.append(f"{clip}: continuity report lacks the mandatory identity anchor")
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
