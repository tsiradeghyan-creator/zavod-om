"""Evidence-backed authorial-voice contracts.

This module deliberately does *not* claim that a regex can judge great writing.  It splits
the job in two:

* code computes objective signals, pins the draft/profile hashes, verifies corpus references,
  checks score math, and refuses fabricated excerpts;
* the script/voice reviewers judge seven creative criteria and provide evidence.

That turns the Maghakian handwriting from optional prose guidance into a non-bypassable,
auditable contract while keeping the mechanism reusable for another author's profile.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
import unicodedata
from pathlib import Path
from typing import Any, Iterable

from lib.armenian_glyph_gate import gate as glyph_gate
from lib.brand_voice_check import check as generic_voice_check


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE_PATH = ROOT / "library" / "authorial_voice" / "maghakian-script-v1.json"
PROFILE_DIR = DEFAULT_PROFILE_PATH.parent

CRITERIA = (
    "behaviour_over_statement",
    "subtext",
    "register_fidelity",
    "dialogue_naturalness",
    "structure",
    "format_fidelity",
    "symbol_and_aphorism_discipline",
)

REGISTER_PATTERNS: dict[str, tuple[str, ...]] = {
    "A1": ("դու", "բլոկադա", "84 ամառ"),
    "A2": ("քեզանից հետո",),
    "A3": ("սոսկալի",),
    "A4": ("հատուկ դասարան",),
    "A5": (),
    "A6": ("ճերմակ",),
    "B": ("մայրենի",),
    "C": ("բլոկադա",),
}

# Source names that are not safe Armenian Unicode are represented only by one-way ids in
# generated artifacts. These opaque ids preserve the known register assignment without copying
# the original filename into the profile.
REGISTER_SOURCE_IDS: dict[str, frozenset[str]] = {
    "A5": frozenset({
        "source-filename-sha256-de0928c8500195ec2a8bc649456441f199c350443343a7342dda1590b717805a",
        "source-filename-sha256-6685771b23d1f7f847c854367c21d680beb7182bd9e9a8962088af108863e7de",
        "source-filename-sha256-ec6357026d0eb72bdacc105b84b9b613f9b1120f1cd9665dc6968a7425283a5e",
        "source-filename-sha256-fc4c4550837859d05a280561c30a4ab6c7055535d639cae45ba0449ba9eb1b39",
    }),
    "C": frozenset({
        "source-filename-sha256-12364174100b93467de63410219347b33f1e476d88814666618ece823d9a5171",
        "source-filename-sha256-f1415b9af74e70400e1cb93a29834c987366c801eeb50f095f19604bd6471838",
    }),
}

EXCLUDED_NAME_PATTERNS = (
    "պայմանագիր", "հեղինակային_իրավունք", "հեղինակային իրավունք", "contract",
)

COLLOQUIAL_TOKENS = frozenset({
    "ա", "սենց", "տենց", "ընենց", "արա", "ախպերս", "վսյո",
    "պռոստը", "կարաս", "տղերք", "բռատ",
})


def _canonical_json(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text).replace("\r\n", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def evidence_source_id(filename: str) -> str:
    """Return a stable evidence id without propagating unsafe/transliterated filenames."""
    normalized = unicodedata.normalize("NFC", filename)
    if normalized.startswith(("source-filename-sha256-", "unsafe-filename-sha256-")):
        return normalized
    stem = Path(normalized).stem
    if any(("a" <= ch.casefold() <= "z") or ("\u0400" <= ch <= "\u052f") for ch in stem):
        return f"source-filename-sha256-{sha256_text(normalized)}"
    return normalized


def resolve_evidence_source(source_id: str, corpus_dir: str | Path) -> Path:
    """Resolve a profile evidence id locally without exposing unsafe names in artifacts."""
    wanted = str(source_id).split("#", 1)[0]
    root = Path(corpus_dir).expanduser()
    matches = [
        path for path in root.glob("*.txt")
        if evidence_source_id(path.name) == wanted
    ]
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Evidence source id {wanted!r} resolved to {len(matches)} local corpus files"
        )
    return matches[0]


def profile_sha256(profile: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(profile)).hexdigest()


def load_profile(path: str | Path = DEFAULT_PROFILE_PATH) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def profile_path(profile_id: str) -> Path:
    """Resolve a profile id inside the local profile directory, without traversal."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,79}", str(profile_id)):
        raise ValueError(f"Unsafe authorial profile id: {profile_id!r}")
    path = (PROFILE_DIR / f"{profile_id}.json").resolve()
    if path.parent != PROFILE_DIR.resolve():
        raise ValueError(f"Authorial profile escapes profile directory: {profile_id!r}")
    return path


