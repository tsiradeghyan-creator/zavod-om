# Universal Content Script Director

Read the locked `content_spec`, `creative_identity`, and selected brief. Then read only the craft files needed for the requested format. For strict Maghakian work, read `style-profile.md`, `corpus-notes.md`, `voice-extractor.md`, and `serial-structure.md`.

## Drafting sequence

1. Build structure before prose: outline, scene grid, argument map, or channel sequence.
2. Produce three genuinely different, complete candidates. Store all three in a schema-valid `candidate_bakeoff`; hide generator labels and system preference, declare at least two creative difference axes, score the candidates blind, and explain every rejection.
3. For one promised output, write the selected draft as `script.blocks`; use `scene_heading`, `action`, `dialogue`, and `parenthetical` blocks for screenplay formats.
4. When `content_spec` promises several outputs, write `script.deliverables`. Its ids must cover every locked deliverable exactly once; each item preserves the locked `kind` and language. Never hide several outputs inside one flat draft.
5. For `screenplay`, `series_episode`, or `stageplay`, include the schema-valid `story_bible`.
6. Trace factual claims with `source_ref`; unsupported claims are removed or clearly framed as opinion.

## Strict authorial voice

When `creative_identity.authorial_voice.mode` is `strict`:

1. Load the pinned profile with `lib.authorial_voice.profile_path`.
2. Create the machine half with `report_seed`.
3. The voice reviewers fill all seven criteria with a score and evidence.
4. Every `draft_excerpt` must exist verbatim in the draft. Every `corpus_ref` must exist in the pinned profile.
5. Run `validate_voice_report`; revise until it passes. Never invent a corpus example.
6. Preserve legitimate Russian code-switching while rejecting Latin-script Armenian and mixed-script Armenian words.

## Exit evidence

`script`, `candidate_bakeoff` whose selected draft hash exactly matches `script`, unchanged `content_spec`, unchanged `creative_identity`, optional/required `story_bible`, strict-mode `authorial_voice_report`, `production_ladder`, and full `bench_report`.
