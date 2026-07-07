"""Regression tests for the 2026-07-04 red-team hardening.

Each test pins a bypass the red-team found (tests/stress/REDTEAM-REPORT-2026-07-04.md)
so it cannot silently reopen.
"""
import sys, tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from lib.bench_gate import run_bench_gates, required_bench  # noqa: E402
from lib.checkpoint import (  # noqa: E402
    ZAVOD_PIPELINE_TYPES, _is_zavod_pipeline, _enforce_artifact_path_existence,
    CheckpointValidationError,
)
from lib.gatechain import run_script_gates  # noqa: E402
from tests.zavod.media_helpers import tiny_mp4, tiny_wav, tiny_png  # noqa: E402


# ── Angle 1: bench rubber-stamp ────────────────────────────────────────────
def _bench(stage, ruling_for):
    return {"stage": stage, "bench": {r: {"ruling": ruling_for(r), "verdict": "approve"}
                                      for r in required_bench(stage)}}

def test_bench_blocks_repeated_word_filler():
    filler = "նույն բառը " * 6  # >60 chars, 2 distinct tokens
    assert not run_bench_gates("asset", _bench("asset", lambda r: filler))["ok"]

def test_bench_blocks_identical_rulings_across_roles():
    same = "The specialist reviewed this stage in depth and confirms the craft bar is met fully."
    assert not run_bench_gates("asset", _bench("asset", lambda r: same))["ok"]

def test_bench_does_not_crash_on_malformed_entry():
    # 2026-07-04 probe: a non-dict bench entry (string/list) used to raise AttributeError.
    rep = _bench("asset", lambda r: f"The {r} independently assessed craft quality across the stage.")
    rep["bench"]["reviewer"] = "just a string, not an object"
    r = run_bench_gates("asset", rep)
    assert not r["ok"] and any("malformed" in v for v in r["violations"])

def test_bench_allows_ruling_that_mentions_reject_in_prose():
    # 2026-07-04 probe: legit approvals ("nothing is blocked", "avoided a reject") must not
    # be false-flagged. Substring reject-detection was removed for this reason.
    rep = _bench("asset", lambda r: f"The {r} confirms nothing is blocked and no rejection "
                                    f"risk remains for role-specific {r} craft; approved cleanly.")
    assert run_bench_gates("asset", rep)["ok"]

def test_bench_allows_genuine_distinct_rulings():
    ok = run_bench_gates("asset", _bench(
        "asset",
        lambda r: f"The {r} examined its own domain thoroughly and reached a clear, specific "
                  f"conclusion about staging, palette, and continuity for this asset stage.",
    ))
    assert ok["ok"], ok["violations"]


# ── Angle 1b: #1 structured verdict contract ──────────────────────────────
def _good(stage):
    return _bench(stage, lambda r: f"The {r} examined its own {r} domain thoroughly and reached a "
                                   f"specific, well-supported conclusion on staging and continuity.")

def test_bench_blocks_missing_verdict():
    rep = _good("asset")
    del rep["bench"]["reviewer"]["verdict"]
    r = run_bench_gates("asset", rep)
    assert not r["ok"] and any("verdict" in v for v in r["violations"])

def test_bench_blocks_invalid_verdict():
    rep = _good("asset")
    rep["bench"]["reviewer"]["verdict"] = "lgtm"
    assert not run_bench_gates("asset", rep)["ok"]

def test_bench_blocks_reject_verdict_stage_cannot_close():
    rep = _good("asset")
    rep["bench"]["identity-guard"]["verdict"] = "reject"
    rep["bench"]["identity-guard"]["blocking_issues"] = ["face identity drifts between shots 2 and 5"]
    r = run_bench_gates("asset", rep)
    assert not r["ok"] and any("reject" in v for v in r["violations"])

def test_bench_blocks_revise_without_blocking_issues():
    rep = _good("asset")
    rep["bench"]["identity-guard"]["verdict"] = "revise"  # no blocking_issues named
    r = run_bench_gates("asset", rep)
    assert not r["ok"] and any("blocking_issues" in v for v in r["violations"])

def test_bench_near_similar_rulings_warn_not_block():
    # Shared template, one distinct token per role → near-identical (>=0.92) but not exact.
    shared = ("The specialist carefully reviewed staging blocking palette continuity lighting "
              "pacing sound and delivery across every shot of this stage and concluded the craft "
              "bar is comfortably met with no outstanding blocking concerns remaining anywhere")
    rep = {"stage": "publish", "bench": {
        r: {"ruling": shared + f" note {i}", "verdict": "approve"}
        for i, r in enumerate(required_bench("publish"))}}
    out = run_bench_gates("publish", rep)
    assert out["ok"], out["violations"]            # near-similarity does NOT hard-block
    assert out["warnings"]                          # …it is surfaced as a warning

def test_bench_exact_duplicate_rulings_still_block():
    same = "The specialist reviewed staging palette continuity and delivery and confirms the bar is met."
    rep = _bench("asset", lambda r: same)           # identical across roles (verdict approve)
    assert not run_bench_gates("asset", rep)["ok"]


# ── Angle 6: pipeline_type canonicalization ────────────────────────────────
@pytest.mark.parametrize("ptype", ["Zavod-reel", "ZAVOD-reel", " zavod-reel", "zavod-reel "])
def test_pipeline_type_casing_whitespace_still_gated(ptype):
    assert _is_zavod_pipeline(ptype) is True

@pytest.mark.parametrize("ptype", ["animation", "cinematic", "reel-zavod", "", None])
def test_non_zavod_pipelines_stay_ungated(ptype):
    assert _is_zavod_pipeline(ptype) is False


def test_zavod_prefixed_unknown_pipeline_fails_closed():
    with pytest.raises(CheckpointValidationError, match="unknown Zavod pipeline"):
        _is_zavod_pipeline("zavodx")


def test_zavod_pipeline_allowlist_matches_manifest_source_of_truth():
    manifests = {
        path.stem for path in (ROOT / "pipeline_defs").glob("zavod-*.yaml")
    }
    assert ZAVOD_PIPELINE_TYPES == manifests


# ── Phase 2 (2026-07-05 council #1): allowlist enforced at stage-navigation too ──
# _is_zavod_pipeline() blocked unknown zavod-* at the gate, but get_pipeline_stages()
# swallowed every exception and fell back to the generic stage list — so an unknown or
# homoglyph/zero-width zavod-* pipeline bypassed the allowlist through get_next_stage()
# / get_completed_stages(), which both route through get_pipeline_stages().
from lib.checkpoint import (  # noqa: E402
    get_pipeline_stages, get_next_stage, get_completed_stages, STAGES,
)


@pytest.mark.parametrize("bad", ["zavodx", "zavod-fake", "zavod-reel​", "zavodх"])
def test_get_pipeline_stages_fails_closed_on_unknown_zavod(bad):
    with pytest.raises(CheckpointValidationError):
        get_pipeline_stages(bad)


@pytest.mark.parametrize("bad", ["zavodx", "zavod-reel​", "zavodх"])
def test_stage_navigation_inherits_fail_closed(tmp_path, bad):
    with pytest.raises(CheckpointValidationError):
        get_next_stage(tmp_path, "p", bad)
    with pytest.raises(CheckpointValidationError):
        get_completed_stages(tmp_path, "p", bad)


@pytest.mark.parametrize("ptype", ["zavod-reel", "  Zavod-Reel  ", " zavod-reel"])
def test_valid_zavod_resolves_real_stages_despite_casing_whitespace(ptype):
    # A real zavod pipeline with stray casing/whitespace must resolve to its actual
    # manifest stages — never the generic fallback that masked the bypass.
    assert get_pipeline_stages(ptype) == get_pipeline_stages("zavod-reel")


def test_non_zavod_unknown_still_falls_back_gracefully():
    # The fail-closed rule is scoped to zavod-* only; a genuinely non-zavod pipeline whose
    # manifest is absent keeps the graceful canonical fallback (no false block).
    assert get_pipeline_stages("totally-unknown-pipeline") == list(STAGES)


