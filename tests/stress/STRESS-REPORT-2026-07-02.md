# ZavodOM Stress Report — 2026-07-02

Օպերատոր՝ Claude (ավտոմատ սևագրային ռեժիմ, զրո credit)։ Brief՝ `tests/stress/STRESS-TEST-BRIEF-2026-07-02.md`։
Ծախսված credit՝ **0**։ Հրապարակում՝ **0**։ Git commit՝ **0**։
Առաջին անցում՝ կոդի ուղղում 0 (միայն արձանագրում)։ **Երկրորդ անցում (owner-ի «Անցիր առաջ»-ից հետո)՝
P0 + P1 + P1.5 + delivery-promise seam ուղղված. տես §6 և աղյուսակի AFTER սյունը։ P2-ը backlog-ում է։**

## 1. Ամփոփում

Գլխավոր backtest-ը **անցավ**. continuity gate-ը 2026-06-18-ի իրական «անհետացող բաժակի» վիդեոյի վրա
տվեց **FAIL՝ բաժակի անհետացումն անունով նշված** (f04→f06 միջակայքում, ցատկի օդային ֆազայում), իսկ
ուղղված v2-ն ու երեք հսկիչ clip-երը ստացան PASS՝ առանց false-positive-ի։ Checkpoint seam-ը իրոք
**բլոկում է** (exception), ոչ թե warning է տալիս՝ և՛ կեղտոտ script/scene_plan-ի, և՛ compose-ում վատ
continuity report-ի դեպքում. dry run-ի negative test-ում հենց 06-18 դասի արտեֆակտը մերժվեց seam-ում։
Երկու իսկական false-negative գտնվեց՝ (1) brand-voice gate-ը **հայերեն** generic-AI տրոփերը չի տեսնում
(TROPES ցուցակը միայն անգլերեն է), (2) glyph gate-ը մաքուր լատինատառ տառադարձված հայերենը («barev dzez»)
չի բռնում, քանի որ բառի ներսում խառնուրդ չկա։ Գտնվեց նաև մեկ **BROKEN հակասություն**. seam-ը continuity
report-ները փնտրում է `render_report.continuity_reports`-ում, բայց render_report-ի schema-ն
(`additionalProperties: false`) այդ դաշտը **մերժում է** — այդ երթուղով gate-ը երբեք չի կրակի (աշխատում է
միայն `artifacts.continuity_reports` առանձին բանալիով)։ Delivery-promise-ի հայտնի բացը վերարտադրվեց
կոնկրետ. motion-led խոստումով slideshow-ն (6/6 slide cut) checkpoint seam-ով անցնում է առանց բլոկի, թեև
ուղիղ կանչով `validate_cuts`-ը նույն մուտքին տալիս է invalid (motion ratio 0% < 70%)։ Dry pipeline run-ը
իրական նյութով անցավ ամբողջությամբ. scene_plan → assets → edit → compose բոլոր checkpoint-ները գրվեցին,
gate-երը կանաչ, և ffmpeg-ով հավաքվեց 10.0վ 1080×1920 սևագիր teaser՝ զրո գեներացիայով։

## 2. Արդյունքների աղյուսակ