def script_text(script: dict[str, Any]) -> str:
    """Extract authored text from timed, flat, or multi-deliverable drafts."""
    chunks: list[str] = []
    for section in script.get("sections") or []:
        if not isinstance(section, dict):
            continue
        for key in ("label", "speaker_directions", "text"):
            value = section.get(key)
            if isinstance(value, str) and value.strip():
                chunks.append(value.strip())
    block_sets = [script.get("blocks") or []]
    block_sets.extend(
        item.get("blocks") or []
        for item in script.get("deliverables") or []
        if isinstance(item, dict)
    )
    for blocks in block_sets:
        for block in blocks:
            if not isinstance(block, dict):
                continue
            speaker = block.get("speaker")
            text = block.get("text")
            if isinstance(speaker, str) and speaker.strip():
                chunks.append(speaker.strip())
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())
    return "\n".join(chunks)


def _armenian_ratio(text: str) -> float:
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return 0.0
    armenian = sum("\u0530" <= ch <= "\u058f" for ch in letters)
    return armenian / len(letters)


def _feature_vector(text: str) -> dict[str, float]:
    chars = max(len(text), 1)
    lines = [line for line in text.splitlines() if line.strip()]
    word_tokens = re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)
    latin_or_cyr = sum(
        any(("a" <= c.lower() <= "z") or ("\u0400" <= c <= "\u052f") for c in token)
        for token in word_tokens
    )
    scene_markers = sum(
        bool(re.search(r"(?:^|\s)(?:\d+(?:\.\d+)?\.\s*)?ՏԵՍԱՐԱՆ(?:\s|$)", line))
        for line in lines
    )
    colloquial = sum(
        unicodedata.normalize("NFC", token).casefold() in COLLOQUIAL_TOKENS
        for token in word_tokens
    )
    return {
        "armenian_letter_ratio": round(_armenian_ratio(text), 6),
        "triple_comma_per_10k_chars": round(text.count(",,,") * 10000 / chars, 6),
        "scene_markers_per_1k_lines": round(scene_markers * 1000 / max(len(lines), 1), 6),
        "colloquial_markers_per_10k_chars": round(colloquial * 10000 / chars, 6),
        "code_switch_tokens_per_1k": round(latin_or_cyr * 1000 / max(len(word_tokens), 1), 6),
    }


def _register_signal(text: str, register: str, profile: dict[str, Any]) -> float:
    """A soft structural signal, not a verdict on literary quality."""
    features = _feature_vector(text)
    register_profile = (profile.get("registers") or {}).get(register, {})
    if register_profile.get("status") == "quarantined_no_clean_sources":
        return 0.0
    targets = register_profile.get("feature_ranges") or {}
    if not targets:
        return 1.0
    scores: list[float] = []
    for name, value in features.items():
        bounds = targets.get(name)
        if not isinstance(bounds, dict):
            continue
        low = float(bounds.get("p10", bounds.get("min", value)))
        high = float(bounds.get("p90", bounds.get("max", value)))
        # Tiny drafts naturally have sparse markers.  A zero lower bound is intentionally
        # permissive; qualitative register fidelity remains a reviewer criterion.
        if low <= value <= high:
            scores.append(1.0)
        else:
            span = max(high - low, abs(high) * 0.25, 0.1)
            distance = low - value if value < low else value - high
            scores.append(max(0.0, 1.0 - distance / (span * 3)))
    range_score = statistics.fmean(scores) if scores else 1.0
    if register.startswith("A"):
        words = [
            unicodedata.normalize("NFC", token).casefold()
            for token in re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)
        ]
        lines = [line for line in text.splitlines() if line.strip()]
        signature = statistics.fmean([
            _armenian_ratio(text) >= 0.70,
            text.count(",,,") > 0,
            any(token in COLLOQUIAL_TOKENS for token in words),
            any(
                re.search(r"(?:^|\s)(?:\d+(?:\.\d+)?\.\s*)?ՏԵՍԱՐԱՆ(?:\s|$)", line)
                for line in lines
            ),
        ])
        return round((range_score * 0.45) + (signature * 0.55), 6)
    return round(range_score, 6)


