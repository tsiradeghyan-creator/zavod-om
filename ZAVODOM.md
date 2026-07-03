# ZavodOM — the content zavod, with a spine

The Maghakian content zavod, rebuilt on the OpenMontage spine: **brain + enforcement**.
(README.md = upstream OpenMontage docs; THIS file is the ZavodOM entry point.)

## Start every session here
```bash
./.venv/bin/python lib/healthcheck.py     # 30s GREEN/RED signal (corpus, gates, manifests, render)
```

Then ask the owner before any production work:

```text
Ո՞ր ռեժիմով ենք աշխատում։
1. Քո հաստատումներով՝ փուլ առ փուլ։ Default. Ամեն փուլ ավարտվում է Agent Report-ով և կանգնում է մինչև «Անցիր առաջ»։
2. Ավտոմատ լրիվ սևագրային վազք։ Կարող եմ ներսում ստուգել, հետ ուղարկել ու սևագիր հավաքել, բայց չեմ հրապարակում, գումար չեմ ծախսում, իրավունք/դեմք/լոկացիա չեմ փակում և վերջնական չեմ հանձնում առանց քո հաստատման։

Ագենտներ՝ ՄՇՏԱԿԱՆ ՀՐԱՄԱՆ (owner, 2026-07-03). ամեն փուլ՝ ամբողջ bench-ով. փուլը չի փակվում, քանի դեռ բոլոր պարտադիր մասնագետները վճիռ չեն տվել (lib/bench_gate.py՝ code-enforced)։
```

If the owner says the script already exists, do not rewrite it by default: start from the
next unlocked stage, produce that stage's report, and wait for approval.

## The three layers
- **Spine** (OpenMontage, AGPLv3): `pipeline_defs/*.yaml` (gated stage DAGs), `schemas/artifacts/*.json`
  (24 schema-validated artifacts), `lib/` (loader, checkpoint, scoring, reviewer), `meta/reviewer` + `meta/checkpoint-protocol`.
- **Brain** (the zavod's 50 craft files + `SKILL.md` + `INDEX.md`): `skills/zavod-craft/` wires each craft file
  to a pipeline stage/role/gate. Voice source = `~/Documents/Maghakian-Scripts/` (style-profile derives from it).
- **Arsenal**: `skills/providers/higgsfield-capabilities.md` — every agent knows the full Higgsfield toolset.

## Pipelines (general; projects/styles sit on top)
`zavod-reel`, `zavod-carousel`, `zavod-promo`. Director bench: `skills/pipelines/zavod/*-director.md`
(executive-producer + idea→script→scene→asset→edit→compose→publish).

## Gate coverage
| Gate | Status | File | Catches |
|---|---|---|---|
| Armenian glyph | checkpoint-enforced | `lib/armenian_glyph_gate.py` | Latin/Cyrillic inside Armenian words |
| Continuity | checkpoint-enforced | `lib/continuity_checker.py` | disappearing in-hand object / identity / architecture |
| Brand voice | checkpoint-enforced | `lib/brand_voice_check.py` | generic-AI tropes / drift |
| Variation | checkpoint-enforced | `lib/variation_checker.py` | slideshow / generic scene plans |
| Schema | checkpoint-enforced | `schemas/artifacts/*.json` | malformed/vague artifacts (incl. scene_plan.staging/text_policy) |
| Delivery promise | reviewer-invoked, not checkpoint seam yet | `lib/delivery_promise.py` | motion-led silently downgraded to slideshow |
| Gate-chain | dispatcher | `lib/gatechain.py` | runs the right gates per stage |

## Self-improvement (Scout) — wake-safe
`skills/meta/scout.md` + `lib/scout.py` + `library/known_capabilities.json` + `tools/com.zavodom.scout.plist`
(launchd, runs healthcheck first). Weekly: web-scan → dedup → score → gated upgrade memo → (on approval)
skill-creator drafts a skill / provider. Nothing auto-installs.

## Rules
Rule Zero: every production runs a pipeline (no ad-hoc prompt-and-pray). Armenian = Eastern Unicode only
(glyph gate). On-image text = overlay (AI-baked only for short display words that pass the glyph gate).
Default mode: no stage advances without its gate + the owner's checkpoint (Անցիր առաջ / Փոխիր / Ինքդ որոշիր).
Autonomous mode may draft, retake, and verify internally, but publish/spend/rights-lock/final delivery still
require the owner's explicit approval.

## Run (portable, any OS)
```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt   # spine deps
cd remotion-composer && npm install                                     # render runtime
# rendering uses portable ffmpeg discovery: system ffmpeg or @ffmpeg-installer
```
