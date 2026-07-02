# ZavodOM Stress Test — 2026-07-02

Դու stress-test օպերատոր ես։ Քո խնդիրն է ZavodOM-ի gate-երն ու spine-ը ստուգել
**իրական** նյութով՝ մինչև որևէ իրական production վազք։ Սա LLM-կոնսիլի վճռի կատարումն է.
«զրո ծախսով backtest՝ նախ, credit-ները՝ հետո»։

## Կանոններ (խախտել չի կարելի)

1. **Ոչ մի credit չես ծախսում** (Higgsfield/fal/Kling/Veo generation՝ արգելված) առանց
   owner-ի բացահայտ «այո»-ի հենց այս պատուհանում։
2. **Ոչինչ չես հրապարակում, ոչինչ չես ջնջում**, git commit չես անում՝ քանի դեռ owner-ը չի խնդրել։
3. **Սխալ գտնելիս լուռ չես ուղղում** — գրանցում ես report-ում ու շարունակում։ Fix-երը owner-ի
   որոշումն են՝ report-ից հետո։
4. Հայերեն ցանկացած տեքստ՝ միայն արևելահայերեն Unicode (ոչ մի տառադարձություն)։
5. Աշխատանքային թղթապանակ՝ `~/zavod-om`։ Ամեն քայլի արդյունքը գրանցիր՝ ինչ սպասվում էր,
   ինչ ստացվեց, PASS / FALSE-POSITIVE / FALSE-NEGATIVE / BROKEN / EXPECTED-GAP։

---

## Փուլ 0 — Preflight (5 րոպե)

- [ ] `cd ~/zavod-om && ./.venv/bin/python lib/healthcheck.py` — արձանագրիր ամբողջ ելքը։
- [ ] Ստուգիր, որ թեստային baseline-ը կանաչ է՝ `./.venv/bin/python -m pytest tests/zavod/test_gates.py -q`
- [ ] Սառեցրու self-improvement daemon-ները թեստի ընթացքում, որ ուղեղը չմուտացվի.
      `launchctl list | grep zavodom` → եթե բեռնված են, unload արա
      (`launchctl bootout gui/$(id -u)/com.zavodom.scout` և `.style-radar`), վերջում՝ վերականգնիր։
      Եթե բեռնված չեն՝ պարզապես արձանագրիր։

## Փուլ 1 — Continuity gate backtest իրական «վատ» վիդեոյով (գլխավոր թեստը)

Ground truth. 2026-06-18-ին հին զավոդը հրապարակել է reel, որտեղ հերոսի ձեռքի բաժակը
**անհետանում է ցատկի ժամանակ**։ Այդ failure-ը հենց `lib/continuity_checker.py`-ի ծննդյան
պատճառն է — բայց gate-ը երբեք չի ստուգվել հենց այդ վիդեոյի վրա։

Ֆայլերը (կարդալու թույլտվություն կունենաս, path-ում space կա՝ quote արա).
- ՎԱՏ (բաժակն անհետանում է)՝
  `"/Users/apple/Documents/Obsidian Vault/Claude/desert-owl/generated/clips/01-A-pooljump.mp4"`
- ՈՒՂՂՎԱԾ (v2)՝ `.../clips/01-A-pooljump-v2.mp4`
- Հսկիչ «լավ» clip-եր՝ `.../clips/02-D-bbqbar.mp4`, `.../clips/03-C-grouppool.mp4`,
  `.../clips/04-B-twilight.mp4`

Քայլերը յուրաքանչյուր clip-ի համար (սկսիր ՎԱՏ-ից).
1. `lib/continuity_checker.py`-ի `build_review_request(video, scene, n=8)`-ով հանիր 8 կադր
   (scene-ում anchor սահմանիր՝ օրինակ `{"name": "drinking glass in hand", "kind": "object"}` +
   կերպարի ինքնությունը + ֆոնի ճարտարապետությունը)։
2. **Իրոք ՆԱՅԻՐ կադրերին** (Read գործիքով, հերթով, բոլորը) և լրացրու review request-ը՝
   ամեն anchor-ի համար `persists` true/false + note։
3. Անցկացրու `verdict(report)`-ով, արձանագրիր վճիռը։

