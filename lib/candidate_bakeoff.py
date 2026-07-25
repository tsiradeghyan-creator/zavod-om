"""Fail-closed proof for blind, full-draft candidate comparisons."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from difflib import SequenceMatcher
from itertools import combinations
from typing import Any

from lib.authorial_voice import script_text
from schemas.artifacts import validate_artifact


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _normalized_text(script: dict[str, Any]) -> str:
    return " ".join(unicodedata.normalize("NFC", script_text(script)).casefold().split())


def validate_candidate_bakeoff(
    final_script: dict[str, Any], bakeoff: dict[str, Any],
) -> dict[str, Any]:
    violations: list[str] = []
    try:
        validate_artifact("candidate_bakeoff", bakeoff)
    except Exception as exc:
        return {"ok": False, "verdict": "fail", "violations": [f"schema: {exc}"]}

    candidates = bakeoff.get("candidates") or []
    by_id: dict[str, dict[str, Any]] = {}
    texts: dict[str, str] = {}
    axes: set[str] = set()
    for item in candidates:
        candidate_id = item.get("candidate_id")
        if candidate_id in by_id:
            violations.append(f"candidate id {candidate_id!r} appears more than once")
            continue
        by_id[candidate_id] = item
        draft = item.get("draft") or {}
        try:
            validate_artifact("script", draft)
        except Exception as exc:
            violations.append(f"candidate {candidate_id!r} draft is not a valid script: {exc}")
            continue
        actual_sha = canonical_sha256(draft)
        if item.get("draft_sha256") != actual_sha:
            violations.append(f"candidate {candidate_id!r} draft_sha256 does not match its draft")
        text = _normalized_text(draft)
        if not text:
            violations.append(f"candidate {candidate_id!r} has no authored text")
        texts[candidate_id] = text
        axes.update(item.get("difference_axes") or [])

    if len(set(item.get("draft_sha256") for item in candidates)) != len(candidates):
        violations.append("candidate drafts are not unique")
    if len(axes) < 2:
        violations.append("candidate set must differ across at least two declared creative axes")
    for left, right in combinations(sorted(texts), 2):
        similarity = SequenceMatcher(None, texts[left], texts[right]).ratio()
        if similarity > 0.90:
            violations.append(
                f"candidates {left!r} and {right!r} are {similarity:.1%} text-identical; "
                "this is not a material alternative"
            )

    selection = bakeoff.get("selection") or {}
    selected_id = selection.get("selected_candidate_id")
    selected = by_id.get(selected_id)
    if selected is None:
        violations.append("selected_candidate_id does not name a candidate")
    elif canonical_sha256(final_script) != selected.get("draft_sha256"):
        violations.append("final script is not byte-for-structure identical to the selected candidate")

    rejected_ids = [
        item.get("candidate_id") for item in selection.get("rejected") or []
        if isinstance(item, dict)
    ]
    expected_rejected = set(by_id) - ({selected_id} if selected_id else set())
    if len(rejected_ids) != len(set(rejected_ids)) or set(rejected_ids) != expected_rejected:
        violations.append("selection.rejected must explain every unselected candidate exactly once")

    return {
        "ok": not violations,
        "verdict": "pass" if not violations else "fail",
        "candidate_count": len(candidates),
        "violations": violations,
    }
