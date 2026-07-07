"""#6 — strict, side-effect-free resume re-validation.

resume_checkpoint()/get_latest_checkpoint(strict_resume=True) must fail-closed on a
hand-edited / downgraded / canon-drifted / artifact-missing checkpoint, while plain
read_checkpoint() stays lenient and NEITHER path may write a canon lock (inspection/resume
must never mutate project state).

The per-gate blocking logic is already covered by test_gates / test_canon_guard_checkpoint /
test_artifact_path_existence_checkpoint. Here we pin what #6 adds: that the resume path RUNS
those gates, that its canon check is read-only, and that plain reads stay lenient.
"""
import json
import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.checkpoint import (  # noqa: E402
    CheckpointValidationError,
    resume_checkpoint,
    get_latest_checkpoint,
    read_checkpoint,
    get_completed_stages,
    write_checkpoint,
    _enforce_resume_contracts,
    _check_canon_guard_readonly,
    _enforce_canon_guard,
    _required_ladder_sub_stages,
)
from lib.canon_guard import LOCK, lock as canon_lock  # noqa: E402
from tests.zavod.media_helpers import tiny_mp4, seed_prior_stages  # noqa: E402
from tests.zavod.test_gates import (  # noqa: E402
    _with_bench, _brief, _ladder, _concept_log, _IDEA_SUBS, _ASSET_SUBS,
)


def _raw_cp(stage, *, status="completed", artifacts=None, ptype="zavod-reel"):
    return {"version": "1.0", "project_id": "p", "pipeline_type": ptype, "stage": stage,
            "status": status, "timestamp": "2026-07-05T00:00:00Z", "artifacts": artifacts or {}}


def _plain_ladder(names):
    return {"sub_stages": [{"name": n, "produces": n, "owner_approved": True} for n in names]}


def _assets_artifacts(asset_path):
    # A structurally-complete completed-assets payload: valid ladder, locked Higgsfield lane,
    # automatic run mode. Only the file behind `asset_path` is the variable under test.
    return {
        "asset_manifest": {"version": "1.0", "assets": [
            {"id": "a1", "type": "video", "path": asset_path,
             "source_tool": "higgsfield", "scene_id": "s1"}]},
        "production_ladder": _plain_ladder(_ASSET_SUBS),
        "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
        "run_mode": "automatic",
    }


# ── resume contracts fail-closed on degraded/tampered state ────────────────
def test_resume_contracts_block_collapsed_ladder():
    # scene_plan with its production_ladder stripped out cannot resume. (project_dir irrelevant.)
    assert _required_ladder_sub_stages("zavod-reel", "scene_plan")
    with pytest.raises(CheckpointValidationError, match="ladder"):
        _enforce_resume_contracts(_raw_cp("scene_plan", artifacts={}), None)


def test_resume_contracts_block_missing_artifact(tmp_path):
    seed_prior_stages(tmp_path, "zavod-reel", "assets")  # a real run has its prior stages
    cp = _raw_cp("assets", artifacts=_assets_artifacts("assets/gone.mp4"))
    with pytest.raises(CheckpointValidationError, match="existence"):
        _enforce_resume_contracts(cp, tmp_path)


def test_resume_contracts_block_fake_media(tmp_path):
    seed_prior_stages(tmp_path, "zavod-reel", "assets")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "fake.mp4").write_bytes(b"12345")  # non-empty but not real video
    cp = _raw_cp("assets", artifacts=_assets_artifacts("assets/fake.mp4"))
    with pytest.raises(CheckpointValidationError, match="not valid content"):
        _enforce_resume_contracts(cp, tmp_path)


def test_resume_contracts_pass_on_clean_state(tmp_path):
    (tmp_path / "assets").mkdir()
    tiny_mp4(tmp_path / "assets" / "real.mp4")
    seed_prior_stages(tmp_path, "zavod-reel", "assets")
    cp = _raw_cp("assets", artifacts=_assets_artifacts("assets/real.mp4"))
    _enforce_resume_contracts(cp, tmp_path)  # no raise


