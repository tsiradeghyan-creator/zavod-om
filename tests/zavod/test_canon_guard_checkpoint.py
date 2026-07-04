"""Checkpoint write-contract wiring for the canon guard."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.bench_gate import RULING_MIN, required_bench  # noqa: E402
from lib.checkpoint import (  # noqa: E402
    CheckpointValidationError,
    _required_ladder_sub_stages,
    enforce_zavod_write_contracts,
)
from lib.canon_guard import LOCK, lock  # noqa: E402


def _bench_report(stage: str) -> dict:
    return {
        "stage": stage,
        "bench": {role: {"ruling": f"The {role} reviewed this stage in depth and confirms craft quality across staging continuity and delivery."} for role in required_bench(stage)},
    }


def _checkpoint(stage: str) -> dict:
    ladder = {
        "sub_stages": [
            {"name": name, "produces": f"{name}_artifact", "owner_approved": True}
            for name in _required_ladder_sub_stages("zavod-reel", stage)
        ]
    }
    return {
        "pipeline_type": "zavod-reel",
        "stage": stage,
        "status": "completed",
        "artifacts": {"bench_report": _bench_report(stage), "production_ladder": ladder},
    }


def test_post_script_canon_drift_blocks_write_contract_until_revalidation(tmp_path):
    (tmp_path / "look-bible.md").write_text("original canon\n", encoding="utf-8")
    lock(str(tmp_path))

    (tmp_path / "look-bible.md").write_text("changed canon\n", encoding="utf-8")

    with pytest.raises(CheckpointValidationError) as exc:
        enforce_zavod_write_contracts(_checkpoint("edit"), project_dir=tmp_path)
    assert "canon-revalidation.md" in str(exc.value)


def test_post_script_canon_drift_passes_after_fresh_revalidation(tmp_path):
    canon = tmp_path / "look-bible.md"
    canon.write_text("original canon\n", encoding="utf-8")
    lock(str(tmp_path))

    canon.write_text("changed canon\n", encoding="utf-8")
    reval = tmp_path / "canon-revalidation.md"
    reval.write_text("Rechecked story spine after canon change.\n", encoding="utf-8")
    now = canon.stat().st_mtime + 10
    reval.touch()
    import os
    os.utime(reval, (now, now))

    enforce_zavod_write_contracts(_checkpoint("edit"), project_dir=tmp_path)


def test_script_stage_write_contract_locks_canon_snapshot(tmp_path):
    (tmp_path / "look-bible.md").write_text("script-approved canon\n", encoding="utf-8")

    enforce_zavod_write_contracts(_checkpoint("script"), project_dir=tmp_path)

    assert (tmp_path / LOCK).exists()