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
    _is_zavod_pipeline, _enforce_artifact_path_existence, CheckpointValidationError,
)
from lib.gatechain import run_script_gates  # noqa: E402


# ── Angle 1: bench rubber-stamp ────────────────────────────────────────────
def _bench(stage, ruling_for):
    return {"stage": stage, "bench": {r: {"ruling": ruling_for(r)} for r in required_bench(stage)}}

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


# ── Angle 6: pipeline_type canonicalization ────────────────────────────────
@pytest.mark.parametrize("ptype", ["Zavod-reel", "ZAVOD-reel", " zavod-reel", "zavod-reel "])
def test_pipeline_type_casing_whitespace_still_gated(ptype):
    assert _is_zavod_pipeline(ptype) is True

@pytest.mark.parametrize("ptype", ["animation", "cinematic", "reel-zavod", "", None])
def test_non_zavod_pipelines_stay_ungated(ptype):
    assert _is_zavod_pipeline(ptype) is False


# ── Angle 3: existence gate content-awareness ──────────────────────────────
def _assets_cp(path_or_none):
    assets = [] if path_or_none is None else [
        {"id": "a", "type": "video", "path": path_or_none, "source_tool": "x", "scene_id": "s"}]
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

def test_existence_allows_real_nonempty_file():
    _run_existence(_assets_cp("r.mp4"), lambda d: (d / "r.mp4").write_bytes(b"12345"))


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


# ── Angle 3 (cont.): symlink provenance ────────────────────────────────────
def test_existence_blocks_symlink_escaping_project():
    def make(d):
        (d / "link.mp4").symlink_to("/etc/hosts")
    with pytest.raises(CheckpointValidationError):
        _run_existence(_assets_cp("link.mp4"), make)

def test_existence_allows_internal_symlink():
    def make(d):
        (d / "real.mp4").write_bytes(b"12345")
        (d / "link.mp4").symlink_to(d / "real.mp4")
    _run_existence(_assets_cp("link.mp4"), make)
