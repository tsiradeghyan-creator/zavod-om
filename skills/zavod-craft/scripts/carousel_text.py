#!/usr/bin/env python3
"""carousel_text.py — Auto-layout Armenian text onto an AI-generated background.

Turns the Background-only render (the brand rule) into a ready-to-publish slide in one
command — no manual Canva pass. Renders proper Eastern Armenian Unicode in Noto Serif/Sans
Armenian or GHEA, with safe-zone-aware placement, and REFUSES to render any Armenian word
that contains a Latin/Cyrillic homoglyph (the glyph gate, enforced in code).

Usage:
    python3 carousel_text.py --bg slide-bg.png --spec slide.json --out slide-01.png

slide.json (one slide):
{
  "size": [1080, 1350],
  "safe": {"top": 0.08, "bottom": 0.12, "left": 0.07, "right": 0.07},
  "blocks": [
    {"text": "Սերը հասցե ուներ", "font": "noto-serif", "size": 92,
     "color": "#FAFAFA", "anchor": "top-center", "max_width": 0.86,
     "highlight": "#6450D2", "rotate": -1.5}
  ]
}
"""
import argparse, json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

ARM = re.compile(r'[԰-֏ﬓ-ﬗ]')
LAT = re.compile(r'[A-Za-z]')
CYR = re.compile(r'[Ѐ-ӿ]')
WORD = re.compile(r'[A-Za-zЀ-ӿ԰-֏ﬓ-ﬗ]+')

FONT_DIRS = ["/Library/Fonts", "/System/Library/Fonts", "/System/Library/Fonts/Supplemental",
             os.path.expanduser("~/Library/Fonts"), "/usr/share/fonts"]
FONT_ALIASES = {
    "noto-serif": ["NotoSerifArmenian", "Noto Serif Armenian"],
    "noto-sans":  ["NotoSansArmenian", "Noto Sans Armenian"],
    "ghea":       ["GHEAGrapalat", "GHEA Grapalat", "GHEAMariam", "Mk_Parz"],
}

def glyph_gate(text):
    bad = [w for w in WORD.findall(text) if ARM.search(w) and (LAT.search(w) or CYR.search(w))]
    if bad:
        sys.exit(f"GLYPH GATE FAILED — mixed-script Armenian token(s): {bad}. Fix before render.")

def find_font(alias):
    names = FONT_ALIASES.get(alias, [alias])
    for d in FONT_DIRS:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            base = os.path.splitext(f)[0].replace(" ", "")
            if any(base.startswith(n.replace(" ", "")) for n in names) and f.lower().endswith((".ttf", ".otf", ".ttc")):
                return os.path.join(d, f)
    return None

def wrap(draw, text, font, max_px):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_px:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg", required=True); ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    W, H = spec.get("size", [1080, 1350])
    safe = spec.get("safe", {"top": .08, "bottom": .12, "left": .07, "right": .07})
    img = Image.open(a.bg).convert("RGBA").resize((W, H))
    draw = ImageDraw.Draw(img)
    sx0, sx1 = int(W*safe["left"]), int(W*(1-safe["right"]))
    sy0, sy1 = int(H*safe["top"]), int(H*(1-safe["bottom"]))
    for b in spec["blocks"]:
        glyph_gate(b["text"])
        fp = find_font(b.get("font", "noto-serif"))
        if not fp:
            sys.exit(f"Font not found for '{b.get('font')}'. Install Noto Serif Armenian or GHEA.")
        font = ImageFont.truetype(fp, b.get("size", 80))
        maxw = int((sx1 - sx0) * b.get("max_width", 1.0))
        lines = wrap(draw, b["text"], font, maxw)
        lh = int(b.get("size", 80) * 1.18)
        block_h = lh * len(lines)
        anchor = b.get("anchor", "top-center")
        ay = sy0 if "top" in anchor else (sy1 - block_h if "bottom" in anchor else (sy0+sy1-block_h)//2)
        for i, ln in enumerate(lines):
            tw = draw.textlength(ln, font=font)
            ax = sx0 if "left" in anchor else (sx1 - tw if "right" in anchor else (sx0+sx1-tw)//2)
            y = ay + i*lh
            if b.get("highlight"):
                pad = int(b.get("size",80)*0.12)
                draw.rectangle([ax-pad, y+pad, ax+tw+pad, y+lh-pad], fill=b["highlight"])
            draw.text((ax, y), ln, font=font, fill=b.get("color", "#FAFAFA"))
    img.convert("RGB").save(a.out, quality=95)
    print(f"OK -> {a.out}  ({len(spec['blocks'])} block(s), glyph gate clean)")

if __name__ == "__main__":
    main()
