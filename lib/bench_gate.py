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
# Two rulings this similar are near-duplicates. This is a WARNING, not a hard block:
# specialists filling a shared template legitimately share boilerplate, so a fuzzy score is
# too soft to fail on (2026-07-05). Only an EXACT normalized match is a hard rubber-stamp.
DUPLICATE_SIMILARITY = 0.92

# A specialist's structured verdict. The bench is well-formed only if every role declares one;
# a completed stage cannot stand over a revise/reject (that is the whole point of the bench).
VALID_VERDICTS = {"approve", "revise", "reject"}


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


# The 5-criterion hook rubric (strategy audit): filled by the story-hook reviewer, each
# criterion 1-5. brand_specificity is the universalized criterion — "could any brand have
# said this?"; what counts as THIS brand's specificity comes from the loaded brand pack.
HOOK_RUBRIC_CRITERIA = (
    "first_3_seconds_promise",   # does the opening promise a concrete reason to watch?
    "brand_specificity",         # could only this brand (per its pack) have made this?
    "emotional_charge",          # is there felt tension, not dry information?
    "clarity",                   # does the viewer know what they will get?
    "share_or_save_reason",      # is there a reason to save/share/comment?
)
HOOK_RUBRIC_PASS = 18  # of 25
HOOK_RUBRIC_MIN_PER_CRITERION = 3  # round-7.1 #12: a gamed single criterion can't carry the total
HOOK_RUBRIC_EVIDENCE_MIN = 8  # chars — "n/a" or "good" is not evidence


def _hook_rubric_violation(entry: dict[str, Any]) -> str | None:
    """Validate the story-hook bench entry's rubric (round-7.1 #11/#12, strategy audit).

    The rubric is still self-scored by the reviewer — code cannot and does not judge hook
    strength. What code CAN demand: a short evidence string per criterion (so a lazy 4/5/5
    across the board at least has to be justified in writing, raising the cost of rubber-
    stamping), and a per-criterion floor (so one inflated criterion can't carry a mediocre
    hook over the total threshold on its own).
    """
    rubric = entry.get("rubric")
    if not isinstance(rubric, dict):
        return ("missing hook rubric — the story-hook ruling must carry scores for "
                f"{list(HOOK_RUBRIC_CRITERIA)} (1-5 each, pass >= {HOOK_RUBRIC_PASS}).")
    evidence = entry.get("rubric_evidence")
    if not isinstance(evidence, dict):
        return ("missing rubric_evidence — each hook rubric criterion needs a short "
                "written justification, not just a number.")
    total = 0
    for crit in HOOK_RUBRIC_CRITERIA:
        score = rubric.get(crit)
        if not isinstance(score, int) or not 1 <= score <= 5:
            return f"hook rubric criterion {crit!r} must be an integer 1-5 (got {score!r})."
        if score < HOOK_RUBRIC_MIN_PER_CRITERION:
            return (f"hook rubric criterion {crit!r} scored {score} < "
                    f"{HOOK_RUBRIC_MIN_PER_CRITERION} — every criterion must clear the "
                    "floor; a high total can't carry a criterion that fails outright.")
        ev = str(evidence.get(crit) or "").strip()
        if len(ev) < HOOK_RUBRIC_EVIDENCE_MIN:
            return (f"hook rubric criterion {crit!r} has no real rubric_evidence "
                    f"(need >= {HOOK_RUBRIC_EVIDENCE_MIN} chars) — a score without a "
                    "reason is not a judgment.")
        total += score
    if total < HOOK_RUBRIC_PASS:
        return (f"hook rubric total {total} < {HOOK_RUBRIC_PASS} — the hook is not strong "
                "enough to close the idea stage; rework the hook, not the rubric.")
    return None


# Round-7.1 (re-audit №6): manifest-declared bench reduction is a PRIVILEGE, not a right
# any manifest gets by writing metadata.bench_roles. Without this allowlist, a brand-new
# manifest could declare e.g. {"compose": ["delivery-qc"]} and legitimately zero out
# compose's full 6-role bench — the fast-lane mechanism becomes a bypass generator. Only
# pipelines named here may have their bench_roles declaration honored; every other
# pipeline's declaration (if any) is IGNORED and falls back to the full default bench.
LIGHT_BENCH_ALLOWED = frozenset({"zavod-reel-fast"})


