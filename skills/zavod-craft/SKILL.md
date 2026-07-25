---
name: content-zavod
description: ZavodOM craft brain — universal production factory for supported written, narrative, image, audio, video, and mixed formats, always run through the ZavodOM routing, manifests, gates, and owner checkpoints. Use for zavod, post, article, screenplay, carousel, reel, promo, and film-mode production. Authorial voice is locked separately from optional visual identity. The bundled Maghakian Script DNA profile activates only on an explicit Maghakian or Ani identifier—never on a bare "for my brand".
metadata:
  version: 2.3.0
  owner: Universal Production Zavod (Maghakian brand pack bundled)
  status: canonical-zavodom-brain
---

# Content Zavod — ZavodOM Brain (universal, shareable)

This skill is the craft brain inside **ZavodOM**. It is not a prose-only workflow. It is
**brand-neutral by default** and routes each supported format through an implemented production
path. `creative_identity` keeps the author's handwriting separate from optional visual branding,
so the Maghakian Script DNA profile can be strict while colors, fonts, and visual packs remain
neutral. Every production must run through:

- `~/zavod-om/ZAVODOM.md`
- `lib/content_router.py` + a schema-valid `content_spec`
- the real manifest returned by the router. Five Zavod-specific manifests are available:
  `zavod-content`, `zavod-carousel`, `zavod-reel`, `zavod-reel-fast`, and `zavod-promo`;
  other supported formats may route to an existing OpenMontage manifest
- `skills/zavod-craft/INDEX.md`
- `skills/zavod-craft/production-protocol.md`

## Required opening question

Before doing any production work, ask:

```text
Ո՞ր ռեժիմով ենք աշխատում։
1. Քո հաստատումներով՝ փուլ առ փուլ։ Default. Ամեն փուլից հետո տալիս եմ հաշվետվություն ու սպասում եմ «Անցիր առաջ» հրամանին։
2. Ավտոմատ լրիվ սևագրային վազք։ Կարող եմ ներսում աշխատել, ստուգել ու հետ ուղարկել, բայց չեմ հրապարակում, գումար չեմ ծախսում, իրավունք/դեմք/լոկացիա չեմ փակում և վերջնական չեմ հանձնում առանց քո հաստատման։

Գործակալները լռելյայն ավտոմատ ընտրվում են հարցին առնչվող կարողություններով։ Ամբողջ բենչը միացրու միայն հստակ հրամանով։
```

Default is **քո հաստատումներով՝ փուլ առ փուլ** unless the owner explicitly chooses the
automatic draft run.

## Automatic agent activation law

Before non-trivial work, build the typed request and run `lib/agent_router.py` against
`agents/registry.yaml`; follow the cross-host contract in `skills/meta/agent-routing.md`. The
activation plan must follow this order:

```text
route → dispatch waves → append-only receipts → hash-bound synthesis candidate
→ independent final verification
```

- The route records intent, topics, formats, languages, risks, required capabilities, selected and
  rejected agents, and the reason for every decision. An unmatched required capability blocks work.
- Independent specialists in the same safe wave may run in parallel; dependencies, maximum team
  size, depth, wall time, and retry/fallback policy are bounded by the registry.
- Every completed task needs a host executor/run identity, output hash, and evidence in the
  `lib/agent_runtime.py` ledger. Terminal tasks are immutable.
- The Executive Producer builds one hash-bound candidate from receipt-backed specialist work and
  preserves objections and blockers.
- `quality-auditor` evaluates that exact candidate after synthesis in a distinct isolated run.
  Same-context self-review cannot satisfy this gate. A `revise` or `reject` verdict requires a new
  hash-linked plan; the producer cannot self-certify or rewrite the terminal result in place.
- Publication, paid generation or a material runtime change, rights/likeness decisions, destructive
  changes, and final delivery stop for owner approval bound to the exact planned action hash.

