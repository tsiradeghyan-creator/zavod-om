# ZavodOM Stress Report — 2026-07-04

Օպերատորներ՝ Hermes Zavod crew (`zavodep`, `zavodqc`, `zavodscene`, `default`)։ Brief՝ `tests/stress/STRESS-TEST-BRIEF-2026-07-04.md`։
Ծախսված credit՝ **0**։ Հրապարակում՝ **0**։ Git commit/push՝ **0**։ Կոդային fix՝ **0**. այս զեկույցը միայն synthesis է A/B/C/D բլոկների kanban մեկնաբանություններից։

## 1. Executive summary

- Ստուգվել են 4 անկախ բլոկներ՝ A wiring-gap, B adversarial gates, C runtime/environment, D zero-credit e2e dry-run։
- Ընդհանուր պատկերը՝ core gate-երի մեծ մասը աշխատում է. Block B-ում 25/25 adversarial case ճիշտ PASS/BLOCK/REJECT վարք է տվել, regression suite-ը՝ `63 passed in 19.39s`։
- Բարձր ռիսկի բացերը seam/governance դասից են, ոչ թե առանձին gate-ի տրամաբանությունից. գոյություն ունեցող story/canon gate-երը production checkpoint seam-ից չեն կանչվում, իսկ assets/compose փուլերը կարող են ընդունել գոյություն չունեցող path-եր։
- Runtime միջավայրում project `.venv`/`uv` ուղին կանաչ է (`419 passed, 8 skipped`), բայց Makefile-ի bare `python`/`pip` ուղին կարմիր է այս shell-ում։
- Առաջարկվող առաջնահերթությունը՝ նախ փակել non-bypassable checkpoint seam բացերը (story/canon, asset/render existence), հետո Makefile runtime path-ը, հետո փաստաթղթային drift-ը։

## 2. Findings ըստ ծանրության

### P0 / P1 — checkpoint seam և production-governance բացեր

1. [P1] [WIRING-GAP] `run_story_gates` wrapper-ը production checkpoint seam-ից չի կանչվում։
   - Ապացույց՝ Block A static scan. `run_story_gates` caller-ները միայն `tests/zavod/test_story_gates.py`-ում են, ոչ `lib/checkpoint.py`-ում։
   - Կոդային հիմք՝ `lib/gatechain.py:37-46` story_bible schema gate ունի, բայց `lib/checkpoint.py:168-174` import list-ում `run_story_gates` չկա, իսկ `lib/checkpoint.py:194-207` stage dispatch-ը story gate չի կանչում։
   - Ռիսկ՝ story_bible failure-ը կարող է unit test-երով բռնվել, բայց production stage close-ը չբլոկվել։

2. [P1] [WIRING-GAP] `run_canon_guard` / `canon_guard.py` production seam-ից չի կանչվում։
   - Ապացույց՝ Block A scan. `run_canon_guard` external_hits=0, իսկ `canon_guard.py`-ը հղված է միայն wrapper/unit test շերտում։
   - Կոդային հիմք՝ `lib/canon_guard.py:9-16` պահանջում է stage advance-ի ժամանակ canon lock/check, բայց `lib/checkpoint.py:425-473` validate/write contract-ներում canon guard չկա։
   - Ռիսկ՝ script-ից հետո canon drift-ը կարող է չդառնալ non-bypassable block մինչև owner/reviewer ձեռքով չնկատի։

3. [P1] [WIRING-GAP] `assets` completed checkpoint-ը կարող է անցնել գոյություն չունեցող asset path-ով։
   - Ապացույց՝ Block D placeholder seam check՝ `PLACEHOLDER_STAGE assets PASS GATES ['run_bench_gates']`, իսկ shell existence check-ը ցույց տվեց, որ `.../assets/video/DRY_RUN_PLACEHOLDER_DOES_NOT_EXIST.mp4` ֆայլը չկա։
   - Կոդային հիմք՝ `schemas/artifacts/asset_manifest.schema.json:14-23` պահանջում է `id/type/path/source_tool/scene_id`, բայց path existence/provenance չի ստուգում։ `lib/checkpoint.py:176-192` assets փուլում փաստացի միայն bench gate է կանչում։
   - Ռիսկ՝ artifact-backed արտադրության շղթան կարող է ձևականորեն անցնել առանց իրական asset-ի։

4. [P1] [WIRING-GAP] `compose` completed checkpoint-ը կարող է անցնել գոյություն չունեցող render output path-ով, թեև manifest-ը պահանջում է ffprobe անցած output։
   - Ապացույց՝ Block D placeholder seam check՝ `PLACEHOLDER_STAGE compose PASS GATES ['run_bench_gates', 'run_compose_gates']`, իսկ `.../renders/DRY_RUN_PLACEHOLDER_DOES_NOT_EXIST.mp4` ֆայլը չկա։
   - Կոդային հիմք՝ `pipeline_defs/zavod-reel.yaml:267-268` success criterion-ը պահանջում է `output passes ffprobe`, բայց `schemas/artifacts/render_report.schema.json:14-24` միայն path/format/resolution/duration դաշտեր է պարտադրում, իսկ `lib/checkpoint.py:203-207` output file/ffprobe չի enforce անում։
   - Ռիսկ՝ final technical QC-ի ամենակարևոր փաստը՝ «render-ը իրոք կա և ընթեռնելի է», seam-ում non-bypassable չէ։