def required_bench(stage: str, pipeline_type: str | None = None) -> list[str]:
    """The stage's required bench roles.

    A pipeline manifest may declare its own bench under ``metadata.bench_roles`` (keys =
    bench-stage names) — the fast-lane mechanism (2026-07-07 strategy audit): same
    enforcement code, fewer and sharper roles declared per pipeline. The declaration is
    honored ONLY for pipelines in ``LIGHT_BENCH_ALLOWED`` (round-7.1 #6). No declaration,
    a non-allowlisted pipeline, or an unloadable manifest all fall back to the FULL
    default bench — the strict direction, always.
    """
    canonical = (pipeline_type or "").strip().casefold()
    if canonical in LIGHT_BENCH_ALLOWED:
        try:
            from lib.pipeline_loader import load_pipeline
            declared = (load_pipeline(canonical).get("metadata") or {}).get("bench_roles") or {}
            roles = declared.get(stage)
            if isinstance(roles, list) and roles and all(isinstance(r, str) for r in roles):
                return list(roles)
        except Exception:
            pass  # full default bench — stricter, never lighter
    return STAGE_BENCH.get(stage, ["reviewer"])


def run_bench_gates(stage: str, report: dict[str, Any],
                    pipeline_type: str | None = None) -> dict[str, Any]:
    violations: list[str] = []
    report_stage = report.get("stage")
    if report_stage != stage:
        violations.append(
            f"bench_report.stage: expected {stage!r}, got {report_stage!r} — a ruling from "
            "another stage cannot certify this work"
        )
    bench = report.get("bench", {})
    if not isinstance(bench, dict):
        return {
            "ok": False,
            "verdict": "fail",
            "violations": [*violations, "bench_report.bench must be an object"],
            "warnings": [],
        }
    required = required_bench(stage, pipeline_type)
    unexpected = sorted(set(bench) - set(required))
    if unexpected:
        violations.append(
            "bench_report.bench: unexpected roles are not part of this routed stage: "
            f"{unexpected}. Unplanned specialists must be rejected, not silently ignored."
        )
    present: dict[str, str] = {}  # role -> ruling, for cross-role independence check

    for role in required:
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

        # Structured verdict (2026-07-05, #1). The reject signal belongs in a field, not sniffed
        # from prose ("nothing is blocked" is a legit approval). Every role must declare one, and
        # a completed stage cannot stand over a revise/reject — that is what the bench is for.
        verdict = str(entry.get("verdict") or "").strip().lower()
        if verdict not in VALID_VERDICTS:
            violations.append(
                f"bench.{role}: missing/invalid verdict {entry.get('verdict')!r} — must be one of "
                f"{sorted(VALID_VERDICTS)}. A ruling without a structured verdict is not a decision.")
            continue
        if verdict in {"revise", "reject"}:
            issues = entry.get("blocking_issues")
            if not (isinstance(issues, list) and any(str(x).strip() for x in issues)):
                violations.append(
                    f"bench.{role}: verdict {verdict!r} with no non-empty blocking_issues — a "
                    "revise/reject must name what blocks it.")
            else:
                violations.append(
                    f"bench.{role}: specialist verdict {verdict!r} ({issues}) — the stage cannot "
                    "close 'completed' over an unresolved specialist objection.")
            continue

        # Hook rubric (strategy audit): the story-hook reviewer judges the hook, the code
        # only demands that the judgment is STRUCTURED — five named criteria, 1-5 each,
        # and a passing total. Code never pretends to measure hook strength itself.
        if role == "story-hook":
            rubric_violation = _hook_rubric_violation(entry)
            if rubric_violation:
                violations.append(f"bench.{role}: {rubric_violation}")
                continue

        present[role] = ruling

    # Independence: an EXACT rubber-stamp (same normalized text across roles) is a hard block;
    # a merely near-identical pair is a warning (shared template ≠ failure to think).
    warnings: list[str] = []
    checked = list(present.items())
    for i in range(len(checked)):
        for j in range(i + 1, len(checked)):
            a_norm = " ".join(_norm_tokens(checked[i][1]))
            b_norm = " ".join(_norm_tokens(checked[j][1]))
            if a_norm == b_norm:
                violations.append(
                    f"bench.{checked[i][0]} and bench.{checked[j][0]}: identical ruling "
                    "rubber-stamped across roles — each specialist must rule independently")
            elif _similarity(checked[i][1], checked[j][1]) >= DUPLICATE_SIMILARITY:
                warnings.append(
                    f"bench.{checked[i][0]} and bench.{checked[j][0]}: near-identical rulings "
                    "({:.0%}) — verify these are independent judgments, not a shared template."
                    .format(_similarity(checked[i][1], checked[j][1])))

    return {"ok": not violations, "verdict": "pass" if not violations else "fail",
            "violations": violations, "warnings": warnings}


if __name__ == "__main__":
    demo_bad = {"stage": "scene", "bench": {"scene-director": {"ruling": "ok"}}}
    print("scene / thin bench ->", run_bench_gates("scene", demo_bad)["violations"][:2])
