# Աուդիտ — Round-7 մեխանիզմներ (2026-07-08)

Սա adversarial աուդիտ է՝ սոսկ round-7-ի 6 նոր/փոփոխված մեխանիզմների վրա (նախորդ
round-6-ի մեխանիզմները արդեն երկու անգամ աուդիտված են, չեն կրկնվում)։ Համատեքստ
նախորդ ռաունդներից տարբեր է․ round-7-ը ծնվել է ոչ թե «ինչպես կկոտրես»-ից, այլ
ռազմավարական եզրակացությունից՝ *նվազեցնել* ձևական բեռը՝ enforcement-ը չկորցնելով։
Ուրեմն այս անգամ հատուկ ուշադրություն դարձրու երկու ուղղությամբ ձախողման՝
(ա) նոր անվտանգության ծակ, (բ) թեթևացումը իրականում ոչինչ չի թեթևացրել /
կամ ապակառուցել է սխալ բանը։

**Պատասխանի ձևաչափ՝ ինչպես միշտ.**

```text
Հարց №
Վճիռ՝ ՀԱՍՏԱՏԵԼ | ՎԵՐԱՆԱՅԵԼ | ՄԵՐԺԵԼ
Գլխավոր դիտարկում՝
Կոնկրետ ձախողման սցենար՝
Ռիսկ՝ ցածր | միջին | բարձր | կրիտիկական
Պարտադիր փոփոխություն՝
```

---

## Մեխանիզմների ամփոփ

1. **Pipeline identity lock** (`lib/checkpoint.py::_enforce_project_pipeline_identity`) —
   project-ի առաջին տիպավորված (ոչ `None`) checkpoint-ը կողպում է pipeline_type-ը․
   հետագա գրառումը այլ տիպով (կամ `None`-ով տիպավորված project-ի մեջ) բլոկվում է։
   Երբեք-չտիպավորված project-ը մնում է unrestricted։
2. **Չափման շերտ** (`lib/production_metrics.py`) — `record_gate_block()`-ը գրանցում է
   ամեն hard block-ը փակ enum-ով (`real_defect|blocked_formality|false_block`) +
   պարտադիր evidence։ `record_production_row()`-ը project-ի per-run CSV տող է
   գրում, block-ի ընդհանուրները վերցնելով ուղիղ log-ից։ `gate_report()`-ը ≥50%
   formality ունեցող gate-երը նշում է որպես պարզեցման թեկնածու։
   `stopping_criterion_met()`-ը՝ 5 հաջորդական production, ≥80% first-preview
   acceptance, ≤1 missed defect։
3. **zavod-reel-fast** (`pipeline_defs/zavod-reel-fast.yaml`) — 4 փուլ (idea, scene_plan,
   compose, publish), manifest-ի `metadata.bench_roles`-ով հայտարարվող bench (idea՝
   story-hook+brand-voice-guard, scene՝ brand-voice-guard, compose/publish՝
   delivery-qc)։ Owner-գեյթված sub-stage ladder չկա։ `metadata.fast_lane.
   max_duration_seconds: 45`-ը enforce է `_enforce_fast_lane_eligibility`-ով՝
   ավելի երկար brief-ը idea փուլում բլոկվում է։ `required_bench(stage,
   pipeline_type)`-ը կարդում է manifest-ի bench_roles-ը, բացակայության դեպքում
   fallback է լինում ամբողջական default bench-ին (խիստ ուղղություն)։
4. **Concept similarity → warning** (`_validate_concept_selection`) — token-Jaccard
   ≥0.85 այլևս hard block չէ, միայն `logging.warning`։ Բառացի նույն label-ը
   (case-insensitive) մնում է hard block։ Կառուցվածքային պահանջները (≥3 ուղղություն,
   ընտրվածը options-ի մեջ, rejected_because ամեն մերժվածին) մնում են hard։
5. **Performance loop** (`lib/performance_loop.py`) — `save_performance_brief()`-ը
   append-only (կրկնվող `performance_id` → error)։ `concept_refs_violation()`-ը՝
   երբ ≥3 brief կա, ամեն նոր `concept_selection` decision-ը պարտադիր
   `performance_refs`-ում պիտի ունենա վերջին 3 `performance_id`-ները (subset
   ստուգում, ոչ exact match)։ Enforce է `_validate_decision_log_merge`-ի ներսում։
   Isolation՝ `ZAVOD_PERFORMANCE_DIR` env var, թեստերում autouse fixture-ով
   մեկուսացված։
