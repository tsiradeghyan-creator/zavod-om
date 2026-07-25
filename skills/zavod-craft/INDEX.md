# ZavodOM — Brain index (52 craft files → spine slots)

> The zavod's brain (taste / voice / craft) lives here as 52 craft files (+ `SKILL.md` and this
> `INDEX.md` = 53 top-level `.md` files). `style-library/` adds the matured style cards.
> `commercial-prompt-library/` adds 6 Seedance 2.0 format cards: 5 commercial (viral-hook,
> saas-launch, luxury-aesthetic, before-after, testimonial-story; source:
> `rediumvex/ai-video-generator-claude`, ingested 2026-07-09 by scout) + `ai-cartoon-reel`
> (3D-character cartoon Reels: 6-block Seedance structure, Character Sheet consistency, format/style
> maps; distilled from the owner's *Soyuz AI Lab* course, ingested 2026-07-24). Stage-organized
> cartoon craft (montage, mistakes-QC, monetization) lives in `ai-cartoon-production-notes.md`;
> a cross-stage tool/engine picker lives in `ai-tools-directory.md` (both distilled from the same
> Soyuz AI Lab course, 2026-07-24). The `ai-cartoon-reel.md` style map carries 14 ready style clauses.
> This index WIRES each
> one to the OpenMontage spine: which pipeline **stage/role** consults it and which **gate** it
> feeds. Director skills (`skills/pipelines/<pipeline>/<role>-director.md`) MUST cite the craft
> files listed for their stage. General first; Maghakian-specific marked [HY].

## Stage → craft → gate map
| Pipeline stage / role | Craft files (brain) | Enforced by |
|---|---|---|
| **idea-director / content-idea-director** | `idea-lab.md`, `serial-structure.md`, `research-accuracy-consultant.md` + `ai-cartoon-production-notes.md` (cartoon idea→script method, when the brief is an AI-cartoon reel) | brief + `content_spec` + `creative_identity` schemas; deterministic route check |
| **script-director / content-script-director** | `style-profile.md` [HY authorial voice], `brand-voice.md`, `voice-extractor.md`, `corpus-notes.md` | script schema + glyph/brand voice + mandatory blind `candidate_bakeoff`; strict mode also requires `authorial_voice_report` with pinned hashes/evidence [HY] |
| **content-quality-director** | `post-production.md`, `editor-final-catch.md`, `localization.md`, `business-affairs.md` | aggregate `content_quality_report`; every locked deliverable exactly once, all eight checks exactly once, exact draft-payload SHA-256, no open/revise issue |
| **scene-director** | `director-craft.md`, `cinematography.md`, `storyboard.md`, `prompt-axes.md`, `art-department.md`, `shotdeck-reference-lab.md`, `color-craft.md`, `style-rider.md` (owner canon) + `style-radar.md` + `style-library/` (cinema_dp + color_luts cards) + `commercial-prompt-library/` (commercial/ad formats, when the brief is promo/ad/social-commercial; `ai-cartoon-reel.md` when the brief is a 3D-character AI cartoon) | **scene_plan schema** (`shot_language`, `staging`, `text_policy`) + variation_checker |
| **asset-director** | `ai-pipeline.md`, `prompt-axes.md`, `motion-design.md`, `identity-guard.md`, `background-environment-artist.md`, `carousel-template.md`, `fal-setup.md`, `ai-tools-directory.md` (which engine for which job), `style-rider.md` (owner canon) + `style-radar.md` + `style-library/` (design_styles cards), `providers/higgsfield-capabilities.md`, `commercial-prompt-library/` (Seedance 2.0 commercial prompt formulas + `ai-cartoon-reel.md` for 3D-character cartoon reels: 6-block structure & Character Sheet consistency) + the standalone `higgsfield` skill (`~/.claude/skills/higgsfield/`, OSideMedia v3.20.1) for MCSLA prompts, model specs & failure modes when generating via Higgsfield + `gpt-image-prompting/` (OpenAI gpt-image models: use-case routing, prompting fundamentals, generate/edit API — for still-image gen/edit: logos, ads, infographics, product/UI mockups, style transfer, object removal, character consistency) | asset_manifest schema + glyph gate on text assets |
| **edit-director** | `post-production.md`, `editor-final-catch.md`, `animatic-editor.md`, `trailer-editor.md`, `compositor.md`, `style-rider.md` (owner canon) + `style-radar.md` + `style-library/` (montage cards) + `ai-cartoon-production-notes.md` (cartoon montage: tempo, plane changes, audio mix ladder, pre-export 5-question check) | edit_decisions schema + reviewer |
| **compose-director** | `sound-craft.md`, `voice-director.md`, `composer-music-supervisor.md`, `final-mixer.md`, `mastering-delivery-qc.md`, `localization.md`, `vfx-render-supervisor.md` | render_report + **continuity_checker** + ffprobe gate; `delivery_promise` is checkpoint-enforced at the edit seam |
| **publish-director / content-publish-director** | `playbook.md`, `growth-analytics.md`, `business-affairs.md` + `ai-cartoon-production-notes.md` (cartoon pricing models + 2026 market reference + client acquisition & commercial-proposal method) | publish_log schema + final rights/provenance gate; export and publish need the exact local payload + matching rights hash, publish also needs returned URL |
| **executive-producer / orchestrator** | `production-protocol.md`, `bench-roster.md`, `production-manager-orchestrator.md`, `production-team.md`, `producer-craft.md`, `business-affairs.md`, `pre-advance-council.md`, `world-benchmark.md`, `ai-tools-directory.md` (tool/engine picker across text/image/video/voice/music) | checkpoint gates + budget cap |
| **continuity / QC (reviewer)** | `continuity-qc-supervisor.md`, `qc-continuity-gate.md`, `no-duplicate-character-empty-plate.md`, `auto-verification-loop.md`, `media-asset-manager.md` + `ai-cartoon-production-notes.md` (12-point cartoon mistakes checklist + 100-pt deliverable scorecard) | **reviewer + continuity_checker + glyph gate** |

## Project knowledge (not core; loaded per project)
`show-khaghaliq.md`, `carousel-khaghaliq-prompts.md`, `filmography.md` → Maghakian project packs.

## Hard gates the brain must pass (code-enforced, see `lib/`)
These are wired into the **checkpoint enforcement seam** (`lib/checkpoint._enforce_zavod_gates`,
dispatched by `lib/gatechain.py`): a `zavod-*` stage **cannot** persist a `completed`/`awaiting_human`
checkpoint whose artifacts fail their gate. Upstream pipelines are untouched. Contract and regression
tests live under `tests/zavod/`.
1. `armenian_glyph_gate.py` — any on-screen text with Latin/Cyrillic spliced into an Armenian word, OR a Cyrillic homoglyph word in Armenian context → **fail**. Runs on **all** text regardless of declared language; the old language-tag bypass is closed. ✅ live & enforced (script + scene_plan seam)
2. `continuity_checker.py` — `staging.in_hand_objects` must persist across each generated clip (object-permanence); `fail` blocks, `needs_human` pauses at the human checkpoint (kept distinct). ✅ live & enforced (compose seam)
3. `variation_checker.py` — slideshow/generic-phrasing taste check. ✅ live & enforced (scene_plan seam)
4. `brand_voice_check.py` — generic-AI-trope / drift vs `style-profile.md`/`brand-voice.md`. ✅ live & enforced (script seam)
5. `delivery_promise.py` — motion-led can't silently become slideshow. ✅ live & enforced (edit seam, 2026-07-02 fix pass)
6. `candidate_bakeoff.py` — requires 3–5 complete schema-valid drafts, blind labels/system preference,
   at least two creative difference axes, unique verified hashes, material text differences, one reason
   per rejection, and exact canonical hash identity between the selected candidate and final script.
   ✅ live & enforced (`zavod-content` script seam)
7. `authorial_voice.py` — strict Script DNA checks draft/profile hashes, seven scored criteria,
   real draft excerpts, pinned corpus references, Unicode, format, and register signals. ✅ live & enforced
   when `creative_identity.authorial_voice.mode = strict` (script seam)
8. `content_router.py` + checkpoint contracts — `content_spec` must map to the selected pipeline;
   automation mode, spec, and creative identity cannot drift between stages. ✅ live & enforced for
   `zavod-content`
9. `content_quality_report` — format-neutral editorial post-production must cover every promised
   deliverable exactly once, run all eight checks exactly once, bind evidence to the reviewed payload
   hash, and pass with no open issue. ✅ live & enforced (`quality` seam)
10. `gatechain.py` + `provenance.py` — final exports/publications block unresolved rights, consent,
   terms/disclosure, missing exact local payload, hash mismatch, or an uncovered final file; publication
   also needs a returned URL. Claimed signed/verified C2PA manifests are file/hash-checked. A hash is
   evidence, not cryptographic signature verification. ✅ live & enforced (final publish seam)

## Rule (Rule Zero + voice law)
- Every production starts by asking the owner for mode: **քո հաստատումներով՝ փուլ առ փուլ** (default)
  or **ավտոմատ լրիվ սևագրային վազք** (draft/verify internally, but no publish/spend/rights-lock/final
  delivery without explicit approval).
- Every production runs a pipeline; every stage cites its craft files above; in default mode no stage
  advances without passing its gate + the owner checkpoint (`Անցիր առաջ / Փոխիր / Ինքդ որոշիր`).
- Written and narrative deliverables use the no-render `zavod-content` lane
  (`idea → script → quality → publish`) when selected by the router; do not manufacture a scene,
  asset, edit, or compose stage for a text-only promise.
- Authorial voice and visual identity are separate locks. Strict Maghakian handwriting may be active
  while the visual identity stays neutral.
- **Armenian = Eastern Unicode only** (glyph gate). **On-image text = overlay**, not AI-baked.
