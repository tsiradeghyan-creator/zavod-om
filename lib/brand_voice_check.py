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

# Armenian generic-AI / marketing-hype tropes. NOT a translation of the English list —
# derived from brand-voice.md's "How the brand never speaks" / "This-not-that" / Lexicon
# never-rules (no hype, no engagement-bait, no stated emotion, no corporate filler) and
# checked against the full Maghakian corpus (54 scripts + «Տակնուվրա» prose) on
# 2026-07-02: zero collisions («աննկարագրելի» was dropped — it occurs in real dialogue).
TROPES_HY = [
    # hype / superlative claims (brand law: earned image, not adjectives)
    "բացահայտեք", "բացահայտիր", "հեղափոխական", "անմոռանալի", "անկրկնելի",
    "եզակի հնարավորություն", "լավագույն ընտրություն", "համաշխարհային մակարդակ",
    # elevate-your / next-level calques
    "նոր մակարդակ", "բարձրացրեք ձեր", "անսահման հնարավորություններ",
    # engagement bait / urgency CTA (brand law: no "don't miss" energy)
    "մի բաց թողեք", "բաց մի թողեք", "միայն այսօր", "գրանցվեք հիմա", "հետևեք մեզ",
    # corporate filler / stated emotion (brand law: behaviour over statement)
    "մեր առաքելությունն", "անհատական մոտեցում", "մատչելի գներ", "վստահեք մեզ",
    "որակյալ ծառայություն", "երազանքներն իրականություն", "երազանքները իրականություն",
    # AI-translationese openers
    "այսօրվա աշխարհում", "ժամանակակից աշխարհում", "եկեք միասին", "պատրաստ ե՞ք",
    "սուզվեք", "գաղտնիքները բացահայտ",
]


def check(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        return {"ok": True, "verdict": "pass", "score": 0.0, "flags": []}
    low = text.lower()
    flags: list[str] = []
    for t in TROPES:
        if t in low:
            flags.append(f"generic trope: \"{t}\"")
    for t in TROPES_HY:
        if t in low:
            flags.append(f"generic trope (hy): \"{t}\"")
    # Excessive em-dashes are a classic AI tell.
    if text.count("—") >= 4:
        flags.append("em-dash overuse (>=4) — typical AI cadence; vary punctuation")
    # Exclamation spam — Latin "!" and the Armenian բացականչական «՜» count together.
    if text.count("!") + text.count("՜") >= 4:
        flags.append("exclamation spam (>=4, incl. Armenian ՜)")
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
    bad_hy = "Բացահայտեք գաղտնիքները մեր հեղափոխական ծառայության։ Բարձրացրեք ձեր բիզնեսը նոր մակարդակի։"
    clean_hy = "Մի մարդ օվկիանոս անցավ սիրո համար, որը գոյություն չուներ։"
    print("CLEAN    ->", check(clean)["verdict"], check(clean)["score"])
    r = check(bad)
    print("BAD      ->", r["verdict"], r["score"], r["flags"][:3])
    r_hy = check(bad_hy)
    print("BAD-HY   ->", r_hy["verdict"], r_hy["score"], r_hy["flags"][:3])
    print("CLEAN-HY ->", check(clean_hy)["verdict"], check(clean_hy)["score"])
    assert check(clean)["ok"] and not check(bad)["ok"]
    assert check(clean_hy)["ok"] and not check(bad_hy)["ok"]
    print("brand_voice gate self-test: PASS")
