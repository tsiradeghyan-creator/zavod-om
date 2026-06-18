"""Continuity gate — object-permanence + identity check across a generated clip.

This is the code answer to the 2026-06-18 failure: Kling dropped a champagne glass
mid-jump and it shipped because QC looked at 5 sparse stills and over-claimed "clean."
This gate forces a DENSE, structured pass over every generated clip, keyed to the
`staging.in_hand_objects` (+ identity) declared in the scene_plan.

Two layers:
  1. Deterministic (runs anywhere): discover a working ffmpeg, sample N frames evenly.
  2. Judgment (delegated to the runtime VLM = the agent): for each declared anchor, mark
     whether it persists across the sampled frames. Pure code cannot judge arbitrary
     object-permanence without a model, so the checker builds the review request and
     gates on the filled-in report. Honest by design.

verdict contract (matches the other gates):
    {"ok": bool, "verdict": "pass"|"fail"|"needs_human", "violations": [...]}
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
from typing import Any


def find_ffmpeg() -> str | None:
    """Portable ffmpeg discovery (works on any OS, no macOS-15 dependency)."""
    env = os.environ.get("FFMPEG_BIN")
    if env and os.path.exists(env):
        return env
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:  # bundled fallback if installed
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def probe_duration(video: str, ffmpeg: str) -> float:
    out = subprocess.run([ffmpeg, "-i", video], capture_output=True, text=True).stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", out)
    if not m:
        return 0.0
    h, mn, s = m.groups()
    return int(h) * 3600 + int(mn) * 60 + float(s)


def sample_frames(video: str, n: int = 8, out_dir: str | None = None) -> list[str]:
    """Sample n evenly-spaced frames; returns jpg paths. Dense enough to catch drops."""
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("No ffmpeg found (set FFMPEG_BIN, install ffmpeg, or pip install imageio-ffmpeg).")
    dur = probe_duration(video, ffmpeg) or 5.0
    out_dir = out_dir or tempfile.mkdtemp(prefix="continuity_")
    paths: list[str] = []
    for i in range(n):
        t = dur * (i + 0.5) / n
        p = os.path.join(out_dir, f"f{i:02d}.jpg")
        subprocess.run(
            [ffmpeg, "-y", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-q:v", "3", p],
            capture_output=True,
        )
        if os.path.exists(p):
            paths.append(p)
    return paths


def build_review_request(video: str, scene: dict[str, Any], n: int = 8) -> dict[str, Any]:
    """Build the structured request the agent (VLM) fills in by LOOKING at the frames.

    Anchors come from the scene's staging.in_hand_objects (must persist) plus identity.
    """
    staging = scene.get("staging", {}) or {}
    anchors = [{"name": o, "kind": "object", "persists": None, "note": ""}
               for o in staging.get("in_hand_objects", [])]
    anchors.append({"name": "subject identity (same people/wardrobe)", "kind": "identity", "persists": None, "note": ""})
    anchors.append({"name": "real property (pool/architecture/trees unchanged)", "kind": "architecture", "persists": None, "note": ""})
    frames = sample_frames(video, n)
    return {
        "clip": os.path.basename(video),
        "frames": frames,
        "anchors": anchors,
        "instruction": (
            "Look at EVERY sampled frame in order. For each anchor set persists=true only if it is "
            "present/consistent across the whole clip. If an in-hand object appears then vanishes, or "
            "identity/architecture changes, set persists=false and describe where. Be strict — this is "
            "the gate that the 06-18 disappearing-glass bug failed."
        ),
    }


def verdict(report: dict[str, Any]) -> dict[str, Any]:
    """Gate on a filled-in continuity report. Any dropped anchor → fail; unfilled → needs_human."""
    anchors = report.get("anchors", [])
    violations = []
    unresolved = False
    for a in anchors:
        if a.get("persists") is None:
            unresolved = True
        elif a.get("persists") is False:
            violations.append(f"{a['kind']}: '{a['name']}' not continuous — {a.get('note','')}".strip())
    if violations:
        return {"ok": False, "verdict": "fail", "violations": violations}
    if unresolved:
        return {"ok": False, "verdict": "needs_human", "violations": ["continuity not yet judged on all anchors"]}
    return {"ok": True, "verdict": "pass", "violations": []}


if __name__ == "__main__":
    print("ffmpeg:", find_ffmpeg() or "NOT FOUND")
    # verdict logic self-test (deterministic, runs anywhere)
    good = {"clip": "c.mp4", "anchors": [{"name": "glass", "kind": "object", "persists": True}]}
    bad = {"clip": "c.mp4", "anchors": [{"name": "glass", "kind": "object", "persists": False, "note": "vanishes at ~4s during the jump"}]}
    pend = {"clip": "c.mp4", "anchors": [{"name": "glass", "kind": "object", "persists": None}]}
    assert verdict(good)["verdict"] == "pass"
    assert verdict(bad)["verdict"] == "fail"
    assert verdict(pend)["verdict"] == "needs_human"
    print("GOOD ->", verdict(good)["verdict"])
    print("BAD  ->", verdict(bad)["verdict"], verdict(bad)["violations"])
    print("PEND ->", verdict(pend)["verdict"])
    print("continuity gate self-test: PASS")