**Role playbooks are not real agents.** The 52 craft files and pipeline director files teach a worker
how to act; they do not prove that separate workers ran. A card in the registry becomes real execution
only when the host dispatches an isolated worker and records the receipt. The router plans; Claude,
Codex, or an API host executes. If isolation is unavailable, label the run
`single_context_simulation`. It is degraded drafting only and cannot close independent verification
or be reported as a complete multi-agent run.

## Owner approval law

- Every stage ends with an Agent Report.
- In owner-gated mode, every output must be approved before the next phase starts.
- The only advance command is **«Անցիր առաջ»**.
- The owner can veto with **«Փոխիր այս դետալը»**.
- The owner can delegate a bounded choice with **«Ինքդ որոշիր»**, but that never authorizes
  publish, spend, rights/likeness/location approval, or final delivery.
- If the owner says the script already exists, treat it as locked input and start from the
  next open phase. Do not rewrite the script unless asked.

## Producer map

The production map lives in `production-protocol.md`:

Written/narrative no-render work uses `idea → script → quality → publish`. Visual/media work uses
the applicable parts of the ten-step production map:

1. Գաղափարի ձևավորում
2. Նախնական մշակում
3. Սցենարի զարգացում
4. Ստեղծագործական թիմի ձևավորում
5. Տեխնիկական նախապատրաստում
6. Նախաարտադրություն
7. Նկարահանում
8. Հետարտադրություն
9. Վերջնականացում
10. Ներկայացում

## Stage routing

Load only the craft files for the current stage from `INDEX.md`.

- Idea/script/story: `idea-lab.md`, `serial-structure.md`, `style-profile.md`, `brand-voice.md`
- Written-content quality: `post-production.md`, `editor-final-catch.md`, `localization.md`,
  `business-affairs.md`; produces `content_quality_report` without forcing a render stage
- Scene/look: `director-craft.md`, `cinematography.md`, `storyboard.md`, `prompt-axes.md`, `art-department.md`, `style-rider.md`
- Assets/render: `ai-pipeline.md`, `prompt-axes.md`, `background-environment-artist.md`, `motion-design.md`, provider docs
- Edit/finish: `post-production.md`, `sound-craft.md`, `compositor.md`, `mastering-delivery-qc.md`
- Publish/growth: `playbook.md`, `growth-analytics.md`
- Governance/QC: `production-protocol.md`, `pre-advance-council.md`, `auto-verification-loop.md`, `qc-continuity-gate.md`

## Creative identity and brand packs

Brand-neutral is the default. Lock these axes independently in `creative_identity`:

1. `authorial_voice`: `neutral`, `reference`, or `strict`, with a named profile and register when active.
2. `visual_identity`: optional `neutral`, `reference`, or `strict` visual pack.

Activate a named pack only when the user explicitly identifies it. For the bundled **Maghakian**
profile that means a Maghakian or Ani identifier ("for Maghakian", "for Ani",
"Մաղաքյան բրենդի համար է", "maghakianscripts"). A generic "this is for my brand" is not enough:
ask which brand, then load that profile/pack or run neutral. Maghakian craft files are marked **[HY]**
in `INDEX.md` (`style-profile.md`, `brand-voice.md`, project packs).

When Maghakian `authorial_voice.mode` is `strict`, the script checkpoint requires the pinned
`maghakian-script-v1` profile plus an evidence-backed `authorial_voice_report`. The report must pin
the draft and profile hashes, cover all seven criteria, quote real draft excerpts, reference only
the pinned corpus, and pass the locked minimum score. Visual colors and fonts are not required unless
the user separately activates a visual identity.

## Hard rules

### Universal — every production, any brand or none
- **Honest routing:** validate `content_spec`, then use the deterministic router. If format and
  modality are incompatible or no audited route exists, fail loudly instead of pretending the
  nearest video pipeline fits.
- **Honest agent claims:** never convert a list of consulted role playbooks into a claim that several
  agents ran. Report activated card IDs, executor types, run IDs, and the ledger head hash.