def _format_signal(script: dict[str, Any], text: str) -> float:
    fmt = script.get("content_format")
    narrative_formats = {"screenplay", "series_episode", "stageplay"}
    package_items = [
        item for item in script.get("deliverables") or []
        if isinstance(item, dict) and item.get("kind") in narrative_formats
    ]
    if fmt not in narrative_formats and not package_items:
        return 1.0
    blocks = list(script.get("blocks") or [])
    for item in package_items:
        blocks.extend(item.get("blocks") or [])
    scene_blocks = sum(isinstance(b, dict) and b.get("type") == "scene_heading" for b in blocks)
    dialogue_blocks = sum(isinstance(b, dict) and b.get("type") == "dialogue" for b in blocks)
    armenian_scene_marker = bool(re.search(r"(?:^|\n)(?:\d+(?:\.\d+)?\.\s*)?ՏԵՍԱՐԱՆ", text))
    signals = [bool(scene_blocks), bool(dialogue_blocks), armenian_scene_marker]
    return round(sum(signals) / len(signals), 6)


def objective_signals(script: dict[str, Any], register: str, profile: dict[str, Any]) -> dict[str, Any]:
    text = script_text(script)
    glyph = authorial_glyph_gate(text)
    tropes = generic_voice_check(text)
    notes = [x.get("reason", str(x)) for x in glyph.get("violations", [])]
    notes.extend(tropes.get("flags", []))
    return {
        "glyph_pass": bool(glyph.get("ok")),
        "generic_trope_pass": bool(tropes.get("ok")),
        "format_signal": _format_signal(script, text),
        "register_signal": _register_signal(text, register, profile),
        "notes": notes,
    }


def authorial_glyph_gate(text: str) -> dict[str, Any]:
    """Apply the Armenian Unicode law without outlawing genuine Russian dialogue.

    The global visual-copy gate intentionally treats every pure-Cyrillic token in Armenian
    context as suspicious.  Ani's A-register screenplays, however, deliberately contain
    Russian code-switching.  For authorial drafts we keep every hard signal (mixed tokens,
    Latin Armenian transliteration, invisible characters) and ignore only the ambiguous
    *pure Cyrillic word* warning.  This preserves her handwriting without permitting Latin-
    script Armenian or homoglyphs inside an Armenian word.
    """
    raw = glyph_gate(text)
    violations = [
        item for item in raw.get("violations", [])
        if not str(item.get("reason") or "").startswith("Cyrillic word in Armenian context")
    ]
    return {
        "ok": not violations,
        "verdict": "pass" if not violations else "fail",
        "violations": violations,
    }


def report_seed(
    script: dict[str, Any],
    *,
    profile: dict[str, Any],
    register: str,
) -> dict[str, Any]:
    """Create the non-creative, machine-computed half of a voice report."""
    text = script_text(script)
    return {
        "version": "1.0",
        "profile_id": profile["profile_id"],
        "register": register,
        "draft_sha256": sha256_text(text),
        "profile_sha256": profile_sha256(profile),
        "objective": objective_signals(script, register, profile),
        "criteria": [],
        "overall_score": 0.0,
        "verdict": "revise",
        "blocking_issues": ["Creative criteria not reviewed yet."],
    }


