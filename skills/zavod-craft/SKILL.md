---
name: content-zavod
description: Content factory ("zavod") for Maghakian Script Writing Agency — runs the full pipeline from idea to published post in Ani Maghakyan's real voice. Use when the user wants to make Instagram/Telegram/Facebook content, write a carousel or Reel script, generate post visuals (photo) or video, write captions + hashtags, or batch-produce posts. Triggers: "զավոդ", "կոնտենտ զավոդ", "սցենար գրի", "կարուսել", "ռիլս", "փոստ սարքի", "նոր post", carousel/reel/script for maghakianscripts. ALWAYS load this for Maghakian content production; it orchestrates maghakian-brand + style-profile + the generation engines.
metadata:
  version: 1.2.0
  owner: Ani Maghakyan / Maghakian Script Writing Agency
---

# Content Zavod — Maghakian Content Factory

A production line that turns one idea into a finished, on-brand, on-voice post
(carousel · Reel · caption) for the agency. It does NOT re-derive the brand or the
voice every time — it reads the locked references below and **learns**: every time the
user gives a new script or feedback, update `style-profile.md` so the factory gets
sharper over time.

## The 4 stations (the pipeline)

```
IDEA ──▶ 1. ՍՑԵՆԱՐ ──▶ 2. ՎԻԶՈՒԱԼ ──▶ 3. ԵՆԹԱԳԻՐ ──▶ 4. ՀՐԱՊԱՐԱԿՈՒՄ
        (script in        (photo /         (caption +       (schedule /
         Ani's voice)      video)           5 hashtags)      hand-off)
```

1. **Script** — write the scene/episode/Reel script in Ani's real **screenwriting voice**.
   → Read `style-profile.md` FIRST — it is her screenplay craft DNA (her exact Armenian format,
     Yerevan-dialect vs literary registers, `,,,` beats, subtext, intercut threads), built from
     her real `.docx` scripts. Match the register of the target series.
   → For carousel *copy* (marketing text, not a script) use `carousel-template.md`'s caption rules.
   → For a multi-episode Instagram serial concept, route to the `mini-scenario` skill.
2. **Visual** — generate the images or video.
   → Carousels: `carousel-template.md` (editorial recipe, **Background-only + Canva text overlay**).
   → Video / Reels: route to `jackvsai-fashion-campaign-prompt-framework` for the storyboard
     prompt, then render on an engine (below).
3. **Caption** — Armenian caption (SEO-keyworded) + exactly 5 hashtags + first-comment.
   → Rules in `playbook.md`.
4. **Publish** — posting time, first-hour velocity, format split. → `playbook.md`.
   → For actual multi-platform scheduling, the `postiz` skill can publish.

Always tell the user, in plain Armenian, which station you are on and what to do next.

## FILM MODE — full production pipeline (idea → finished product)

For anything bigger than a single post (micro-drama, sizzle, TV pitch, shot film/episode),
the zavod runs the full specialist bench. Each station = a craft file with world-class
technique tuned to Ani's voice:

```
0. ԻԴԵԱ ──▶ 0.5 ԿԱՌՈՒՑՎԱԾՔ ──▶ 1. ՍՑԵՆԱՐ ──▶ 2. ՊՐՈԴՅՈՒՍԻՆԳ ──▶ 3. ՌԵԺԻՍՈՒՐԱ ──▶ 4. ՕՊԵՐԱՏՈՐ ──▶
(idea-lab)  (serial-structure)  (style-profile)  (producer-craft)  (director-craft)  (cinematography)
──▶ 5. ՆԿԱՐԱՀԱՆՈՒՄ / AI-ՌԵՆԴԵՐ ──▶ 6. ՓՈՍՏ-ՊՐՈԴԱԿՇՆ ──▶ 7. ՀՐԱՊԱՐԱԿՈՒՄ ──▶ 8. ԱՃ
    (ai-pipeline)                    (post-production)      (playbook)         (growth-analytics)
```

