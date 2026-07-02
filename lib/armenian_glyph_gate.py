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

# High-frequency Armenian words in Latin transliteration ("barev dzez" class).
# Pure-Latin translit contains no mixed-script token, so the per-token checks are blind
# to it; this list closes that hole. Curated to be unambiguous against English/French
# ("apres", "scenar", "inch", "shat" were dropped as collisions) and checked against the
# Maghakian corpus 2026-07-02 (zero hits — the corpus is proper Armenian Unicode).
# Requires >=2 DISTINCT matches before flagging, so a stray loanword never fires alone.
TRANSLIT_TOKENS = [
    "barev", "dzez", "shnorhakalutyun", "heghinak", "inchpes", "inchu",
    "vonc", "vonts", "hima", "aysor", "menq", "menk", "duq", "duk", "irenq",
    "sirum", "uzum", "gitem", "chgitem", "khosum", "xosum", "grum", "asum",
    "anum", "karogh", "karox", "petq", "petk", "hayeren", "akhper", "akhpers",
    "axper", "aghjik", "axjik", "tgha", "txa", "kyanq", "kyank", "chka",
    "tsavum", "cavum", "hishum", "spasum", "lsum", "tesnum", "haskanum",
    "erevi", "yerevi", "bayc", "vorovhetev", "orovhetev",
]
TRANSLIT_RE = re.compile(
    r"\b(" + "|".join(sorted(TRANSLIT_TOKENS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def check_text(text: str, field: str = "") -> list[dict[str, str]]:
    """Return violations for a single string.

    Catches two failure modes:
      1. Mixed-script: an Armenian-bearing token that also contains Latin/Cyrillic letters
         (e.g. "Vanը", "Դարpասները") — the classic transliteration splice.
      2. Homoglyph masquerade: inside Armenian context, a token written entirely in
         Cyrillic look-alikes with NO Armenian letters (e.g. an Armenian word typed with
         Cyrillic "а/о/е/с/р/у/н"). Pure-Latin tokens are left alone here because English
         brand words ("Joshua Tree", "Airbnb") legitimately appear in Armenian copy;
         stray Cyrillic in Armenian content is, in practice, always wrong.
    """
    violations: list[dict[str, str]] = []
    if not text:
        return violations
    tokens = [m.group(0) for m in TOKEN.finditer(text)]
    armenian_context = any(ARMENIAN.search(t) for t in tokens)
    for tok in tokens:
        has_arm = bool(ARMENIAN.search(tok))
        bad_latin = LATIN.findall(tok)
        bad_cyr = CYRILLIC.findall(tok)
        if has_arm:
            # An Armenian-bearing token must NOT contain Latin or Cyrillic letters.
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
        elif bad_cyr and armenian_context:
            # No Armenian letters, but Cyrillic inside Armenian content → likely a
            # homoglyph masquerade / wrong-script word.
            confusables = "".join(sorted({c for c in tok if c in CONFUSABLES}))
            hint = f" (look-alike chars: '{confusables}')" if confusables else ""
            violations.append({
                "text": tok,
                "field": field,
                "reason": (
                    f"Cyrillic word in Armenian context — likely a homoglyph masquerade or "
                    f"wrong-script word{hint}. Retype it in proper Eastern Armenian Unicode."
                ),
            })
    # 3. Pure-Latin transliterated Armenian ("barev dzez" class): no token mixes scripts,
    #    so the per-token checks above can't see it. Two or more DISTINCT known translit
    #    words in one string → the text is Latin-script Armenian, which the language law bans.
    translit_hits = sorted({m.group(0).lower() for m in TRANSLIT_RE.finditer(text)})
    if len(translit_hits) >= 2:
        violations.append({
            "text": ", ".join(translit_hits),
            "field": field,
            "reason": (
                f"Transliterated Armenian detected — Latin-script Armenian words "
                f"({', '.join(translit_hits[:6])}). Rewrite the whole passage in proper "
                f"Eastern Armenian Unicode; transliteration is never allowed."
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
