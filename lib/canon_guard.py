"""Canon guard — mid-pipeline canon-change detector (born 2026-07-03, «Մոռացողը»).

The failure it encodes: during the Moratsoghy production the era pivoted to the 1920s at the
ASSET stage. The look bible was updated, but nobody re-validated the story spine upstream
(diagnosis language, child idiom, 25-years-back math). The gap was caught by an external
review — expensively late. Prose advice ("re-check upstream on canon change") does not
execute; this module does.

Usage at each stage advance:
    lock(project_dir)            -> writes/updates .canon.lock with content hashes
    check(project_dir, stage)    -> {"ok": bool, "changed": [...], "action": "..."}

If a canon file's hash differs from the lock AFTER the script stage has been passed,
check() returns ok=False and the checkpoint seam must refuse to advance until a
`canon-revalidation.md` note exists that is NEWER than every changed canon file.
Re-validation = a human/owner-visible artifact, not a silent flag.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

CANON_FILES = ("bible*.md", "look-bible.md", "canon-secret.md")
LOCK = ".canon.lock"
REVALIDATION = "canon-revalidation.md"

# Stages at or before which canon may change freely (story is still forming).
FREE_STAGES = {"idea", "script"}


def _canon_paths(project_dir: str) -> list[str]:
    import glob as _glob
    out: list[str] = []
    for pat in CANON_FILES:
        out.extend(sorted(_glob.glob(os.path.join(project_dir, pat))))
    return out


def _hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def lock(project_dir: str) -> dict[str, str]:
    """Snapshot canon hashes. Call when a stage completes cleanly."""
    snap = {os.path.basename(p): _hash(p) for p in _canon_paths(project_dir)}
    with open(os.path.join(project_dir, LOCK), "w") as f:
        json.dump(snap, f, indent=1, ensure_ascii=False)
    return snap


def check(project_dir: str, stage: str) -> dict[str, Any]:
    """Compare current canon against the lock. Past the free stages, a drifted canon
    blocks unless a fresh re-validation note exists."""
    lock_path = os.path.join(project_dir, LOCK)
    if not os.path.exists(lock_path):
        return {"ok": True, "changed": [], "action": "no lock yet — call lock() at first stage pass"}
    snap = json.load(open(lock_path))
    changed = []
    for p in _canon_paths(project_dir):
        name = os.path.basename(p)
        if snap.get(name) and snap[name] != _hash(p):
            changed.append(name)
        elif name not in snap:
            changed.append(name + " (new)")
    if not changed or stage in FREE_STAGES:
        return {"ok": True, "changed": changed, "action": "free stage" if changed else ""}
    reval = os.path.join(project_dir, REVALIDATION)
    if os.path.exists(reval):
        reval_mtime = os.path.getmtime(reval)
        stale = [c for c in changed
                 if os.path.exists(os.path.join(project_dir, c.replace(" (new)", "")))
                 and os.path.getmtime(os.path.join(project_dir, c.replace(" (new)", ""))) > reval_mtime]
        if not stale:
            return {"ok": True, "changed": changed, "action": "re-validated"}
        changed = stale
    return {
        "ok": False,
        "changed": changed,
        "action": (f"CANON CHANGED MID-PIPELINE at stage '{stage}': {', '.join(changed)}. "
                   f"Blocked until upstream re-validation is written to {REVALIDATION} "
                   "(what changed, which upstream documents were re-checked, what was fixed)."),
    }


if __name__ == "__main__":
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    st = sys.argv[2] if len(sys.argv) > 2 else "asset"
    print(json.dumps(check(d, st), ensure_ascii=False, indent=1))
