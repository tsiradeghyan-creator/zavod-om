"""ZavodOM health-check — the council's #1 ask: a human-readable session-start signal.

Run at the top of any session: `./.venv/bin/python lib/healthcheck.py`.
Answers in ~seconds: is the brain present, are the gates live, do the manifests/schemas
validate, is render reachable, is the Scout registry there. Prints GREEN/RED per item so
failures are visible to a human instead of silently drifting.
"""

from __future__ import annotations

import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OK, BAD = "✅", "❌"


def _corpus():
    # the brain's voice source (style-profile.md derives from it)
    cands = [os.path.expanduser("~/Documents/Maghakian-Scripts/docx"),
             os.path.expanduser("~/Documents/Maghakian-Scripts/txt")]
    hit = [c for c in cands if os.path.isdir(c) and os.listdir(c)]
    return (bool(hit), f"{len(glob.glob(hit[0]+'/*'))} files in {hit[0]}" if hit else "NOT FOUND (style-profile source) — back it up")


def _brain():
    d = os.path.join(ROOT, "skills/zavod-craft")
    files = glob.glob(d + "/*.md")
    craft = [
        p for p in files
        if os.path.basename(p) not in {"SKILL.md", "INDEX.md"}
    ]
    return (
        len(craft) >= 40 and os.path.exists(d + "/INDEX.md"),
        f"{len(craft)} craft files + SKILL + INDEX" if craft else "missing",
    )


def _ffmpeg():
    from lib.continuity_checker import find_ffmpeg
    f = find_ffmpeg()
    return (bool(f), f or "NOT FOUND — render/continuity sampling will fail")


def _manifests():
    from lib.pipeline_loader import load_pipeline
    names = [os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, "pipeline_defs/zavod-*.yaml"))]
    bad = []
    for n in names:
        try:
            load_pipeline(n)
        except Exception as e:
            bad.append(f"{n}({e.__class__.__name__})")
    return (not bad and bool(names), f"{len(names)} zavod manifests valid" if not bad else f"INVALID: {bad}")


def _gates():
    from lib.armenian_glyph_gate import gate as glyph
    from lib.continuity_checker import verdict as cont
    from lib.brand_voice_check import check as voice
    g = glyph({"t": "Vanը"})["verdict"] == "fail"
    c = cont({"anchors": [{"name": "x", "kind": "object", "persists": False}]})["verdict"] == "fail"
    v = voice("unlock revolutionary cutting-edge seamless")["verdict"] == "revise"
    native = []
    for m in ("lib.delivery_promise", "lib.variation_checker", "lib.verify_scene_pacing"):
        __import__(m)
        native.append(m.split(".")[-1])
    allok = g and c and v
    return (allok, f"glyph/continuity/brand_voice live; native: {','.join(native)}" if allok else "a gate failed self-check")


def _schemas():
    import jsonschema
    files = glob.glob(os.path.join(ROOT, "schemas/artifacts/*.json"))
    bad = []
    for f in files:
        try:
            jsonschema.Draft202012Validator.check_schema(json.load(open(f)))
        except Exception:
            bad.append(os.path.basename(f))
    return (not bad, f"{len(files)} artifact schemas valid" if not bad else f"INVALID: {bad}")


def _enforcement():
    # the wiring that makes gates non-bypassable: a dirty zavod checkpoint MUST be blocked.
    from lib.checkpoint import _enforce_zavod_gates, CheckpointValidationError
    dirty = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "completed",
             "artifacts": {"continuity_report": {"clip": "c.mp4",
                "anchors": [{"name": "glass", "kind": "object", "persists": False}]}}}
    try:
        _enforce_zavod_gates(dirty)
        return (False, "NOT WIRED — a broken zavod checkpoint was NOT blocked")
    except CheckpointValidationError:
        # and an upstream pipeline must remain ungated
        ok_up = {"pipeline_type": "cinematic", "stage": "compose", "status": "completed",
                 "artifacts": {"continuity_report": {"clip": "c.mp4",
                    "anchors": [{"name": "glass", "kind": "object", "persists": False}]}}}
        _enforce_zavod_gates(ok_up)  # must NOT raise
        return (True, "checkpoint seam blocks dirty zavod artifacts; upstream untouched")


def _scout():
    p = os.path.join(ROOT, "library/known_capabilities.json")
    if not os.path.exists(p):
        return (False, "known_capabilities.json missing")
    reg = json.load(open(p))
    n = sum(len(v) for v in reg.get("capabilities", {}).values())
    return (n > 0, f"{n} known capabilities (Scout dedup ready)")


