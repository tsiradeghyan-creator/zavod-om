"""Style Radar — the visual-taste twin of Scout.

Keeps ZavodOM's TASTE current. Weekly, the agent (an LLM with web search) scans the
sources in SCAN_SOURCES for in-demand, current visual / cinema / color-grade / montage
styles + named director/DP references, then drops findings into
`library/style_inbox.json`. This module dedups them against `library/style_radar.json`
and emits a GATED card-proposal memo. It NEVER auto-adds a style — a human approves,
then a mature card is written into `skills/zavod-craft/style-library/`.

Same contract as Scout (lib/scout.py): wake-safe, health-gated, nothing self-installs.
The registry reuses the known_capabilities.json shape, so scout.load_registry / is_new
work on it directly.

Run: `./.venv/bin/python lib/style_radar.py`   (exit 0 = ran/clean, 1 = health RED)
Dedup/score demo: `./.venv/bin/python -m lib.style_radar`
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib.scout import is_new, load_registry  # noqa: E402  (reuse Scout's dedup)

LIB_DIR = os.path.join(ROOT, "library")
REGISTRY = os.path.join(LIB_DIR, "style_radar.json")
INBOX = os.path.join(LIB_DIR, "style_inbox.json")
LOG = os.path.join(LIB_DIR, "style_radar.log")

# The exact pages the owner chose to scan (style-rider.md sections 8-11). The weekly scan
# reads ONLY these — taste updates come from these tastemakers, nothing else. Owner-set 2026-06-25.
SCAN_SOURCES = {
    "linkedin": [
        "Chris Do", "Debbie Millman", "Jessica Walsh", "Brian Collins", "Paula Scher",
        "Pentagram", "The Futur", "AIGA", "It's Nice That",
        "Brand New / UnderConsideration", "Andy Budd", "Julie Zhuo",
    ],
    "x": [
        "@chrisdo", "@jessicahische", "@brad_frost", "@maggieappleton", "@vanschneider",
        "@joulee", "@davidhoang", "@rachelnabors", "@awwwards", "@motionographer",
        "@letterboxd", "@criterion", "@A24", "@shotdeck",
    ],
    "instagram": [
        "@thebrandidentity", "@itsnicethat", "@aigaeyeondesign", "@bpando", "@designmilk",
        "@awwwards", "@motionographer", "@typewolf", "@thedesignkids",
        "@worldbranddesignsociety", "@posteritati", "@criterioncollection", "@mubi",
        "@shotdeck", "@letterboxd",
    ],
    "reddit": [
        "r/graphic_design", "r/Design", "r/typography", "r/logodesign", "r/branding",
        "r/web_design", "r/UI_Design", "r/cinematography", "r/Filmmakers", "r/editors",
        "r/colorists", "r/MotionDesign", "r/animation", "r/AfterEffects", "r/ObscureMedia",
    ],
}

# Taste axes covered by the rider (style-rider.md sections 1-7) + grading.
AXES = ("directors", "cinematographers", "montage", "animators",
        "design_styles", "production_designers", "costume_designers", "color_luts")


def score_style_finding(f: dict[str, Any]) -> float:
    """Priority for a style finding (higher = more worth a card). Agent supplies 0-1 inputs.

    Taste-tuned (not capability-tuned like Scout): reward demand + currency + brand fit +
    durability; penalize pure fad so we don't chase disposable trends.
    """
    return (
        1.5 * float(f.get("demand", 0))       # 0-1: how requested / viral right now
        + 1.0 * float(f.get("recency", 0))    # 0-1: how current to this year
        + 1.0 * float(f.get("fit", 0))        # 0-1: fits Maghakian/brand register & taste
        + 0.5 * float(f.get("durability", 0)) # 0-1: lasting language vs disposable fad
        - 0.5 * float(f.get("fad_risk", 0))   # 0-1: pure trend-bait penalty
    )


def build_style_memo(findings: list[dict[str, Any]], reg: dict[str, Any]) -> str:
    new = [f for f in findings if is_new(f.get("id", ""), reg)]
    new.sort(key=score_style_finding, reverse=True)
    lines = [f"# ZavodOM Style Radar — card-proposal memo {date.today().isoformat()}", ""]
    if not new:
        lines.append("No genuinely new styles this pass. Taste registry already current.")
        return "\n".join(lines)
    lines.append(
        f"{len(new)} new style candidate(s) — GATED, nothing added. "
        f"Approve to write a card into skills/zavod-craft/style-library/.\n"
    )
    for f in new:
        lines += [
            f"## {f.get('name', f['id'])}  (score {score_style_finding(f):.1f})",
            f"- id: `{f['id']}`  · axis: {f.get('axis','?')}  · source: {f.get('source','?')}",
            f"- essence: {f.get('essence','')}",
            f"- signature markers: {f.get('markers','')}",
            f"- Maghakian application: {f.get('maghakian','')}",
            f"- anti-pattern: {f.get('anti_pattern','')}",
            f"- proposed: {f.get('proposed_action','write a style card; wire into playbooks + prompt-builder Layer 5')}",
            "",
        ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Wake-safe driver (mirrors lib/scout_run.py): health-gate, inbox -> memo.
# --------------------------------------------------------------------------- #
def _log(line: str) -> None:
    os.makedirs(LIB_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(LOG, "a") as f:
        f.write(f"[{stamp}] {line}\n")
    print(line)


def _healthcheck_green() -> bool:
    """Scan-safe gate (see lib/scout_run._healthcheck_green): full health minus the TCC-gated
    corpus and the render binary, neither of which a scan needs."""
    from lib import healthcheck
    ok, reds = healthcheck.scan_safe_ok()
    if not ok:
        _log(f"scan-safe health RED — aborting Style Radar run (wake-safe). Red: {reds}")
    return ok


def _load_inbox() -> list[dict]:
    if not os.path.exists(INBOX):
        return []
    try:
        data = json.load(open(INBOX))
    except Exception as e:
        _log(f"style_inbox.json unreadable ({e}) — skipping memo build")
        return []
    return data if isinstance(data, list) else data.get("findings", [])


def main() -> int:
    if not _healthcheck_green():
        return 1
    findings = _load_inbox()
    if not findings:
        _log("health GREEN; no queued style findings (agent-driven scan pending) — heartbeat only.")
        return 0
    reg = load_registry(REGISTRY)
    memo = build_style_memo(findings, reg)
    out = os.path.join(LIB_DIR, f"style_memo_{datetime.now(timezone.utc):%Y-%m-%d}.md")
    with open(out, "w") as f:
        f.write(memo)
    _log(f"health GREEN; processed {len(findings)} style finding(s) → GATED memo "
         f"{os.path.basename(out)} (nothing added — owner approves to write a card).")
    return 0


if __name__ == "__main__":
    # `python lib/style_radar.py` (__spec__ is None) → run the wake-safe driver.
    # `python -m lib.style_radar` (__spec__ set)      → dedup/score demo.
    if __spec__ is None:
        sys.exit(main())
    reg = load_registry(REGISTRY)
    print("style registry axes:", {k: len(v) for k, v in reg.get("capabilities", {}).items()})
    demo = [
        {"id": "liquid_glass", "name": "Liquid Glass"},  # already known → filtered
        {"id": "claymation_grain_2026", "name": "Tactile Clay-grain", "axis": "design_styles",
         "source": "r/graphic_design", "essence": "hand-built clay textures over type",
         "demand": 0.8, "recency": 0.9, "fit": 0.6, "durability": 0.5, "fad_risk": 0.3},
    ]
    print(build_style_memo(demo, reg))