6. **Hook rubric** (`lib/bench_gate.py::_hook_rubric_violation`) — `story-hook`
   դերի entry-ն պարտադիր ունի `rubric` դաշտ 5 բանալիով (int 1-5 ամեն մեկը),
   գումարը ≥18/25։ Բացակա/սխալ դաշտ կամ ցածր գումար → bench violation
   (`bench.story-hook: ...`)։ Այլ դերերի վրա ազդեցություն չունի։

---

## Ա. Pipeline identity lock

**1.** Lock-ը սկանավորում է project directory-ի ամեն `checkpoint_*.json` և առաջին
ոչ-«unknown» pipeline_type-ը վերցնում որպես ճշմարտություն։ Ինչպե՞ս կարող ես
շրջանցել՝ առանց նոր pipeline_type-ը ուղիղ գրելու (օր․ project directory-ի ֆայլային
մանիպուլյացիա, checkpoint ֆայլերի ջնջում/վերանվանում, կամ սկան-կարգի
կախվածություն)։

**2.** Lock-ը կիրառվում է `write_checkpoint`-ի սկզբում՝ մինչ որևէ այլ ստուգում։
Ի՞նչ կողմնակի ազդեցություն կամ performance ծախս ունի project-ի ամեն checkpoint-ի
վրա iterating-ը ամեն write-ի ժամանակ, և ինչպե՞ս կմասշտաբավորվի, եթե project-ը
ունենա տասնյակ checkpoint ֆայլ (retry-ներ, resume-ներ)։

## Բ. Չափման շերտ

**3.** `record_gate_block()`-ի դասակարգումը (`real_defect|blocked_formality|
false_block`) լրիվ ինքնահայտարարական է՝ ոչ մի կոդային ստուգում չի հաստատում, որ
`classifier`-ը (owner/agent) ազնիվ է դասակարգել։ Ինչպե՞ս գործակալը (ոչ չարամտորեն,
այլ ինքնավստահությունից) կարող է համակարգված կերպով ամեն իր իսկ block-ը
նշանակել `blocked_formality` կամ `false_block`՝ խուսափելով metric-ի վատացումից,
և ինչ ինքնաստուգում կփակի սա։

**4.** `gate_report()`-ի policy-ն է՝ ≥50% formality → «պարզեցման թեկնածու»։ Այս շեմը
կիրառելով քիչ նմուշի (2-3 production) վրա՝ ի՞նչ սխալ եզրակացության կհանգեցնի, և
ինչու՞ շեմը ինքնին (50%, ոչ, ասենք, min-N + statistical confidence) խնդրահարույց է։

## Գ. Fast-lane

**5.** Eligibility guard-ը (`_enforce_fast_lane_eligibility`) ստուգում է միայն
`brief.target_duration_seconds ≤ 45`։ Manifest-ի `metadata.fast_lane.
owner_override_required_if` ցուցակը (paid_client_delivery, new_series_launch,
legal_or_sensitive_topic) փաստագրված է, բայց ո՞ր կոդն է այն enforce անում։ Եթե
ոչ մեկը՝ սա փաստաթղթային ցանկություն է, ոչ դարպաս։ Կոնկրետ սցենար՝ ինչպե՞ս
paid client-ի reel-ը կանցնի fast-lane-ով unnoticed։

**6.** `required_bench(stage, pipeline_type)`-ը manifest-ից ընթերցում է
`bench_roles`։ Ի՞նչ է կանխում ցանկացած ուրիշ (ոչ-fast) manifest-ից նոր, ինքնահորինված
pipeline ավելացնելը՝ `metadata.bench_roles: {compose: []}` դատարկ ցուցակով, և դրանով
ամբողջ bench-ը զրոյացնելը legitimate-ի տեսք տալով։ (Ուշադրություն՝ կոդում կա
`isinstance(roles, list) and roles` ստուգում. արդյո՞ք դատարկ ցուցակը այս ստուգումով
անցնում, թե՞ fallback է լինում full bench-ին. ստուգիր երկուսն էլ սցենարները։)

## Դ. Concept similarity → warning

