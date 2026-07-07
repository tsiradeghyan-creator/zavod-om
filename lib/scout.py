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
LIB_DIR = os.path.join(os.path.dirname(__file__), "..", "library")
DECISIONS = os.path.join(LIB_DIR, "memo_decisions.json")
ADOPTIONS = os.path.join(LIB_DIR, "adoption_ledger.json")


class AdoptionError(ValueError):
    """An adoption that violates the pre/post-change control protocol (round-6 #5)."""


def _approved_items(decisions_path: str = DECISIONS) -> dict[str, str]:
    """memo item id -> decision string, for every item whose decision starts with 'approve'."""
    if not os.path.exists(decisions_path):
        return {}
    try:
        data = json.load(open(decisions_path))
    except Exception:
        return {}
    out: dict[str, str] = {}
    for memo in data.get("decisions", {}).values():
        for item, verdict in (memo.get("items") or {}).items():
            if str(verdict).lower().startswith("approve"):
                out[item] = str(verdict)
    return out


def record_adoption(
    item_id: str,
    *,
    memo: str,
    pre_commit: str,
    post_commit: str,
    suite_passed: int,
    suite_failed: int,
    files_changed: list[str],
    decisions_path: str = DECISIONS,
    ledger_path: str = ADOPTIONS,
) -> dict[str, Any]:
    """The ONE valid way to mark a Scout finding as adopted (round-6 #5, audit №15).

    The memo/decision loop already keeps Scout from installing anything on its own, but the
    ADOPTION step — the agent wiring an approved capability in — had no pre/post-change
    control: nothing forced a green suite after the change or left a one-step rollback
    anchor. This ledger does both, fail-closed:
      - the item must carry an owner 'approve*' decision in memo_decisions.json;
      - pre and post git commits are mandatory and distinct — the adoption is ONE commit,
        so `git revert <post_commit>` is always the one-step rollback;
      - the full regression suite must have run green AFTER the change (failed == 0).
    Healthcheck cross-validates this ledger, so a hand-written entry that skips the
    protocol turns the tree RED (which also blocks the next Scout run).
    """
    verdict = _approved_items(decisions_path).get(item_id)
    if verdict is None:
        raise AdoptionError(
            f"adoption of {item_id!r} has no owner 'approve' decision in memo_decisions.json "
            "— Scout findings are adopted only after explicit approval."
        )
    if not pre_commit or not post_commit or pre_commit == post_commit:
        raise AdoptionError(
            f"adoption of {item_id!r} needs distinct pre/post commits — the post commit is "
            "the one-step rollback anchor (git revert <post_commit>)."
        )
    if suite_failed != 0 or suite_passed <= 0:
        raise AdoptionError(
            f"adoption of {item_id!r} requires the full suite green after the change "
            f"(got {suite_passed} passed / {suite_failed} failed) — a targeted new test "
            "passing while old protections regress is exactly the failure this blocks."
        )
    if not files_changed:
        raise AdoptionError(f"adoption of {item_id!r} lists no changed files.")

    entry = {
        "item": item_id,
        "memo": memo,
        "decision": verdict,
        "pre_commit": pre_commit,
        "post_commit": post_commit,
        "rollback": f"git revert {post_commit}",
        "suite": {"passed": suite_passed, "failed": suite_failed},
        "files_changed": sorted(files_changed),
        "adopted": date.today().isoformat(),
    }
    ledger = {"note": "Scout adoption ledger — every adopted finding with its rollback "
                      "anchor and post-change suite proof. Written ONLY via "
                      "lib.scout.record_adoption; healthcheck cross-validates.",
              "adoptions": []}
    if os.path.exists(ledger_path):
        try:
            ledger = json.load(open(ledger_path))
        except Exception:
            pass
    ledger.setdefault("adoptions", []).append(entry)
    with open(ledger_path, "w") as f:
        json.dump(ledger, f, indent=1, ensure_ascii=False)
    return entry


def adoption_ledger_violations(
    ledger_path: str = ADOPTIONS, decisions_path: str = DECISIONS
) -> list[str]:
    """Cross-validate the adoption ledger for healthcheck (round-6 #5).

    Every entry must reference an owner-approved item, carry distinct pre/post commits,
    and a green post-change suite. A hand-edited entry that skips the protocol is a
    violation — the tree goes RED, which also blocks the next Scout run (wake-safe gate).
    """
    if not os.path.exists(ledger_path):
        return []
    try:
        ledger = json.load(open(ledger_path))
    except Exception as e:
        return [f"adoption_ledger.json unreadable ({e})"]
    approved = _approved_items(decisions_path)
    out: list[str] = []
    for i, e in enumerate(ledger.get("adoptions", [])):
        tag = f"adoption[{i}] {e.get('item')!r}"
        if e.get("item") not in approved:
            out.append(f"{tag}: no owner approve decision")
        if not e.get("pre_commit") or not e.get("post_commit") \
                or e.get("pre_commit") == e.get("post_commit"):
            out.append(f"{tag}: missing/identical pre/post commits (no rollback anchor)")
        suite = e.get("suite") or {}
        if suite.get("failed") != 0 or not suite.get("passed"):
            out.append(f"{tag}: no green post-change suite proof")
    return out


def undecided_memos(lib_dir: str = LIB_DIR, decisions_path: str = DECISIONS) -> list[str]:
    """Memo files the owner has not decided on yet. A GATED memo with no entry in
    memo_decisions.json is decision-debt: the next scheduled run must fail LOUDLY instead
    of silently emitting a duplicate memo (2026-07-02 council ruling — silence is the
    zavod's recurring failure pattern; make it expensive)."""
    import glob as _glob
    decided: set[str] = set()
    if os.path.exists(decisions_path):
        try:
            decided = set(json.load(open(decisions_path)).get("decisions", {}))
        except Exception:
            pass  # unreadable ledger = nothing is decided; stay loud
    memos = _glob.glob(os.path.join(lib_dir, "scout_memo_*.md")) + \
        _glob.glob(os.path.join(lib_dir, "style_memo_*.md"))
    return sorted(os.path.basename(m) for m in memos if os.path.basename(m) not in decided)


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
