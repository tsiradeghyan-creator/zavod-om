# ZavodOM Red-Team Report — 2026-07-04 (round 2, run by Claude)

Օպերատոր՝ Claude (Hermes crew-ի փոխարեն, ChatGPT-ի քվոտան սպառված էր)։ Brief՝ `REDTEAM-BRIEF-2026-07-04.md`։
Credit՝ **0**, publish/commit՝ **0**, fix՝ **0**. Ամեն exploit վերարտադրվել է իրական `write_checkpoint` /
`read_checkpoint` / gate seam-ով (harness՝ `/tmp/redteam*.py`)։

## 1. Executive summary
- 7 angle փորձարկվեց, **5 իրական bypass/թուլություն** գտնվեց, defense-in-depth-ի մի քանի շերտ ազնվորեն դիմացավ։
- Ամենավտանգավոր երկուսը՝ **(P1) bench rubber-stamp** (gate-ը չափում է միայն երկարություն, ոչ բովանդակություն/verdict/անկախություն) և **(P1) pipeline_type case-sensitivity** (`startswith("zavod")` → մեկ մեծատառ տառ լուռ անջատում է ԲՈԼՈՐ gate-երը)։
- Լավ նորությունը՝ շերտավորումը իրական է. ֆանտոմ-asset հարձակումներս full write path-ում բռնվեցին ladder/engine-lane շերտերով **նախքան** existence gate-ին հասնելը։

## 2. Confirmed exploits

### [P1] [ANGLE-1] Bench gate = rubber-stamp detector-ը rubber-stamp-ով անցնում է
- Reproduction՝ `run_bench_gates("asset", bench={8 role : {"ruling": "<60 նիշ լցոն>"}})`։
- Արդյունք՝ `ok=True`։ Երեք տարբերակ անցավ․
  1. 60 նիշ անիմաստ լցոն («նույն բառը» x6) → PASS։
  2. Նույն ruling տեքստը **8 մասնագետի համար նույնությամբ** copy-paste → PASS (անկախության ստուգում չկա)։
  3. Ruling, որի **բովանդակությունը** ասում է «REJECT this is broken do not ship» (>60 նիշ) → PASS (gate-ը verdict չի կարդում)։
- Ինչու է bypass՝ `lib/bench_gate.py:51-55` միակ ստուգումն է `len(ruling.strip()) >= 60`։ Ագենտը կարող է 8 փոս-ruling սարքել 30 վայրկյանում ու «ամբողջ բենչ» հրամանը ձևականորեն բավարարել առանց և ոչ մի իրական վճռի։
- Blast radius՝ բոլոր փուլերը (bench gate-ը ամենուր է)։ Սա հենց այն rubber-stamp-ն է, որ gate-ը հայտարարում է թե բռնում է (`bench_gate.py:14-15`)։

### [P1] [ANGLE-6] pipeline_type-ի case/prefix զգայունությունը անջատում է ամբողջ enforcement-ը
- Reproduction՝ `write_checkpoint(..., "completed", {phantom asset}, pipeline_type="Zavod-reel")`։
- Արդյունք՝ **completed checkpoint գրվեց ֆանտոմ asset path-ով**։ Նույնը՝ `"ZAVOD-reel"`, `"reel-zavod"`, `"montage-reel"`, ցանկացած non-zavod ptype։
- Ինչու է bypass՝ ամեն gate սկսվում է `if not ptype.startswith("zavod"): return` (case-sensitive, prefix-only, 6 տեղ `lib/`-ում)։ Ոչ մի canonicalization/lower/strip չկա (grep՝ 0 արդյունք)։ Մեկ մեծատառ «Z» կամ zavod-ը ոչ-սկզբում = glyph, bench, ladder, existence, canon, story — ԲՈԼՈՐԸ լուռ off։
- Blast radius՝ ամբողջական։ Latent է (իրական manifest-ները lowercase են՝ `zavod-reel/carousel/promo`), բայց predicate-ը փխրուն է. ցանկացած alias/rename/mis-case/ձեռքով-set pipeline_type անաղմուկ բացում է ամեն դուռ։ Ուղղումը փոքր է՝ canonical lower + exact-set membership։

