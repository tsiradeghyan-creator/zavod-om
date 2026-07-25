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

Ագենտների ընտրությունը ավտոմատ է․ համակարգը գործարկում է խնդրին համապատասխան ամենափոքր բավարար
թիմը։ Ամբողջ բենչը գործարկվում է միայն քո հստակ հրամանով։
```

If the owner says **the script already exists**, do not rewrite it by default. Treat the
script as the locked input, identify the next open phase, produce only that phase's work,
then freeze for approval.

## Universal routing law — պարտադիր

Before choosing a production path, create a schema-valid `content_spec` and route it through
`lib/content_router.py`. The requested format and primary modality must be compatible. If no audited
route exists, stop with a routing error; do not disguise the request as the nearest video format.

Five Zavod manifests are currently available:

| Route | Use |
|---|---|
| `zavod-content` | social post, caption, article, newsletter, screenplay, series episode, stage play |
| `zavod-carousel` | slide-based image/mixed storytelling |
| `zavod-reel` | full short-video production |
| `zavod-reel-fast` | explicitly selected, audited short-video fast lane |
| `zavod-promo` | promotional image/video/mixed production with preflight locks |

Other supported formats—such as talking head, screen demo, podcast repurposing, localization,
documentary, or character animation—route to their existing OpenMontage manifests. The router's
decision, not the nearest-sounding Zavod manifest, is authoritative.

A `campaign_package` is an explicit governed bundle, not one oversized pipeline. The router assigns
its primary and companion pipelines while preserving the same master promise.

At intake, `creative_identity` locks authorial voice independently from optional visual identity.
Strict Maghakian handwriting may therefore be active while palette, typography, and other visual
branding stay neutral.

## Automatic agent activation law — պարտադիր

Every non-trivial request must pass through the typed agent control plane before craft work begins.
The host-neutral handoff and receipt rules are in `skills/meta/agent-routing.md`, and the flow is:

```text
schema-valid request → deterministic route → isolated dispatch waves → hash-linked ledger receipts
→ hash-bound synthesis candidate → independent final verification → pipeline checkpoints
→ owner-gated action
```

1. Validate `agents/registry.yaml`, its agent cards, referenced playbooks, and platform-adapter files.
2. Record every selected and rejected agent with its score and concrete reasons. If a required
   capability has no eligible agent, block instead of silently assigning the nearest role.
3. Dispatch dependency-safe waves through the active host adapter. Parallel work is allowed only for
   cards marked `parallel_safe`; later waves wait for required dependencies.
4. A task counts as completed only when the append-only ledger has the executor type, isolated run ID,
   exact output hash, and declared evidence. A role name in prose is not an execution receipt.
5. The Executive Producer may synthesize only receipt-backed contributions. It must preserve dissent
   and blockers, then lock the exact candidate hash before final review.
6. The independent `quality-auditor` must use a different isolated run from every producer and must
   challenge that exact candidate. A `revise` or `reject` verdict requires a new hash-linked plan;
   the Executive Producer cannot self-certify or rewrite the terminal result in place.

A **role playbook** is a craft instruction file used inside a task. A **real agent execution** is a
typed registry card actually dispatched by the host and proven by the ledger receipt above. If the host
cannot launch isolated workers, the run must be labeled `single_context_simulation`; it is a degraded
planning/rehearsal mode and can never satisfy the independent-audit gate or support a multi-agent claim.

Publishing, paid generation, material runtime/provider changes, rights or likeness commitments,
destructive changes, and final delivery remain owner-gated. Approval must be bound to the exact action,
asset set, diff, or payload hash; a prior general approval cannot authorize a changed action.

### Written-content no-render lane

`zavod-content` has four real stages:

```text
idea → script → quality → publish
```

It does not manufacture scene, asset, edit, compose, or render work for a text-only deliverable.
The `quality` stage is written-content post-production: structural edit, factual review, authorial-
voice review, language/copy edit, channel adaptation, accessibility, rights readiness, and delivery
completeness. A single draft may contain one deliverable or an exact package matching the locked
`content_spec`. The aggregate quality report must cover each promised deliverable exactly once, run
all eight checks exactly once per item, bind each item to the exact reviewed payload SHA-256, and
carry no `revise` result or open issue.

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
Media pipelines may keep broad artifact stages (`idea`, `script`, `scene_plan`, `assets`, `edit`,
`compose`, `publish`) for schema/checkpoint compatibility; `zavod-content` uses its four-stage lane.
In every route, work must run through the ordered specialist sub-stages declared in that manifest.
A broad stage is not permission to do all its work at once.

Rules:
1. The Executive Producer must expose the current `stage.sub_stage` in every Agent Report.
2. Every sub-stage with `human_approval_default: true` freezes and waits for the owner's command.
3. No sub-stage can be skipped unless the owner explicitly says that input is locked
   (example: "սցենարը կա" skips only script-writing, then the next open phase is identified).
4. If there is no idea, the first active sub-stage is the writers' room brainstorm: 3-5 ideas,
   then freeze for selection.
5. After an idea is approved, the script group uses the format-appropriate structure. Narrative
   media may proceed through expanded structure → scenes → dialogue → motives → shoot/render-ready
   script; written formats use structure → blind candidate bake-off → authorial-voice/accuracy pass → final draft.
6. After script lock, the creative-language council proceeds in order: director → cinematographer →
   production designer → sound lead → editor → composer → colorist, then freezes.
7. Technical preparation and pre-production are separate gates: camera, optics, light, sound,
   format, storage; then casting, locations, references, schedule, costume, decor, props, tests.
8. Render/shoot/generation cannot begin until storyboard/shot cards and prompts/shoot setup are
   approved.
9. Media post-production proceeds in order: story edit → rhythm → sound → music → color → VFX if
   needed → final technical QC. Written-content post-production uses the `quality` sequence above.

## Blind candidate bake-off law

A `zavod-content` script checkpoint cannot close with a prose claim that alternatives were explored.
It requires the schema-valid `candidate_bakeoff` artifact:

1. three to five complete schema-valid draft candidates;
2. hidden generator labels and hidden system preference during review;
3. unique candidate IDs and verified canonical draft hashes;
4. at least two declared creative difference axes across the set;
5. materially different authored text, not cosmetic rewrites;
6. one explicit rejection reason for every unselected candidate;
7. exact canonical hash identity between the selected candidate draft and the final `script` artifact.

Any edit after selection creates a different draft and requires a new bake-off identity; the selected
label cannot be used to smuggle in an unreviewed final script.

## Strict Maghakian Script DNA law

When `creative_identity.authorial_voice.mode` is `strict`, the authorial profile and report are not
advice—they are checkpoint inputs. The script stage requires:

1. the pinned `maghakian-script-v1` profile and selected register;
2. the unchanged `creative_identity` and `content_spec` from intake;
3. an `authorial_voice_report` covering all seven criteria;
4. draft/profile hashes, real draft excerpts, and references inside the pinned corpus snapshot;
5. passing Unicode, format, register, generic-trope, and minimum-score checks.

Literary judgment remains human/reviewer work. The code verifies that the judgment is attached to
the actual draft and actual corpus evidence. Visual identity is governed separately and may remain
neutral.

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

**Mode interaction (removes the Mode-2 contradiction).** The freeze law above describes
**Mode 1 (default)**. In **Mode 2 («Ավտոմատ լրիվ սևագրային վազք»)** the per-sub-stage freeze is
*deferred, not cancelled*: the agent still emits every Agent Report, but appends them to a run log
and continues to the next sub-stage without waiting. Only the **hard stops always freeze in both
modes** — publishing, spending money, rights/likeness/location commitments, prompt-approved
generation calls (Promo preflight law), and final delivery. At the end of a Mode-2 run the full
report log is presented as one batch for the owner's levers.

## The three levers (owner's command after every report)
- **«Անցիր առաջ» (Approved).** The agent hands the project to the next gate.
- **«Փոխիր այս դետալը» (Veto).** The agent goes back and fixes exactly what was named
  (location, face structure, car model, line, palette…), then re-reports the same gate.
- **«Ինքդ որոշիր» (Delegate).** The owner authorizes me as **Co-Producer** to make the
  optimal creative/technical call on that item. It does not authorize publishing, spending,
  rights/likeness/location approval, or final delivery unless the owner explicitly says so.

## The gates (numbered agent chain)
Each gate = a freeze point with its own report.

For `zavod-content`, the gate chain is:

| # | Gate | Locks before passing |
|---|---|---|
| 1 | **INTAKE + CONCEPT** | `content_spec`, deterministic route, acceptance criteria, `creative_identity`, selected concept |
| 2 | **DRAFT + SCRIPT DNA** | blind 3–5 candidate proof, selected/final hash identity, structured draft or exact package, unchanged locks, claims, story bible when narrative, strict voice evidence when active |
| 3 | **EDITORIAL POST-PRODUCTION** | every promised deliverable exactly once, all eight checks, exact payload hash, no open issue; variants preserve the master promise |
| 4 | **PRESENTATION** | owner decision; final export/publish requires exact local payload + matching rights hash; publish also requires returned URL |

The six-gate chain below governs visual/media production:

| # | Agent (gate) | Stations | Locks before passing |
|---|---|---|---|
| 1 | **ԻԴԵԱ · ՍՑԵՆԱՐ · ԿԱՌՈՒՑՎԱԾՔ** | idea-lab · serial-structure · style-profile · director-craft | logline/turns, beats, look bible |
| 2 | **ԳԵՂԱՐՎԵՍՏ · ՔԱՍԹԻՆԳ · ԻԴԵՆՏԻՏԵՏ · ՌԱՍԿԱԴՐՈՎԿԱ** | art-department · production-team · identity-guard · ai-pipeline(identity-lock) · storyboard | locations, props/subtext objects, character DESIGN + identity refs, costume/silhouette, shot cards (storyboard-ը ՊԱՀԱՆՋՈՒՄ է art-department-ի լոկացիա/props/կերպար-դիզայնը որպես մուտք, դրա համար է այս դարպասում) |
| 3 | **ՕՊԵՐԱՏՈՐ · AI ՌԵՆԴԵՐ** | cinematography · color-craft · ai-pipeline | engine choice, prompts, bake-off, consistency, render QC |
| 4 | **ՓՈՍՏ · ՁԱՅՆ · ՏԻՊՈԳՐԱՖԻԿԱ** | post-production · sound-craft · motion-design · localization | cut, grade, 4-layer sound, captions+glyph, subtitles |
| 5 | **ՊՐՈԴՅՈՒՍԻՆԳ · ԻՐԱՎՈՒՆՔ** | producer-craft · business-affairs | budget, rights/consent, C2PA, deliverables |
| 6 | **ՀՐԱՊԱՐԱԿՈՒՄ · ԱՃ** | playbook · carousel-template · growth-analytics | platform specs, schedule, first-hour plan |

## Agent Report template (every freeze emits this)
```
📋 ԱԳԵՆՏ <#>. <ԲԱԺԻՆ> | ՀԱՇՎԵՏՎՈՒԹՅՈՒՆ
Փուլ․ <stage>.<sub_stage>   ← պարտադիր (Specialist-chain law, կանոն 1)
Գործարկված ագենտներ․ <agent IDs>
Կատարման ապացույցներ․ <executor type / isolated run ID / receipt refs>
Մատյանի վերջնական հեշ․ <SHA-256>
Կատարման ռեժիմ․ <isolated execution | single_context_simulation>
QC-Continuity: PASS/FAIL (ledger կցված)   ← պարտադիր frame/shot արտադրող փուլերում (qc-continuity-gate.md)
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
  Unicode + glyph gate; rights before money). A final local export must exist, match its declared
  SHA-256, and have a matching rights row. Both `exported` and `published` states need that exact local
  payload; a published entry must also carry the returned URL. Claimed `signed`/`verified` C2PA status
  requires a real manifest file and matching declared hash. A file hash proves file identity; it does
  not create or cryptographically verify a C2PA signature. These don't wait for a lever — they're law.
- **One gate per report.** Don't bundle two stages' decisions into one freeze.
- **Co-Producer delegation** does not override the hard gates, the owner's prior vetoes, or
  the final approval rule.
- **Agent-claim gate.** A list of role rulings or one-context self-review cannot be reported as
  multi-agent execution. Report the activated card IDs, executor/run receipts, ledger head, and any
  degraded mode explicitly.
- **Superiority-claim gate.** Green schemas, unit tests, and internal scores prove contract integrity,
  not world leadership. “Best in the world” may be stated only after a versioned blind evaluation
  against named current baselines on identical briefs, inputs, budgets, and rubrics, with repeated
  runs, independent expert preference evidence, and disclosed failures and limits.

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