- **Blind candidate proof:** every `zavod-content` script stage carries a `candidate_bakeoff` with
  three to five complete schema-valid drafts. Labels and system preference stay hidden; the set must
  differ across at least two creative axes, use unique verified hashes and materially different text,
  explain every rejection exactly once, and make the final script canonically identical to the
  selected candidate.
- **Text correctness (glyph gate):** no Latin/Cyrillic homoglyph spliced into a word in ANY
  language; when Armenian is used it must be proper Eastern Armenian Unicode. On-image body text
  goes through overlay, not AI-baked; AI-baked text only for short display words that pass the gate.
- **Written-content post-production:** `zavod-content` runs `idea → script → quality → publish`.
  A script may carry one deliverable or an exact package matching all locked deliverable IDs.
  The aggregate quality report must cover every promised deliverable exactly once, include all eight
  checks exactly once, carry no open/revise issue, and bind each result to the exact draft payload
  SHA-256. It does not invent scene/render work for a text deliverable.
- **Rights/provenance:** `draft` and `pending_review` may remain non-public with unresolved rights.
  Final `exported`/`published` entries require owner approval, passing rights/consent/disclosure,
  an exact local payload, and hash-verified coverage by a matching rights row. `published` also
  requires the returned URL. If C2PA status is claimed as `signed`/`verified`, the manifest file and
  declared hash must match; this local hash check is not cryptographic signature verification.
- **Superiority claims require blind evidence:** "best in the world" remains an ambition until a
  versioned blind evaluation compares named current baselines on identical briefs, inputs, budgets,
  and rubrics, repeats runs for variance, and includes expert human preference review. Green unit
  tests prove contract enforcement, not global creative superiority.
- No actor faces, likenesses, copyrighted stills, music, locations, or rights-sensitive material without explicit approval.
- Respect the platform hashtag cap (e.g. max 5 total) when publishing.
- Label realistic AI video per platform rules.
- For promo/generative visual work, never produce polished art or video before the owner locks:
  source frame, visual style, typography, character/people policy, technical storyboard, and prompt.
- Text-only `zavod-content` uses the `none` engine and no compose runtime. Media generation uses two
  mutually-exclusive engine lanes, asked up front and locked in `engine_lock` (never mixed):
  **Higgsfield** = AI footage (real source media attached) + **ffmpeg** overlay/assembly, **zero Remotion**;
  **Remotion** = programmatic build, no AI footage, compose via `remotion`/`hyperframes`.

### Brand-pack rules — only when a pack is active (named explicitly)
- **Maghakian authorial profile:** preserve behaviour over statement, subtext, register fidelity,
  natural dialogue, structure, format, and disciplined symbols/aphorisms. Legitimate Russian
  code-switching may remain; Latin-script Armenian and mixed-script Armenian words fail.
- **Maghakian visual pack, only if separately active:** Armenian body text on overlay/Canva only; **no actor
  faces** in AI frames (hands/back/silhouette/object); the storyboard **Maghakian-quiet** preset
  (restraint, behaviour over statement, board the hands). A different pack may allow faces or another
  language. `brand_voice_check` runs against the active pack's `style-profile.md`/`brand-voice.md`.

## Reporting template

```text
📋 ԱԳԵՆՏ <#>. <ԲԱԺԻՆ> | ՀԱՇՎԵՏՎՈՒԹՅՈՒՆ
- Արվածը՝ ...
- Ստուգված դարպասները՝ ...
- Բաց հարցերը՝ ... [ԼՈՒԾՎԱԾ Է | ❓ ՔՈ ՈՐՈՇՈՒՄԸ ՊԵՏՔ Է]
- Հաջորդ փուլը՝ ...

Սպասում եմ հրամանին՝ [Անցիր առաջ] · [Փոխիր <դետալ>] · [Ինքդ որոշիր]
```
