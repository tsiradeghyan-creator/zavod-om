# Production Protocol — Դարպասավորված աշխատանք (GOVERNANCE LAW)

> The owner's standing law. Applies to EVERY station and FILM-MODE project, always.
> No autonomy across gates: a station does its own work, but **never advances the project
> to the next stage on its own.** At the end of each phase the responsible agent FREEZES,
> presents a Report (Checklist), and waits for the owner's single command.

## Opening question — պարտադիր
Before starting any project, ask:

```text
Ո՞ր ռեժիմով ենք աշխատում։
1. Քո հաստատումներով՝ փուլ առ փուլ։ Default. Ամեն փուլից հետո տալիս եմ հաշվետվություն ու սպասում եմ «Անցիր առաջ» հրամանին։
2. Ավտոմատ լրիվ սևագրային վազք։ Կարող եմ ներսում աշխատել, ստուգել ու հետ ուղարկել, բայց չեմ հրապարակում, գումար չեմ ծախսում, իրավունք/դեմք/լոկացիա չեմ փակում և վերջնական չեմ հանձնում առանց քո հաստատման։

Ո՞ր ագենտներով ենք գնում՝ ամբողջ բենչո՞վ, թե միայն տվյալ փուլին պետք եղողներով։
```

If the owner says **the script already exists**, do not rewrite it by default. Treat the
script as the locked input, identify the next open phase, produce only that phase's work,
then freeze for approval.

## Promo visual/video preflight law — պարտադիր
For `zavod-promo` and every generated/edited promo visual, a request like "սարքենք վիզուալ"
does **not** authorize final art, video generation, or a polished export. It authorizes a
decision board first.

Before any PNG, image edit, video clip, or motion render is produced, the owner must approve
these choices in order:

1. **Կադրի ընտրություն** — exact source photos/frames + why each one fits the hook.
2. **Վիզուալ ոճի ընտրություն** — 2-3 style directions with palette/grade references.
3. **Ֆոնտի ընտրություն** — font pair, title/caption hierarchy, safe-zone behavior.
4. **Կերպարների քաղաքականություն** — no people / hands / backs / silhouettes / licensed faces.
   Default: no identifiable faces unless rights and consent are explicitly approved.
5. **Կադրատախտակ** — every shot card lists source media, camera body/format, lens mm,
   aperture/DoF, camera move/rig, lighting recipe, color grade, duration, audio bed, and
   overlay text.
6. **Prompt pack** — final image/video prompt, negative prompt, model, params, cost estimate,
   and source media attachment plan. The owner approves every prompt before any generation.

Hard stops:
- No polished visual mockup/export before steps 1-4 are locked. Text-only option boards and
  source-contact-sheet markups are allowed.
- No Higgsfield, image, or video generation call before the exact prompt is approved.
- Route by the locked engine lane (`engine_lock`), and never mix the two:
  - **Higgsfield lane** — motion is generated via Higgsfield (`generate_video` with real source media
    attached); composition/overlay/assembly is **ffmpeg only** — **zero Remotion/Hyperframes**.
  - **Remotion lane** — programmatic build with **no AI footage**; composition is `remotion` or
    `hyperframes` (the render_runtime sub-choice).
- If the owner flags device/OS compatibility problems with a composition route, stop and present
  alternatives before rendering.

## Specialist-chain law — պարտադիր
The pipeline may keep broad artifact stages (`idea`, `script`, `scene_plan`, `assets`, `edit`,
`compose`, `publish`) for schema/checkpoint compatibility, but the work must run through the ordered
specialist sub-stages declared in the manifest. A broad stage is not permission to do all its work at
once.

Rules:
1. The Executive Producer must expose the current `stage.sub_stage` in every Agent Report.
2. Every sub-stage with `human_approval_default: true` freezes and waits for the owner's command.
3. No sub-stage can be skipped unless the owner explicitly says that input is locked
   (example: "սցենարը կա" skips only script-writing, then the next open phase is identified).
4. If there is no idea, the first active sub-stage is the writers' room brainstorm: 3-5 ideas,
   then freeze for selection.
5. After an idea is approved, the script group proceeds in order: expanded structure → scenes →
   dialogue → motives → shoot/render-ready script.
6. After script lock, the creative-language council proceeds in order: director → cinematographer →
   production designer → sound lead → editor → composer → colorist, then freezes.
7. Technical preparation and pre-production are separate gates: camera, optics, light, sound,
   format, storage; then casting, locations, references, schedule, costume, decor, props, tests.
