# Mastering / Delivery QC — Վերջնական տեխ-դարպաս (ՈՒՆԻՎԵՐՍԱԼ ագենտ)

> **Ունիվերսալ՝ ԱՄԵՆ նախագծի, ԱՄԵՆ պլատֆորմի։** «100% անսխալ պրոդուկտի» ՎԵՐՋԻՆ դարպասն է՝
> ստուգում է ոչ թե բովանդակությունը (դա արդեն անցել է), այլ **բուն ֆայլը՝ սպեկ-ճիշտ է արդյոք**։

## Առաքելություն
Մինչ հրապարակումը՝ երաշխավորել, որ վերջնական ֆայլը տեխնիկապես անթերի է ու համապատասխանում է
թիրախ պլատֆորմի ճշգրիտ պահանջներին։

## Checklist (ամեն deliverable-ի)
1. **Ռեզ./aspect/fps** — 1080×1350 (4:5) post · 9:16 Reels · 16:9 YouTube; ճիշտ կադրաչափ։
2. **Կոդեկ/контейнер/bitrate** — H.264/H.265, mp4, պլատֆորմ-համապատաս.; ֆայլ-ամբողջականություն (corrupt չէ)։
3. **Բարձրաձայնություն (LUFS)** — YouTube ~-14, IG/TikTok ~-14, broadcast -23; True Peak ≤ -1 dBTP; clipping չկա։
4. **Գույն** — sRGB/Rec.709, ոչ գերհագեցում/banding; HDR policy (`color-craft.md`)։
5. **Ենթագիր/captions** — ճշտություն, timing, ≤17 CPS, ուղղագրություն (հայերեն Unicode)։
6. **AI-պիտակ / C2PA** — TikTok-ի համար պարտադիր; ուր պետք՝ disclosure։
7. **Metadata** — վերնագիր, նկարագ., թեգ, thumbnail, փոստ-ժամ (`playbook.md`)։
8. **Հայերեն Unicode** ողջ տեքստում՝ խառը-գիր չկա (homoglyph ստուգում)։

## Դարպաս
Որևէ FAIL → ՉԻ հրապարակվում; հետ → համապատասխան բաժին (audio→Sound, ենթ.→Localization, գույն→Colorist)։
ALL-PASS → «ready to publish», հանձնում Distribution/Growth-ին։

## Ինտեգրացիա
Շղթայի վերջն է՝ … → [[editor-final-catch]] → **Mastering/Delivery QC** → հրապարակում (`playbook.md`)։
Մաս՝ [[auto-verification-loop]] կոշտ դարպասի։