5. [P1] [BROKEN / EXPECTED-GAP] `assets` փուլում generation-ից առաջ բնական human stop-ը չի serialize լինում առանց կեղծ `asset_manifest`-ի։
   - Ապացույց՝ Block D dry-run-ը `idea`, `script`, `scene_plan` completed checkpoints-ից հետո կանգնեց `assets`-ում։ `awaiting_human` checkpoint առանց generated `asset_manifest`-ի մերժվեց՝ `Stage 'assets' with status 'awaiting_human' must include canonical artifact 'asset_manifest'`։
   - Կոդային հիմք՝ checkpoint contract-ը `awaiting_human` status-ի համար էլ canonical artifact է պահանջում (`lib/checkpoint.py:95-105`), իսկ `assets` canonical artifact-ը `asset_manifest` է (`lib/checkpoint.py:36`)։
   - Ռիսկ՝ generation/credit կետից առաջ օրինական owner freeze-ը ստիպում է կամ չգրել checkpoint, կամ գրել fake manifest։

### P2 — runtime և opt-in governance բացեր

6. [P2] [BROKEN] `make test` և `make test-contracts` կոտրված են ընթացիկ shell-ում, որովհետև Makefile-ը bare `python` է կանչում։
   - Ապացույց՝ Block C. `make test` ելք՝ `/Users/apple/.hermes/hermes-agent/venv/bin/python: No module named pytest`; `make test-contracts` նույն սխալով կարմիր է։
   - Կոդային հիմք՝ `Makefile:43-44` և `Makefile:46-47` օգտագործում են `python -m pytest ...`։ Այս shell-ում `command -v python` → `/Users/apple/.hermes/hermes-agent/venv/bin/python`, որը project dependency-ներ չունի։
   - Հակակշիռ՝ canonical `uv run --with pytest pytest tests/ -q` կանաչ է՝ `419 passed, 8 skipped in 259.72s`։

7. [P2] [BROKEN] Install target-ները կախված են bare `pip`-ից, որը shell-ում չկա։
   - Ապացույց՝ Block C probe՝ `pip: command not found`, `python -m pip` → `No module named pip`, մինչդեռ `./.venv/bin/python -m pip` աշխատում է։
   - Կոդային հիմք՝ `Makefile:7`, `Makefile:13`, `Makefile:32`, `Makefile:35`, `Makefile:38-39`։
   - Ռիսկ՝ setup/install հրահանգները տարբեր միջավայրերում non-reproducible են և չեն օգտագործում project `.venv`/`uv` source of truth-ը։

8. [P2] [BROKEN] `make preflight` exit 0 է վերադարձնում, բայց bare `python` registry discovery-ում լուռ բաց է թողնում `green_screen_composite`-ը dependency mismatch-ի պատճառով։
   - Ապացույց՝ Block C. `make preflight` ելք՝ `exit=0`, բայց warning՝ `tool module 'tools.video.green_screen_composite' skipped during discovery: No module named 'numpy'`։
   - Կոդային հիմք՝ `tools/video/green_screen_composite.py:19` import անում է `numpy`, իսկ `tools/video/green_screen_composite.py:45` հայտարարում է `python:numpy` dependency։
   - Հակակշիռ՝ project `.venv` dependency probe-ում `numpy`, `PIL`, `pytest`, `jsonschema` և մյուս core dependency-ները OK են։

9. [P2] [WIRING-GAP / EXPECTED-GAP] Delivery promise gate-ը seam-ում opt-in է, որովհետև `delivery_promise` artifact-ը պարտադիր չէ։
   - Ապացույց՝ Block A. `lib/checkpoint.py:199-202` edit stage-ում կանչում է `run_edit_gates(edit_decisions, artifacts.get("delivery_promise"))`, իսկ `lib/gatechain.py:99-111` violation ստեղծում է միայն երբ promise-ը truthy է։
   - Schema evidence՝ `schemas/artifacts/proposal_packet.schema.json:67-70` `production_plan.required` = `["pipeline", "stages", "render_runtime"]`; `delivery_promise` property կա, բայց required չէ։
   - Ռիսկ՝ motion-led խոստումը կարող է չստուգվել, եթե promise carry-forward artifact-ը բացակայի։

### P3 — փաստաթղթային drift և non-blocking signals

