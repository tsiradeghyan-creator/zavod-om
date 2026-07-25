# Bench Roster & Org-Chart — Զավոդի կազմը և պատասխանատվության քարտեզ

> Two connected rosters live here. `agents/registry.yaml` contains real dispatchable agent cards.
> The craft names below are role playbooks and gate responsibilities. A playbook may instruct a real
> worker, but the name alone does not prove that a separate worker ran. Cross-host execution follows
> `skills/meta/agent-routing.md`.

## Real executable agent roster

| Card | Kind | Responsibility |
|---|---|---|
| `executive-producer` | coordinator | route, dependency plan, owner gates, synthesis, preserved dissent |
| `research-accuracy` | specialist | current primary evidence, factual accuracy, source provenance, benchmark |
| `story-architect` | specialist | premise, structure, serial logic, format strategy |
| `authorial-voice-guardian` | specialist | Armenian integrity, dialogue register, pinned Maghakian Script DNA |
| `scriptwriter` | specialist | complete format-valid drafts and alternatives |
| `visual-director` | specialist | direction, camera, staging, storyboard, production design when visual work is relevant |
| `rights-provenance` | specialist | rights, consent, likeness, licenses, disclosures, payload provenance |
| `localization-director` | specialist | translation, subtitles, dubbing consent, glyph and register quality |
| `media-producer` | specialist | locked generation/edit/compose/sound/mastering path and receipts |
| `distribution-growth` | specialist | channel adaptation, publication plan, measurement, approval-bound external action |
| `system-architect` | specialist | routing, schemas, reliability, tests, and agent-system changes |
| `resilience-generalist` | fallback only | one bounded allowlisted replacement after a recoverable primary failure; never normal routing |
| `quality-auditor` | independent verifier | separate-run adversarial acceptance; cannot certify its own production work |

The router selects the smallest sufficient relevant team, not every card. Explicit request signals,
risks, and required capabilities decide activation; visual exclusions prevent visual work from being
added to a text-only request. Every selected and rejected card is recorded with reasons.

```text
executive-producer route
        ↓
specialist wave 1 (parallel only when safe)
        ↓
dependent specialist wave(s)
        ↓
executive-producer hash-bound synthesis candidate with dissent preserved
        ↓
independent final verification by quality-auditor in a different isolated run
```

Each completed task needs an execution-ledger receipt containing executor type, unique run ID,
prompt version, output hash, and evidence. A same-context performance of several roles is labeled
`single_context_simulation`; it is degraded drafting and cannot satisfy the independent audit. A
`revise` or `reject` verdict requires a new hash-linked plan; no producer may self-certify the same
terminal result.

## Craft role playbooks by department
- **Կառավարում.** `producer-craft` · `business-affairs` · **`production-manager-orchestrator`** · `production-protocol`
- **Պատմություն.** `idea-lab` · `serial-structure` · `style-profile` · `brand-voice` · `voice-extractor` · **`research-accuracy-consultant`**
- **Ռեժիսուրա.** `director-craft` · `production-team` (1st AD·casting·dialect·script-sup) · `storyboard`
- **Շարունակ./QC դարպասներ.** **`continuity-qc-supervisor`** (Կիքս-բռնող) · `qc-continuity-gate` · `auto-verification-loop` · `pre-advance-council` · **`editor-final-catch`**
- **Արվեստ.** `art-department` · **`background-environment-artist`** · `identity-guard`
- **Կամերա/Look.** `cinematography` · `color-craft` · **`vfx-render-supervisor`**
- **AI-ռենդեր.** `ai-pipeline`
- **Previz.** **`animatic-editor`**
- **Post/Finish.** `post-production` · **`compositor`** · `motion-design` · **`mastering-delivery-qc`** · `localization`
- **Ձայն.** `sound-craft` · **`voice-director`** · **`composer-music-supervisor`** · **`final-mixer`**
- **Ասսեթ/Ops.** **`media-asset-manager`**
- **Հարթակ/Աճ.** `playbook` · `growth-analytics` · `carousel-template` · **`trailer-editor`**
- **Մետա/Ռեֆ.** `world-benchmark` · `shotdeck-reference-lab`

(Bold names are emphasized craft responsibilities, not proof of isolated execution.)

## Role responsibility gate chain
```
1  ԻԴԵԱ ............ idea-lab        + Accuracy gate (research-accuracy)
2  ՍՑԵՆԱՐ .......... style-profile   + Pre-Advance Council
3  ՖՈՆ-PLATE ....... background-environment-artist
4  STORYBOARD ...... storyboard      + Continuity (ռիսկ)
5  ANIMATIC ........ animatic-editor  ⛔ տեմպ-կողպեք նախ ռենդերի
6  ՌԵՆԴԵՐ ......... vfx-render-supervisor (single-instance)
7  QC (frame) ...... continuity-qc-supervisor  ⛔ 17 կատ.
8  COMPOSITE ....... compositor       ⛔ անխզում
9  EDITOR .......... editor-final-catch ⛔ shot-to-shot
10 ՁԱՅՆ ........... voice-director → composer/music → final-mixer ⛔
11 MASTER .......... mastering-delivery-qc ⛔ LUFS/AI-պիտակ/սպեկ
12 ՀՐԱՊ. .......... playbook/growth  (+ trailer-editor promo)
─ Միջանցիկ՝ media-asset-manager (ոչ մի ֆայլ չկորչի) · auto-verification-loop (կոշտ դարպաս ամեն ⛔-ում)
─ Բոլորը հսկում է production-manager-orchestrator · owner-որոշումները՝ production-protocol
```

## Gate and claim law

At every ⛔: fail → bounded retake/fallback → owner escalation. No downstream wave starts
until required dependencies have terminal acceptable receipts. In automatic draft mode, internal
work may continue across non-owner gates, but publication, spend, rights/likeness/location decisions,
destructive changes, and final delivery still require exact owner approval.

The roster is not evidence that the system is globally superior. Any "best in the world" claim
requires a versioned blind benchmark against named current systems on identical briefs, inputs,
budgets, and rubrics, repeated runs for variance, plus expert human preference review.