# ── Phase 3a (2026-07-05 council #5-seam): compose continuity is mandatory ──
# The compose branch ran the continuity gate only "if reports:", so a completed compose
# with the render_report.continuity_reports field silently absent skipped the gate entirely
# — a missing report was a bypass. Closure now requires the field to be present as a list.
from lib.checkpoint import _enforce_zavod_gates  # noqa: E402

_RR_BASE = {"version": "1.0", "outputs": [
    {"path": "o.mp4", "format": "mp4", "resolution": "1080x1920", "duration_seconds": 5}]}


def _compose_cp(status, render_report):
    return {"pipeline_type": "zavod-reel", "stage": "compose", "status": status,
            "artifacts": {"bench_report": _good("compose"), "render_report": render_report}}


def test_completed_compose_without_continuity_field_is_blocked():
    with pytest.raises(CheckpointValidationError, match="continuity_reports"):
        _enforce_zavod_gates(_compose_cp("completed", dict(_RR_BASE)))


def test_completed_compose_empty_continuity_allowed_only_without_outputs():
    # #5 tightened 2026-07-06: an empty continuity list is a valid "nothing to track"
    # declaration ONLY when there are no rendered outputs.
    _enforce_zavod_gates(_compose_cp("completed", {"version": "1.0", "outputs": [], "continuity_reports": []}))


def test_completed_compose_with_outputs_requires_nonempty_continuity():
    # Real outputs + empty continuity = "rendered N clips, checked zero" → bypass, now blocked.
    with pytest.raises(CheckpointValidationError, match="continuity"):
        _enforce_zavod_gates(_compose_cp("completed", {**_RR_BASE, "continuity_reports": []}))


def test_awaiting_human_compose_without_continuity_is_allowed():
    # A mid-flight pause before continuity is judged is legitimate — only closure is gated.
    _enforce_zavod_gates(_compose_cp("awaiting_human", dict(_RR_BASE)))


def test_completed_compose_with_failing_continuity_still_blocks():
    rr = {**_RR_BASE, "continuity_reports": [
        {"clip": "o.mp4", "anchors": [{"name": "glass", "kind": "object", "persists": False}]}]}
    with pytest.raises(CheckpointValidationError):
        _enforce_zavod_gates(_compose_cp("completed", rr))


# ── Phase 3b (2026-07-05 council #7): cross-artifact referential integrity ──
# Each artifact passed its own schema, but nothing checked the links between them: an
# asset_manifest could name a scene_id ("GHOST") absent from the scene_plan and still pass.
import json as _json7  # noqa: E402
from lib.checkpoint import _enforce_referential_integrity  # noqa: E402


def _project_with_scene_plan(tmp_path, scene_ids=("s1", "s2")):
    (tmp_path / "checkpoint_scene_plan.json").write_text(_json7.dumps(
        {"artifacts": {"scene_plan": {"scenes": [{"id": s} for s in scene_ids]}}}))
    return tmp_path


def _assets_checkpoint(scene_id, ptype="zavod-reel"):
    return {"pipeline_type": ptype, "stage": "assets",
            "artifacts": {"asset_manifest": {"assets": [{"id": "a1", "scene_id": scene_id}]}}}


def test_asset_referencing_ghost_scene_id_is_blocked(tmp_path):
    pd = _project_with_scene_plan(tmp_path)
    with pytest.raises(CheckpointValidationError, match="Referential integrity"):
        _enforce_referential_integrity(_assets_checkpoint("GHOST"), pd)


def test_asset_referencing_real_scene_id_passes(tmp_path):
    pd = _project_with_scene_plan(tmp_path)
    _enforce_referential_integrity(_assets_checkpoint("s1"), pd)


def test_referential_integrity_scoped_to_zavod(tmp_path):
    pd = _project_with_scene_plan(tmp_path)
    _enforce_referential_integrity(_assets_checkpoint("GHOST", ptype="animation"), pd)  # non-zavod → skip


def test_referential_integrity_skips_when_no_scene_plan(tmp_path):
    # Partial run / isolated stage write: nothing to check against, so do not fabricate a block.
    _enforce_referential_integrity(_assets_checkpoint("GHOST"), tmp_path)


# ── Phase 4c (2026-07-06 dry re-probe #7-cont): edit -> asset_manifest references ──
def _project_with_assets(tmp_path, ids=("a1", "a2")):
    (tmp_path / "checkpoint_assets.json").write_text(_json7.dumps(
        {"artifacts": {"asset_manifest": {"assets": [{"id": i} for i in ids]}}}))
    return tmp_path


def _edit_checkpoint(asset_id):
    return {"pipeline_type": "zavod-reel", "stage": "edit",
            "artifacts": {"edit_decisions": {"overlays": [{"asset_id": asset_id}]}}}


def test_edit_referencing_ghost_asset_id_is_blocked(tmp_path):
    pd = _project_with_assets(tmp_path)
    with pytest.raises(CheckpointValidationError, match="Referential integrity"):
        _enforce_referential_integrity(_edit_checkpoint("GHOST"), pd)


def test_edit_referencing_real_asset_id_passes(tmp_path):
    pd = _project_with_assets(tmp_path)
    _enforce_referential_integrity(_edit_checkpoint("a1"), pd)


def test_edit_asset_reference_skips_when_no_asset_manifest(tmp_path):
    _enforce_referential_integrity(_edit_checkpoint("GHOST"), tmp_path)  # partial run → skip


# ── Phase A#7 (2026-07-06 owner decision): completed stages follow manifest order ──
from lib.checkpoint import _enforce_stage_order  # noqa: E402
from tests.zavod.media_helpers import seed_prior_stages  # noqa: E402


def _completed(stage, status="completed"):
    return {"pipeline_type": "zavod-reel", "stage": stage, "status": status, "artifacts": {}}


def test_stage_order_blocks_out_of_order_completion(tmp_path):
    # assets cannot complete before scene_plan/script/idea have completed — this is what closed
    # the assets-before-scene_plan bypass that left referential integrity nothing to check.
    with pytest.raises(CheckpointValidationError, match="Stage order"):
        _enforce_stage_order(_completed("assets"), tmp_path)


def test_stage_order_allows_in_order_completion(tmp_path):
    seed_prior_stages(tmp_path, "zavod-reel", "assets")
    _enforce_stage_order(_completed("assets"), tmp_path)  # all priors completed → ok


def test_stage_order_first_stage_needs_no_priors(tmp_path):
    _enforce_stage_order(_completed("idea"), tmp_path)  # first stage → nothing before it


def test_stage_order_only_gates_completed_status(tmp_path):
    _enforce_stage_order(_completed("assets", status="in_progress"), tmp_path)  # not a closure


# ── Phase A#7 round-4 (2026-07-06): ordering trusts no forged marker, gates pauses + resume ──
def test_stage_order_rejects_forged_bare_markers(tmp_path):
    # A hand-dropped {"status":"completed"} with no stage/pipeline_type must not satisfy ordering.
    for prior in ("idea", "script", "scene_plan", "assets", "edit"):
        (tmp_path / f"checkpoint_{prior}.json").write_text('{"status": "completed"}')
    with pytest.raises(CheckpointValidationError, match="Stage order"):
        _enforce_stage_order(_completed("compose"), tmp_path)


def test_stage_order_accepts_structural_markers(tmp_path):
    seed_prior_stages(tmp_path, "zavod-reel", "compose")  # carries stage + pipeline_type
    _enforce_stage_order(_completed("compose"), tmp_path)


def test_stage_order_gates_awaiting_human_pause(tmp_path):
    # A late-stage owner-pause cannot be created out of order (bogus resumable checkpoint).
    with pytest.raises(CheckpointValidationError, match="Stage order"):
        _enforce_stage_order(_completed("compose", status="awaiting_human"), tmp_path)


def test_resume_contracts_re_run_stage_order(tmp_path):
    from lib.checkpoint import _enforce_resume_contracts
    seed_prior_stages(tmp_path, "zavod-reel", "compose")
    (tmp_path / "checkpoint_scene_plan.json").unlink()  # a prior vanishes after the fact
    with pytest.raises(CheckpointValidationError, match="Stage order"):
        _enforce_resume_contracts(_completed("compose"), tmp_path)


