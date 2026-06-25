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
results: list[tuple[bool, str]] = []


def check(name: str, fn) -> None:
    try:
        ok, detail = fn()
    except Exception as e:  # never let the health-check itself crash
        ok, detail = False, f"error: {e}"
    results.append((ok, f"{name}: {detail}"))


def _corpus():
    # the brain's voice source (style-profile.md derives from it)
    cands = [os.path.expanduser("~/Documents/Maghakian-Scripts/docx"),
             os.path.expanduser("~/Documents/Maghakian-Scripts/txt")]
    hit = [c for c in cands if os.path.isdir(c) and os.listdir(c)]
    return (bool(hit), f"{len(glob.glob(hit[0]+'/*'))} files in {hit[0]}" if hit else "NOT FOUND (style-profile source) — back it up")


def _brain():
    d = os.path.join(ROOT, "skills/zavod-craft")
    n = len(glob.glob(d + "/*.md"))
    return (n >= 40 and os.path.exists(d + "/INDEX.md"), f"{n} craft files + INDEX" if n else "missing")


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


if __name__ == "__main__":
    check("corpus (voice source)", _corpus)
    check("brain (craft files)", _brain)
    check("render (ffmpeg)", _ffmpeg)
    check("pipelines", _manifests)
    check("gates", _gates)
    check("enforcement seam", _enforcement)
    check("schemas", _schemas)
    check("scout registry", _scout)
    check("style radar", _style_radar)
    print("\n  ZavodOM health-check\n  " + "-" * 24)
    for ok, line in results:
        print(f"  {OK if ok else BAD} {line}")
    reds = [l for ok, l in results if not ok]
    print("  " + "-" * 24)
    print(f"  {'ALL GREEN' if not reds else str(len(reds)) + ' RED — fix before producing'}\n")
    sys.exit(0 if not reds else 1)
