# ZavodOM — Brain index (49 craft files → spine slots)

> The zavod's brain (taste / voice / craft) lives here as 49 craft files. This index WIRES each
> one to the OpenMontage spine: which pipeline **stage/role** consults it and which **gate** it
> feeds. Director skills (`skills/pipelines/<pipeline>/<role>-director.md`) MUST cite the craft
> files listed for their stage. General first; Maghakian-specific marked [HY].

## Stage → craft → gate map
| Pipeline stage / role | Craft files (brain) | Enforced by |
|---|---|---|
| **idea-director** | `idea-lab.md`, `serial-structure.md`, `research-accuracy-consultant.md` | brief schema + reviewer `review_focus` |
| **script-director** | `style-profile.md` [HY voice], `brand-voice.md`, `voice-extractor.md`, `corpus-notes.md` | script schema + `brand_voice_check` + glyph gate [HY] |
| **scene-director** | `director-craft.md`, `cinematography.md`, `storyboard.md`, `art-department.md`, `shotdeck-reference-lab.md`, `color-craft.md` | **scene_plan schema** (`shot_language`, `staging`, `text_policy`) + variation_checker |
| **asset-director** | `ai-pipeline.md`, `motion-design.md`, `identity-guard.md`, `background-environment-artist.md`, `carousel-template.md`, `fal-setup.md`, `providers/higgsfield-capabilities.md` | asset_manifest schema + glyph gate on text assets |
| **edit-director** | `post-production.md`, `editor-final-catch.md`, `animatic-editor.md`, `trailer-editor.md`, `compositor.md` | edit_decisions schema + reviewer |
| **compose-director** | `sound-craft.md`, `voice-director.md`, `composer-music-supervisor.md`, `final-mixer.md`, `mastering-delivery-qc.md`, `localization.md`, `vfx-render-supervisor.md` | render_report + **continuity_checker** + delivery_promise + ffprobe gate |
| **publish-director** | `playbook.md`, `growth-analytics.md` | publish_log schema |
| **executive-producer / orchestrator** | `production-protocol.md`, `bench-roster.md`, `production-manager-orchestrator.md`, `production-team.md`, `producer-craft.md`, `business-affairs.md`, `pre-advance-council.md`, `world-benchmark.md` | checkpoint gates + budget cap |
| **continuity / QC (reviewer)** | `continuity-qc-supervisor.md`, `qc-continuity-gate.md`, `auto-verification-loop.md`, `media-asset-manager.md` | **reviewer + continuity_checker + glyph gate** |

## Project knowledge (not core; loaded per project)
`show-khaghaliq.md`, `carousel-khaghaliq-prompts.md`, `filmography.md` → Maghakian project packs.

## Hard gates the brain must pass (code-enforced, see `lib/`)
1. `armenian_glyph_gate.py` — any Armenian text (`text_policy.language=hy`) with Latin/Cyrillic → **fail**. ✅ live
2. `continuity_checker.py` — `staging.in_hand_objects` must persist across each generated clip (object-permanence). ⏳
3. `delivery_promise.py` — motion-led can't silently become slideshow. (port) ⏳
4. `variation_checker.py` — slideshow/generic-phrasing taste check. (native, tune GENERIC_PHRASES) ⏳
5. `brand_voice_check.py` — drift vs `style-profile.md`/`brand-voice.md`. ⏳

## Rule (Rule Zero + voice law)
- Every production runs a pipeline; every stage cites its craft files above; no stage advances without
  passing its gate + the human checkpoint (`Անցիր առաջ / Փոխիր / Ինքդ որոշիր`).
- **Armenian = Eastern Unicode only** (glyph gate). **On-image text = overlay**, not AI-baked.
