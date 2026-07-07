"""Performance loop — publish+48h results become structural input to the next concept.

The strategy audit's missing layer: governance protects against spoiling, but nothing
teaches the system what WORKS in the market. Two pieces:

1. ``save_performance_brief()`` — stores the schema-validated publish+48h record under
   the performance directory (``library/performance/`` by default; the
   ``ZAVOD_PERFORMANCE_DIR`` env var overrides — tests point it at a tmp dir).
2. The coupling rule: once >=3 briefs exist, every NEW ``concept_selection`` decision
   must carry ``performance_refs`` covering the latest 3 published items — performance
   stops being a "we learned" sentence and becomes a checked input to the next choice.
   Enforced at the decision-log merge seam (checkpoint.py). With fewer than 3 briefs the
   rule is dormant: the loop has to warm up before it can bind.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from schemas.artifacts import validate_artifact

_DEFAULT_DIR = Path(__file__).resolve().parent.parent / "library" / "performance"
REQUIRED_REFS = 3


def performance_dir() -> Path:
    override = os.environ.get("ZAVOD_PERFORMANCE_DIR")
    return Path(override) if override else _DEFAULT_DIR


def save_performance_brief(brief: dict[str, Any]) -> Path:
    """Persist one schema-valid performance brief. Duplicate ids are a rewrite — refused."""
    validate_artifact("performance_brief", brief)
    pdir = performance_dir()
    pdir.mkdir(parents=True, exist_ok=True)
    path = pdir / f"{brief['performance_id']}.json"
    if path.exists():
        raise ValueError(
            f"performance brief {brief['performance_id']!r} already exists — "
            "history is append-only; use a new performance_id."
        )
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(brief, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)
    return path


def latest_performance_ids(n: int = REQUIRED_REFS) -> list[str]:
    """The n most recently published performance ids (by published_at)."""
    pdir = performance_dir()
    if not pdir.exists():
        return []
    briefs = []
    for p in pdir.glob("*.json"):
        try:
            b = json.load(open(p))
            briefs.append((str(b.get("published_at") or ""), str(b.get("performance_id") or "")))
        except Exception:
            continue
    briefs.sort(reverse=True)
    return [pid for _, pid in briefs[:n] if pid]


def concept_refs_violation(decision: dict[str, Any]) -> str | None:
    """The coupling rule for one concept_selection decision, or None when satisfied.

    Dormant until the loop has >=3 published briefs; after that, a concept decision that
    does not reference ALL of the latest 3 performance ids is blocked — choosing the next
    direction while ignoring what just happened is exactly the failure this closes.
    """
    if decision.get("category") != "concept_selection":
        return None
    latest = latest_performance_ids()
    if len(latest) < REQUIRED_REFS:
        return None
    refs = {
        str(r.get("performance_id"))
        for r in decision.get("performance_refs") or []
        if isinstance(r, dict)
    }
    missing = [pid for pid in latest if pid not in refs]
    if missing:
        return (
            f"concept_selection {decision.get('decision_id')!r} ignores the latest "
            f"published results {missing} — every new concept decision must reference "
            f"the last {REQUIRED_REFS} performance briefs (performance_refs)."
        )
    return None
