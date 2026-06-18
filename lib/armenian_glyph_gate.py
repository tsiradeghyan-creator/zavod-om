"""Armenian glyph gate — HARD enforcement of the [[rules]] language law.

The zavod's #1 brand law: every Armenian word must be proper Eastern Armenian
Unicode — never transliteration, never Latin/Cyrillic lookalikes mixed into an
Armenian word. Prose rules failed to enforce this; this module makes it a code
gate that the reviewer runs and CANNOT bypass.

Verdict contract (matches the other QC libs):
    {
      "ok": bool,
      "verdict": "pass" | "fail",
      "violations": [{"text", "reason", "field"}],
    }
"""

from __future__ import annotations

import re
from typing import Any

# Armenian letters: main block U+0531–U+0556 (caps), U+0561–U+0586 (lower),
# plus ligatures U+FB13–U+FB17. Punctuation (U+0559–U+055F) is allowed.
ARMENIAN = re.compile(r"[Ա-Ֆա-ևﬓ-ﬗ]")
LATIN = re.compile(r"[A-Za-z]")
CYRILLIC = re.compile(r"[Ѐ-ӿ]")
# A token = run of letters across scripts (so we can catch MIXED tokens).
TOKEN = re.compile(r"[^\s\d.,;:!?()\[\]{}«»\"'—–\-/|]+")

# Common Latin/Cyrillic glyphs people wrongly substitute for Armenian letters.
CONFUSABLES = {
    "o", "O", "0", "n", "p", "c", "y", "e",      # latin lookalikes
    "о", "е", "а", "р", "с", "у", "н",            # cyrillic lookalikes
}


def check_text(text: str, field: str = "") -> list[dict[str, str]]:
    """Return violations for a single string."""
    violations: list[dict[str, str]] = []
    if not text:
        return violations
    for m in TOKEN.finditer(text):
        tok = m.group(0)
        has_arm = bool(ARMENIAN.search(tok))
        if not has_arm:
            continue  # pure non-Armenian token (e.g. an English brand word) is fine
        # An Armenian-bearing token must NOT contain Latin or Cyrillic letters.
        bad_latin = LATIN.findall(tok)
        bad_cyr = CYRILLIC.findall(tok)
        if bad_latin or bad_cyr:
            mixed = "".join(sorted(set(bad_latin + bad_cyr)))
            violations.append({
                "text": tok,
                "field": field,
                "reason": (
                    f"Mixed-script Armenian word — contains non-Armenian letters "
                    f"'{mixed}'. Use proper Eastern Armenian Unicode for the whole word."
                ),
            })
    return violations


def _walk(obj: Any, path: str = "") -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if isinstance(obj, str):
        out += check_text(obj, path)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            out += _walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += _walk(v, f"{path}[{i}]")
    return out


def gate(artifact: Any) -> dict[str, Any]:
    """Run the glyph gate over any artifact (str / dict / list). HARD gate."""
    violations = _walk(artifact)
    return {
        "ok": not violations,
        "verdict": "pass" if not violations else "fail",
        "violations": violations,
    }


if __name__ == "__main__":
    # Self-test: a clean Armenian line passes; a transliterated/mixed one fails.
    ok_case = {"headline": "Վանը Հայկական դարպասների հեղինակն է"}
    bad_case = {"headline": "Vanը Haykakan", "sub": "Դարpասները"}  # latin in arm words
    r_ok = gate(ok_case)
    r_bad = gate(bad_case)
    print("CLEAN  ->", r_ok["verdict"], r_ok["violations"])
    print("DIRTY  ->", r_bad["verdict"])
    for v in r_bad["violations"]:
        print("   ✗", v["field"], "|", v["text"], "|", v["reason"][:60])
    assert r_ok["ok"] is True, "clean Armenian must pass"
    assert r_bad["ok"] is False, "mixed-script must fail"
    print("glyph gate self-test: PASS")
