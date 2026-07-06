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


def test_completed_compose_with_explicit_empty_continuity_is_allowed():
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
          "continuity_reports": [], "metadata": {"caption": "Ձմեռային արձակուրդ 🏔️ weekend"}}
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
