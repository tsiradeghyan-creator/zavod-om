---
name: content-zavod
description: ZavodOM craft brain for Maghakian Script Writing Agency. Use for zavod, carousel, reel, script, post, promo, and film-mode production, but always through the ZavodOM pipeline spine, manifests, gates, and owner checkpoints.
metadata:
  version: 2.0.0
  owner: Ani Maghakyan / Maghakian Script Writing Agency
  status: canonical-zavodom-brain
---

# Content Zavod — ZavodOM Brain

This skill is the craft brain inside **ZavodOM**. It is not a prose-only workflow.
Every production must run through:

- `~/zavod-om/ZAVODOM.md`
- `pipeline_defs/zavod-reel.yaml`, `zavod-carousel.yaml`, or `zavod-promo.yaml`
- `skills/zavod-craft/INDEX.md`
- `skills/zavod-craft/production-protocol.md`

## Required opening question

Before doing any production work, ask:

```text
Ո՞ր ռեժիմով ենք աշխատում։
1. Քո հաստատումներով՝ փուլ առ փուլ։ Default. Ամեն փուլից հետո տալիս եմ հաշվետվություն ու սպասում եմ «Անցիր առաջ» հրամանին։
2. Ավտոմատ լրիվ սևագրային վազք։ Կարող եմ ներսում աշխատել, ստուգել ու հետ ուղարկել, բայց չեմ հրապարակում, գումար չեմ ծախսում, իրավունք/դեմք/լոկացիա չեմ փակում և վերջնական չեմ հանձնում առանց քո հաստատման։

Ո՞ր ագենտներով ենք գնում՝ ամբողջ բենչո՞վ, թե միայն տվյալ փուլին պետք եղողներով։
```

Default is **քո հաստատումներով՝ փուլ առ փուլ** unless the owner explicitly chooses the
automatic draft run.

## Owner approval law

- Every stage ends with an Agent Report.
- In owner-gated mode, every output must be approved before the next phase starts.
- The only advance command is **«Անցիր առաջ»**.
- The owner can veto with **«Փոխիր այս դետալը»**.
- The owner can delegate a bounded choice with **«Ինքդ որոշիր»**, but that never authorizes
  publish, spend, rights/likeness/location approval, or final delivery.
- If the owner says the script already exists, treat it as locked input and start from the
  next open phase. Do not rewrite the script unless asked.

## Producer map

The production map lives in `production-protocol.md`:

1. Գաղափարի ձևավորում
2. Նախնական մշակում
3. Սցենարի զարգացում
4. Ստեղծագործական թիմի ձևավորում
5. Տեխնիկական նախապատրաստում
6. Նախաարտադրություն
7. Նկարահանում
8. Հետարտադրություն
9. Վերջնականացում
10. Ներկայացում

## Stage routing

Load only the craft files for the current stage from `INDEX.md`.

- Idea/script/story: `idea-lab.md`, `serial-structure.md`, `style-profile.md`, `brand-voice.md`
- Scene/look: `director-craft.md`, `cinematography.md`, `storyboard.md`, `art-department.md`, `style-rider.md`
- Assets/render: `ai-pipeline.md`, `background-environment-artist.md`, `motion-design.md`, provider docs
- Edit/finish: `post-production.md`, `sound-craft.md`, `compositor.md`, `mastering-delivery-qc.md`
- Publish/growth: `playbook.md`, `growth-analytics.md`
- Governance/QC: `production-protocol.md`, `pre-advance-council.md`, `auto-verification-loop.md`, `qc-continuity-gate.md`

## Hard rules

- Armenian text must be proper Eastern Armenian Unicode only.
- Armenian body text goes through overlay/Canva-style text, not AI-baked text.
- AI-baked Armenian is allowed only for short display words that pass the glyph gate.
- No actor faces, likenesses, copyrighted stills, music, locations, or rights-sensitive material without explicit approval.
- Max 5 hashtags total when publishing.
- Label realistic AI video per platform rules.
- For promo/generative visual work, never produce polished art or video before the owner locks:
  source frame, visual style, typography, character/people policy, technical storyboard, and prompt.
- Two mutually-exclusive engine lanes, asked up front and locked in `engine_lock` (never mixed):
  **Higgsfield** = AI footage (real source media attached) + **ffmpeg** overlay/assembly, **zero Remotion**;
  **Remotion** = programmatic build, no AI footage, compose via `remotion`/`hyperframes`.

## Reporting template

```text
📋 ԱԳԵՆՏ <#>. <ԲԱԺԻՆ> | ՀԱՇՎԵՏՎՈՒԹՅՈՒՆ
- Արվածը՝ ...
- Ստուգված դարպասները՝ ...
- Բաց հարցերը՝ ... [ԼՈՒԾՎԱԾ Է | ❓ ՔՈ ՈՐՈՇՈՒՄԸ ՊԵՏՔ Է]
- Հաջորդ փուլը՝ ...

Սպասում եմ հրամանին՝ [Անցիր առաջ] · [Փոխիր <դետալ>] · [Ինքդ որոշիր]
```
