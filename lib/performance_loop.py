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
from datetime import datetime
from pathlib import Path
from typing import Any

from schemas.artifacts import validate_artifact

_DEFAULT_DIR = Path(__file__).resolve().parent.parent / "library" / "performance"
REQUIRED_REFS = 3


def performance_dir() -> Path:
    override = os.environ.get("ZAVOD_PERFORMANCE_DIR")
    return Path(override) if override else _DEFAULT_DIR


def _parse_dt(raw: Any) -> datetime:
    """Parse an ISO-8601 timestamp. Raises ValueError on anything else.

    Round-7.1 (re-audit №10): the schema only described ``published_at`` as "ISO-8601" in
    prose — ``jsonschema.validate`` never enforces ``format`` without an explicit
    FormatChecker, so any string passed. Sorting was then lexicographic on that unchecked
    string, so a timezone offset or an unpadded date could silently reorder "latest 3" and
    couple a concept decision to the wrong results. Every timestamp is now actually parsed;
    naive timestamps are treated as UTC so mixed naive/aware brief histories still compare.
    """
    s = str(raw or "").strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)  # raises ValueError on anything non-ISO-8601
    return dt


def save_performance_brief(brief: dict[str, Any]) -> Path:
    """Persist one schema-valid performance brief. Duplicate ids are a rewrite — refused."""
    validate_artifact("performance_brief", brief)
    try:
        _parse_dt(brief.get("published_at"))
    except ValueError as exc:
        raise ValueError(
            f"performance brief {brief.get('performance_id')!r}: published_at "
            f"{brief.get('published_at')!r} is not a parseable ISO-8601 timestamp — "
            f"sorting 'latest 3' depends on it. ({exc})"
        ) from exc
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
    """The n most recently published performance ids, ordered by PARSED timestamp.

    A brief on disk with an unparseable published_at is a corrupted/hand-edited record —
    it is surfaced by raising, not silently skipped (silently dropping it would let a bad
    file quietly fall out of "latest 3" consideration, the same failure mode this closes).
    """
    pdir = performance_dir()
    if not pdir.exists():
        return []
    briefs = []
    for p in pdir.glob("*.json"):
        try:
            b = json.load(open(p))
        except Exception:
            continue
        pid = str(b.get("performance_id") or "")
        if not pid:
            continue
        try:
            dt = _parse_dt(b.get("published_at"))
        except ValueError as exc:
            raise ValueError(
                f"performance brief {p.name} has an unparseable published_at "
                f"{b.get('published_at')!r} — fix or remove it before the loop can order "
                f"'latest {n}' correctly. ({exc})"
            ) from exc
        briefs.append((dt, pid))
    briefs.sort(reverse=True)
    return [pid for _, pid in briefs[:n]]


def concept_refs_violation(decision: dict[str, Any]) -> str | None:
    """The coupling rule for one concept_selection decision, or None when satisfied.

    Dormant until the loop has >=3 published briefs; after that, a concept decision that
    does not reference ALL of the latest 3 performance ids is blocked — choosing the next
    direction while ignoring what just happened is exactly the failure this closes.

    Round-7.1 (re-audit №9): a plain subset check was gameable by padding
    ``performance_refs`` with every known performance_id — the latest 3 are trivially
    "included" without being the actual basis for the decision. Two closures:
      - every ref matching a latest-3 id must carry non-empty ``used_for`` AND ``signal``
        (schema already requires used_for; signal is enforced here);
      - every ref NOT among the latest 3 ("extras") must carry a non-empty ``rationale`` —
        padding is still possible, but each pad is now a written, auditable claim, not a
        free trivial-pass trick.
    """
    if decision.get("category") != "concept_selection":
        return None
    latest = latest_performance_ids()
    if len(latest) < REQUIRED_REFS:
        return None
    latest_set = set(latest)
    did = decision.get("decision_id")
    refs = [r for r in decision.get("performance_refs") or [] if isinstance(r, dict)]
    by_id = {str(r.get("performance_id")): r for r in refs}

    missing = [pid for pid in latest if pid not in by_id]
    if missing:
        return (
            f"concept_selection {did!r} ignores the latest published results {missing} — "
            f"every new concept decision must reference the last {REQUIRED_REFS} "
            "performance briefs (performance_refs)."
        )
    for pid in latest:
        r = by_id[pid]
        if not str(r.get("signal") or "").strip():
            return (
                f"concept_selection {did!r}: performance_refs entry for {pid!r} (one of "
                "the latest results) has no 'signal' — a real reference names what it "
                "observed, not just an id."
            )
    for pid, r in by_id.items():
        if pid in latest_set:
            continue
        if not str(r.get("rationale") or "").strip():
            return (
                f"concept_selection {did!r}: performance_refs entry for {pid!r} is not "
                "among the latest results and carries no 'rationale' — extra references "
                "must justify themselves, not just pad the list."
            )
    return None
