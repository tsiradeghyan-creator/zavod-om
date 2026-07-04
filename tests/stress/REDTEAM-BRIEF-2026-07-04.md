# ZavodOM Red-Team / Bypass Audit — 2026-07-04 (round 2)

Դու red-team օպերատոր ես Hermes zavod crew-ից։ Նախորդ ստրես-տեստը հարցնում էր «gate-երը
**աշխատո՞ւմ** են»։ Այս անգամ հարցը հակառակն է՝ **«ի՞նչպես կարելի է gate-երը ԽԱԲԵԼ»**։
Դու հարձակվողն ես․ քո խնդիրն է գտնել, թե ինչպես կարող է անբարեխիղճ (կամ ծույլ) ագենտը/մարդը
փուլ փակել՝ առանց իրական աշխատանք անելու։ Ամեն bypass, որ գտնում ես, հաղթանակ է։

## Կանոններ (խախտել չի կարելի)

1. **Ոչ մի credit** (generation/provider call՝ արգելված), **ոչ մի publish/delete/commit/push**։
2. **Bypass գտնելիս չես ուղղում** — գրանցում ես որպես exploit՝ քայլերով վերարտադրելի։ Fix-երը owner-ի որոշումն են։
3. Հայերեն՝ միայն արևելահայերեն Unicode։ Աշխատանքային repo՝ `~/zavod-om` (branch `main`)։
4. Ամեն exploit-ի ձևաչափ՝ **[SEVERITY] [ANGLE] վերնագիր → reproduction (կոդ/հրաման) → ի՞նչ ստացվեց → ինչո՞ւ է սա շրջանցում → blast radius**։
5. Աշխատիր **իրական seam-ով** (`enforce_zavod_write_contracts` / `write_checkpoint`), ոչ թե ներքին helper-ով — schema/ladder/existence շերտերը այնտեղ են։ Եթե exploit-ը միայն ներքին helper-ի դռնով է անցնում բայց իրական write path-ով՝ ոչ, նշիր դա (partial)։

---

## Angle 1 — Rubber-stamp escalation (bench gate)

`lib/bench_gate.py`-ը «substantive ruling» սահմանում է որպես `len(ruling) >= 60` (RULING_MIN)։
- [ ] Ապացուցիր, որ 60 նիշ **անիմաստ լցոն** (կրկնվող բառ, lorem, պատահական տառեր, նույն նախադասությունը 3 անգամ) անցնում է bench gate-ը բոլոր փուլերում։ Սա rubber-stamp-ի հենց այն ձևն է, որ gate-ը հայտարարում է թե բռնում է։
- [ ] Փորձիր նույն ruling տեքստը **բոլոր ролям**ի համno copy-paste — մի՞թե gate-ը նկատում է, որ 8 մասնագետ նույն բառերն են գրել (ոչ մի independence check)։
- [ ] Ruling, որ ասում է «REJECT, սա սխալ է» բայց 60+ նիշ է — gate-ը ստուգո՞ւմ է ruling-ի **բովանդակությունը/verdict-ը**, թե միայն երկարությունը։

## Angle 2 — Read vs write asymmetry

`read_checkpoint` (line 708) դիտմամբ **չի** enforce անում write contract-ները (legacy load)։
- [ ] Ձեռքով գրիր (ֆայլային մակարդակում, ոչ seam-ով) մի `completed` checkpoint JSON, որ խախտում է gate — հետո `read_checkpoint`-ով կարդա։ Անցնո՞ւմ է։ Եթե այո՝ ապա pipeline-ի resume/continue ուղին հնարավոր bypass է (փուլ, որ մեկ անգամ վատ գրվել է ֆայլ, հետո ազատ կարդացվում է)։
- [ ] Կա՞ ընդհանրապես ուղի, որ checkpoint ֆայլ գրվի **առանց** `write_checkpoint`-ի (ուղիղ ֆայլ-գրում, cache, checkpoint copy, project import)։ grep արա `json.dump`/`.write(` checkpoint path-երի վրա։

## Angle 3 — Path-existence gate-ի խաբեություն

