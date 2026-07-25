#!/usr/bin/env python3
"""Incremental feeder for a curated authorial-voice profile.

The extractor never edits the canon.  It builds a deterministic corpus snapshot and writes
reviewable deltas for new or changed text files.  An agent/human may then inspect the delta
and explicitly update the curated profile or style rules.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.authorial_voice import (  # noqa: E402
    DEFAULT_PROFILE_PATH,
    _feature_vector,
    _register_for_name,
    authorial_glyph_gate,
    build_profile,
    discover_corpus,
    evidence_source_id,
)


DEFAULT_CORPUS = Path.home() / "Documents" / "Maghakian-Scripts" / "txt"
DEFAULT_STATE = ROOT / "library" / "authorial_voice" / ".seen.json"
DEFAULT_DELTAS = ROOT / "library" / "authorial_voice" / "deltas"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)


def _candidate_lines(text: str) -> dict[str, list[str]]:
    aphorisms: list[str] = []
    devices: list[str] = []
    for raw in text.splitlines():
        line = " ".join(raw.split()).strip()
        if not line:
            continue
        if 18 <= len(line) <= 180 and ("«" in line or "»" in line):
            aphorisms.append(line)
        if any(marker in line for marker in ("ՏԵՍԱՐԱՆ", "ՖԼԵՇԲԵՔ", "ՊԵՐԵԽՈԴ", "ԱՆՑՈՒՄ", "արտակադրային ձայն")):
            devices.append(line)
    # Candidates are evidence for review, never automatically promoted to canon.
    return {
        "aphorism_candidates": list(dict.fromkeys(aphorisms))[:20],
        "device_candidates": list(dict.fromkeys(devices))[:20],
    }


def scan(corpus: Path, prior: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    files, excluded = discover_corpus(corpus)
    old_files = {
        evidence_source_id(str(name)): value
        for name, value in (prior.get("files") or {}).items()
    }
    current: dict[str, dict[str, Any]] = {}
    deltas: list[dict[str, Any]] = []

    for path in files:
        source_id = evidence_source_id(path.name)
        digest = _hash(path)
        stat = path.stat()
        current[source_id] = {
            "sha256": digest,
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
        old = old_files.get(source_id)
        if isinstance(old, dict) and old.get("sha256") == digest:
            continue
        text = path.read_text(encoding="utf-8")
        glyph = authorial_glyph_gate(text)
        deltas.append({
            "file": source_id,
            "change": "new" if old is None else "changed",
            "sha256": digest,
            "register_candidates": _register_for_name(path.name),
            "features": _feature_vector(text),
            "glyph": {
                "ok": glyph.get("ok", False),
                "violation_count": len(glyph.get("violations") or []),
                "violations": glyph.get("violations") or [],
            },
            **_candidate_lines(text),
        })

    removed = sorted(set(old_files) - set(current))
    state = {
        "version": "1.0",
        "corpus": str(corpus),
        "scanned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": current,
        "excluded_files": excluded,
    }
    return state, deltas, removed


def _markdown(delta: dict[str, Any]) -> str:
    lines = [
        f"# Voice delta — {delta['date']}",
        "",
        "> Review-only evidence. Nothing in this file updates the authorial canon automatically.",
        "",
        f"- Corpus: `{delta['corpus']}`",
        f"- New or changed files: {len(delta['files'])}",
        f"- Removed files: {len(delta['removed_files'])}",
        "",
    ]
    for entry in delta["files"]:
        lines.extend([
            f"## {entry['file']} — {entry['change']}",
            f"- Register candidates: {', '.join(entry['register_candidates'])}",
            f"- Glyph gate: {'PASS' if entry['glyph']['ok'] else 'FAIL'}",
            f"- Features: `{json.dumps(entry['features'], ensure_ascii=False, sort_keys=True)}`",
        ])
        for key, title in (("aphorism_candidates", "Aphorism candidates"), ("device_candidates", "Device candidates")):
            values = entry.get(key) or []
            if values:
                lines.append(f"- {title}:")
                lines.extend(f"  - {value}" for value in values)
        lines.append("")
    if delta["removed_files"]:
        lines.append("## Removed files")
        lines.extend(f"- {name}" for name in delta["removed_files"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and incrementally scan an authorial voice corpus")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--deltas", type=Path, default=DEFAULT_DELTAS)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE_PATH)
    parser.add_argument("--baseline", action="store_true", help="Rebuild the pinned aggregate profile")
    args = parser.parse_args()

    prior = _read_json(args.state, {"version": "1.0", "files": {}})
    state, changed, removed = scan(args.corpus.expanduser(), prior)

    rebuild_profile = args.baseline or not args.profile.exists()
    if rebuild_profile:
        profile = build_profile(args.corpus.expanduser())
        _write_json(args.profile, profile)

    today = datetime.now(timezone.utc).date().isoformat()
    delta = {
        "version": "1.0",
        "date": today,
        "corpus": str(args.corpus.expanduser()),
        "profile": str(args.profile),
        "files": changed,
        "removed_files": removed,
        "requires_human_acceptance": True,
    }
    if (changed or removed) and not args.baseline:
        args.deltas.mkdir(parents=True, exist_ok=True)
        _write_json(args.deltas / f"{today}.json", delta)
        (args.deltas / f"{today}.md").write_text(_markdown(delta), encoding="utf-8")

    _write_json(args.state, state)
    print(json.dumps({
        "profile": str(args.profile),
        "profile_rebuilt": rebuild_profile,
        "changed": len(changed),
        "removed": len(removed),
        "delta_written": bool((changed or removed) and not args.baseline),
    }, ensure_ascii=False))
    return 2 if any(not item["glyph"]["ok"] for item in changed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