# ── Phase B (2026-07-06 owner decision): manifest-driven checkpoint spine ──
# The spine hardcoded 9 stages, so character-animation's character_design/rig_plan could not
# be checkpoint-written (KeyError) and character_id had nothing to resolve against.
def test_spine_covers_manifest_declared_stages():
    from lib.checkpoint import CANONICAL_STAGE_ARTIFACTS, ALL_KNOWN_STAGES, _validate_artifacts_for_stage
    assert CANONICAL_STAGE_ARTIFACTS.get("character_design") == "character_design"
    assert CANONICAL_STAGE_ARTIFACTS.get("rig_plan") == "rig_plan"
    assert {"character_design", "rig_plan"} <= ALL_KNOWN_STAGES
    assert CANONICAL_STAGE_ARTIFACTS.get("assets") == "asset_manifest"  # core unchanged
    _validate_artifacts_for_stage("character_design", "in_progress", {})  # no KeyError


def _known_char_project(tmp_path, ids=("van", "hayk")):
    (tmp_path / "checkpoint_character_design.json").write_text(_json7.dumps(
        {"artifacts": {"character_design": {"characters": [{"id": i} for i in ids]}}}))
    return tmp_path


def _scene_plan_with_character(cid):
    return {"pipeline_type": "character-animation", "stage": "scene_plan",
            "artifacts": {"scene_plan": {"scenes": [
                {"id": "s1", "character_actions": [{"character_id": cid}]}]}}}


def test_scene_plan_ghost_character_id_is_blocked(tmp_path):
    pd = _known_char_project(tmp_path)
    with pytest.raises(CheckpointValidationError, match="character_id"):
        _enforce_referential_integrity(_scene_plan_with_character("GHOST"), pd)


def test_scene_plan_real_character_id_passes(tmp_path):
    pd = _known_char_project(tmp_path)
    _enforce_referential_integrity(_scene_plan_with_character("van"), pd)


def test_character_id_skipped_without_character_design(tmp_path):
    _enforce_referential_integrity(_scene_plan_with_character("GHOST"), tmp_path)  # no source → skip


# ── Round-4 #11.1: structural gates cover every manifest pipeline, not only zavod ──
def test_non_zavod_manifest_pipeline_gets_stage_ordering(tmp_path):
    # character-animation compose completed first (empty project) must block — it used to pass.
    with pytest.raises(CheckpointValidationError):
        _enforce_stage_order({"pipeline_type": "character-animation", "stage": "compose",
                              "status": "completed", "artifacts": {}}, tmp_path)


def test_non_zavod_manifest_pipeline_gets_existence_gate(tmp_path):
    # A phantom render must not close a character-animation compose even with priors seeded.
    from lib.checkpoint import _enforce_artifact_path_existence
    rr = {"version": "1.0", "outputs": [{"path": "missing.mp4", "format": "mp4",
                                          "resolution": "1080x1920", "duration_seconds": 5}]}
    cp = {"pipeline_type": "character-animation", "stage": "compose", "status": "completed",
          "artifacts": {"render_report": rr}}
    with pytest.raises(CheckpointValidationError, match="existence"):
        _enforce_artifact_path_existence(cp, tmp_path)


def test_unmanifested_pipeline_stays_ungated(tmp_path):
    # A pipeline with no manifest keeps the lenient behaviour — no false block.
    _enforce_stage_order({"pipeline_type": "some-custom-flow", "stage": "compose",
                          "status": "completed", "artifacts": {}}, tmp_path)


# ── Round-4 #6: character_id RI scoped by manifest, not file presence ──
def test_stale_character_design_does_not_block_zavod_scene_plan(tmp_path):
    # zavod-reel declares no character_design stage; a stale checkpoint_character_design.json
    # dropped into its project must not false-block an unrelated character_id-shaped field.
    _known_char_project(tmp_path)
    cp = {"pipeline_type": "zavod-reel", "stage": "scene_plan",
          "artifacts": {"scene_plan": {"scenes": [
              {"id": "s1", "character_actions": [{"character_id": "unrelated"}]}]}}}
    _enforce_referential_integrity(cp, tmp_path)  # must NOT raise


# ── Round-5 (2026-07-06): invalid-manifest fail-closed, all-produces, cache, orchestrator canon ──
def test_previously_invalid_manifests_resolve_real_first_stage():
    # documentary-montage / screen-demo were schema-invalid and silently fell back to the
    # generic 9-stage order (false-blocking their real first stage 'idea').
    assert get_pipeline_stages("documentary-montage")[0] == "idea"
    assert get_pipeline_stages("screen-demo")[0] == "idea"


def test_invalid_manifest_fails_closed_not_generic_fallback(monkeypatch):
    import lib.pipeline_loader as pl
    real = pl.load_pipeline
    monkeypatch.setattr(pl, "load_pipeline",
                        lambda pt, *a, **k: (_ for _ in ()).throw(ValueError("bad")) if pt == "documentary-montage" else real(pt, *a, **k))
    with pytest.raises(CheckpointValidationError, match="failed to load"):
        get_pipeline_stages("documentary-montage")


def test_sidecar_unschematized_produce_blocks_stage(monkeypatch):
    # produces:[script, unregistered_blob] must block — not only the canonical (first) produce.
    import lib.checkpoint as cp
    monkeypatch.setattr(cp, "_stage_declared_produces",
                        lambda pt, st: ["script", "unregistered_blob"] if st == "script" else [])
    with pytest.raises(CheckpointValidationError, match="no registered.*schema"):
        cp._validate_artifacts_for_stage("script", "completed",
                                         {"script": {"x": 1}, "unregistered_blob": {"evil": 1}}, "zavod-reel")


def test_ordering_rejects_schema_invalid_prior(tmp_path):
    # A prior that is not a schema-valid checkpoint (garbage artifacts) must not satisfy ordering.
    for prior in ("idea", "script", "scene_plan", "assets", "edit"):
        (tmp_path / f"checkpoint_{prior}.json").write_text(
            '{"pipeline_type":"zavod-reel","stage":"%s","status":"completed","artifacts":"garbage"}' % prior)
    with pytest.raises(CheckpointValidationError, match="Stage order"):
        _enforce_stage_order(_completed("compose"), tmp_path)


def test_reset_pipeline_caches_rebuilds_spine():
    from lib.checkpoint import reset_pipeline_caches, CANONICAL_STAGE_ARTIFACTS, ALL_KNOWN_STAGES
    reset_pipeline_caches()
    import lib.checkpoint as cp
    assert cp.CANONICAL_STAGE_ARTIFACTS.get("character_design") == "character_design"
    assert cp.ALL_KNOWN_STAGES == frozenset(cp.CANONICAL_STAGE_ARTIFACTS)


def test_orchestrator_canonicalizes_raw_pipeline_type(tmp_path):
    from lib.orchestrator import run_state
    st = run_state(tmp_path, "p", "  Character-Animation  ")
    assert st["next_stage"] == "research"  # real ca first stage, not the generic fallback


def test_stage_with_unschematized_canonical_artifact_fails_closed(monkeypatch):
    # #3 round-4: a manifest could register a stage whose canonical artifact has no schema;
    # the validation loop skips unknown names, so the payload would ride through unvalidated.
    import lib.checkpoint as cp
    monkeypatch.setitem(cp.CANONICAL_STAGE_ARTIFACTS, "evil_stage", "unregistered_blob")
    with pytest.raises(CheckpointValidationError, match="no registered.*schema"):
        cp._validate_artifacts_for_stage("evil_stage", "completed", {"unregistered_blob": {"x": 1}})


