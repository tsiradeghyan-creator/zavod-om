"""Scout driver — the wake-safe weekly entry point the launchd job actually runs.

Wake-safe protocol (fixes the audit's "cron asleep / broken tree" failure class):
  1. Run the health-check FIRST. If the tree is RED, abort — never act on a broken base.
  2. If GREEN, process any findings the agent queued in `library/scout_inbox.json`
     into a GATED upgrade memo (`library/scout_memo_<date>.md`). Nothing is installed.
  3. Always leave a heartbeat line in `library/scout.log` so a human can see it ran.

The web-scan itself is agent-driven (an LLM with search): the agent drops findings into
the inbox; this driver only dedups/scores/memos them. So the scheduled job is safe to run
unattended — it can health-gate and summarize, but it can never adopt anything on its own.

Run: `./.venv/bin/python lib/scout_run.py`   (exit 0 = ran/clean, 1 = health RED)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib.scout import build_memo, load_registry  # noqa: E402

LIB_DIR = os.path.join(ROOT, "library")
INBOX = os.path.join(LIB_DIR, "scout_inbox.json")
LOG = os.path.join(LIB_DIR, "scout.log")


def _log(line: str) -> None:
    os.makedirs(LIB_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(LOG, "a") as f:
        f.write(f"[{stamp}] {line}\n")
    print(line)


def _healthcheck_green() -> bool:
    """Scan-safe gate: full health MINUS the TCC-gated corpus (~/Documents) and the render
    binary — a trend-scan touches neither and only writes a GATED memo. This lets the weekly
    launchd run survive before Full Disk Access is granted, while still aborting on a genuinely
    broken tree (gates / schemas / enforcement / registries must still pass)."""
    from lib import healthcheck
    ok, reds = healthcheck.scan_safe_ok()
    if not ok:
        _log(f"scan-safe health RED — aborting Scout run (wake-safe). Red: {reds}")
    return ok


def _load_inbox() -> list[dict]:
    if not os.path.exists(INBOX):
        return []
    try:
        data = json.load(open(INBOX))
    except Exception as e:
        _log(f"scout_inbox.json unreadable ({e}) — skipping memo build")
        return []
    return data if isinstance(data, list) else data.get("findings", [])


def main() -> int:
    if not _healthcheck_green():
        return 1

    findings = _load_inbox()
    if not findings:
        _log("health GREEN; no queued findings (agent-driven scan pending) — heartbeat only.")
        return 0

    reg = load_registry()
    memo = build_memo(findings, reg)
    out = os.path.join(LIB_DIR, f"scout_memo_{datetime.now(timezone.utc):%Y-%m-%d}.md")
    with open(out, "w") as f:
        f.write(memo)
    _log(f"health GREEN; processed {len(findings)} finding(s) → GATED memo {os.path.basename(out)} "
         f"(nothing installed — owner approves to adopt).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
