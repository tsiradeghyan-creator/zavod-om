"""Production metrics — the measurement layer the strategy audit demanded (2026-07-07).

Governance is worth its cost only if measured on real production flow. Two instruments:

1. **Gate-block log** (`<project_dir>/gate_blocks.json`) — every hard block is recorded
   and CLASSIFIED so gates earn their keep with evidence, not vibes:
     - ``real_defect``       — had it not blocked, the owner/audience would have seen a
                               real problem in the published result;
     - ``blocked_formality`` — the requirement is right in general, but this production's
                               result would not have been worse without it;
     - ``false_block``       — the gate was wrong; the artifact was legitimate and should
                               have passed unchanged.
   Decision rule for classifiers: "would the problem have reached the published result?"

2. **Production metrics CSV** (`library/production_metrics.csv`) — one row per finished
   production, the six agreed metrics. Operational definitions:
     - idea_to_first_preview_minutes: owner approves the brief -> first watchable preview
       file is sent to the owner;
     - owner_revision_rounds: one round = owner feedback that requires a NEW preview
       (comments within the same round do not count);
     - gate_blocks_total: hard blocks that stopped progress;
     - false_block_minutes: sum of duration_minutes over false_block-classified entries;
     - missed_defects_count: defects an EXISTING gate should have caught but that reached
       the owner preview (recorded by owner at preview or agent at postmortem);
     - first_preview_accepted: owner allows publish or asks only caption-level tweaks.

The simplify-or-warn policy: if a gate's blocks are >=50% blocked_formality over the
measurement window, that gate is a simplification candidate (surfaced by gate_report()).
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CLASSIFICATIONS = ("real_defect", "blocked_formality", "false_block")
CLASSIFIERS = ("owner", "agent")

_LIB_DIR = Path(__file__).resolve().parent.parent / "library"
METRICS_CSV = _LIB_DIR / "production_metrics.csv"

CSV_FIELDS = [
    "project_id", "format", "idea_to_first_preview_minutes", "owner_revision_rounds",
    "gate_blocks_total", "false_block_minutes", "missed_defects_count",
    "first_preview_accepted",
]


class MetricsError(ValueError):
    """A metrics record that violates the measurement contract."""


def _blocks_path(project_dir: Path | str) -> Path:
    return Path(project_dir) / "gate_blocks.json"


def record_gate_block(
    project_dir: Path | str,
    *,
    gate: str,
    stage: str,
    classification: str,
    classifier: str,
    evidence: str,
    resolution_action: str = "",
    duration_minutes: float = 0.0,
    would_have_reached_owner_preview: bool | None = None,
) -> dict[str, Any]:
    """Record one classified gate block for the project. Classification is a closed enum —
    free-text-only reasons don't aggregate, and the whole point is comparability."""
    if classification not in CLASSIFICATIONS:
        raise MetricsError(
            f"classification {classification!r} is not one of {CLASSIFICATIONS} — "
            "an unclassified block cannot be measured."
        )
    if classifier not in CLASSIFIERS:
        raise MetricsError(f"classifier {classifier!r} must be one of {CLASSIFIERS}.")
    if not str(evidence).strip():
        raise MetricsError("a gate block needs evidence — what exactly was blocked?")
    path = _blocks_path(project_dir)
    blocks: list[dict[str, Any]] = []
    if path.exists():
        try:
            blocks = json.load(open(path)).get("blocks", [])
        except Exception:
            blocks = []
    entry = {
        "block_id": f"gb_{len(blocks) + 1:03d}",
        "gate": gate,
        "stage": stage,
        "blocked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration_minutes": float(duration_minutes),
        "classification": classification,
        "classifier": classifier,
        "evidence": evidence,
        "resolution_action": resolution_action,
        "would_have_reached_owner_preview": would_have_reached_owner_preview,
    }
    blocks.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump({"blocks": blocks}, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)
    return entry