def test_edit_metadata_asset_id_is_not_a_reference(tmp_path):
    # 2026-07-06 dry re-probe regression: an asset_id under free-form metadata is a label
    # (e.g. an analytics tag), NOT a manifest reference — it must not be resolved/blocked.
    pd = _project_with_assets(tmp_path)
    cp = {"pipeline_type": "zavod-reel", "stage": "edit", "artifacts": {"edit_decisions": {
        "overlays": [{"asset_id": "a1"}], "metadata": {"asset_id": "analytics-label"}}}}
    _enforce_referential_integrity(cp, pd)  # must NOT raise on the metadata label

    # …but a real overlay reference to a ghost is still blocked.
    bad = {"pipeline_type": "zavod-reel", "stage": "edit", "artifacts": {"edit_decisions": {
        "overlays": [{"asset_id": "GHOST"}], "metadata": {"asset_id": "x"}}}}
    with pytest.raises(CheckpointValidationError, match="Referential integrity"):
        _enforce_referential_integrity(bad, pd)


def test_strict_resume_re_runs_referential_integrity(tmp_path):
    # 2026-07-06 dry re-probe: RI was write-time only, so a valid asset checkpoint hand-edited
    # on disk to a GHOST scene_id passed strict resume. resume contracts now re-run RI.
    from lib.checkpoint import _enforce_resume_contracts
    (tmp_path / "checkpoint_scene_plan.json").write_text(_json7.dumps(
        {"artifacts": {"scene_plan": {"scenes": [{"id": "s1"}]}}}))
    cp = {"pipeline_type": "zavod-reel", "stage": "assets", "status": "in_progress",
          "artifacts": {"asset_manifest": {"assets": [
              {"id": "a1", "type": "video", "path": "x.mp4", "source_tool": "t", "scene_id": "GHOST"}]}}}
    with pytest.raises(CheckpointValidationError, match="Referential integrity"):
        _enforce_resume_contracts(cp, tmp_path)
    cp["artifacts"]["asset_manifest"]["assets"][0]["scene_id"] = "s1"
    _enforce_resume_contracts(cp, tmp_path)  # valid reference resumes cleanly


# ── Phase 3c (2026-07-05 council #8): glyph gate sweeps every text surface ──
# The seam only glyph-checked scene_plan text_policy.text and the script strings, so an
# invisible/zero-width char hiding in metadata.caption, an asset field, or any other artifact
# surface slipped through. The seam now sweeps every string leaf of every artifact.
_ZWSP = "​"


def test_glyph_caught_in_render_report_caption():
    # metadata.caption is NOT a stage-specific glyph field — it was previously unchecked.
    rr = {"version": "1.0",
          "outputs": [{"path": "o.mp4", "format": "mp4", "resolution": "1080x1920", "duration_seconds": 5}],
          "continuity_reports": [], "metadata": {"caption": f"Ձմ{_ZWSP}եռ"}}
    cp = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "completed",
          "artifacts": {"render_report": rr}}
    with pytest.raises(CheckpointValidationError, match="glyph"):
        _enforce_zavod_gates(cp)


def test_glyph_caught_in_asset_manifest_surface():
    cp = {"pipeline_type": "zavod-reel", "stage": "assets", "status": "completed",
          "artifacts": {"asset_manifest": {"assets": [
              {"id": "a1", "type": "video", "path": "o.mp4", "source_tool": "x",
               "scene_id": "s1", "caption": f"Վան{_ZWSP}ը"}]}}}
    with pytest.raises(CheckpointValidationError, match="glyph"):
        _enforce_zavod_gates(cp)


def test_glyph_sweep_allows_clean_multilingual_caption():
    rr = {"version": "1.0",
          "outputs": [{"path": "o.mp4", "format": "mp4", "resolution": "1080x1920", "duration_seconds": 5}],
          "continuity_reports": [{"clip": "o.mp4", "anchors": [
              {"name": "h", "kind": "object", "persists": True},
              {"name": "subject identity", "kind": "identity", "persists": True}]}],
          "metadata": {"caption": "Ձմեռային արձակուրդ 🏔️ weekend"}}
    cp = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "completed",
          "artifacts": {"bench_report": _good("compose"), "render_report": rr}}
    _enforce_zavod_gates(cp)  # clean text on any surface must still pass


# ── Angle 3: existence gate content-awareness ──────────────────────────────
def _assets_cp(path_or_none, atype="video"):
    assets = [] if path_or_none is None else [
        {"id": "a", "type": atype, "path": path_or_none, "source_tool": "x", "scene_id": "s"}]
    return {"pipeline_type": "zavod-reel", "stage": "assets", "status": "completed",
            "artifacts": {"asset_manifest": {"assets": assets}}}

def _run_existence(cp, make):
    with tempfile.TemporaryDirectory() as td:
        pdir = Path(td) / "p1"; pdir.mkdir(parents=True)
        make(pdir)
        _enforce_artifact_path_existence(cp, pdir)

def test_existence_blocks_zero_byte_file():
    with pytest.raises(CheckpointValidationError):
        _run_existence(_assets_cp("e.mp4"), lambda d: (d / "e.mp4").write_bytes(b""))

def test_existence_blocks_symlink_to_devnull():
    with pytest.raises(CheckpointValidationError):
        _run_existence(_assets_cp("n.mp4"), lambda d: (d / "n.mp4").symlink_to("/dev/null"))

def test_existence_blocks_directory_path():
    with pytest.raises(CheckpointValidationError):
        _run_existence(_assets_cp("d.mp4"), lambda d: (d / "d.mp4").mkdir())

def test_existence_blocks_empty_asset_list():
    with pytest.raises(CheckpointValidationError):
        _run_existence(_assets_cp(None), lambda d: None)

def test_existence_allows_real_video():
    _run_existence(_assets_cp("r.mp4"), lambda d: tiny_mp4(d / "r.mp4"))


# ── Angle 3b: #5 content validation — a non-empty file must BE valid media of its type ──
def test_content_gate_blocks_fake_video_bytes():
    # A non-empty .mp4 full of garbage bytes passed the old exists()+size check.
    with pytest.raises(CheckpointValidationError, match="not valid content"):
        _run_existence(_assets_cp("fake.mp4"), lambda d: (d / "fake.mp4").write_bytes(b"12345"))

def test_content_gate_blocks_text_renamed_mp4():
    with pytest.raises(CheckpointValidationError, match="not valid content"):
        _run_existence(_assets_cp("note.mp4"),
                       lambda d: (d / "note.mp4").write_text("this is not a video"))

def test_content_gate_allows_real_audio():
    _run_existence(_assets_cp("a.wav", atype="audio"), lambda d: tiny_wav(d / "a.wav"))

def test_content_gate_blocks_fake_audio_bytes():
    with pytest.raises(CheckpointValidationError, match="not valid content"):
        _run_existence(_assets_cp("a.wav", atype="audio"),
                       lambda d: (d / "a.wav").write_bytes(b"nonsense"))

def test_content_gate_allows_real_image():
    _run_existence(_assets_cp("i.png", atype="image"), lambda d: tiny_png(d / "i.png"))

def test_content_gate_allows_data_type_without_probe():
    # subtitle/font/lut/code carry no A/V stream — a non-empty file is the right bar.
    _run_existence(_assets_cp("s.srt", atype="subtitle"),
                   lambda d: (d / "s.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n"))

def test_content_gate_blocks_fake_compose_render():
    cp = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "completed",
          "artifacts": {"render_report": {"outputs": [
              {"path": "o.mp4", "format": "mp4", "resolution": "64x64", "duration_seconds": 1}]}}}
    with pytest.raises(CheckpointValidationError, match="not valid content"):
        _run_existence(cp, lambda d: (d / "o.mp4").write_bytes(b"12345"))

def test_content_gate_allows_real_compose_render():
    cp = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "completed",
          "artifacts": {"render_report": {"outputs": [
              {"path": "o.mp4", "format": "mp4", "resolution": "64x64", "duration_seconds": 1}]}}}
    _run_existence(cp, lambda d: tiny_mp4(d / "o.mp4"))


# ── Angle 5: glyph gate invisible characters ───────────────────────────────
def test_glyph_blocks_zero_width_joiner_in_armenian():
    assert not run_script_gates("Բա‍րև ձեզ ընկերներ")["ok"]

