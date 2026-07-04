# ZavodOM Full-Factory Stress Test — 2026-07-04 (Hermes crew run)

Դու stress-test օպերատոր ես Hermes zavod crew-ից։ Խնդիրը՝ ստուգել գործարանի **ամեն ինչը**՝
gate-երից մինչև daemon-ներ, և գտնել այն, ինչ աչքից վրիպել է։ Նախադեպը՝ bench_gate-ը, որի
wrapper-ը կար, թեստերն անցնում էին, բայց checkpoint seam-ին միացված չէր (գտնվեց 2026-07-04-ին,
արդեն ուղղված է՝ commit 17463d5)։ Փնտրիր հենց **այդ դասի** խնդիրներ։

## Կանոններ (խախտել չի կարելի)

1. **Ոչ մի credit չես ծախսում** (Higgsfield/fal/Kling/Veo generation՝ արգելված)։
2. **Ոչինչ չես հրապարակում, ոչինչ չես ջնջում, git commit/push չես անում։**
3. **Սխալ գտնելիս լուռ չես ուղղում** — գրանցում ես ու շարունակում։ Fix-երը owner-ի որոշումն են։
4. Հայերեն ցանկացած տեքստ՝ միայն արևելահայերեն Unicode։
5. Աշխատանքային թղթապանակ՝ `~/zavod-om`։ Ամեն ստուգման արդյունքը՝
   PASS / FALSE-POSITIVE / FALSE-NEGATIVE / BROKEN / EXPECTED-GAP / WIRING-GAP։
6. Արդյունքները գրի՛ր kanban task-իդ կոմենտներում՝ կառուցվածքված ցուցակով։

## Բլոկ A — Wiring-gap որս (ամենակարևորը)

Փնտրիր «կոդը կա, բայց ոչ մի տեղից չի կանչվում» դասի խնդիրներ.

- [ ] `lib/gatechain.py`-ի ամեն export (`run_*`) — ո՞վ է կանչում։ `grep -rn` արա ամբողջ repo-ով․
      wrapper առանց caller = WIRING-GAP։
- [ ] `lib/`-ի ամեն gate/checker մոդուլ (`*_gate.py`, `*_checker.py`, `*_check.py`, `canon_guard.py`,
      `delivery_promise.py`…) — մտնո՞ւմ է checkpoint seam (`lib/checkpoint.py`), gatechain,
      կամ healthcheck։ Ոչ մի տեղ = WIRING-GAP։
- [ ] `schemas/artifacts/*.schema.json` — ամեն schema որևէ validator-ից հղվո՞ւմ է։
- [ ] `pipeline_defs/` manifest-ները — բոլոր հղված sub_stages/craft ֆայլերը գոյություն ունե՞ն։
- [ ] ZAVODOM.md-ի ամեն «standing order» / «gate» պնդում — ցույց տուր այն կոդի տողը, որ enforce է անում։
      Չկա = WIRING-GAP (prose-only rule)։

## Բլոկ B — Gate-երի adversarial ստուգում (զրո credit)

Ամեն gate-ի տուր և՛ հայտնի-վատ, և՛ հայտնի-լավ մուտք․ գրանցիր false-positive/negative-ները.

- [ ] **Glyph gate** — տառադարձված հայերեն, խառը գիր մեկ բառի մեջ, կիրիլյան homoglyph,
      մաքուր հայերեն (պիտի անցնի), մաքուր անգլերեն (պիտի անցնի)։
- [ ] **Brand voice** — generic-AI տրոպերով տեքստ vs corpus-ոճ տեքստ։
- [ ] **Variation checker** — slideshow-անման միապաղաղ scene_plan vs իրական վարիացիա։
- [ ] **Continuity checker API** — կեղծ report-ով՝ persists=false → REJECT, բոլորը true → PASS,
      խառը → ի՞նչ է անում (edge case)։
- [ ] **Bench gate (նորը)** — ամբողջ բենչ → PASS; պակաս մասնագետ, «ok» ռետինե վճիռ,
      bench_report չկա → երեքն էլ BLOCK։ Ստուգիր բոլոր փուլերի mapping-ը (scene_plan→scene, assets→asset)։
- [ ] **Canon guard / story gates** — canon-ը փոխի script-ից հետո առանց canon-revalidation.md → BLOCK։
- [ ] **Delivery promise** — motion-led promise + slideshow edit_decisions → BLOCK։

## Բլոկ C — Runtime / միջավայր

- [ ] `./.venv/bin/python lib/healthcheck.py` — ամբողջ ելքը արձանագրիր։
- [ ] Ամբողջ test suite (ոչ միայն zavod/)՝ `uv run --with pytest pytest tests/ -q` — ամեն fail՝ առանձին տողով։
- [ ] `make lint` և Makefile-ի բոլոր target-ները — կոտրված path/հրաման կա՞ (հենց նոր մեկն ուղղվեց՝
      composition_validator; ստուգիր մնացածը, ներառյալ `python` vs `python3` հարցը)։
- [ ] launchd daemon-ներ՝ `launchctl list | grep -iE "zavodom|hermes"` — ո՞րն է բեռնված, ո՞րը exit code ≠ 0։
- [ ] requirements*.txt vs venv — import ձախողումներ կա՞ն core մոդուլներում։

## Բլոկ D — E2E չոր վազք (զրո credit)

- [ ] Վերցրու `zavod-reel` pipeline-ը ու տար այն checkpoint-առ-checkpoint մինչև այն կետը,
      որտեղ generation/credit է պահանջվում — այնտեղ ԿԱՆԳ։ Արձանագրիր՝ ամեն փուլի gate-երը
      իրո՞ք կանչվեցին (ապացույց՝ log/traceback), որ փուլում ինչ artifact է պահանջվում,
      որտեղ է առաջին անգամ մարդ պահանջվում։
- [ ] Հատուկ ուշադրություն՝ փուլ, որ «անցնում է» առանց որևէ gate-ի կանչի = WIRING-GAP։

## Զեկույցի ձևաչափ (վերջում, task կոմենտով)

1. Executive summary — 5 տող․ քանի ստուգում, քանի PASS, քանի խնդիր՝ ըստ ծանրության։
2. Findings ցուցակ — ամեն մեկը՝ [SEVERITY] [CLASS] նկարագրություն + ապացույց (ֆայլ:տող / հրաման+ելք)։
3. Ոչ մի fix՝ միայն փաստեր։