| Gate | Test case | Expected | Actual (BEFORE) | Verdict | AFTER (fix pass, §6) |
|---|---|---|---|---|---|
| continuity | 01-A-pooljump.mp4 (ՎԱՏ, ground truth) | REJECT՝ բաժակն անունով | FAIL. «drinking glass in hand» not continuous, f04→f06 անհետացում + բոնուս՝ wardrobe morph f05 | **PASS** | — (անփոփոխ) |
| continuity | 01-A-pooljump-v2.mp4 (ուղղված) | PASS | PASS (բաժակը ձեռքից դուրս է գալիս ցատկից ԱՌԱՋ՝ կոհերենտ) | **PASS** | — |
| continuity | 02-D-bbqbar.mp4 (հսկիչ) | PASS | PASS (8/8 կադր կայուն) | **PASS** | — |
| continuity | 03-C-grouppool.mp4 (հսկիչ) | PASS | PASS (8/8 կադր կայուն) | **PASS** | — |
| continuity | 04-B-twilight.mp4 (հսկիչ) | PASS | PASS (գրեթե static, ամեն ինչ կայուն) | **PASS** | — |
| glyph | (ա) տառադարձված հայերեն «barev dzez, heghinak» | ցանկալի՝ BLOCK | ok=True, անցավ | **FALSE-NEGATIVE** | ✅ **FIXED** — BLOCK (translit detector, ≥2 token) |
| glyph | (բ) խառը գիր «Vanը Հայկական» | BLOCK | BLOCK (Mixed-script Armenian word) | PASS | ✅ դեռ BLOCK |
| glyph | (գ) մաքուր արևելահայերեն | PASS | PASS | PASS | ✅ դեռ PASS |
| glyph | (դ) էմոջի + հայերեն | PASS (չփակի) | PASS | PASS | ✅ դեռ PASS |
| glyph | (դ) ամբողջական ռուսերեն նախադասություն | PASS (չփակի) | PASS | PASS | ✅ դեռ PASS |
| glyph | (դ) կիրիլյան տառ հայերեն բառում | BLOCK | BLOCK | PASS | ✅ դեռ BLOCK |
| glyph | (նոր) մեկ պատահական translit-նման բառ («hima») | PASS (չփակի) | — | — | ✅ PASS (≥2 կանոնի պաշտպանություն) |
| brand-voice | (ա) հայերեն generic-AI տրոփեր («Բացահայտեք գաղտնիքները…, հեղափոխական») | FLAG/FAIL | ok=True, score=0, ոչ մի flag | **FALSE-NEGATIVE** | ✅ **FIXED** — revise, score=5.0, 6 flag |
| brand-voice | (ա′) անգլերեն generic տրոփեր (self-test) | FLAG | FLAG (revise) | PASS | ✅ դեռ FLAG |
| brand-voice | (բ) իրական Maghakian հատված (Taknuvra.txt) | PASS | PASS | PASS | ✅ դեռ PASS (ամբողջ վեպը՝ 1 «՜»-flag, score 1.25 < 2.5 → pass) |
| variation | (ա) 5 միանման static կադր | revise/fail | fail («wide 5/5», «4 consecutive same-size») | PASS | — |
| variation | (բ) բազմազան 4-կադրանոց պլան | pass | «acceptable» → gatechain-ում անցնում է (ok=True) | PASS* | — |
| schema | (ա) աղքատ scene_plan (առանց staging/text_policy) | ցանկալի՝ բռնվի | schema ok, բոլոր gate-երը ok — ոչինչ չբռնեց | **EXPECTED-GAP** | ⏸ **BACKLOG** (P2, owner-ի որոշմամբ) |
| schema | (բ) վալիդ scene_plan | pass | pass | PASS | ✅ դեռ PASS |
| checkpoint seam | կեղտոտ scene_plan, status=completed | BLOCK (exception) | CheckpointValidationError, glyph violation-ով | PASS | ✅ դեռ BLOCK |
| checkpoint seam | կեղտոտ scene_plan, status=awaiting_human | BLOCK (hard fail-ը միշտ) | BLOCK | PASS | ✅ դեռ BLOCK |
| checkpoint seam | կեղտոտ script (schema-վալիդ), completed | BLOCK | BLOCK՝ հենց glyph gate-ով («Vanը») | PASS | ✅ դեռ BLOCK |
| checkpoint seam | մաքուր scene_plan՝ առանց ladder sub-stages | — | BLOCK՝ «Production ladder collapsed» | PASS (governance) | ✅ դեռ BLOCK |
| checkpoint seam | compose + ՎԱՏ clip-ի continuity report | BLOCK | BLOCK՝ 06-18 վիոլացիան մեջբերված | PASS | ✅ դեռ BLOCK |
| delivery-promise | ուղիղ կանչ՝ motion_led + 6 slide cuts | invalid | invalid, motion ratio 0% < 70% | PASS | ✅ դեռ invalid |
| delivery-promise | նույնը checkpoint seam-ով (stage=edit, completed) | հայտնի բաց | անցավ ԱՌԱՆՑ բլոկի | **EXPECTED-GAP** (վերարտադրված) | ✅ **FIXED** — seam-ը ԲԼՈԿՈՒՄ Է (run_edit_gates) |
| delivery-promise | (նոր) խոստումը պահված՝ 4/4 motion cuts | pass | — | — | ✅ PASS (ոչ մի նոր false-positive) |
| delivery-promise | (նոր) edit checkpoint ԱՌԱՆՑ promise artifact-ի | pass (opt-in gate) | — | — | ✅ PASS (legacy անվտանգ) |
| seam↔schema | render_report + continuity_reports դաշտ | seam-ի փաստագրված երթուղի | schema-ն ՄԵՐԺՈՒՄ Է դաշտը (`additionalProperties: false`) | **BROKEN** (հակասություն) | ✅ **FIXED** — schema-վալիդ երթուղով ՎԱՏ report-ը ԲԼՈԿՎՈՒՄ Է, մաքուրը՝ անցնում |
| dry run | scene_plan→assets→edit→compose, իրական assets | շղթան կապվի | 4/4 checkpoint գրված, gates կանաչ, 10.0վ 1080×1920 draft | PASS | ✅ regression-ները մշտական pytest են |