### [P2] [ANGLE-3] Existence gate-ը content/format-կույր է
- Reproduction՝ `_enforce_artifact_path_existence` isolated։
- Բոլորը **PASS**՝ 0-բայթ ֆայլ, plain-text վերանվանված `.mp4`, `symlink → /dev/null`, path որ **թղթապանակ** է (ոչ ֆայլ)։
- Ինչու է bypass՝ `lib/checkpoint.py:551` միայն `resolved.exists()`։ Ոչ size, ոչ format/ffprobe, ոչ «ֆայլ է թե դիր»։ `touch output.mp4` բավական է existence gate-ը գոհացնելու։
- Մեղմացում՝ full write path-ում ladder+engine-lane շերտերը ավելի վաղ բռնում են fresh phantom-checkpoint-ը, բայց այս gate-ը ինքնին ապահովում է միայն «path-ը գոյություն ունի», ոչ «render-ը իրական է»։

### [P2] [ANGLE-2] read_checkpoint-ը շրջանցում է write-only gate-երը (existence + ladder)
- Reproduction՝ ձեռքով ֆայլ գրած schema-valid + bench-valid `completed` checkpoint, path-ը ֆանտոմ → `read_checkpoint()`։
- Արդյունք՝ **բեռնվեց `status=completed`**՝ առանց existence/ladder ստուգման (դրանք միայն write-ի ժամանակ են՝ `checkpoint.py:575-579`, կոմենտով բացահայտ)։
- Ինչու է կարևոր՝ resume/continue ուղին ֆայլից է կարդում։ (ա) checkpoint, որ գրվել է երբ ֆայլը կար, հետո ֆայլը ջնջվել է → resume-ը մաքուր է անցնում ֆանտոմով։ (բ) ձեռքով խմբագրած checkpoint ֆայլը շրջանցում է existence/ladder-ը։ Content gate-երը (bench/glyph/…) read-ի ժամանակ **աշխատում են** (լավ), միայն կառուցվածքային write-contract-ներն են բաց։
- Նշում՝ սա մասամբ **դիտավորյալ** է (legacy load), բայց trust boundary է՝ արժե գոնե existence-ը read-ին էլ քաշել resume-ի դեպքում։

### [P3] [ANGLE-5] Glyph gate-ը բաց է թողնում zero-width joiner-ը հայ բառի մեջ
- Reproduction՝ `run_script_gates("Բա‍րև ձեզ")` → `ok=True` (մաքուր համարեց)։
- Ինչու է թուլություն՝ ZWJ/ZWSP (U+200D/U+200B) անտեսանելի են, բայց render/overlay-ի ժամանակ կարող են կոտրել shaping-ը կամ օգտագործվել filter-evasion-ի համար։ Gate-ը homoglyph/mixed-script է բռնում, բայց invisible-format նիշերը՝ ոչ։
- Դիմացավ՝ լատինատառ «o» հայ բառի մեջ (`Բարo`) → **բռնվեց** (`ok=False`)։ Այսինքն script-mixing-ը աշխատում է, բացը միայն format/invisible նիշերն են։

## 3. Ի՞նչը դիմացավ (ազնիվ հաշիվ)
- **Defense-in-depth իրական է**․ schema → content gates → production ladder → engine-lane lock → existence — ամեն շերտ ուրիշ բան է բռնում։ Ֆանտոմ-asset-ը full write path-ում հասավ միայն մինչև ladder/engine-lock, existence-ին անգամ չհասավ։
- `pipeline_type="zavod-reel "` (**վերջում** space) → `startswith` դեռ match է անում → gate-երը **մնում են միացած** (միայն casing/non-prefix է կոտրում)։
- Latin homoglyph հայ բառում → բռնվեց։
- read_checkpoint-ը content gate-երը (bench missing) **բռնում է**՝ միայն կառուցվածքային write-contract-ներն է բաց թողնում։

## 4. Առաջարկվող առաջնահերթություն (owner-ի որոշման համար, fix չի արվել)
1. **[P1]** Bench gate՝ ավելացնել verdict/semantics + inter-role independence ստուգում (ոչ միայն `len>=60`). rubber-stamp/copy-paste բռնել։
2. **[P1]** pipeline_type՝ canonicalize (lower+strip) և exact-membership zavod pipeline-ների ցուցակի դեմ, ոչ `startswith`։ Un-canonical ptype = loud fail, ոչ լուռ bypass։
3. **[P2]** Existence gate՝ ավելացնել min-size + «ֆայլ է, ոչ dir/symlink-to-null» + (compose-ում) ffprobe sanity։
4. **[P2]** read/resume ուղում՝ existence-ը վերաստուգել completed asset/compose checkpoint բեռնելիս։
5. **[P3]** Glyph gate՝ արգելել zero-width/format control նիշերը (U+200B–200F, U+FEFF) հայ overlay տեքստում։