**Full specialist bench (each is a loadable craft file):** around the core pipeline run
the departments — **camera:** `cinematography.md` · `color-craft.md`; **directing:**
`director-craft.md` · `production-team.md` · `storyboard.md` · `art-department.md`; **story:** `idea-lab.md`
· `serial-structure.md` · `style-profile.md` · `brand-voice.md` · `voice-extractor.md`; **business:**
`producer-craft.md` · `business-affairs.md`; **post:** `post-production.md` ·
`sound-craft.md` · `motion-design.md` · `identity-guard.md` · `localization.md`; **platform/AI:** `playbook.md`
· `carousel-template.md` · `ai-pipeline.md` · `growth-analytics.md`; **meta/reference:**
`world-benchmark.md` · `shotdeck-reference-lab.md`.

- The director's beat sheet + shot list feed the DoP's prompt-translation table — craft
  survives the AI pipeline, vibes don't.
- Big bets pass `idea-lab.md`'s gates (G1–G4) + an `llm-council` verdict before money moves.
- Hard rules (faces, Armenian Unicode, Background) apply in every mode.
- Craft depth + 2026-market corrections: wiki [[zavod-craft-audit-2026-06]].

## Hard rules (never break)

- **Gated workflow (GOVERNANCE — `production-protocol.md`).** No station advances the
  project to the next stage on its own. Each phase ends with an **Agent Report (checklist)**;
  the system **freezes** and waits for the owner's ONE command — **Անցիր առաջ** (approve) /
  **Փոխիր այս դետալը** (veto) / **Ինքդ որոշիր** (delegate to Co-Producer). Never render,
  publish, spend, or hand off without it. Flag anything needing the owner (face/identity ref,
  location, rights, budget) as **❓ ՔՈ ՈՐՈՇՈՒՄԸ ՊԵՏՔ Է** — never silently invent it.
- **Armenian = proper Eastern Unicode only.** Never transliteration, never Latin-Armenian.
- **Background-default for Armenian text → test-then-trust:** default to generating the
  **Background only** + Canva text overlay (the "Ֆոն → Background" rule). Short display words
  MAY be AI-rendered if they pass the character-by-character glyph gate; body text always
  stays Canva. Protocol in `ai-pipeline.md`.
- **No actor faces / no copyrighted stills** as AI output — use objects, symbols, posters-as-prop,
  editorial layout. Faces only from licensed/owned material.
- **Max 5 hashtags** (caption + comments COMBINED, Dec-2025 cap) — put 3–5 in the CAPTION,
  Armenian keyword-aligned (`playbook.md`).
- **1080×1350** (4:5) for carousels/posts; vertical 9:16 for Reels.
- **Label AI video** per platform (TikTok C2PA mandatory).

## Living voice — the self-improving loop

- Before writing ANY script, read `style-profile.md`.
- After the user edits your draft, gives a new example script, or says "more like this /
  less like that" → **append the lesson to `style-profile.md`** (Changelog section) and adjust
  the rules. The user explicitly wants the factory to keep learning from the scripts they feed.
