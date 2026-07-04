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

run_bench_gates(stage, report) fails if any required role is missing, its entry is
malformed, its ruling is shorter than RULING_MIN chars, its ruling is low-information
filler, or two roles rubber-stamp the same text. Length alone is not a ruling; the
2026-07-04 red-team showed 60 chars of repeated filler — and 8 identical copy-pasted
rulings — sailed through the length-only check. See tests/stress/REDTEAM-REPORT-2026-07-04.md.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

RULING_MIN = 60
# A ruling must carry at least this many DISTINCT word-tokens; "նույն բառը" x6 is 60 chars
# but only 2 unique tokens — a rubber-stamp, not analysis.
RULING_MIN_UNIQUE_TOKENS = 8
# Two rulings whose normalized token sets are this similar are treated as the same
# rubber-stamp pasted across roles (independence failure).
DUPLICATE_SIMILARITY = 0.92


def _norm_tokens(text: str) -> list[str]:
    """Lowercased unicode-normalized word tokens — for filler / duplicate detection."""
    text = unicodedata.normalize("NFKC", text).lower()
    return re.findall(r"\w+", text, flags=re.UNICODE)


def _similarity(a: str, b: str) -> float:
    """Token-set Jaccard similarity between two rulings (0..1)."""
    ta, tb = set(_norm_tokens(a)), set(_norm_tokens(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

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
    present: dict[str, str] = {}  # role -> ruling, for cross-role independence check

    for role in required_bench(stage):
        entry = bench.get(role)
        if entry is None:
            violations.append(f"bench.{role}: MISSING — the specialist never worked this stage")
            continue
        if not isinstance(entry, dict):
            violations.append(
                f"bench.{role}: malformed entry ({type(entry).__name__}) — expected an object "
                "with a 'ruling' field")
            continue
        ruling = (entry.get("ruling") or "").strip()

        if len(ruling) < RULING_MIN:
            violations.append(
                f"bench.{role}: ruling too thin ({len(ruling)} chars < {RULING_MIN}) — "
                "a rubber-stamp is not a ruling")
            continue

        # Low-information filler: long enough but too few distinct word-tokens
        # (e.g. one phrase repeated to clear the length bar).
        unique_tokens = len(set(_norm_tokens(ruling)))
        if unique_tokens < RULING_MIN_UNIQUE_TOKENS:
            violations.append(
                f"bench.{role}: filler ruling ({unique_tokens} distinct tokens < "
                f"{RULING_MIN_UNIQUE_TOKENS}) — repeated words are not analysis")
            continue

        # NOTE: a specialist voicing a *reject verdict* is intentionally NOT detected by
        # prose substring matching here — "nothing is blocked" / "avoided a reject" are
        # legitimate approvals that such a heuristic false-flags (2026-07-04 probe). A real
        # reject signal belongs in a structured verdict field, not sniffed from the ruling text.
        present[role] = ruling

    # Independence: no two required specialists may submit (near-)identical rulings.
    checked = list(present.items())
    for i in range(len(checked)):
        for j in range(i + 1, len(checked)):
            if _similarity(checked[i][1], checked[j][1]) >= DUPLICATE_SIMILARITY:
                violations.append(
                    f"bench.{checked[i][0]} and bench.{checked[j][0]}: identical ruling "
                    "rubber-stamped across roles — each specialist must rule independently")

    return {"ok": not violations, "verdict": "pass" if not violations else "fail",
            "violations": violations}


if __name__ == "__main__":
    demo_bad = {"bench": {"scene-director": {"ruling": "ok"}}}
    print("scene / thin bench ->", run_bench_gates("scene", demo_bad)["violations"][:2])