10. [P3] [BROKEN/DOC-DRIFT] `ZAVODOM.md` delivery_promise gate coverage table-ը հնացած է։
    - Ապացույց՝ `ZAVODOM.md:43` ասում է՝ `Delivery promise | reviewer-invoked, not checkpoint seam yet`, մինչդեռ `lib/checkpoint.py:199-202` արդեն edit seam-ից կանչում է `run_edit_gates`, և `tests/zavod/test_gates.py:677-692` seam-level tests ունի։
    - Ռիսկ՝ owner/operator-ին սխալ operational պատկեր է տալիս։

11. [P3] [EXPECTED-GAP] HyperFrames doctor-ը pass է, բայց ցույց է տալիս low-memory և optional backend բացակայություններ։
    - Ապացույց՝ Block C `make hyperframes-doctor` → `OK`, `runtime_available: true`, `node_major: 22`, `npm_package_version: 0.7.31`, բայց նաև `Memory 8.0 GB total · 1.9 GB available — Low memory`, optional `whisper-cpp`, `Kokoro`, `MusicGen`, `Docker` բացակայում են։
    - Դասակարգում՝ non-blocking, որովհետև doctor-ը exit 0 է վերադարձրել։

## 3. Passed / green evidence

- Block B adversarial gates՝ 25/25 PASS, 0 false-positive, 0 false-negative, 0 broken, 0 expected-gap, 0 wiring-gap։
- Gate self-tests՝ `python3 lib/armenian_glyph_gate.py`, `python3 lib/brand_voice_check.py`, `python3 lib/continuity_checker.py` բոլորը PASS։
- Targeted regression՝ `uv run --with pytest --with jsonschema pytest tests/zavod/test_gates.py tests/zavod/test_bench_gate.py tests/zavod/test_bench_gate_checkpoint.py -q` → `63 passed in 19.39s`։
- Full suite canonical path՝ `uv run --with pytest pytest tests/ -q` → `419 passed, 8 skipped in 259.72s`։
- Healthcheck՝ `./.venv/bin/python lib/healthcheck.py` → `ALL GREEN`՝ corpus, brain craft files, ffmpeg, zavod manifests, gates, checkpoint seam, schemas, scout registry, style radar, memo inbox, specialist ladders, engine lanes։
- `make lint` կանաչ է և նոր `tools/analysis/composition_validator.py` path-ը ճիշտ է։
- Schema registry՝ 25 artifact schema listed են `schemas/artifacts/__init__.py::ARTIFACT_NAMES`-ում և `validate_artifact()`-ով հասանելի են։
- Pipeline refs՝ 16 manifest-ների `orchestration.skill`, `required_skills`, `stage.skill` հղումները missing=0 են։ Zavod manifests-ում owner-gated sub_stage առանց produces՝ 0։
- `zavod-reel` dry-run-ը զրո credit-ով ճիշտ հերթականությամբ հասավ generation stop-point-ին՝ `idea → script → scene_plan → assets`։ `idea`, `script`, `scene_plan` checkpoint-ները կանաչ էին և կանչեցին համապատասխան bench/script/scene_plan gates։
- launchd վիճակ՝ Hermes երեք label-ները running են PID-ներով, ZavodOM scout/style-radar label-ները loaded են և last exit code-ը 0 է։

## 4. Առաջարկվող fix հերթականություն

1. P1՝ story/canon gates-ը դարձնել checkpoint seam-ի non-bypassable մաս, կամ հստակ սահմանել որ փուլերում են canonical `story_bible`/canon lock artifacts պարտադիր։
2. P1՝ `assets` checkpoint-ում ստուգել asset paths/provenance-ը, իսկ `compose` checkpoint-ում ստուգել output existence + ffprobe՝ manifest success criterion-ին համապատասխան։
3. P1՝ pre-generation `assets` owner stop-ի համար ավելացնել օրինական checkpoint ձև, որը fake `asset_manifest` չի պահանջում։
4. P2՝ Makefile-ը կապել project `.venv`/`uv` source of truth-ին (`make test`, `make test-contracts`, install/preflight targets), որպեսզի bare Hermes Python-ը չդառնա false-red կամ degraded-green։
5. P2՝ delivery_promise carry-forward-ը պարտադիրացնել այն pipelines/stages-ում, որտեղ motion-led promise կա, կամ checkpoint seam-ում hard-fail անել missing promise-ը համապատասխան context-ի դեպքում։
6. P3՝ թարմացնել `ZAVODOM.md` delivery_promise status-ը և runtime caveat-ները։

## 5. Անվտանգության արձանագրություն

- Ոչ մի provider/generation call չի արվել։
- Credit չի ծախսվել։
- Հրապարակում, delete, commit/push չի արվել։
- Այս synthesis-ի միակ թույլատրելի repo write-ը այս ֆայլն է՝ `tests/stress/STRESS-REPORT-2026-07-04.md`։
- Վերջին արձանագրված `git status --short` synthesis-ից հետո՝ `?? tests/stress/STRESS-REPORT-2026-07-04.md` և նախապես եղած `?? tests/stress/STRESS-TEST-BRIEF-2026-07-04.md`։
