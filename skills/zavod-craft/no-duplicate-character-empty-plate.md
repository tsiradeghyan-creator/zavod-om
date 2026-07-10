# No-Duplicate-Character / Empty-Plate Method — Կրկնված կերպարի դեմ մեթոդ (FILM MODE)

> Ծնվել է 2026-06-14-ի «Վան» նախագծի արատից (Վանը կադրում կրկնվեց)։ Մինչ այս ֆայլը մեթոդի
> միակ ամբողջական շարադրանքը մնացել էր հին conversation-memory-ում — այժմ canon-ը ՍԱ է։
> Հղվում են՝ [[background-environment-artist]] · [[continuity-qc-supervisor]] ·
> [[auto-verification-loop]] · [[vfx-render-supervisor]] · [[qc-continuity-gate]]։

## Խնդիրը (ինչու է մեթոդը գոյություն ունի)
Երբ reframe/expand ես անում **բնակեցված** (կերպարներով լիքը) master-կադրից, մոդելը պահում է
հին կերպարը ՈՒ ավելացնում նորը → նույն հերոսը կադրում երկու անգամ, էքստրաները՝ անկայուն։

## Արգելքը (կոշտ)
**Բնակեցված master-ից reframe/outpaint ԱՐԳԵԼՎԱԾ Է։** Ոչ մի բացառություն ռենդեր-փուլում։

## Մեթոդը (4 քայլ)
1. **Empty plate** — նախ ռենդերվում է ԴԱՏԱՐԿ լոկացիա-plate-ը (առանց որևէ կերպարի)՝
   կողպված ֆոն ([[background-environment-artist]]-ի սեփականությունն է)։
2. **Single-instance placement** — ամեն կերպար դրվում է plate-ի վրա գիտակցաբար **մեկ անգամ**;
   prompt-ում պարտադիր՝ «only ONE [character]; no duplicate [character]»։
3. **Canonical portrait as reference** — ամեն կերպարի կանոնական դեմք-պորտրետը կցվում է որպես
   identity reference (Seedance @Image / Kling Elements / Veo Ingredients — `ai-pipeline.md`)։
4. **Composite the extras** — կարևոր էքստրաները (օր.՝ ուսուցիչը) մտնում են composite-ով կամ
   հետևողական առանձին շրջանակով, ոչ թե «ամբոխ» prompt-ով։

## Դարպասը
Ամեն frame ստուգվում է [[qc-continuity-gate]]-ի Per-frame Continuity Ledger-ով
(«Կրկնված կերպար ՉԿԱ», «Բոլոր դեմքերը = կանոնական պորտրետ»)։ FAIL → retake, ոչ reroll։