- Keep examples real (from the user's own posts), not invented.

## Script corpus (the real source of her voice)

Her actual screenplays (~54 `.docx` episodes across ~12 series) live canonically in
`~/Documents/Maghakian-Scripts/docx/` (extracted text: `~/Documents/Maghakian-Scripts/txt/`,
backed up 2026-06-11; the old `~/Downloads/` copies are legacy). `style-profile.md` is derived from them.
The Instagram carousel HTML in `~/insta ej scripts/` is marketing copy, NOT scripts.

## Brand source of truth

Read the `maghakian-brand` skill for identity, colors (`#6450D2` purple, `#0D0D0D`,
`#FAFAFA`), logo, fonts, portfolio numbers, and tone. This zavod does not duplicate those —
it consumes them. **Never** describe a single show as the whole career; use the aggregate
portfolio numbers from `maghakian-brand/portfolio.md`.

## Generation engines (Station 2)

The 2026 engine lineup (Nano Banana Pro · Ideogram 4.0 · Veo 3.1 · Kling 3.0 · Seedance ·
Sync · MiniMax Music · ElevenLabs v3 Armenian TTS · Topaz), the Armenian-text protocol,
the consistency/seed/cost workflow and render QC all live in **`ai-pipeline.md`**. Setup/
keys → `fal-setup.md` (✅ `FAL_KEY` configured 2026-06-05; restart Claude Code if absent).
Fallback engines live now without setup: Canva + Adobe Firefly (Kling inside).

## Reference files (load on demand)

| File | Load when |
|------|-----------|
| `bench-roster.md` | **START HERE for any production** — full agent roster (universal) + the responsibility gate-chain; the Orchestrator's map |
| `production-manager-orchestrator.md` | autonomous/self-governing run — route every asset through the gate-chain, track status, escalate blocks |
| `pre-advance-council.md` | BEFORE advancing ANY stage — relevant agents brainstorm flaws/pros/cons/ideas, then proceed |
| `continuity-qc-supervisor.md` | the "kiks-catcher" — per-frame 17-category continuity QC (= Script/Animation Supervisor) |
| `auto-verification-loop.md` | autonomous self-checking gate — forced per-person enumeration, bounded retake, escalate |
| `qc-continuity-gate.md` | continuity acceptance criteria + accountability matrix (who owns which defect) |
| `editor-final-catch.md` | shot-to-shot final QC — match-on-action, drift, object-permanence, audio sync |
| `research-accuracy-consultant.md` | fact/cultural/mythology/historical accuracy — Canon Sheet, every project |
| `vfx-render-supervisor.md` | per-shot quality/approach of generated imagery (creative layer over `ai-pipeline`) |
| `background-environment-artist.md` | locked location plates (empty-plate method) — environment continuity |
| `animatic-editor.md` | assemble storyboard + temp VO/music into an animatic; lock pacing BEFORE final render |
| `compositor.md` | combine layers (plate+character+FX+titles) into a seamless final shot |
| `voice-director.md` | direct the VO performance + pronunciation (ElevenLabs/Armenian) |
| `composer-music-supervisor.md` | original music/leitmotifs + licensed-music selection & clearance |
| `final-mixer.md` | final audio balance (VO/music/sfx) before mastering |
| `mastering-delivery-qc.md` | final technical deliverable gate — resolution/LUFS/captions/AI-label/platform spec |
| `media-asset-manager.md` | no file lost — download expiring URLs, name/version/backup, asset registry |
| `trailer-editor.md` | cut teasers/promos/trailers (hook-first, spoiler-safe) for marketing |
| `no-duplicate-character-empty-plate.md` | rendering shots from a populated master — the single-instance rule (anti-duplication) |
| `style-profile.md` | writing any script/scene — Ani's screenwriting **handwriting** (craft) + Voice Fingerprint |
| `brand-voice.md` | ANY external voice — captions, bios, pitches, decks, taglines: the agency's **brand voice** + the Maghakian universe |
| `carousel-template.md` | building a carousel (structure + visual recipe) |
| `playbook.md` | captions, hashtags, posting time, algorithm, format split |
| `corpus-notes.md` | per-work map of the real script corpus (characters, premises, devices) |
| `filmography.md` | the full 47-project portfolio (years, episode/page counts, aggregates) — cite for scale stats & to confirm a show's year/episode count |
| `show-khaghaliq.md` | any post about «Խաղալիք» (2021) — verified facts, logline, themes, cast, sources |
| `carousel-khaghaliq-prompts.md` | rendering the «Խաղալիք» carousel — ready copy-paste all-AI prompt set (poster-referenced) |
| `fal-setup.md` | fal.ai engine status/setup — ✅ key configured 2026-06-05; restart Claude Code to load |
| `idea-lab.md` | generating/validating ANY new concept — what-if engine, high-concept + craft tests, route-weighted scoring, gates G1–G4, ethics gate |
| `serial-structure.md` | building a season/serial/micro-drama — arc grid, A/B/C braiding, tentpoles, typed cliffhanger menu, story bible |
| `director-craft.md` | planning a shoot or AI scene — shot grammar, blocking, actor direction, vertical 2026, AI-scene directing doctrine |
| `production-team.md` | crew around the director — 1st AD, script supervisor/continuity, casting, dialect coach, storyboard/previz |
| `storyboard.md` | **ՌԱՍԿԱԴՐՈՎԿԱ** — shot-by-shot board; the maximal per-frame card (camera·lens·light·color gradient·subtext object·audio); coverage minimum; real-shoot + AI-frame bridge |
| `art-department.md` | the physical world — production design, the subtext-object registry, costume, props, poster-prop stills |
| `cinematography.md` | lighting/lens/composition + modern-FX allow/forbid + the DoP→AI-prompt table (Veo 3.1/Kling 3.0/Seedance) + real-set kits |
| `color-craft.md` | the grade — show-LUT workflow, skin protection, cross-engine matching, halation, day-for-night, HDR policy |
| `producer-craft.md` | budgets, schedules, rights, ՓԼԵՅՍՄԵՆԹ rate card, format licensing, vertical economics, Armenian arbitrage |
| `business-affairs.md` | chain of title, AI/likeness/music rights, clearance & E&O, sponsor clauses, grants & co-production |
| `post-production.md` | edit grammar (Murch, eye-trace, match-on-action), modern FX, export specs 2026, QC |
| `sound-craft.md` | sound for silent AI footage — 4-layer build, dialogue chain, music licensing, leitmotifs, loudness |
| `motion-design.md` | Armenian kinetic typography — caption/title cards, the glyph gate, spelling/canonical-phrase lock, premium display type |
| `identity-guard.md` | premium logo/wordmark/vector gate — rejects cheap design, exports print-ready SVG, mono/inverse variants |
| `voice-extractor.md` | weekly auto-scan of the script corpus → draft voice deltas (new characters/aphorisms) for human-confirmed canon updates |
| `localization.md` | EN/RU voice-transfer + subtitle QC (≤17 CPS) + AI dubbing (ElevenLabs v3 Armenian) for the diaspora |
| `ai-pipeline.md` | the engine layer — 2026 model lineup, Armenian-text protocol, consistency/seed/cost registry, render QC |
| `growth-analytics.md` | the analytics loop — Trial Reels A/B, weekly metrics → content decisions, community/Telegram ops, paid boosts |
| `production-protocol.md` | ALWAYS in FILM MODE — the gated workflow law: every stage freezes, emits an Agent Report (checklist), waits for the owner's one command (approve/veto/delegate) |
| `world-benchmark.md` | before any big bet — benchmark every station vs the world's strongest tools; 12 fillable rival-beating templates + agent-by-agent upgrade map + greenlight memo |
| `shotdeck-reference-lab.md` | visual-reference research — ShotDeck Community live source map (copyright-safe), reference→Maghakian translation, shot-reference cards |

## Default run order

When the user says "make a post about X":
0. **Pre-flight (30 sec, silent):** corpus exists at `~/Documents/Maghakian-Scripts/`;
   `style-profile.md` loaded; any Armenian text you produce passes the mixed-script check
   (no Cyrillic/Latin lookalikes inside Armenian words). If something's off — say so first.
1. Confirm format (carousel vs Reel) + the one hook idea (offer 3 hooks).
2. Write the script (read `style-profile.md`).
3. Produce visuals (Background-only + note for Canva overlay, or render video).
4. Write caption (keyword-SEO in first 2 sentences) + 3–5 hashtags in the caption.
5. Give posting note (diaspora window 19:00–21:00 Yerevan, first-hour action).
6. If the user corrected the voice anywhere → update `style-profile.md`.
