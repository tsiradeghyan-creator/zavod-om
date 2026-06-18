"""Brand-voice gate — flag generic-AI tropes and voice drift.

Heuristic structural check (not final creative judgment): catches the lazy-AI phrasing
that makes copy feel off-brand/generic. The script-director's voice (style-profile.md /
brand-voice.md) is the source of truth; this gate stops the obvious drift before it ships.

verdict contract: {"ok": bool, "verdict": "pass"|"revise", "score": float(0-5), "flags": [...]}
(lower score is better, like variation_checker).
"""

from __future__ import annotations

import re
from typing import Any

# Generic AI tropes / filler that signal off-voice copy.
TROPES = [
    "in today's world", "in the world of", "look no further", "game-changer",
    "game changer", "unlock", "unleash", "elevate your", "take it to the next level",
    "revolutionary", "cutting-edge", "state-of-the-art", "seamless", "effortless",
    "dive in", "let's dive", "in conclusion", "the power of", "embark on",
    "whether you're", "say goodbye to", "say hello to", "more than just",
    "it's not just", "when it comes to", "at the end of the day", "needless to say",
]


def check(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        return {"ok": True, "verdict": "pass", "score": 0.0, "flags": []}
    low = text.lower()
    flags: list[str] = []
    for t in TROPES:
        if t in low:
            flags.append(f"generic trope: \"{t}\"")
    # Excessive em-dashes are a classic AI tell.
    if text.count("—") >= 4:
        flags.append("em-dash overuse (>=4) — typical AI cadence; vary punctuation")
    # Exclamation spam.
    if text.count("!") >= 4:
        flags.append("exclamation spam (>=4)")
    score = min(5.0, len(flags) * 1.25)
    return {
        "ok": score < 2.5,
        "verdict": "pass" if score < 2.5 else "revise",
        "score": score,
        "flags": flags,
    }


if __name__ == "__main__":
    clean = "Two acres of high desert. One private pool. Ten minutes from Joshua Tree."
    bad = "In today's world, unlock a revolutionary, cutting-edge, seamless escape — elevate your stay!"
    print("CLEAN ->", check(clean)["verdict"], check(clean)["score"])
    r = check(bad)
    print("BAD   ->", r["verdict"], r["score"], r["flags"][:3])
    assert check(clean)["ok"] and not check(bad)["ok"]
    print("brand_voice gate self-test: PASS")
