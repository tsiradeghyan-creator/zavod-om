# ZavodOM — the content zavod, with a spine

The Maghakian content zavod, rebuilt on the OpenMontage spine: **brain + enforcement**.
(README.md = upstream OpenMontage docs; THIS file is the ZavodOM entry point.)

## Start every session here
```bash
./.venv/bin/python lib/healthcheck.py     # 30s GREEN/RED signal (corpus, gates, manifests, render)
```

## The three layers
- **Spine** (OpenMontage, AGPLv3): `pipeline_defs/*.yaml` (gated stage DAGs), `schemas/artifacts/*.json`
  (24 schema-validated artifacts), `lib/` (loader, checkpoint, scoring, reviewer), `meta/reviewer` + `meta/checkpoint-protocol`.
- **Brain** (the zavod's 50 craft files): `skills/zavod-craft/` + `INDEX.md` wires each craft file to a
  pipeline stage/role/gate. Voice source = `~/Documents/Maghakian-Scripts/` (style-profile derives from it).
- **Arsenal**: `skills/providers/higgsfield-capabilities.md` — every agent knows the full Higgsfield toolset.

## Pipelines (general; projects/styles sit on top)
`zavod-reel`, `zavod-carousel`, `zavod-promo`. Director bench: `skills/pipelines/zavod/*-director.md`
(executive-producer + idea→script→scene→asset→edit→compose→publish).

## Hard, code-enforced gates (the 06-18 failure class — proven in lib/gatechain.py)
| Gate | File | Catches |
|---|---|---|
| Armenian glyph | `lib/armenian_glyph_gate.py` | Latin/Cyrillic inside Armenian words |
| Continuity | `lib/continuity_checker.py` | disappearing in-hand object / identity / architecture |
| Brand voice | `lib/brand_voice_check.py` | generic-AI tropes / drift |
| Delivery promise | `lib/delivery_promise.py` | motion-led silently downgraded to slideshow |
| Variation | `lib/variation_checker.py` | slideshow / generic scene plans |
| Schema | `schemas/artifacts/*.json` | malformed/vague artifacts (incl. scene_plan.staging/text_policy) |
| Gate-chain | `lib/gatechain.py` | the reviewer's dispatcher — runs the right gates per stage |

## Self-improvement (Scout) — wake-safe
`skills/meta/scout.md` + `lib/scout.py` + `library/known_capabilities.json` + `tools/com.zavodom.scout.plist`
(launchd, runs healthcheck first). Weekly: web-scan → dedup → score → gated upgrade memo → (on approval)
skill-creator drafts a skill / provider. Nothing auto-installs.

## Rules
Rule Zero: every production runs a pipeline (no ad-hoc prompt-and-pray). Armenian = Eastern Unicode only
(glyph gate). On-image text = overlay (AI-baked only for short display words that pass the glyph gate).
No stage advances without its gate + the human checkpoint (Անցիր առաջ / Փոխիր / Ինքդ որոշիր).

## Run (portable, any OS)
```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt   # spine deps
cd remotion-composer && npm install                                     # render runtime
# rendering uses portable ffmpeg discovery: system ffmpeg or @ffmpeg-installer
```