**7.** Warning-ը `logging.warning`-ով է գրվում, ոչ մի կառուցվածքային տեղում
(decision_log, checkpoint metadata) չի պահվում։ Եթե log ֆայլը ռոտացվում/ջնջվում է
կամ գործակալի stdout-ը ոչ ոք չի կարդում, ինչպե՞ս warning-ը դառնում է անտեսանելի,
և ի՞նչ նվազագույն փոփոխություն կպահեր հետագիծը structured տվյալում (ոչ
հրապարակային տեքստ)։

**8.** Հիմա միայն *literal* label-equality-ն է hard block։ Կրկնվող՝ բայց տարբեր
casing/whitespace/punctuation ունեցող label-ը (օր․ "Pool Party." vs "pool party")
կանցնի՞ որպես տարբեր, թե՞ casefold-ը արդեն ծածկում է սա։ Ստուգիր կոդը
(`la == lb` casefold-ից հետո) և տուր կոնկրետ եզրահանգում։

## Ե. Performance loop

**9.** `concept_refs_violation()`-ը subset ստուգում է (`performance_refs`-ը պիտի
ծածկի վերջին 3 id-ն), ոչ թե exact-3 պահանջում։ Ինչպե՞ս գործակալը (ցանկացած
դիտավորությամբ) կարող է «բավարարել» պահանջը՝ ավելացնելով բոլոր հայտնի
performance_id-ները `performance_refs`-ում (ոչ միայն relevant 3-ը), դարձնելով
ստուգումը միշտ trivially true, և ինչ լրացուցիչ ստուգում կփակեր սա։

**10.** `latest_performance_ids()`-ը սորտավորում է ըստ `published_at` string
արժեքի (lexicographic, ոչ parsed date)։ Ինչ ձևաչափային շեղում (timezone, ոչ-ISO
format, կամ պարզապես incorrect timestamp) կարող է շրջել «վերջին 3»-ի կարգը, և
ինչ իրական հետևանք կունենա, եթե concept decision-ը սխալ performance-ի հիման
վրա է կայացվում։

## Զ. Hook rubric

**11.** Rubric-ի 5 միավորները (1-5 ամեն մեկը, ≥18/25 շեմ) ամբողջությամբ LLM-ի
ինքնագնահատականն են՝ ոչ մի արտաքին ստուգում (օր․ մեկ այլ անկախ reviewer-ի
համեմատություն) դրանց դեմ։ Ինչպե՞ս գործակալը, ցանկանալով արագ անցնել gate-ը,
համակարգված rubric-ը կլրացնի բարձր (օր․ միշտ 4-5) առանց իրական հայեցողության,
և ի՞նչ մեխանիզմ (անգամ թեթևակի) կդժվարացներ սա՝ առանց rubric-ը կրկին կոդային
դատավոր դարձնելու։

**12.** Շեմը 18/25 է (72%)՝ կամայական թիվ։ Ինչո՞ւ 18-ը (ոչ 15, ոչ 20) ողջամիտ
կամ կամայական է, և ի՞նչ կպատահի, եթե ամբողջ ցուցակի 5 միավորներից մեկը
համակարգված misuse է լինում (օր․ միշտ `brand_specificity: 5`, մնացածները
իրական)՝ արդյունքում գումարը կեղծ բարձրանում է շեմից վեր։

## Է. Ինտեգրացիա և կողմնակի ազդեցություններ

**13.** Round-7-ի 6 մեխանիզմները միասին գործարկելիս (fast-lane project-ում
identity lock + bench_roles + fast_lane eligibility + hook rubric + concept
similarity warning + performance refs) — կա՞ մեկ իրական արտադրական սցենար, որտեղ
երկու մեխանիզմ իրար հակասում են կամ կրկնակի բլոկում են նույն բանը տարբեր
հաղորդագրությամբ, շփոթեցնելով գործակալին/owner-ին։

**14.** Ամբողջ round-7-ի նպատակը «նվազեցնել ձևական բեռը» էր։ Չափելով նոր
կոդի ծավալը (6 նոր/փոփոխված ֆայլ, նոր schema, նոր manifest, ~30 նոր թեստ)՝
իրապե՞ս պակասել է *ընդհանուր* համակարգային բարդությունը, թե՞ պարզապես
ավելացել է նոր շերտ (fast-lane) առանց հին շերտի (zavod-reel) նվազման, և
ընդհանուր բարդությունը զուտ աճել է։ Կոնկրետ չափանիշ առաջարկիր՝ ինչպես
որոշել սա։