8. Render/shoot/generation cannot begin until storyboard/shot cards and prompts/shoot setup are
   approved.
9. Post-production proceeds in order: story edit → rhythm → sound → music → color → VFX if needed
   → final technical QC.

## Producer's 10-step map
This is the creative-production map underneath the gates:

| # | Phase | Producer question | Output before gate |
|---|---|---|---|
| 1 | Գաղափարի ձևավորում | Ի՞նչ պատմություն է պատմվում, ինչո՞ւ է կարևոր, ինչ զգացողություն պետք է թողնի։ | գլխավոր գաղափար, ժանր, հերոս, կոնֆլիկտ, զգացողություն |
| 2 | Նախնական մշակում | Ինչպե՞ս է գաղափարը դառնում պատմության կմախք։ | աշխարհ, կարճ սինոփսիս, կերպարներ, սկիզբ/զարգացում/ավարտ, տոնայնություն |
| 3 | Սցենարի զարգացում | Սցենարը հետաքրքիր, իրագործելի և ռեժիսորական աշխատանքի պատրաստ է՞։ | տեսարաններ, երկխոսություն, շարժառիթներ, նկարահանման պատրաստ սցենար |
| 4 | Ստեղծագործական թիմ | Ովքե՞ր են որոշում ֆիլմի լեզուն։ | ռեժիսոր, սցենարիստ, օպերատոր, բեմադրող նկարիչ, ձայն, մոնտաժ, կոմպոզիտոր, գույն |
| 5 | Տեխնիկական նախապատրաստում | Ստեղծագործական ցանկությունը տեխնիկապես ո՞նց է իրականացվելու։ | տեսախցիկ, օպտիկա, լույս, ձայնագրում, ձևաչափ, նյութերի պահպանում |
| 6 | Նախաարտադրություն | Նկարահանման օրը ամեն ինչ պատրա՞ստ է։ | դերասաններ, լոկացիաներ, էսքիզներ, պլան, հագուստ, դեկոր, ռեկվիզիտ, փորձարկումներ |
| 7 | Նկարահանում | Ամեն օր նկարահանվող նյութը ծառայո՞ւմ է նույն պատմությանը։ | օրվա տեսարաններ, որակի ստուգում, տեխնիկական կարգապահություն, նյութի դիտում |
| 8 | Հետարտադրություն | Նյութը ինչպե՞ս է դառնում ֆիլմ։ | մոնտաժ, ռիթմ, ձայն, երաժշտություն, գույն, տեսողական էֆեկտներ |
| 9 | Վերջնականացում | Ֆիլմը պատկերի, ձայնի և տարբերակների մակարդակով պատրա՞ստ է։ | որակի ստուգում, ենթագրեր, գունային ամբողջականություն, վերջնական տարբերակներ |
| 10 | Ներկայացում | Ո՞ր միջավայրով է ֆիլմը հասնելու հանդիսատեսին։ | փառատոն, կինոթատրոն, առցանց թողարկում, մասնավոր դիտում, մամուլի նյութեր |

## The freeze law
1. A station completes ONLY its own phase, then **stops**.
2. It emits an **Agent Report** (the checklist below) confirming every item in its
   responsibility is resolved or flagged.
3. The system **freezes** and waits. It does NOT render, publish, spend, or hand off.
4. The owner gives ONE of three commands. Nothing moves until then.

## The three levers (owner's command after every report)
- **«Անցիր առաջ» (Approved).** The agent hands the project to the next gate.
- **«Փոխիր այս դետալը» (Veto).** The agent goes back and fixes exactly what was named
  (location, face structure, car model, line, palette…), then re-reports the same gate.
- **«Ինքդ որոշիր» (Delegate).** The owner authorizes me as **Co-Producer** to make the
  optimal creative/technical call on that item. It does not authorize publishing, spending,
  rights/likeness/location approval, or final delivery unless the owner explicitly says so.

## The gates (numbered agent chain)
Each gate = a freeze point with its own report.