def _norm_space(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def validate_voice_report(
    script: dict[str, Any],
    report: dict[str, Any],
    *,
    profile: dict[str, Any],
    register: str,
    minimum_score: float = 0.8,
) -> dict[str, Any]:
    """Validate evidence and return a gate-style verdict."""
    violations: list[str] = []
    text = script_text(script)
    normalized_draft = _norm_space(text)

    if report.get("profile_id") != profile.get("profile_id"):
        violations.append("authorial voice report uses the wrong profile_id")
    if report.get("register") != register:
        violations.append(f"authorial voice report register must be {register!r}")
    if report.get("draft_sha256") != sha256_text(text):
        violations.append("authorial voice report draft_sha256 does not match the submitted draft")
    if report.get("profile_sha256") != profile_sha256(profile):
        violations.append("authorial voice report profile_sha256 does not match the current profile")

    expected_objective = objective_signals(script, register, profile)
    actual_objective = report.get("objective") or {}
    for key in ("glyph_pass", "generic_trope_pass"):
        if actual_objective.get(key) is not expected_objective[key]:
            violations.append(f"authorial voice objective.{key} is not the computed value")
    for key in ("format_signal", "register_signal"):
        actual = actual_objective.get(key)
        if not isinstance(actual, (int, float)) or not math.isclose(
            float(actual), float(expected_objective[key]), abs_tol=0.001
        ):
            violations.append(f"authorial voice objective.{key} is not the computed value")
    if actual_objective.get("notes") != expected_objective.get("notes"):
        violations.append("authorial voice objective.notes is not the computed value")

    items = report.get("criteria") or []
    by_name: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("criterion")
        if name in by_name:
            violations.append(f"authorial voice criterion {name!r} appears more than once")
        elif isinstance(name, str):
            by_name[name] = item
    missing = [name for name in CRITERIA if name not in by_name]
    extra = sorted(set(by_name) - set(CRITERIA))
    if missing:
        violations.append(f"authorial voice report is missing criteria {missing}")
    if extra:
        violations.append(f"authorial voice report has unknown criteria {extra}")

    source_files = set((profile.get("sources") or {}).get("files") or [])
    scores: list[int] = []
    cited_excerpts: list[str] = []
    cited_corpus_refs: list[str] = []
    rationales: list[str] = []
    for name in CRITERIA:
        item = by_name.get(name)
        if not item:
            continue
        score = item.get("score")
        if isinstance(score, int):
            scores.append(score)
            if score < 3:
                violations.append(f"authorial voice criterion {name!r} scored {score} < 3")
        for evidence in item.get("evidence") or []:
            if not isinstance(evidence, dict):
                continue
            excerpt = _norm_space(str(evidence.get("draft_excerpt") or ""))
            cited_excerpts.append(excerpt)
            if not excerpt or excerpt not in normalized_draft:
                violations.append(f"authorial voice criterion {name!r} cites an excerpt not found in the draft")
            corpus_ref = str(evidence.get("corpus_ref") or "")
            cited_corpus_refs.append(corpus_ref)
            rationales.append(_norm_space(str(evidence.get("rationale") or "")))
            # A reference may add a line/page suffix after '#'.  The filename before it must
            # still come from the pinned corpus snapshot.
            corpus_file = corpus_ref.split("#", 1)[0]
            if corpus_file not in source_files and not corpus_ref.startswith("style-profile.md#"):
                violations.append(
                    f"authorial voice criterion {name!r} cites corpus_ref {corpus_ref!r} "
                    "outside the pinned profile"
                )

    authored_lines = [line for line in text.splitlines() if line.strip()]
    required_excerpt_count = min(3, max(1, len(authored_lines)))
    if len(set(cited_excerpts)) < required_excerpt_count:
        violations.append(
            f"authorial voice evidence reuses too little of the draft: need at least "
            f"{required_excerpt_count} distinct excerpts"
        )
    if len(set(cited_corpus_refs)) < 2:
        violations.append("authorial voice evidence must compare against at least two corpus references")
    if len(set(rationales)) < max(3, len(CRITERIA) // 2):
        violations.append("authorial voice evidence rationales are duplicated instead of criterion-specific")

    calculated_score = round((sum(scores) / (len(CRITERIA) * 5)) if len(scores) == len(CRITERIA) else 0.0, 6)
    reported_score = report.get("overall_score")
    if not isinstance(reported_score, (int, float)) or not math.isclose(
        float(reported_score), calculated_score, abs_tol=0.001
    ):
        violations.append(
            f"authorial voice overall_score must equal the criterion mean ({calculated_score})"
        )

    if not expected_objective["glyph_pass"]:
        violations.append("authorial voice draft fails the Armenian glyph gate")
    if not expected_objective["generic_trope_pass"]:
        violations.append("authorial voice draft contains generic AI/marketing tropes")
    if expected_objective["format_signal"] < 0.66:
        violations.append("authorial voice draft lacks enough screenplay-format evidence")
    register_floor = float(
        ((profile.get("registers") or {}).get(register) or {}).get("minimum_signal", 0.35)
    )
    if expected_objective["register_signal"] < register_floor:
        violations.append(
            f"authorial voice draft is structurally too far from the selected register "
            f"({expected_objective['register_signal']:.3f} < {register_floor:.3f})"
        )
    if calculated_score < minimum_score:
        violations.append(
            f"authorial voice score {calculated_score:.3f} is below the locked minimum {minimum_score:.3f}"
        )

    if report.get("blocking_issues"):
        violations.append("authorial voice report still contains blocking_issues")

    should_pass = not violations
    if report.get("verdict") != ("pass" if should_pass else "revise"):
        violations.append("authorial voice report verdict contradicts its evidence and score")

    return {
        "ok": not violations,
        "verdict": "pass" if not violations else "revise",
        "score": calculated_score,
        "objective": expected_objective,
        "violations": violations,
    }


def _register_for_name(name: str) -> list[str]:
    low = unicodedata.normalize("NFC", name).casefold()
    matches: list[str] = []
    for register, patterns in REGISTER_PATTERNS.items():
        if any(pattern.casefold() in low for pattern in patterns):
            matches.append(register)
    source_id = evidence_source_id(name)
    for register, source_ids in REGISTER_SOURCE_IDS.items():
        if source_id in source_ids and register not in matches:
            matches.append(register)
    return matches or ["unclassified"]


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lo = math.floor(index)
    hi = math.ceil(index)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)


def _ranges(vectors: Iterable[dict[str, float]]) -> dict[str, dict[str, float]]:
    rows = list(vectors)
    names = sorted({key for row in rows for key in row})
    result: dict[str, dict[str, float]] = {}
    for name in names:
        values = [float(row[name]) for row in rows if name in row]
        result[name] = {
            "min": round(min(values), 6),
            "p10": round(_percentile(values, 0.10), 6),
            "median": round(statistics.median(values), 6),
            "p90": round(_percentile(values, 0.90), 6),
            "max": round(max(values), 6),
        }
    return result


def discover_corpus(corpus_dir: str | Path) -> tuple[list[Path], list[str]]:
    root = Path(corpus_dir).expanduser()
    included: list[Path] = []
    excluded: list[str] = []
    for path in sorted(root.glob("*.txt"), key=lambda p: unicodedata.normalize("NFC", p.name).casefold()):
        low = unicodedata.normalize("NFC", path.name).casefold()
        if any(pattern.casefold() in low for pattern in EXCLUDED_NAME_PATTERNS):
            excluded.append(path.name)
            continue
        # A corrupt mixed-script filename is not a stable evidence identifier.  Keep the
        # source file untouched, but never copy the corrupt token into generated artifacts.
        # Record a one-way alias so the exclusion remains auditable without propagating bad
        # Armenian Unicode into the profile/delta files.
        if not authorial_glyph_gate(path.name).get("ok"):
            excluded.append(f"unsafe-filename-sha256-{sha256_text(path.name)}")
            continue
        if path.stat().st_size < 256:
            excluded.append(path.name)
            continue
        try:
            source_text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            excluded.append(f"decode-failure-sha256-{sha256_text(path.name)}")
            continue
        if not authorial_glyph_gate(source_text).get("ok"):
            excluded.append(f"content-glyph-failure-sha256-{sha256_text(path.name)}")
            continue
        included.append(path)
    return included, excluded


def build_profile(corpus_dir: str | Path) -> dict[str, Any]:
    files, excluded = discover_corpus(corpus_dir)
    if not files:
        raise ValueError(f"No eligible UTF-8 text corpus files found in {corpus_dir}")

    snapshot = hashlib.sha256()
    per_register: dict[str, list[dict[str, float]]] = {}
    register_files: dict[str, list[str]] = {}
    for path in files:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        snapshot.update(unicodedata.normalize("NFC", path.name).encode("utf-8"))
        snapshot.update(hashlib.sha256(raw).digest())
        vector = _feature_vector(text)
        for register in _register_for_name(path.name):
            per_register.setdefault(register, []).append(vector)
            register_files.setdefault(register, []).append(evidence_source_id(path.name))

    registers = {}
    for register in sorted(set(REGISTER_PATTERNS) | set(per_register)):
        rows = per_register.get(register, [])
        active = bool(rows)
        registers[register] = {
            "status": "active" if active else "quarantined_no_clean_sources",
            "files": sorted(register_files.get(register, [])),
            "sample_count": len(rows),
            "minimum_signal": (
                (0.62 if register.startswith("A") else 0.35) if active else 1.0
            ),
            "feature_ranges": _ranges(rows),
        }
    return {
        "version": "1.0",
        "profile_id": "maghakian-script-v1",
        "language": "hy-AM",
        "description": "Անի Մաղաքյան authorial screenplay/prose fingerprint; visual branding is intentionally separate.",
        "sources": {
            "corpus_kind": "private_owner_supplied",
            "file_count": len(files),
            "files": [evidence_source_id(path.name) for path in files],
            "excluded_files": excluded,
            "snapshot_sha256": snapshot.hexdigest(),
        },
        "criteria": list(CRITERIA),
        "registers": registers,
    }