def _style_radar():
    # the living visual-taste registry (style Scout dedups against it)
    p = os.path.join(ROOT, "library/style_radar.json")
    if not os.path.exists(p):
        return (False, "style_radar.json missing")
    reg = json.load(open(p))
    axes = reg.get("capabilities", {})
    n = sum(len(v) for v in axes.values())
    cards = len(glob.glob(os.path.join(ROOT, "skills/zavod-craft/style-library/*.md")))
    return (n > 0, f"{n} styles across {len(axes)} axes, {cards} matured cards (Style Radar ready)")


def _production_sequence():
    from lib.pipeline_loader import load_pipeline, get_stage_order

    required = {
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
    problems = []
    for name, expected in required.items():
        manifest = load_pipeline(name)
        order = set(get_stage_order(manifest, include_sub_stages=True))
        problems.extend(f"{name}:{item} missing" for item in sorted(expected - order))
        # Every owner-gated sub-stage must be artifact-backed (produces) so the ladder
        # is enforceable at the checkpoint seam, not merely named in prose.
        for stage in manifest["stages"]:
            for ss in stage.get("sub_stages", []):
                if ss.get("human_approval_default", True) and not ss.get("produces"):
                    problems.append(f"{name}:{stage['name']}.{ss['name']} not artifact-backed")
    msg = (
        "reel/promo specialist ladders wired + artifact-backed (non-collapsible)"
        if not problems else f"{problems}"
    )
    return (not problems, msg)


def _engine_lanes():
    """Both lanes declared and mutually exclusive: Remotion (no AI footage) vs Higgsfield
    (zero Remotion, ffmpeg compose). Mirrors lib/checkpoint.LANE_COMPOSE_RUNTIMES."""
    from lib.pipeline_loader import load_pipeline
    problems = []
    for name in ("zavod-reel", "zavod-promo"):
        pe = load_pipeline(name).get("metadata", {}).get("production_engine", {})
        lanes = pe.get("lanes", {})
        if not pe.get("ask_at_start"):
            problems.append(f"{name}: production_engine.ask_at_start not set")
        for lane in ("remotion", "higgsfield"):
            if lane not in lanes:
                problems.append(f"{name}: lane {lane!r} missing")
        if lanes.get("higgsfield", {}).get("compose_runtime") != ["ffmpeg"]:
            problems.append(f"{name}: higgsfield lane must compose via [ffmpeg] (zero Remotion)")
        if "higgsfield" not in (lanes.get("remotion", {}).get("forbids") or []):
            problems.append(f"{name}: remotion lane must forbid higgsfield")
    return (not problems, "remotion/higgsfield lanes separated (ask-first, no cross-lane)" if not problems else f"{problems}")


# Named checks (label, fn) — the full production profile, in display order.
_ALL_CHECKS = [
    ("corpus (voice source)", _corpus),
    ("brain (craft files)", _brain),
    ("render (ffmpeg)", _ffmpeg),
    ("pipelines", _manifests),
    ("gates", _gates),
    ("enforcement seam", _enforcement),
    ("schemas", _schemas),
    ("scout registry", _scout),
    ("style radar", _style_radar),
    ("production sequence", _production_sequence),
    ("engine lanes", _engine_lanes),
]

# What a trend-scan actually needs. The Scout / Style-Radar weekly scans only web-scan and
# write a GATED memo — they touch neither the corpus nor the render binary — so excluding the
# TCC-protected corpus (~/Documents) and ffmpeg lets the launchd scan run GREEN even before
# Full Disk Access is granted, while still refusing to act on a genuinely broken tree
# (gates / schemas / enforcement / registries must still pass).
_SCAN_EXCLUDE = {"corpus (voice source)", "render (ffmpeg)"}


def evaluate(checks: list | None = None) -> list[tuple[bool, str]]:
    out: list[tuple[bool, str]] = []
    for label, fn in (checks if checks is not None else _ALL_CHECKS):
        try:
            ok, detail = fn()
        except Exception as e:  # never let the health-check itself crash
            ok, detail = False, f"error: {e}"
        out.append((ok, f"{label}: {detail}"))
    return out


def scan_safe_ok() -> tuple[bool, list[str]]:
    """Lighter gate for the weekly scans: full profile minus the TCC-gated corpus and the
    render binary. Returns (ok, [red lines])."""
    res = evaluate([c for c in _ALL_CHECKS if c[0] not in _SCAN_EXCLUDE])
    reds = [line for ok, line in res if not ok]
    return (not reds, reds)


if __name__ == "__main__":
    results = evaluate()
    print("\n  ZavodOM health-check\n  " + "-" * 24)
    for ok, line in results:
        print(f"  {OK if ok else BAD} {line}")
    reds = [l for ok, l in results if not ok]
    print("  " + "-" * 24)
    print(f"  {'ALL GREEN' if not reds else str(len(reds)) + ' RED — fix before producing'}\n")
    sys.exit(0 if not reds else 1)
