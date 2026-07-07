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

import base64
import html as _html
import re
import unicodedata
import urllib.parse
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


# Round-6 #7 (external audit №4): the gate checked only the immediately visible string,
# but text often materializes at a later decode/render step — Latin transliteration hidden
# in a base64 `data:` URI inside an SVG, a percent-encoded caption, a \uXXXX-escaped JSON
# splice, or an HTML entity. Decode every such layer (bounded depth) and sweep the result.
_B64_DATA_URI = re.compile(r"data:[\w.+/-]*;base64,([A-Za-z0-9+/=\s]{8,})")
_BARE_B64 = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{24,}={0,2}")
_PCT_ESC = re.compile(r"%[0-9A-Fa-f]{2}")
_U_ESC = re.compile(r"\\u([0-9A-Fa-f]{4})")
_HTML_ENT = re.compile(r"&(#\d+|#x[0-9A-Fa-f]+|[A-Za-z]+);")
_DECODE_DEPTH = 3


def _decoded_payloads(text: str) -> list[tuple[str, str]]:
    """Text layers hiding inside `text` that only appear after a decode step."""
    out: list[tuple[str, str]] = []
    blobs = [m.group(1) for m in _B64_DATA_URI.finditer(text)]
    blobs += [m.group(0) for m in _BARE_B64.finditer(text)]
    for blob in blobs:
        blob = re.sub(r"\s+", "", blob)
        blob += "=" * (-len(blob) % 4)  # regex word-boundaries may shave the padding
        try:
            raw = base64.b64decode(blob, validate=True)
            decoded = raw.decode("utf-8")
        except Exception:
            continue  # binary payload — nothing textual to sweep
        if decoded.strip():
            out.append((decoded, "base64"))
    if _PCT_ESC.search(text):
        try:
            decoded = urllib.parse.unquote(text, errors="strict")
        except Exception:
            decoded = text
        if decoded != text:
            out.append((decoded, "percent-encoding"))
    if _U_ESC.search(text):
        decoded = _U_ESC.sub(lambda m: chr(int(m.group(1), 16)), text)
        if decoded != text:
            out.append((decoded, "unicode-escape"))
    if _HTML_ENT.search(text):
        decoded = _html.unescape(text)
        if decoded != text:
            out.append((decoded, "html-entity"))
    return out


def check_text(text: str, field: str = "", _depth: int = 0) -> list[dict[str, str]]:
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

    # 0. Invisible format/zero-width characters spliced INTO WORDS. 2026-07-04 red-team: a
    #    zero-width joiner (U+200D) inside an Armenian word passed as "clean" — invisible to
    #    the eye and to the per-token script checks, but it breaks shaping and defeats text
    #    filters. Flag a Cf/soft-hyphen char only when it sits next to a LETTER (the splice
    #    attack); the same joiners between emoji (👨‍👩‍👧, 🏳️‍🌈) are legitimate caption
    #    sequences (2026-07-04 probe) and must not be flagged.
    #    Scope the check to letters of scripts where a zero-width/format char between letters
    #    is never linguistically needed — Armenian, Latin, Cyrillic — so its presence there is
    #    always a splice. Arabic/Persian and Indic scripts legitimately use ZWNJ/ZWJ
    #    (U+200C/U+200D) as joiners, so a format char next to THOSE letters is left alone
    #    (2026-07-06: legit Persian ZWNJ "می‌روم" was being false-rejected).
    def _joinerless_letter(ch: str) -> bool:
        return bool(ch) and bool(ARMENIAN.search(ch) or LATIN.search(ch) or CYRILLIC.search(ch))

    spliced = set()
    for i, ch in enumerate(text):
        if unicodedata.category(ch) == "Cf" or ch == "­":
            prev_ch = text[i - 1] if i > 0 else ""
            next_ch = text[i + 1] if i + 1 < len(text) else ""
            if _joinerless_letter(prev_ch) or _joinerless_letter(next_ch):
                spliced.add(ch)
    if spliced:
        names = ", ".join(f"U+{ord(ch):04X}" for ch in sorted(spliced))
        violations.append({
            "text": text[:40],
            "field": field,
            "reason": (
                f"Invisible format/zero-width character(s) [{names}] spliced into text — "
                "strip them; only visible Eastern Armenian Unicode is allowed inside words."
            ),
        })

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
    # 4. Decode-sweep (round-6 #7): text that only materializes after base64 / percent /
    #    \uXXXX / entity decoding gets the SAME checks, bounded depth against decode bombs.
    if _depth < _DECODE_DEPTH:
        for decoded, how in _decoded_payloads(text):
            violations += check_text(decoded, f"{field}<decoded:{how}>", _depth + 1)
    return violations


def _walk(obj: Any, path: str = "") -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if isinstance(obj, str):
        out += check_text(obj, path)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            # Dict KEYS are text surfaces too — an invisible/homoglyph char hidden in a key
            # must not slip past because we only walked values (2026-07-06 dry re-probe).
            if isinstance(k, str):
                out += check_text(k, f"{path}.<key>{k}" if path else f"<key>{k}")
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