# ── the crux: the resume canon check is READ-ONLY (never writes a lock) ─────
def test_resume_canon_check_blocks_drift_without_writing_lock(tmp_path):
    (tmp_path / "look-bible.md").write_text("original\n")
    canon_lock(str(tmp_path))
    lock_path = tmp_path / LOCK
    before_bytes, before_mtime = lock_path.read_bytes(), lock_path.stat().st_mtime
    (tmp_path / "look-bible.md").write_text("drifted\n")
    with pytest.raises(CheckpointValidationError, match="[Cc]anon guard block on resume"):
        _check_canon_guard_readonly(_raw_cp("edit"), tmp_path)
    assert lock_path.read_bytes() == before_bytes         # untouched
    assert lock_path.stat().st_mtime == before_mtime


def test_resume_canon_check_clean_does_not_refresh_but_write_seam_does(tmp_path):
    (tmp_path / "look-bible.md").write_text("original\n")
    canon_lock(str(tmp_path))
    lock_path = tmp_path / LOCK
    before_mtime = lock_path.stat().st_mtime
    time.sleep(0.02)
    cp = _raw_cp("edit")
    _check_canon_guard_readonly(cp, tmp_path)              # clean → passes, must NOT refresh lock
    assert lock_path.stat().st_mtime == before_mtime
    _enforce_canon_guard(cp, tmp_path)                     # contrast: the WRITE seam refreshes it
    assert lock_path.stat().st_mtime > before_mtime


# ── plain read stays lenient; resume is strict (didn't break inspection) ────
def _valid_idea_project(tmp_path):
    write_checkpoint(
        tmp_path, "proj", "idea", "completed",
        _with_bench("idea", {"brief": _brief(), "production_ladder": _ladder(_IDEA_SUBS),
                             "engine_lock": {"engine": "higgsfield", "compose_runtime": "ffmpeg"},
                             "run_mode": "automatic", "decision_log": _concept_log("proj")}),
        pipeline_type="zavod-reel",
    )


def test_plain_read_lenient_where_resume_blocks_on_downgrade(tmp_path):
    _valid_idea_project(tmp_path)
    # Tamper on disk: strip the production_ladder (simulates a hand-edited downgrade).
    cp_file = tmp_path / "proj" / "checkpoint_idea.json"
    data = json.loads(cp_file.read_text())
    data["artifacts"].pop("production_ladder")
    cp_file.write_text(json.dumps(data))

    # resume refuses the downgraded checkpoint…
    with pytest.raises(CheckpointValidationError, match="ladder"):
        resume_checkpoint(tmp_path, "proj", stage="idea")
    # …but plain inspection stays lenient and does not mutate the canon lock.
    lock_path = tmp_path / "proj" / LOCK
    lock_before = (lock_path.read_bytes(), lock_path.stat().st_mtime) if lock_path.exists() else None
    got = read_checkpoint(tmp_path, "proj", "idea")
    assert got is not None and got["stage"] == "idea"
    assert "idea" in get_completed_stages(tmp_path, "proj", "zavod-reel")
    lock_after = (lock_path.read_bytes(), lock_path.stat().st_mtime) if lock_path.exists() else None
    assert lock_after == lock_before  # inspection wrote/changed no lock


# ── positive + entry-point equivalence ─────────────────────────────────────
def test_resume_returns_valid_checkpoint(tmp_path):
    _valid_idea_project(tmp_path)
    latest = resume_checkpoint(tmp_path, "proj")
    assert latest is not None and latest["stage"] == "idea"
    assert resume_checkpoint(tmp_path, "proj", stage="idea")["stage"] == "idea"
    assert resume_checkpoint(tmp_path, "proj", stage="publish") is None  # absent stage → None


def test_strict_resume_flag_blocks_where_plain_get_latest_would_not(tmp_path):
    _valid_idea_project(tmp_path)
    cp_file = tmp_path / "proj" / "checkpoint_idea.json"
    data = json.loads(cp_file.read_text())
    data["artifacts"].pop("production_ladder")
    cp_file.write_text(json.dumps(data))

    assert get_latest_checkpoint(tmp_path, "proj") is not None          # lenient default
    with pytest.raises(CheckpointValidationError, match="ladder"):
        get_latest_checkpoint(tmp_path, "proj", strict_resume=True)     # strict