def test_glyph_blocks_zero_width_space():
    assert not run_script_gates("Բարև​ ձեզ")["ok"]

def test_glyph_allows_clean_armenian():
    assert run_script_gates("Բարև ձեզ սիրելի ընկերներ")["ok"]

def test_glyph_allows_zwj_emoji_sequences_in_captions():
    # 2026-07-04 probe: ZWJ-joined emoji (family, rainbow flag) are legit caption content;
    # only zero-width chars spliced next to LETTERS are the attack.
    assert run_script_gates("Մեր ընտանիքը 👨‍👩‍👧 այս ամառ")["ok"]
    assert run_script_gates("Հպարտություն 🏳️‍🌈 բոլորին")["ok"]


def test_glyph_allows_persian_arabic_zwnj():
    # 2026-07-06 dry re-probe: the #8 sweep false-rejected legit Persian ZWNJ (U+200C), which
    # is a linguistically-required joiner in Arabic-script text — not an exploit. The invisible-
    # char check is scoped to Armenian/Latin/Cyrillic neighbours, where zero-width is never
    # needed; Arabic/Indic joiners are left alone.
    assert run_script_gates("می‌روم")["ok"]        # Persian "I go" with ZWNJ
    assert run_script_gates("نمی‌خواهم")["ok"]     # Persian "I don't want" with ZWNJ


def test_glyph_still_blocks_zwnj_spliced_into_armenian():
    # …but the SAME character spliced next to Armenian letters is still the attack.
    assert not run_script_gates("Հա‌յ")["ok"]


def test_glyph_gate_walks_dict_keys():
    # 2026-07-06 dry re-probe: the sweep walked only dict values, so an invisible char hidden
    # in a KEY slipped through. The gate now checks keys too.
    from lib.armenian_glyph_gate import gate as _g
    assert not _g({"cap​tion": "clean value"})["ok"]   # U+200B in the key
    assert _g({"version": "1.0", "title": "Ձմեռ"})["ok"]  # clean keys still pass


def test_glyph_seam_blocks_zero_width_in_artifact_key():
    from lib.checkpoint import _enforce_zavod_gates as _gz
    rr = {**_RR_BASE, "continuity_reports": [], "metadata": {"cap​tion": "clean"}}  # U+200B in key
    cp = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "completed",
          "artifacts": {"render_report": rr}}
    with pytest.raises(CheckpointValidationError, match="glyph"):
        _gz(cp)


def test_glyph_seam_blocks_poisoned_top_level_artifact_name():
    # 2026-07-06 dry re-probe: a zero-width in the top-level artifact NAME (the key in the
    # artifacts dict) rode along unchecked because only artifact contents were swept.
    from lib.checkpoint import _enforce_zavod_gates as _gz
    cp = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "completed",
          "artifacts": {"render_report": {**_RR_BASE, "continuity_reports": []},
                        "Հայ​երեն": {"x": "y"}}}  # U+200B in the artifact name
    with pytest.raises(CheckpointValidationError, match="glyph"):
        _gz(cp)


# ── Angle 3 (cont.): symlink provenance ────────────────────────────────────
def test_existence_blocks_symlink_escaping_project():
    def make(d):
        (d / "link.mp4").symlink_to("/etc/hosts")
    with pytest.raises(CheckpointValidationError):
        _run_existence(_assets_cp("link.mp4"), make)

def test_existence_allows_internal_symlink():
    def make(d):
        tiny_mp4(d / "real.mp4")
        (d / "link.mp4").symlink_to(d / "real.mp4")
    _run_existence(_assets_cp("link.mp4"), make)


# ── Phase 1 (2026-07-05 council #9): atomic, crash-safe checkpoint persistence ──
# Before this fix write_checkpoint used open(path, "w") (truncates in place) and merged
# the decision log BEFORE writing the checkpoint. A crash mid-write destroyed the prior
# valid checkpoint; a crash between the two writes left a decision with no carrying
# checkpoint (split-brain). The exact class of failure — API error mid-write — is what
# forced the 2026-07-05 recovery session.
import json as _json
import lib.checkpoint as _cp
from lib.checkpoint import (
    _atomic_write_json, write_checkpoint, _checkpoint_path,
)


def _valid_decision_log(pid="projX"):
    return {"version": "1.0", "project_id": pid, "decisions": []}


def test_atomic_write_preserves_prior_file_on_replace_crash(tmp_path, monkeypatch):
    target = tmp_path / "checkpoint_idea.json"
    _atomic_write_json(target, {"state": "valid-v1"})

    def boom(*a, **k):
        raise OSError("simulated crash during atomic rename")
    monkeypatch.setattr(_cp.os, "replace", boom)

    with pytest.raises(OSError):
        _atomic_write_json(target, {"state": "would-be-v2"})
    # prior valid file survives fully intact — never truncated to empty/corrupt
    assert _json.loads(target.read_text()) == {"state": "valid-v1"}
    # and no orphan temp file is left behind
    assert list(tmp_path.glob(".*tmp*")) == []


