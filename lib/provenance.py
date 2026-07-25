"""Local provenance verification for final deliverables.

The rights schema records declarations; this module verifies the file-backed part of those
declarations at the checkpoint seam.  It is intentionally compatible with a future C2PA
signing step, but does not pretend a plain SHA-256 hash is a signature.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_project_path(project_dir: str | Path, raw: str) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else Path(project_dir) / path


def verify_rights_files(
    rights_manifest: dict[str, Any],
    publish_log: dict[str, Any],
    project_dir: str | Path,
) -> dict[str, Any]:
    violations: list[str] = []
    covered_paths: dict[Path, dict[str, Any]] = {}

    for entry in rights_manifest.get("entries") or []:
        if not isinstance(entry, dict) or not entry.get("artifact_path"):
            continue
        path = resolve_project_path(project_dir, str(entry["artifact_path"])).resolve()
        if not path.is_file():
            violations.append(f"rights {entry.get('asset_id')!r}: artifact_path does not exist: {path}")
            continue
        declared = entry.get("artifact_sha256")
        if not declared:
            violations.append(f"rights {entry.get('asset_id')!r}: file-backed row has no artifact_sha256")
            continue
        actual = sha256_file(path)
        if actual != declared:
            violations.append(
                f"rights {entry.get('asset_id')!r}: artifact hash mismatch for {path.name} "
                f"(declared {declared[:12]}, actual {actual[:12]})"
            )
            continue
        covered_paths[path] = entry

    for item in publish_log.get("entries") or []:
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        if status in {"exported", "published"}:
            raw = item.get("export_path")
            if not raw:
                violations.append(
                    f"publish_log {status} entry has no export_path for the exact local payload"
                )
            else:
                path = resolve_project_path(project_dir, str(raw)).resolve()
                if not path.is_file():
                    violations.append(f"publish_log export_path does not exist: {path}")
                elif path not in covered_paths:
                    violations.append(
                        f"final export {path.name!r} has no hash-verified rights row with matching artifact_path"
                    )
        if status == "published" and not str(item.get("url") or "").strip():
            violations.append("publish_log published entry has no returned URL")

    c2pa = rights_manifest.get("c2pa") or {}
    if c2pa.get("status") in {"signed", "verified"}:
        raw = c2pa.get("manifest_path")
        declared = c2pa.get("manifest_sha256")
        if not raw or not declared:
            violations.append(
                "rights_manifest.c2pa signed/verified status requires manifest_path and manifest_sha256"
            )
        else:
            path = resolve_project_path(project_dir, str(raw)).resolve()
            if not path.is_file():
                violations.append(f"C2PA manifest_path does not exist: {path}")
            else:
                actual = sha256_file(path)
                if actual != declared:
                    violations.append(
                        f"C2PA manifest hash mismatch for {path.name} "
                        f"(declared {declared[:12]}, actual {actual[:12]})"
                    )

    return {
        "ok": not violations,
        "verdict": "pass" if not violations else "fail",
        "verified_files": len(covered_paths),
        "violations": violations,
    }