Հաջողության չափանիշ.
- `01-A-pooljump.mp4` → REJECT՝ բաժակի անհետացումը **անունով** նշված (ոչ FALSE-NEGATIVE)։
- v2 և հսկիչ clip-երը → PASS (ոչ FALSE-POSITIVE)։
- Առանձին արձանագրիր՝ որքան ժամանակ/քայլ պահանջվեց — սա seam-ի իրական արժեքի չափումն է։

## Փուլ 2 — Gate-երի adversarial ստուգում (զրո credit)

Մուտքակետը `lib/gatechain.py`-ն է (`run_script_gates`, `run_scene_plan_gates`)։ Ամեն gate-ի
տուր և՛ հայտնի-վատ, և՛ հայտնի-լավ մուտք, գրանցիր false-positive/negative-ները.

- [ ] **Glyph gate** — (ա) տառադարձված հայերեն («barev dzez», «heghinak»), (բ) խառը գիր
      (հայերեն բառի մեջ լատինական տառ), (գ) մաքուր արևելահայերեն, (դ) եզրային՝ էմոջի + հայերեն,
      ռուսերեն ամբողջական նախադասություն (պիտի ՉՓԱԿԻ, եթե հայերեն բառի մեջ չէ)։
- [ ] **Brand-voice gate** — (ա) generic-AI տրոփերով տեքստ («Բացահայտեք գաղտնիքները...,
      հեղափոխական, աննկարագրելի»), (բ) `~/Documents/Maghakian-Scripts/`-ի իրական հատված
      (պիտի անցնի)։
- [ ] **Variation checker** — (ա) slideshow-անման scene plan (5 միանման static կադր),
      (բ) իրական բազմազան պլան։
- [ ] **Schema gates** — (ա) աղքատ/vague scene_plan (առանց `staging`/`text_policy`),
      (բ) վալիդ արտեֆակտ (նմուշներ կան `tests/`-ում)։
- [ ] **Checkpoint seam** — փորձիր «կեղտոտ» արտեֆակտ անցկացնել checkpoint-ով
      (`lib/checkpoint.py`) և համոզվիր, որ seam-ը ԲԼՈԿՈՒՄ Է, ոչ միայն warning։
- [ ] **Delivery-promise gate (հայտնի բաց)** — փաստաթղթավորիր, որ motion-led խոստումը
      slideshow դարձնելը checkpoint seam-ում ոչինչ ՉԻ բռնում (gate-ը reviewer-invoked է)։
      Սա EXPECTED-GAP է — ցույց տուր կոնկրետ վերարտադրությամբ։

## Փուլ 3 — Dry pipeline run (զրո credit)

- [ ] Քշիր `zavod-reel` pipeline-ը ավտոմատ սևագրային ռեժիմով ներքին թեստ-brief-ով
      («desert-owl 10վ teaser» ոճի), որպես source media օգտագործելով ՄԻԱՅՆ արդեն գոյություն
      ունեցող `desert-owl/generated/` ակտիվները — ոչ մի նոր գեներացիա։ Նպատակը՝ տեսնել,
      որ փուլերը, արտեֆակտները, gate-երը և checkpoint-ները իրար կապվում են իրական նյութով։
- [ ] Եթե որևէ փուլ պահանջում է paid generation՝ կանգնիր, արձանագրիր որտեղ ու ինչու,
      և անցիր առաջ mock/skip-ով։

## Փուլ 4 — Report

Գրիր `~/zavod-om/tests/stress/STRESS-REPORT-2026-07-02.md`՝
1. Ամփոփում հայերեն՝ 5-7 նախադասություն (անցա՞վ գլխավոր backtest-ը, թե՞ ոչ)։
2. Աղյուսակ՝ gate | test case | expected | actual | verdict։
3. Բոլոր FALSE-NEGATIVE-ները՝ վերևում, կարմիր նշումով — դրանք փող ու վստահություն արժեն։
4. Top-3 fix առաջարկ՝ առաջնահերթությամբ (բայց ՉՈՒՂՂԱԾ)։
5. Վերջում՝ վերականգնիր daemon-ները (եթե unload էիր արել) և նշիր դա report-ում։
