"""Bench gate — full-bench enforcement (owner standing order, 2026-07-03).

The failure it encodes: during «Մոռացողը» the minimal-bench mode let stages advance with
specialists silently skipped — wardrobe/location/style questions surfaced only when the
owner asked "did my specialists work on this?", and the visual bar collapsed because the
maker graded his own homework. The owner's standing order: EVERY stage summons its FULL
bench, every specialist leaves a substantive ruling, no stage closes without them.

A stage's bench report is an artifact:
    {"stage": "scene",
     "bench": {"scene-director": {"ruling": "...", "craft": ["director-craft.md", ...]},
               "cinematographer": {"ruling": "..."}, ...}}

run_bench_gates(stage, report) fails if any required role is missing or its ruling is
shorter than RULING_MIN chars (a rubber-stamp is not a ruling).
"""

from __future__ import annotations

from typing import Any

RULING_MIN = 60

# Stage -> required bench roles (derived from skills/zavod-craft/INDEX.md stage->craft map).
STAGE_BENCH: dict[str, list[str]] = {
    "idea": ["idea-director", "serial-architect", "research-consultant", "reviewer"],
    "script": ["script-director", "voice-keeper", "brand-voice-guard", "reviewer"],
    "scene": ["scene-director", "cinematographer", "production-designer", "costume-designer",
              "background-environment-artist", "colorist", "style-rider-keeper", "reviewer"],
    "asset": ["asset-director", "background-environment-artist", "identity-guard",
              "style-rider-keeper", "prompt-engineer", "reviewer"],
    "edit": ["edit-director", "editor-final-catch", "compositor", "reviewer"],
    "compose": ["compose-director", "sound-designer", "voice-director", "final-mixer",
                "delivery-qc", "reviewer"],
    "publish": ["publish-director", "growth-analyst", "reviewer"],
}


def required_bench(stage: str) -> list[str]:
    return STAGE_BENCH.get(stage, ["reviewer"])


def run_bench_gates(stage: str, report: dict[str, Any]) -> dict[str, Any]:
    bench = report.get("bench", {})
    violations: list[str] = []
    for role in required_bench(stage):
        entry = bench.get(role)
        if entry is None:
            violations.append(f"bench.{role}: MISSING — the specialist never worked this stage")
            continue
        ruling = (entry.get("ruling") or "").strip()
        if len(ruling) < RULING_MIN:
            violations.append(
                f"bench.{role}: ruling too thin ({len(ruling)} chars < {RULING_MIN}) — "
                "a rubber-stamp is not a ruling")
    return {"ok": not violations, "verdict": "pass" if not violations else "fail",
            "violations": violations}


if __name__ == "__main__":
    demo_bad = {"bench": {"scene-director": {"ruling": "ok"}}}
    print("scene / thin bench ->", run_bench_gates("scene", demo_bad)["violations"][:2])