\* variation-ի «pass»-ը gatechain-ում binary չէ. «acceptable»-ը նույնպես անցնում է (միայն revise/fail-ն է վիոլացիա ավելացնում)։

### Փուլ 0 (preflight) արձանագրություն
- `lib/healthcheck.py` → **ALL GREEN** (corpus 54, brain 51+SKILL+INDEX, ffmpeg, 3 manifest, gates live, seam, 24 schema, scout 28, radar 151/8, ladders, lanes)։
- `pytest tests/zavod/test_gates.py -q` → **42 passed** (13.4վ)։
- Daemon-ներ՝ `com.zavodom.scout`, `com.zavodom.style-radar` բեռնված էին → unload արվեցին թեստի ընթացքում։

### Seam-ի արժեքի չափում (Փուլ 1)
- Կադրահանում `build_review_request`-ով՝ 5 clip × 8 կադր = **44.7վ** (ffmpeg, deterministic)։
- Վիզուալ դատում՝ 40 կադր, 10 Read-փաթեթ, մոտ **4–5 րոպե** մեկ անգամվա համար. սա է gate-ի իրական
  գինը մեկ reel-ի QC-ի համար (ընդունելի է compose փուլի համար, բայց batch-երում կուտակվում է)։
- `verdict()`՝ ակնթարթային, deterministic։

## 3. 🔴 FALSE-NEGATIVE-ներ (փող ու վստահություն արժեն) — *առաջին անցման վիճակը; ուղղումները՝ §6*

1. **🔴 brand-voice gate-ը հայերենում կույր է։** `lib/brand_voice_check.py`-ի TROPES ցուցակը 27 տրոփ
   ունի՝ բոլորն անգլերեն։ «Բացահայտեք գաղտնիքները…, հեղափոխական, աննկարագրելի, բարձրացրեք ձեր
   բիզնեսը նոր մակարդակի» տեքստը ստանում է score=0, verdict=pass։ Զավոդի հիմնական աշխատանքային
   լեզուն հայերենն է — gate-ը հենց հիմնական լեզվում չի աշխատում։
2. **🔴 glyph gate-ը մաքուր տառադարձությունը չի բռնում։** «barev dzez, es heghinak em» → pass, քանի որ
   gate-ը միայն բառի ՆԵՐՍՈՒՄ խառը գիր է որսում։ CLAUDE.md-ի բացարձակ կանոնը («NEVER use
   transliteration») code-ում enforcement չունի. ամբողջությամբ լատինատառ հայերեն script-ը seam-ով
   կանցնի։ (Design-սահմանափակում է՝ առանց բառարանի translit-ը անգլերենից չտարբերել, բայց ռիսկն իրական է։)
3. **🔴 BROKEN. seam↔schema հակասություն compose-ում։** `checkpoint._continuity_reports()`-ը կարդում է
   `render_report.continuity_reports`, բայց `render_report.schema.json`-ը (`additionalProperties: false`)
   այդ դաշտով artifact-ը ՄԵՐԺՈՒՄ Է։ Փաստագրված երթուղով gate-ը երբեք չի կրակում. աշխատում է միայն
   չփաստագրված `artifacts.continuity_reports` բանալիով, որը ARTIFACT_NAMES-ում չլինելու պատճառով
   ընդհանրապես schema-validation ՉԻ անցնում (երկրորդային բաց՝ ցանկացած աղբ կարող է լինել այնտեղ)։

### EXPECTED-GAP-եր (հաստատված վերարտադրությամբ)
- **Delivery-promise-ը seam-ում չկա։** Motion-led + 6/6 slide checkpoint (stage=edit, completed) անցնում է
  առանց բլոկի. gate-ը կա միայն որպես reviewer-invoked կանչ և `final_review.promise_preservation`
  self-report դաշտ, որի արժեքները ոչ ոք չի վերահաշվարկում։
