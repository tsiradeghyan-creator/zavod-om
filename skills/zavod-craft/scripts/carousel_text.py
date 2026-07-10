#!/usr/bin/env python3
"""carousel_text.py — Auto-layout Armenian text onto an AI-generated background.

Turns the Background-only render (the brand rule) into a ready-to-publish slide in one
command — no manual Canva pass. Renders proper Eastern Armenian Unicode in Noto Serif/Sans
Armenian or GHEA, with safe-zone-aware placement, and REFUSES to render any Armenian word
that contains a Latin/Cyrillic homoglyph (the glyph gate, enforced in code).

Layout guarantees (all enforced, render fails loudly instead of shipping a broken slide):
- Armenian punctuation (՝ ՛ ՞ ։ …) never triggers the glyph gate on adjacent Latin words.
- `rotate` (degrees, counter-clockwise) is applied to the whole block.
- Blocks sharing a vertical zone (top/center/bottom) stack with a gap — never overlap.
- Any block that exits the safe area, or any single word wider than max_width, is an error.

Usage (from the repo root ~/zavod-om/):
    python3 skills/zavod-craft/scripts/carousel_text.py --bg slide-bg.png --spec slide.json --out slide-01.png

slide.json (one slide):
{
  "size": [1080, 1350],
  "safe": {"top": 0.08, "bottom": 0.12, "left": 0.07, "right": 0.07},
  "gap": 24,
  "blocks": [
    {"text": "Սերը հասցե ուներ", "font": "noto-serif", "size": 92,
     "color": "#FAFAFA", "anchor": "top-center", "max_width": 0.86,
     "highlight": "#6450D2", "rotate": -1.5}
  ]
}
"""
import argparse, json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

# Armenian LETTERS only (Ա-Ֆ, ա-և, ligatures) — Armenian punctuation such as ՝ ՛ ՜ ՞ ։ ֊
# is deliberately excluded so that "promo՝" tokenizes as pure-Latin "promo" and passes.
ARM = re.compile(r'[Ա-Ֆա-ևﬓ-ﬗ]')
LAT = re.compile(r'[A-Za-z]')
CYR = re.compile(r'[Ѐ-ӿ]')
WORD = re.compile(r'[A-Za-zЀ-ӿԱ-Ֆա-ևﬓ-ﬗ]+')

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

def coverage_gate(font_path, text, alias):
    """Fail if the chosen font lacks glyphs for any character (tofu prevention).
    The Noto *Armenian* fonts carry no Latin/Cyrillic — mixed text needs another font/block."""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return  # soft-skip: PIL will still render, tofu risk stays on the operator
    try:
        cmap = TTFont(font_path, fontNumber=0).getBestCmap()
    except Exception:
        return
    missing = sorted({ch for ch in text if not ch.isspace() and ord(ch) not in cmap})
    if missing:
        sys.exit(f"FONT COVERAGE FAILED — '{alias}' ({os.path.basename(font_path)}) has no glyphs "
                 f"for {missing}. Split that text into its own block with a full-coverage font.")

def wrap(draw, text, font, max_px):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if draw.textlength(w, font=font) > max_px:
            sys.exit(f"LAYOUT FAILED — single word wider than max_width: «{w}». "
                     f"Reduce font size, raise max_width, or hyphenate.")
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_px:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def render_block_layer(b, font, lines, lh, measure):
    """Draw one block on its own transparent layer; return (layer, w, h)."""
    pad = int(b.get("size", 80) * 0.15)
    widths = [measure.textlength(ln, font=font) for ln in lines]
    bw, bh = int(max(widths)) + 2 * pad, lh * len(lines) + 2 * pad
    layer = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    anchor = b.get("anchor", "top-center")
    for i, ln in enumerate(lines):
        tw = widths[i]
        x = pad if "left" in anchor else (bw - pad - tw if "right" in anchor else (bw - tw) / 2)
        y = pad + i * lh
        if b.get("highlight"):
            hp = int(b.get("size", 80) * 0.12)
            d.rectangle([x - hp, y + hp, x + tw + hp, y + lh - hp], fill=b["highlight"])
        d.text((x, y), ln, font=font, fill=b.get("color", "#FAFAFA"))
    if b.get("rotate"):
        layer = layer.rotate(b["rotate"], resample=Image.BICUBIC, expand=True)
    return layer, layer.width, layer.height

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bg", required=True); ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding="utf-8"))
    W, H = spec.get("size", [1080, 1350])
    safe = spec.get("safe", {"top": .08, "bottom": .12, "left": .07, "right": .07})
    gap = int(spec.get("gap", 24))
    img = Image.open(a.bg).convert("RGBA").resize((W, H))
    measure = ImageDraw.Draw(img)
    sx0, sx1 = int(W*safe["left"]), int(W*(1-safe["right"]))
    sy0, sy1 = int(H*safe["top"]), int(H*(1-safe["bottom"]))
    top_cur, bottom_cur, center_cur = sy0, sy1, None
    placed = []  # (x0, y0, x1, y1, index)
    for idx, b in enumerate(spec["blocks"]):
        glyph_gate(b["text"])
        fp = find_font(b.get("font", "noto-serif"))
        if not fp:
            sys.exit(f"Font not found for '{b.get('font')}'. Install Noto Serif Armenian or GHEA.")
        coverage_gate(fp, b["text"], b.get("font", "noto-serif"))
        font = ImageFont.truetype(fp, b.get("size", 80))
        maxw = int((sx1 - sx0) * b.get("max_width", 1.0))
        lines = wrap(measure, b["text"], font, maxw)
        lh = int(b.get("size", 80) * 1.18)
        layer, bw, bh = render_block_layer(b, font, lines, lh, measure)
        anchor = b.get("anchor", "top-center")
        # vertical zone cursors: same-zone blocks stack instead of overlapping
        if "top" in anchor:
            ay = top_cur; top_cur = ay + bh + gap
        elif "bottom" in anchor:
            ay = bottom_cur - bh; bottom_cur = ay - gap
        else:
            ay = (sy0 + sy1 - bh) // 2 if center_cur is None else center_cur
            center_cur = ay + bh + gap
        ax = sx0 if "left" in anchor else (sx1 - bw if "right" in anchor else (sx0 + sx1 - bw) // 2)
        rect = (ax, ay, ax + bw, ay + bh)
        # out-of-bounds gate (safe area is the brand law, not a suggestion)
        if rect[0] < sx0 - 1 or rect[1] < sy0 - 1 or rect[2] > sx1 + 1 or rect[3] > sy1 + 1:
            sys.exit(f"LAYOUT FAILED — block {idx+1} («{b['text'][:30]}…») exits the safe area "
                     f"{rect} vs safe ({sx0},{sy0},{sx1},{sy1}). Reduce size/blocks or adjust anchors.")
        # cross-zone overlap gate
        for (px0, py0, px1, py1, pidx) in placed:
            if rect[0] < px1 and rect[2] > px0 and rect[1] < py1 and rect[3] > py0:
                sys.exit(f"LAYOUT FAILED — block {idx+1} overlaps block {pidx+1}. "
                         f"Move one to another zone or shrink text.")
        placed.append((*rect, idx))
        img.alpha_composite(layer, (int(ax), int(ay)))
    img.convert("RGB").save(a.out, quality=95)
    print(f"OK -> {a.out}  ({len(spec['blocks'])} block(s), glyph gate clean, layout verified)")

if __name__ == "__main__":
    main()
