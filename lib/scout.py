"""Scout — self-improvement registry + upgrade-memo builder.

The Scout loop keeps ZavodOM current: weekly it (the agent) web-searches for new models,
tools, and techniques, then uses THIS module to dedup against what we already have and to
emit a GATED upgrade memo. It never auto-installs — a human approves before anything is wired.

Pairs with skills/meta/scout.md (the weekly protocol) and library/known_capabilities.json
(the registry of what ZavodOM already knows).
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any

REGISTRY = os.path.join(os.path.dirname(__file__), "..", "library", "known_capabilities.json")


def load_registry(path: str = REGISTRY) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def known_ids(reg: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for items in reg.get("capabilities", {}).values():
        out |= {i["id"].lower() for i in items}
        out |= {a.lower() for i in items for a in i.get("aliases", [])}
    return out


def is_new(candidate_id: str, reg: dict[str, Any]) -> bool:
    return candidate_id.lower() not in known_ids(reg)


def score_finding(f: dict[str, Any]) -> float:
    """Cheap priority score (higher = more worth adopting). Agent supplies the inputs."""
    return (
        2.0 * float(f.get("capability_gain", 0))   # 0-1: does it do something we can't?
        + 1.0 * float(f.get("quality_gain", 0))    # 0-1: better than our current best?
        - 1.0 * float(f.get("cost", 0))            # 0-1: relative cost
        + 0.5 * float(f.get("license_ok", 0))      # 0/1: usable license
        + 0.5 * float(f.get("fit", 0))             # 0-1: fits our pipelines
    )


def build_memo(findings: list[dict[str, Any]], reg: dict[str, Any]) -> str:
    new = [f for f in findings if is_new(f.get("id", ""), reg)]
    new.sort(key=score_finding, reverse=True)
    lines = [f"# ZavodOM Scout — upgrade memo {date.today().isoformat()}", ""]
    if not new:
        lines.append("No genuinely new capabilities this pass. Registry already current.")
        return "\n".join(lines)
    lines.append(f"{len(new)} new candidate(s) — GATED, nothing installed. Approve to adopt.\n")
    for f in new:
        lines += [
            f"## {f.get('name', f['id'])}  (score {score_finding(f):.1f})",
            f"- id: `{f['id']}`  · source: {f.get('source','?')}",
            f"- what: {f.get('what','')}",
            f"- why adopt: {f.get('why','')}",
            f"- cost/license: {f.get('cost_note','')} / {f.get('license','?')}",
            f"- proposed: {f.get('proposed_action','draft a skill via meta/skill-creator, wire as provider')}",
            "",
        ]
    return "\n".join(lines)


if __name__ == "__main__":
    reg = load_registry()
    print("registry capabilities:", {k: len(v) for k, v in reg.get("capabilities", {}).items()})
    demo = [
        {"id": "kling3_0", "name": "Kling 3.0"},  # already known → filtered
        {"id": "some_new_v1", "name": "Some New Model", "source": "reddit",
         "what": "1-min coherent video", "why": "beats our 15s cap",
         "capability_gain": 1, "quality_gain": 0.8, "cost": 0.4, "license_ok": 1, "fit": 0.9},
    ]
    print(build_memo(demo, reg))