- **Աղքատ scene_plan-ը ոչինչ չի բռնում։** `staging`/`text_policy` դաշտերը schema-ում optional են. մեկ
  vague scene → variation=strong, բոլոր gate-երը կանաչ։ Continuity gate-ը anchor չի ունենա, եթե
  scene-director-ը in_hand_objects չհայտարարի — 06-18 դասի բագը կարող է վերադառնալ հենց այս դռնով։

### Այլ դիտարկումներ (ոչ բլոկող)
- `final_review` schema-ն ուժեղ է. ազատ ձևաչափի self-review-ն երկու անգամ մերժվեց, մինչև կառուցվածքային
  (technical_probe/visual_spotcheck/audio_spotcheck/promise_preservation/subtitle_check) չլրացվեց — լավ governance։
- Ladder-ի non-collapse-ը իրոք աշխատում է (մաքուր scene_plan-ը առանց sub-stage արձանագրության բլոկվեց)։
- Idea/script փուլերը բաց թողնելուց հետո `get_next_stage` → «idea». spine-ը locked-input սցենարը
  («script-ը կա, սկսիր հաջորդից») resume-pointer-ում չի արտացոլում։
- Լոկալ ffmpeg build-ում drawtext չկա. overlay տեքստի lane-ը (HTML/Canva) սա փակում է policy-ով, բայց
  ffmpeg-fallback overlay հնարավոր չէ այս մեքենայի վրա։
- Վճարովի գեներացիայի stop-point-ը dry run-ում մեկն էր՝ assets.asset_generation_or_shoot (ցանկացած ՆՈՐ
  asset = Higgsfield credit)։ Շրջանցվեց գոյություն ունեցող assets-ի reuse-ով, զրո գեներացիա։

## 4. Top-3 fix առաջարկ — *կարգավիճակ. P0 ✅ ուղղված, P1 ✅ ուղղված (+P1.5, +promise seam), P2 ⏸ backlog (§6)*

1. **P0. Վերացնել seam↔schema հակասությունը compose-ում** — կա՛մ `render_report.schema.json`-ին ավելացնել
   `continuity_reports` (schema-validated), կա՛մ `continuity_reports`-ը դարձնել ինքնուրույն artifact
   ARTIFACT_NAMES-ում. երկու դեպքում էլ seam-ի երթուղին ու schema-ն համընկնում են, և report-ները դադարում
   են validation-ից դուրս մնալ։ Սա 06-18 gate-ի ՄԻԱԿ enforcement կետն է compose-ում — հիմա այն կախված է
   կոնվենցիայից։
2. **P1. Brand-voice gate-ին ավելացնել հայերեն (և ռուսերեն) տրոփերի շերտ** — «բացահայտեք գաղտնիքները»,
   «հեղափոխական», «աննկարագրելի», «բարձրացրեք … նոր մակարդակի», «անսահման հնարավորություններ» դասի
   30–40 տրոփ + «՜» spam-ի հաշվառում։ Զավոդի հիմնական լեզուն hy է. gate-ը հիմա միայն en-ում է աշխատում։
3. **P2. Scene_plan-ի «աղքատության» գիծ** — zavod-* pipeline-ներում generated scene-երի համար seam-ում
   պահանջել `staging` (գոնե դատարկ ոչ-null) և `text_policy`, կամ gatechain-ում ավելացնել «declared
   anchors ≥ 1, եթե սցենարում ձեռքի պրոպ կա» ստուգում. հակառակ դեպքում continuity gate-ը anchor-զուրկ
   scene-երի վրա ձևականորեն «pass» է՝ ոչինչ չստուգելով։ (Բոնուս-թեկնածու, եթե P2-ը փոքր է թվում՝
   delivery_promise-ը միացնել edit/compose seam-ին որպես չորրորդ gate։)

## 5. Վերականգնում

Daemon-ները վերաբեռնվեցին թեստից հետո (`launchctl bootstrap gui/$UID` երկուսի համար էլ) և ստուգվեցին
`launchctl list | grep zavodom`-ով՝ երկուսն էլ ակտիվ ✅ (տես ստորև)։ Աշխատանքային արտեֆակտները
(կադրեր, verdicts, dry-run checkpoints, draft teaser) մնացին session scratchpad-ում. repo-ում ոչինչ
չի փոխվել, բացի այս report-ից։

## 6. AFTER — fix pass (owner-ի «Անցիր առաջ», 2026-07-02)

