# BACKLOG P2 — Scene-plan-ի «աղքատության» գիծ (դիզայն-memo, ՉԻՐԱԿԱՆԱՑՎԱԾ)

Կարգավիճակ՝ backlog, owner-ի առանձին որոշման։ Ծագումը՝ 2026-07-02 stress test, EXPECTED-GAP.
«nice pool video» մեկ-scene vague scene_plan-ը անցնում է schema + variation + glyph բոլոր gate-երը,
որովհետև `staging`/`text_policy` դաշտերը optional են։ Ռիսկը՝ continuity gate-ը anchor-զուրկ scene-երի
վրա ձևականորեն pass է՝ ոչինչ չստուգելով — 06-18 դասի բագի վերադարձի դուռը։

## Առաջարկվող դիզայն (նվազագույն, seam-կողմ)

`lib/gatechain.run_scene_plan_gates`-ում, ՄԻԱՅՆ zavod-* pipeline-ների համար (այսինքն՝ ինչպես մյուս
zavod gate-երը, upstream-ը անփոփոխ), ամեն `type: generated` scene-ի վրա երեք նոր ստուգում.

1. **text_policy պարտադիր է** — `text_policy` դաշտը պիտի լինի (թեկուզ `{"mode": "none"}`)։
   Բացակա text_policy = ոչ ոք չի որոշել՝ տեքստ կա՞, ինչ լեզվով, overlay թե baked։
2. **staging պարտադիր է** — `staging` object պիտի լինի. դատարկ `{}`-ն ընդունելի է ՄԻԱՅՆ եթե
   scene-ի description-ում ձեռքի պրոպի հուշում չկա (տես #3)։
3. **Anchor-consistency heuristic** — եթե description-ը պարունակում է held-prop լեքսիկա
   (glass, cup, bottle, drink, phone, բաժակ, շիշ, հեռախոս, ձեռքին… ~20 բառանոց ցուցակ երկու լեզվով,
   corpus-ստուգված), իսկ `staging.in_hand_objects`-ը դատարկ է → violation
   «held prop implied but no continuity anchor declared»։ Սա է փակում 06-18 դռան բուն մեխանիզմը՝
   scene-director-ը չի կարող «մոռանալ» anchor-ը, երբ սցենարը պրոպ է ենթադրում։

Վերդիկտի մոդել՝ #1/#2 = hard violation (fail), #3 = fail՝ նույն կանոնով (heuristic-ը false-positive
տալու դեպքում scene-director-ը ուղղում է either description-ը, either anchor-ն է հայտարարում —
երկուսն էլ էժան են)։

## Ինչու seam-ում ոչ schema-ում

Schema-ում `staging`/`text_policy` required դարձնելը կկոտրի upstream OpenMontage pipeline-ները,
որոնք նույն scene_plan schema-ն են կիսում։ Gatechain-ի zavod-ճյուղը արդեն ունի «միայն zavod» semantics
(checkpoint._enforce_zavod_gates)՝ ուղղումը այնտեղ zero-upstream-risk է։

## Ընդունման չափանիշներ (երբ իրականացվի)

- Stress case «(ա) աղքատ scene_plan» → FAIL ≥1 violation (հիմա՝ անցնում է)։
- «(բ) վալիդ scene_plan» (text_policy/staging լրացված) → անփոփոխ PASS։
- Real dry-run scene_plan-ը (desert-owl teaser, 4 scene) → անփոփոխ PASS։
- `held-prop` heuristic-ի բառացուցակը corpus-ի դեմ ստուգված (false-positive rate՝ 0 գոյություն
  ունեցող վալիդ պլանների վրա)։
- Նոր regression test-եր test_gates.py-ում + healthcheck-ի gates տողի թարմացում։

Գնահատված ծավալ՝ ~60 տող կոդ + ~40 տող test։