| # | Agent (gate) | Stations | Locks before passing |
|---|---|---|---|
| 1 | **ԻԴԵԱ · ՍՑԵՆԱՐ · ԿԱՌՈՒՑՎԱԾՔ · ՌԱՍԿԱԴՐՈՎԿԱ** | idea-lab · serial-structure · style-profile · director-craft · storyboard | logline/turns, beats, shot cards, look bible |
| 2 | **ԳԵՂԱՐՎԵՍՏ · ՔԱՍԹԻՆԳ · ԻԴԵՆՏԻՏԵՏ** | art-department · production-team · identity-guard · ai-pipeline(identity-lock) | locations, props/subtext objects, character DESIGN + identity refs, costume/silhouette |
| 3 | **ՕՊԵՐԱՏՈՐ · AI ՌԵՆԴԵՐ** | cinematography · color-craft · ai-pipeline | engine choice, prompts, bake-off, consistency, render QC |
| 4 | **ՓՈՍՏ · ՁԱՅՆ · ՏԻՊՈԳՐԱՖԻԿԱ** | post-production · sound-craft · motion-design · localization | cut, grade, 4-layer sound, captions+glyph, subtitles |
| 5 | **ՊՐՈԴՅՈՒՍԻՆԳ · ԻՐԱՎՈՒՆՔ** | producer-craft · business-affairs | budget, rights/consent, C2PA, deliverables |
| 6 | **ՀՐԱՊԱՐԱԿՈՒՄ · ԱՃ** | playbook · carousel-template · growth-analytics | platform specs, schedule, first-hour plan |

## Agent Report template (every freeze emits this)
```
📋 ԱԳԵՆՏ <#>. <ԲԱԺԻՆ> | ՀԱՇՎԵՏՎՈՒԹՅՈՒՆ
- <item>: <value> [ԼՈՒԾՎԱԾ Է | ❓ ՔՈ ՈՐՈՇՈՒՄԸ ՊԵՏՔ Է]
- …
Սեփականատիրոջ հրամանին սպասող կարգավիճակ․ Անցնե՞նք <հաջորդ դարպաս>-ին։
   [Անցիր առաջ] · [Փոխիր <դետալ>] · [Ինքդ որոշիր]
```

## Rules for the report
- **Honesty gate.** Mark an item **[ԼՈՒԾՎԱԾ Է]** only if it truly is. Anything needing the
  owner's input (a face/identity reference, a real location, a brand-safety/rights call,
  a budget) is flagged **❓ ՔՈ ՈՐՈՇՈՒՄԸ ՊԵՏՔ Է** — never silently invented.
- **Hard gates still bind** (no faces in AI output unless licensed + consent; Armenian
  Unicode + glyph gate; rights before money). These don't wait for a lever — they're law.
- **One gate per report.** Don't bundle two stages' decisions into one freeze.
- **Co-Producer delegation** does not override the hard gates, the owner's prior vetoes, or
  the final approval rule.

## Station-brief law — 6-slot frame (absorbed from МЕТАФЛОРА Claudebook, 2026-07-04)

Every brief handed to a station/agent (EP → station, station → sub-agent, crew kanban task)
closes SIX slots — a weak brief offloads decisions onto the model and gets averaged mush back:

```
[դեր]      ով է պատասխանում, ում ձայնով, ինչն է արգելված (craft file reference counts)
[խնդիր]    ՄԵԿ բայ, ՄԵԿ արդյունք — առանց «և նաև»
[կոնտեքստ] ինչ է հայտնի՝ փաստեր, սահմանափակումներ, ինչ արդեն փորձվել է
[ֆորմատ]   արդյունքի կմախքը (schema/template/չափ)
[օրինակ]   մեկ էտալոն input→output (few-shot > նկարագրություն)
[չափանիշ]  3–5 ՍՏՈՒԳԵԼԻ ընդունման պայման — «լավը» չափվում է, ոչ թե զգացվում
```

**Repair diagnostics — երբ արդյունքը վատն է, նորոգիր ՄԵԿ սլոտ, ոչ ամբողջ բրիֆը:**

| Ախտանիշ | Կաղացող սլոտ | Ինչ ավելացնել |
|---|---|---|
| Տոնը «բոլորինն է» | դեր | ում ձայնով, ինչ է արգելված (brand-voice ref) |
| Հարևան խնդիրն է լուծել | խնդիր | մեկ բայ, մեկ արդյունք |
| Հորինել է ելակետեր | կոնտեքստ | փաստերը գրավոր, ինչ արդեն փորձված է |
| Ֆորմատը ամեն անգամ նոր է | ֆորմատ + օրինակ | կմախք + մեկ էտալոն |
| «Պատրաստ է», բայց ստուգելու բան չկա | չափանիշ | 3–5 ստուգելի պայման |

One slot per iteration — so it's visible WHAT fixed it. Versions + date live in the brief.