Owner-ի հաստատած ծավալը՝ P0 + P1 + P1.5 + delivery-promise seam. **P2-ը (scene_plan-ի աղքատության
գիծ) backlog-ում է՝ առանձին որոշման։** Փոփոխված ֆայլերը (commit ՉԻ արված).

1. **P0 — seam↔schema** · `schemas/artifacts/render_report.schema.json`
   Ավելացվեց `continuity_reports` դաշտը (կառուցվածքային՝ clip/frames/anchors, kind enum-ով)։
   Հիմա seam-ի փաստագրված երթուղին schema-վալիդ է. compose gate-ը իրոք կրակում է այդ երթուղով։
   Regression՝ `test_render_report_schema_accepts_continuity_reports`,
   `test_compose_seam_blocks_bad_clip_via_schema_valid_render_report` (Փուլ 3-ի negative test-ը՝
   մշտական pytest), `test_compose_seam_passes_clean_reports_via_schema_valid_render_report`։
   *Մնացորդը փակվեց նույն օրը owner-ի հրամանով (երրորդ անցում)՝ loose
   `artifacts.continuity_report(s)` բանալիները այլևս ՉԵՆ կարդացվում. միակ վալիդ երթուղին
   `render_report.continuity_reports` schema-դաշտն է։ Fixture-ները (healthcheck, 2 test)
   տեղափոխվեցին վալիդ երթուղի; նոր regression՝ `test_loose_continuity_keys_are_closed`։
   Ամբողջ suite՝ 322 passed, 6 skipped; healthcheck՝ ALL GREEN։*

2. **P1 — brand-voice hy տրոփեր** · `lib/brand_voice_check.py`
   Ավելացվեց `TROPES_HY` (28 տրոփ)՝ ածանցված brand-voice.md-ի «How the brand never speaks» /
   «This-not-that» / Lexicon never-կանոններից (hype, engagement-bait, stated emotion, corporate
   filler, translationese) — ոչ թե անգլերեն ցուցակի թարգմանություն։ Ամեն թեկնածու ստուգվեց ամբողջ
   corpus-ի դեմ (54 սցենար + «Տակնուվրա»)՝ զրո բախում («աննկարագրելի»-ն հանվեց, քանի որ իրական
   երկխոսությունում կա)։ Բացականչական spam-ը հիմա հաշվում է նաև հայերեն «՜»-ը։
   Ստուգում՝ ամբողջ «Տակնուվրա» վեպը gate-ով անցնում է (1 flag, score 1.25 → pass)։

3. **P1.5 — glyph translit** · `lib/armenian_glyph_gate.py`
   Ավելացվեց `TRANSLIT_TOKENS` (49 բարձրաճախական հայերեն բառ լատինագիր տառադարձությամբ,
   corpus-ստուգված; «apres/scenar/inch/shat» դասի անգլերեն-ֆրանսերեն բախումները հանված)։
   Կանոնը՝ ≥2 ՏԱՐԲԵՐ token մեկ string-ում → վիոլացիա. մեկ պատահական համընկնումը («hima») երբեք
   մենակ չի կրակում։ «barev dzez, es heghinak em u scenar em grum» → BLOCK (4 hit)։

4. **Delivery-promise seam** · `lib/gatechain.py` (`run_edit_gates`) + `lib/checkpoint.py`
   Edit փուլի checkpoint-ը հիմա անցնում է delivery-promise gate-ով, երբ artifacts-ում կա
   `delivery_promise` (locked promise, `DeliveryPromise.to_dict()`)։ Motion-led + slideshow →
   `CheckpointValidationError`։ Promise չկա → gate չկա (legacy/upstream անվտանգ, opt-in)։

**Վերիֆիկացիա fix-երից հետո.**
- Stress case-երի rerun՝ 14 case → 5 FIXED, 9 անփոփոխ PASS, **զրո նոր false-positive**
  (մանրամասն՝ scratchpad/after_rerun.json)։
- `tests/zavod/test_gates.py` → **54 passed** (42 հին + 12 նոր regression)։
- Ամբողջ `tests/zavod` + `tests/contracts` → **320 passed, 7 skipped** — ոչինչ չի կոտրվել։
- `lib/healthcheck.py` → ALL GREEN։

---
*Փուլ 1 մանրամասն արձանագրությունը՝ scratchpad/continuity_verdicts.json, Փուլ 2՝ phase2_part1.json /
phase2_part2.json, Փուլ 3՝ phase3_dryrun.json + dryrun/pipeline/desert-owl-teaser-dry-2026-07-02/,
AFTER rerun՝ after_rerun.json։*