def test_atomic_write_concurrent_writers_do_not_collide(tmp_path):
    # 2026-07-06 dry re-probe: a pid-only temp name collided when multiple threads of the
    # same process wrote the same path — most writes died with FileNotFoundError. A unique
    # temp name (pid + uuid) lets every writer complete; the final file is a valid checkpoint.
    import threading
    target = tmp_path / "checkpoint_research.json"
    errors = []

    def w(i):
        try:
            _atomic_write_json(target, {"writer": i})
        except Exception as e:  # noqa: BLE001
            errors.append((i, repr(e)))

    threads = [threading.Thread(target=w, args=(i,)) for i in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert isinstance(_json.loads(target.read_text())["writer"], int)  # valid, one winner
    assert list(tmp_path.glob(".*tmp*")) == []


def test_atomic_write_never_truncates_on_serialize_crash(tmp_path, monkeypatch):
    target = tmp_path / "checkpoint_idea.json"
    _atomic_write_json(target, {"state": "valid-v1"})

    def boom(*a, **k):
        raise ValueError("simulated crash mid-serialization")
    monkeypatch.setattr(_cp.json, "dump", boom)

    with pytest.raises(ValueError):
        _atomic_write_json(target, {"state": "would-be-v2"})
    assert _json.loads(target.read_text()) == {"state": "valid-v1"}
    assert list(tmp_path.glob(".*tmp*")) == []


def test_checkpoint_persisted_before_decision_log_merge(tmp_path, monkeypatch):
    # Split-brain guard: the carrying checkpoint must reach disk BEFORE the derived
    # decision-log projection, so a crash during the merge can never leave a decision
    # recorded with no checkpoint behind it.
    seen = {}

    def spy(pipeline_dir, project_id, new_log):
        seen["cp_on_disk"] = _checkpoint_path(pipeline_dir, project_id, "idea").exists()
        raise RuntimeError("simulated crash during decision-log merge")
    monkeypatch.setattr(_cp, "_merge_decision_log", spy)

    with pytest.raises(RuntimeError):
        write_checkpoint(
            tmp_path, "projX", "idea", "in_progress",
            {"decision_log": _valid_decision_log()}, pipeline_type=None,
        )
    assert seen["cp_on_disk"] is True
    assert _checkpoint_path(tmp_path, "projX", "idea").exists()


# ── Phase 4a (2026-07-05 dry re-probe #11): canonical pipeline identity ──
# ' zavod-reel ' was recognized as a valid zavod pipeline by the gate but STORED raw, so the
# ladder resolver (load_pipeline(raw) -> except -> []) yielded no required rungs and a stage
# could close without its specialist ladder — the whole production-ladder governance bypassed.
from lib.checkpoint import _canonical_pipeline_type, _required_ladder_sub_stages  # noqa: E402


def test_pipeline_type_canonicalized_on_write(tmp_path):
    p = write_checkpoint(tmp_path, "p", "idea", "in_progress", {}, pipeline_type="  Zavod-Reel  ")
    assert _json.loads(p.read_text())["pipeline_type"] == "zavod-reel"


def test_canonical_pipeline_type_helper():
    assert _canonical_pipeline_type(" zavod-reel ") == "zavod-reel"
    assert _canonical_pipeline_type("animation") == "animation"  # non-zavod unchanged


@pytest.mark.parametrize("raw", [" zavod-reel ", "zavod-reel​"])
def test_ladder_resolver_fails_closed_on_unresolvable_zavod(raw):
    # A zavod pipeline whose manifest cannot be resolved by the given (raw) value — the
    # whitespace/zero-width variants load_pipeline rejects — must not yield an empty ladder
    # requirement. That empty result was the ladder bypass; write-time canonicalization
    # prevents the raw value from ever persisting, and this keeps the resolver itself honest.
    with pytest.raises(CheckpointValidationError):
        _required_ladder_sub_stages(raw, "scene_plan")


def test_ladder_resolver_stays_lenient_for_non_zavod():
    assert _required_ladder_sub_stages("some-unknown-nonzavod", "scene_plan") == []


# ── Round 5 (2026-07-06 #2): broken manifest fails closed, not silent fallback ──
# get_pipeline_stages() swallowed EVERY load failure into the generic STAGES fallback.
# For a pipeline whose manifest exists but is schema-invalid (documentary-montage's
# 'documentary' category, screen-demo's top-level production_modes) that silently
# mis-sequenced the run: both start at 'idea', but the fallback demanded research/proposal
# first — false-blocking the pipeline's true first stage while looking like governance.
import lib.pipeline_loader as _pl  # noqa: E402
from lib.pipeline_loader import load_pipeline, get_stage_order  # noqa: E402

_ALL_MANIFESTS = sorted(p.stem for p in (ROOT / "pipeline_defs").glob("*.yaml"))


@pytest.mark.parametrize("name", _ALL_MANIFESTS)
def test_every_pipeline_manifest_loads_and_orders(name):
    # Every manifest that exists must load against the schema and yield a stage order —
    # otherwise the fail-closed rule below turns it into a hard block, by design.
    order = get_stage_order(load_pipeline(name))
    assert order, f"{name} produced an empty stage order"


@pytest.mark.parametrize("name", ["screen-demo", "documentary-montage"])
def test_manifest_pipelines_resolve_real_order_not_generic_fallback(name):
    order = get_pipeline_stages(name)
    assert order[0] == "idea"          # their true first stage
    assert order != list(STAGES)       # never the generic fallback that false-blocked it


def test_broken_manifest_of_manifest_pipeline_fails_closed(monkeypatch):
    # A manifest that EXISTS but fails to load is a configuration error — block loudly,
    # never substitute the generic stage order.
    def _boom(name, defs_dir=None):
        raise ValueError("schema-invalid manifest")
    monkeypatch.setattr(_pl, "load_pipeline", _boom)
    with pytest.raises(CheckpointValidationError, match="failed to load"):
        get_pipeline_stages("screen-demo")


def test_pipeline_without_any_manifest_keeps_lenient_fallback(monkeypatch):
    # Scope check: even with the loader broken, a pipeline that has NO manifest at all
    # still gets the graceful generic fallback — the fail-closed rule is manifest-scoped.
    def _boom(name, defs_dir=None):
        raise FileNotFoundError("no manifest")
    monkeypatch.setattr(_pl, "load_pipeline", _boom)
    assert get_pipeline_stages("totally-unknown-pipeline") == list(STAGES)


# ── Round 6 #1 (2026-07-06 external audit №2): manifest deletion is a downgrade path ──
# _is_manifest_pipeline() is a live filesystem glob, so deleting/renaming a manifest between
# runs reclassified the pipeline as generic in a FRESH process: zavod-* included, its stage
# order silently downgraded to the generic fallback. Two closures: (a) zavod pipelines never
# fall back regardless of manifest presence; (b) every checkpoint written under a manifest
# pins its hash + stage order, and navigation/resume refuse a vanished or re-sequenced pin.
import lib.checkpoint as _cpm  # noqa: E402
from lib.checkpoint import get_latest_checkpoint  # noqa: E402


def _simulate_deleted_manifest(monkeypatch, gone: str):
    """A fresh process after `pipeline_defs/<gone>.yaml` was deleted: the glob-backed set
    no longer contains it and loading it fails."""
    remaining = frozenset(s for s in _cpm._manifest_pipeline_types() if s != gone)
    monkeypatch.setattr(_cpm, "_manifest_pipeline_types", lambda: remaining)
    def _missing(name, defs_dir=None):
        raise FileNotFoundError(f"pipeline_defs/{name}.yaml")
    monkeypatch.setattr(_pl, "load_pipeline", _missing)


def test_zavod_manifest_deletion_never_falls_back(monkeypatch):
    _simulate_deleted_manifest(monkeypatch, "zavod-reel")
    with pytest.raises(CheckpointValidationError, match="will not be substituted"):
        get_pipeline_stages("zavod-reel")


def test_checkpoint_pins_manifest_on_write(tmp_path):
    p = write_checkpoint(tmp_path, "p", "idea", "in_progress", {}, pipeline_type="screen-demo")
    pin = _json.loads(p.read_text())["manifest_pin"]
    assert pin["stage_order"][0] == "idea"
    assert len(pin["manifest_sha256"]) == 64


def test_non_manifest_pipeline_writes_no_pin(tmp_path):
    p = write_checkpoint(tmp_path, "p", "idea", "in_progress", {}, pipeline_type=None)
    assert "manifest_pin" not in _json.loads(p.read_text())


def test_navigation_blocks_when_pinned_manifest_vanishes(tmp_path, monkeypatch):
    write_checkpoint(tmp_path, "p", "idea", "in_progress", {}, pipeline_type="screen-demo")
    _simulate_deleted_manifest(monkeypatch, "screen-demo")
    with pytest.raises(CheckpointValidationError, match="no longer exists"):
        get_completed_stages(tmp_path, "p", None)


def test_resume_blocks_when_pinned_manifest_vanishes(tmp_path, monkeypatch):
    write_checkpoint(tmp_path, "p", "idea", "in_progress", {}, pipeline_type="screen-demo")
    _simulate_deleted_manifest(monkeypatch, "screen-demo")
    with pytest.raises(CheckpointValidationError, match="no longer exists"):
        get_latest_checkpoint(tmp_path, "p", strict_resume=True)


def test_navigation_blocks_on_pinned_stage_order_drift(tmp_path):
    p = write_checkpoint(tmp_path, "p", "idea", "in_progress", {}, pipeline_type="screen-demo")
    cp = _json.loads(p.read_text())
    cp["manifest_pin"]["stage_order"] = ["research", "idea"]  # what an older manifest pinned
    p.write_text(_json.dumps(cp))
    with pytest.raises(CheckpointValidationError, match="stage order changed"):
        get_completed_stages(tmp_path, "p", "screen-demo")


def test_legacy_checkpoint_without_pin_still_navigates(tmp_path):
    p = write_checkpoint(tmp_path, "p", "idea", "in_progress", {}, pipeline_type="screen-demo")
    cp = _json.loads(p.read_text())
    del cp["manifest_pin"]  # checkpoint written before pinning existed
    p.write_text(_json.dumps(cp))
    assert get_completed_stages(tmp_path, "p", "screen-demo") == []


def test_intact_pin_navigates_normally(tmp_path):
    write_checkpoint(tmp_path, "p", "idea", "in_progress", {}, pipeline_type="screen-demo")
    assert get_completed_stages(tmp_path, "p", "screen-demo") == []  # in_progress ≠ completed
    assert get_next_stage(tmp_path, "p", "screen-demo") == "idea"


# ── Round 6 #2 (2026-07-06 external audit №7): continuity is content, not presence ──
# The compose gate checked that continuity_reports EXISTS and is non-empty, but not that it
# proves anything: a report with zero anchors "passed" trivially, a report missing the
# identity anchor never judged the one dimension every clip has, and N outputs with one
# report closed with N-1 clips never checked.
_IDENTITY_OK = {"name": "subject identity", "kind": "identity", "persists": True}


def test_zero_anchor_continuity_report_blocks_completed_and_awaiting():
    rr = {**_RR_BASE, "continuity_reports": [{"clip": "o.mp4", "anchors": []}]}
    for status in ("completed", "awaiting_human"):
        with pytest.raises(CheckpointValidationError, match="no anchors"):
            _enforce_zavod_gates(_compose_cp(status, dict(rr)))


def test_continuity_report_without_identity_anchor_blocks():
    rr = {**_RR_BASE, "continuity_reports": [
        {"clip": "o.mp4", "anchors": [{"name": "glass", "kind": "object", "persists": True}]}]}
    with pytest.raises(CheckpointValidationError, match="identity anchor"):
        _enforce_zavod_gates(_compose_cp("completed", rr))


def test_uncovered_output_blocks_completed_compose():
    # 2 rendered outputs, 1 continuity report → the unchecked clip blocks closure.
    rr = {"version": "1.0",
          "outputs": [
              {"path": "a.mp4", "format": "mp4", "resolution": "1080x1920", "duration_seconds": 5},
              {"path": "renders/b.mp4", "format": "mp4", "resolution": "1080x1920", "duration_seconds": 5}],
          "continuity_reports": [{"clip": "a.mp4", "anchors": [dict(_IDENTITY_OK)]}]}
    with pytest.raises(CheckpointValidationError, match="b.mp4"):
        _enforce_zavod_gates(_compose_cp("completed", rr))


def test_fully_covered_judged_reports_still_close():
    # Control: one judged report per output (matched by clip basename) closes normally.
    rr = {"version": "1.0",
          "outputs": [
              {"path": "a.mp4", "format": "mp4", "resolution": "1080x1920", "duration_seconds": 5},
              {"path": "renders/b.mp4", "format": "mp4", "resolution": "1080x1920", "duration_seconds": 5}],
          "continuity_reports": [
              {"clip": "a.mp4", "anchors": [dict(_IDENTITY_OK)]},
              {"clip": "b.mp4", "anchors": [dict(_IDENTITY_OK)]}]}
    _enforce_zavod_gates(_compose_cp("completed", rr))  # must not raise


def test_zero_anchor_report_fails_render_report_schema():
    # Belt and suspenders: the artifact schema itself now rejects an anchor-less report.
    from schemas.artifacts import validate_artifact
    rr = {**_RR_BASE, "continuity_reports": [{"clip": "o.mp4", "anchors": []}]}
    with pytest.raises(Exception):
        validate_artifact("render_report", rr)


# ── Round 6 #3 (2026-07-06 external audit №11): decision lifecycle + conflict blocking ──
# The decision log was append-only by id, but: a re-submitted id with DIFFERENT content was
# silently dropped (a history-rewrite attempt vanished untraced), and two active decisions
# on the same (category, subject) could contradict — "the current decision" was whichever
# entry a consumer happened to read (day-4 Remotion vs day-18 FFmpeg, resume picks wrong).
from lib.checkpoint import active_decisions, _validate_decision_log_merge  # noqa: E402


def _decision(did, selected, *, category="render_runtime_selection",
              subject="compose runtime", supersedes=None):
    d = {"decision_id": did, "stage": "proposal", "category": category, "subject": subject,
         "options_considered": [{"option_id": selected, "label": selected, "score": 1.0,
                                 "reason": "fits the brief"}],
         "selected": selected, "reason": "best fit"}
    if supersedes:
        d["supersedes"] = supersedes
    return d


def _log(*decisions, pid="p"):
    return {"version": "1.0", "project_id": pid, "decisions": list(decisions)}


def test_decision_id_resubmission_with_different_content_blocks(tmp_path):
    write_checkpoint(tmp_path, "p", "idea", "in_progress",
                     {"decision_log": _log(_decision("d-001", "remotion"))}, pipeline_type=None)
    with pytest.raises(CheckpointValidationError, match="append-only"):
        write_checkpoint(tmp_path, "p", "script", "in_progress",
                         {"decision_log": _log(_decision("d-001", "ffmpeg"))}, pipeline_type=None)


def test_identical_resubmission_is_idempotent(tmp_path):
    for stage in ("idea", "script"):
        write_checkpoint(tmp_path, "p", stage, "in_progress",
                         {"decision_log": _log(_decision("d-001", "remotion"))}, pipeline_type=None)
    log = _json.loads((tmp_path / "p" / "decision_log.json").read_text())
    assert [d["decision_id"] for d in log["decisions"]] == ["d-001"]


def test_contradicting_active_decision_blocks_without_supersedes(tmp_path):
    write_checkpoint(tmp_path, "p", "idea", "in_progress",
                     {"decision_log": _log(_decision("d-001", "remotion"))}, pipeline_type=None)
    with pytest.raises(CheckpointValidationError, match="contradict"):
        write_checkpoint(tmp_path, "p", "script", "in_progress",
                         {"decision_log": _log(_decision("d-002", "ffmpeg"))}, pipeline_type=None)


def test_supersedes_resolves_the_contradiction_and_history_survives(tmp_path):
    write_checkpoint(tmp_path, "p", "idea", "in_progress",
                     {"decision_log": _log(_decision("d-001", "remotion"))}, pipeline_type=None)
    write_checkpoint(tmp_path, "p", "script", "in_progress",
                     {"decision_log": _log(_decision("d-002", "ffmpeg", supersedes="d-001"))},
                     pipeline_type=None)
    log = _json.loads((tmp_path / "p" / "decision_log.json").read_text())
    assert [d["decision_id"] for d in log["decisions"]] == ["d-001", "d-002"]  # append-only
    act = active_decisions(log)
    assert [d["decision_id"] for d in act] == ["d-002"]  # the answer is unambiguous
    assert act[0]["selected"] == "ffmpeg"


def test_supersedes_unknown_target_blocks(tmp_path):
    with pytest.raises(CheckpointValidationError, match="unknown"):
        write_checkpoint(tmp_path, "p", "idea", "in_progress",
                         {"decision_log": _log(_decision("d-002", "ffmpeg", supersedes="d-404"))},
                         pipeline_type=None)


def test_double_supersede_is_forked_history_and_blocks():
    existing = _log(_decision("d-001", "remotion"),
                    _decision("d-002", "ffmpeg", supersedes="d-001"))
    with pytest.raises(CheckpointValidationError, match="forked"):
        _validate_decision_log_merge(
            existing, _log(_decision("d-003", "hyperframes", supersedes="d-001")))


def test_same_subject_same_selection_may_coexist():
    # Re-affirming the same answer is not a conflict — only a DIFFERENT answer is.
    _validate_decision_log_merge(
        _log(_decision("d-001", "remotion")), _log(_decision("d-002", "remotion")))


def test_blocked_decision_conflict_leaves_no_checkpoint(tmp_path):
    # The lifecycle check fires pre-persist: a contradicting write must not leave the
    # carrying checkpoint on disk (unlike a post-persist merge crash).
    write_checkpoint(tmp_path, "p", "idea", "in_progress",
                     {"decision_log": _log(_decision("d-001", "remotion"))}, pipeline_type=None)
    with pytest.raises(CheckpointValidationError):
        write_checkpoint(tmp_path, "p", "script", "in_progress",
                         {"decision_log": _log(_decision("d-002", "ffmpeg"))}, pipeline_type=None)
    assert not _checkpoint_path(tmp_path, "p", "script").exists()


# ── Round 6 #4 (2026-07-06 external audit №12): concept contract + forbidden directions ──
# Nothing guaranteed that proposal directions were genuinely different, that the choice
# rationale survived, or that a rejected direction could not silently return later. Now:
# concept_selection decisions must offer ≥3 mechanism-different options with recorded
# rejections; a zavod idea stage cannot close without one; and a direction an active
# decision rejected cannot be re-selected in that category without superseding it.
from tests.zavod.test_gates import (  # noqa: E402
    _with_bench as _gb_bench, _brief as _gb_brief, _ladder as _gb_ladder,
    _concept_log as _gb_concept, _IDEA_SUBS as _GB_IDEA_SUBS,
)


def _concept(did="d-c", options=None, selected="c1", subject="reel concept direction",
             supersedes=None):
    opts = options if options is not None else [
        {"option_id": "c1", "label": "desert dawn confession", "score": 0.9,
         "reason": "single intimate voice carries the arc"},
        {"option_id": "c2", "label": "pool-party cold open", "score": 0.6,
         "reason": "ensemble energy hook on the beat",
         "rejected_because": "tone clashes with brand restraint"},
        {"option_id": "c3", "label": "static architecture study", "score": 0.4,
         "reason": "slow wordless visual meditation",
         "rejected_because": "no narrative pull in 30s"}]
    d = {"decision_id": did, "stage": "idea", "category": "concept_selection",
         "subject": subject, "options_considered": opts, "selected": selected,
         "reason": "strongest mechanism"}
    if supersedes:
        d["supersedes"] = supersedes
    return d


def test_concept_selection_with_two_options_blocks(tmp_path):
    c = _concept()
    c["options_considered"] = c["options_considered"][:2]
    with pytest.raises(CheckpointValidationError, match="three"):
        write_checkpoint(tmp_path, "p", "idea", "in_progress",
                         {"decision_log": _log(c)}, pipeline_type=None)


def test_concept_rejection_without_rationale_blocks(tmp_path):
    c = _concept()
    del c["options_considered"][1]["rejected_because"]
    with pytest.raises(CheckpointValidationError, match="rejected_because"):
        write_checkpoint(tmp_path, "p", "idea", "in_progress",
                         {"decision_log": _log(c)}, pipeline_type=None)


def test_concept_same_direction_reworded_blocks(tmp_path):
    c = _concept()
    # c3 becomes a paraphrase of c1 — same mechanism, different words.
    c["options_considered"][2] = {
        "option_id": "c3", "label": "desert dawn confession, retold", "score": 0.5,
        "reason": "single intimate voice carries the arc",
        "rejected_because": "weaker variant"}
    with pytest.raises(CheckpointValidationError, match="same direction"):
        write_checkpoint(tmp_path, "p", "idea", "in_progress",
                         {"decision_log": _log(c)}, pipeline_type=None)


def test_concept_selected_outside_options_blocks(tmp_path):
    with pytest.raises(CheckpointValidationError, match="not among"):
        write_checkpoint(tmp_path, "p", "idea", "in_progress",
                         {"decision_log": _log(_concept(selected="c9"))}, pipeline_type=None)


def test_zavod_idea_cannot_close_without_concept_decision(tmp_path):
    with pytest.raises(CheckpointValidationError, match="concept_selection"):
        write_checkpoint(
            tmp_path, "p", "idea", "completed",
            _gb_bench("idea", {"brief": _gb_brief(), "production_ladder": _gb_ladder(_GB_IDEA_SUBS),
                               "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
                               "run_mode": "automatic"}),
            pipeline_type="zavod-reel",
        )


def test_zavod_idea_with_concept_decision_closes(tmp_path):
    p = write_checkpoint(
        tmp_path, "p", "idea", "completed",
        _gb_bench("idea", {"brief": _gb_brief(), "production_ladder": _gb_ladder(_GB_IDEA_SUBS),
                           "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
                           "run_mode": "automatic", "decision_log": _gb_concept("p")}),
        pipeline_type="zavod-reel",
    )
    assert p.exists()


def test_rejected_direction_cannot_return_without_supersede(tmp_path):
    write_checkpoint(tmp_path, "p", "idea", "in_progress",
                     {"decision_log": _log(_concept("d-c1"))}, pipeline_type=None)
    # New decision in the SAME category but a different subject re-selects the direction
    # d-c1 explicitly rejected ('pool-party cold open').
    comeback = _concept("d-c2", subject="teaser concept direction", selected="c2")
    comeback["options_considered"][1] = dict(comeback["options_considered"][1])
    del comeback["options_considered"][1]["rejected_because"]
    comeback["options_considered"][0]["rejected_because"] = "already used for the reel"
    with pytest.raises(CheckpointValidationError, match="explicitly rejected"):
        write_checkpoint(tmp_path, "p", "script", "in_progress",
                         {"decision_log": _log(comeback)}, pipeline_type=None)


def test_rejected_direction_returns_only_by_superseding(tmp_path):
    write_checkpoint(tmp_path, "p", "idea", "in_progress",
                     {"decision_log": _log(_concept("d-c1"))}, pipeline_type=None)
    comeback = _concept("d-c2", subject="teaser concept direction", selected="c2",
                        supersedes="d-c1")
    comeback["options_considered"][1] = dict(comeback["options_considered"][1])
    del comeback["options_considered"][1]["rejected_because"]
    comeback["options_considered"][0]["rejected_because"] = "already used for the reel"
    write_checkpoint(tmp_path, "p", "script", "in_progress",
                     {"decision_log": _log(comeback)}, pipeline_type=None)  # must not raise


# ── Round 6 #5 (2026-07-06 external audit №15): Scout adoption pre/post control ──
# The memo/decision loop keeps the Scout DRIVER from installing anything, but the adoption
# step (the agent wiring an approved capability in) had no enforcement: nothing forced a
# green suite after the change or left a one-step rollback anchor. record_adoption() is now
# the one valid write path, and healthcheck turns the tree RED on a ledger entry that skips
# the protocol — which also blocks the next wake-safe Scout run.
from lib.scout import (  # noqa: E402
    AdoptionError, record_adoption, adoption_ledger_violations,
)


def _decisions_file(tmp_path, items):
    p = tmp_path / "memo_decisions.json"
    p.write_text(_json.dumps({"decisions": {
        "scout_memo_x.md": {"decided": "2026-07-07", "by": "owner", "items": items}}}))
    return str(p)


def _adopt(tmp_path, items=None, **over):
    dec = _decisions_file(tmp_path, items if items is not None else {"new_model_v1": "approve"})
    led = str(tmp_path / "adoption_ledger.json")
    kw = dict(memo="scout_memo_x.md", pre_commit="aaa1111", post_commit="bbb2222",
              suite_passed=600, suite_failed=0, files_changed=["lib/x.py"],
              decisions_path=dec, ledger_path=led)
    kw.update(over)
    return record_adoption("new_model_v1", **kw), led, dec


def test_adoption_without_owner_approval_blocks(tmp_path):
    with pytest.raises(AdoptionError, match="approve"):
        _adopt(tmp_path, items={"new_model_v1": "reject"})


def test_adoption_of_undecided_item_blocks(tmp_path):
    with pytest.raises(AdoptionError, match="approve"):
        _adopt(tmp_path, items={"other_item": "approve"})


def test_adoption_without_rollback_anchor_blocks(tmp_path):
    with pytest.raises(AdoptionError, match="rollback"):
        _adopt(tmp_path, post_commit="aaa1111")  # same as pre → no revert anchor


def test_adoption_with_red_suite_blocks(tmp_path):
    with pytest.raises(AdoptionError, match="green"):
        _adopt(tmp_path, suite_failed=2)


def test_valid_adoption_lands_in_ledger_with_rollback(tmp_path):
    entry, led, dec = _adopt(tmp_path)
    ledger = _json.loads(Path(led).read_text())
    assert ledger["adoptions"][0]["rollback"] == "git revert bbb2222"
    assert adoption_ledger_violations(led, dec) == []


def test_hand_edited_ledger_entry_is_a_violation(tmp_path):
    entry, led, dec = _adopt(tmp_path)
    ledger = _json.loads(Path(led).read_text())
    ledger["adoptions"][0]["suite"] = {"passed": 1, "failed": 3}   # forged after the fact
    Path(led).write_text(_json.dumps(ledger))
    bad = adoption_ledger_violations(led, dec)
    assert bad and "suite" in bad[0]


def test_unapproved_ledger_entry_is_a_violation(tmp_path):
    entry, led, dec = _adopt(tmp_path)
    dec2 = _decisions_file(tmp_path, {"new_model_v1": "reject"})   # approval revoked
    bad = adoption_ledger_violations(led, dec2)
    assert bad and "approve" in bad[0]