Existence gate-ը ստուգում է՝ path-ը `.exists()`։
- [ ] 0-բայթ ֆայլ, խորհրդանշական link (`ln -s /dev/null`), սխալ ընդլայնումով ֆայլ (`.txt` անունով «video»), 3-բայթ աղբ .mp4 — բոլորը `.exists()==True`։ Ապացուցիր, որ **դատարկ/աղբ ֆայլը** անցնում է asset/compose existence gate-ը (gate-ը content/format/duration չի ստուգում, միայն գոյություն)։
- [ ] `path`-ը դարձրու գոյություն ունեցող **ուրիշ** ֆայլի (օրինակ՝ `README.md` որպես «render output.mp4»)։ Անցնո՞ւմ է։ Provenance/format ստուգում կա՞։
- [ ] Manifest, որտեղ `assets` list-ը **դատարկ** է (`[]`) կամ `path` field-ը բացակայում է entry-ում — gate-ը skip է անում (`not isinstance(...path, str): continue`)։ Այսինքն՝ 0 asset = existence gate-ը ոչինչ չի ստուգում = փուլը փակվում է առանց և ոչ մի asset-ի։

## Angle 4 — Ladder / sub-stage collapse

`_enforce_production_ladder`-ը պահանջում է owner-gated sub-stage-երը `production_ladder.sub_stages`-ում։
- [ ] Ապացուցիր՝ ագентը կարո՞ղ է sub-stage-երը **անվանապես** լցնել (ճիշտ name-եր, դատարկ/կեղծ բովանդակություն) ու ladder-ը անցնել։ Ladder-ը ստուգում է existence-ը, թե՞ նաև որ ամեն sub-stage-ը իրական produces artifact ունի։
- [ ] Manifest-ից sub-stage-ի `human_approval_default: false` — կա՞ ագентի ձեռքի տակ ուղի, որ մասնագետ «անջատի» ladder-ից՝ manifest խմբագրելով (manifest-ը trusted input է, թե՞ ստուգվում է)։

## Angle 5 — Glyph gate-ի Unicode շրջանցում

`armenian_glyph_gate.py`-ը homoglyph/mixed-script է բռնում։
- [ ] Փորձիր՝ zero-width joiner/space (U+200D/U+200B) հայ բառի մեջ, հայ-լատին homoglyph-եր որ gate-ը դեռ չի ցուցակագրել (օր․ հայ «օ» vs լատին «o», հայ «ո»), NFD vs NFC նորմալացում, RTL/LTR mark-եր։ Ո՞րն է անցնում որպես «մաքուր հայերեն» բայց render-ի ժամանակ կկոտրվի։
- [ ] Emoji/math-alphanumeric (𝗕𝗮𝗿𝗲𝘃) — gate-ը սրանք հայերե՞ն է համարում, թե՞ բաց թողնում։

## Angle 6 — Non-zavod pipeline escape hatch

Բոլոր gate-երը սկսվում են `if not ptype.startswith("zavod"): return`։
- [ ] Ապացուցիր՝ `pipeline_type: "zavod-reel "` (վերջում space), `"Zavod-reel"` (մեծատառ), `"zavodx"`, կամ ընդհանրապես non-zavod ptype-ով production՝ **բոլոր** zavod gate-երը լուռ անջատվում են։ Այսինքն՝ pipeline_type-ը մեկ տողի փոփոխությամբ ամբողջ enforcement-ը կ desh. Որքանո՞վ է pipeline_type-ը trusted/validated։

## Angle 7 — Empty/degenerate artifacts

- [ ] Ամեն canonical artifact-ի համար՝ schema-valid բայց **դատարկ իմաստով** (script՝ մեկ բառ, scene_plan՝ 1 shot, story_bible՝ minimal-ը schema-ի) — անցնո՞ւմ է։ Որտե՞ղ է «schema-valid բայց աղքատ» սահմանը (նախորդ BACKLOG-ում կար scene-plan-poverty հարց՝ ստուգիր՝ դեռ բա՞ց է)։

## Զեկույց

1. Executive summary՝ քանի angle, քանի իրական bypass (ըստ severity), որն է ամենավտանգավորը։
2. Exploit ցուցակ վերևի ձևաչափով, ամեն մեկը վերարտադրելի։
3. Առանձին բաժին՝ «Ի՞նչը ԴԻՄԱՑԱՎ» — angle-եր, որ փորձեցիր ու gate-ը ազնվորեն բռնեց (սա էլ արժեքավոր է)։
4. Ոչ մի fix։ Գրի kanban task-իդ կոմենտում + ֆայլ `tests/stress/REDTEAM-REPORT-2026-07-04.md` (միայն այս ֆայլը գրել, commit՝ ոչ)։