def gate_block_summary(project_dir: Path | str) -> dict[str, Any]:
    """Totals the CSV row needs, derived from the block log — not hand-entered."""
    path = _blocks_path(project_dir)
    if not path.exists():
        return {"gate_blocks_total": 0, "false_block_minutes": 0.0, "by_gate": {}}
    blocks = json.load(open(path)).get("blocks", [])
    by_gate: dict[str, dict[str, int]] = {}
    false_minutes = 0.0
    for b in blocks:
        g = by_gate.setdefault(b.get("gate", "?"), {c: 0 for c in CLASSIFICATIONS})
        cls = b.get("classification")
        if cls in g:
            g[cls] += 1
        if cls == "false_block":
            false_minutes += float(b.get("duration_minutes") or 0)
    return {"gate_blocks_total": len(blocks),
            "false_block_minutes": round(false_minutes, 1),
            "by_gate": by_gate}


def gate_report(project_dirs: list[Path | str]) -> list[str]:
    """Simplification candidates across a window of productions: gates whose blocks are
    >=50% blocked_formality (the agreed simplify-or-warn policy)."""
    totals: dict[str, dict[str, int]] = {}
    for pd in project_dirs:
        for gate, counts in gate_block_summary(pd)["by_gate"].items():
            t = totals.setdefault(gate, {c: 0 for c in CLASSIFICATIONS})
            for c in CLASSIFICATIONS:
                t[c] += counts.get(c, 0)
    out = []
    for gate, t in sorted(totals.items()):
        n = sum(t.values())
        if n and t["blocked_formality"] / n >= 0.5:
            out.append(f"{gate}: {t['blocked_formality']}/{n} blocks were formality — "
                       "simplification candidate (move to warning or narrow the rule)")
    return out


def record_production_row(
    *,
    project_id: str,
    format: str,
    idea_to_first_preview_minutes: float,
    owner_revision_rounds: int,
    missed_defects_count: int,
    first_preview_accepted: bool,
    project_dir: Path | str | None = None,
    csv_path: Path | str = METRICS_CSV,
) -> dict[str, Any]:
    """Append one production's row. Block totals come FROM the gate-block log when the
    project_dir is given — the two instruments must not disagree."""
    summary = (gate_block_summary(project_dir)
               if project_dir is not None
               else {"gate_blocks_total": 0, "false_block_minutes": 0.0})
    row = {
        "project_id": project_id,
        "format": format,
        "idea_to_first_preview_minutes": round(float(idea_to_first_preview_minutes), 1),
        "owner_revision_rounds": int(owner_revision_rounds),
        "gate_blocks_total": summary["gate_blocks_total"],
        "false_block_minutes": summary["false_block_minutes"],
        "missed_defects_count": int(missed_defects_count),
        "first_preview_accepted": bool(first_preview_accepted),
    }
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not csv_path.exists()
    with open(csv_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if is_new:
            w.writeheader()
        w.writerow(row)
    return row


def stopping_criterion_met(csv_path: Path | str = METRICS_CSV) -> dict[str, Any]:
    """The agreed hardening-stop rule: 5 consecutive productions with first-preview
    acceptance >=80%, total missed defects <=1. (False-block share of production time
    needs the time denominators, so it is reported, not judged, here.)"""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        return {"met": False, "reason": "no productions measured yet"}
    rows = list(csv.DictReader(open(csv_path)))
    last5 = rows[-5:]
    if len(last5) < 5:
        return {"met": False, "reason": f"only {len(last5)} production(s) measured"}
    accepted = sum(1 for r in last5 if r["first_preview_accepted"] == "True")
    missed = sum(int(r["missed_defects_count"]) for r in last5)
    met = accepted / 5 >= 0.8 and missed <= 1
    return {"met": met, "acceptance": accepted / 5, "missed_defects": missed,
            "false_block_minutes": sum(float(r["false_block_minutes"]) for r in last5)}
