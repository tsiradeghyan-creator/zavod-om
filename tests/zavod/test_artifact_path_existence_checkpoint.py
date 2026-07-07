"""Checkpoint write seam rejects phantom assets/renders."""

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
from tests.zavod.media_helpers import tiny_mp4, seed_prior_stages  # noqa: E402


def _bench_report(stage: str) -> dict:
    bench_stage = {"assets": "asset"}.get(stage, stage)
    return {
        "stage": bench_stage,
        "bench": {role: {"ruling": f"The {role} reviewed this stage in depth and confirms craft quality across staging continuity and delivery.", "verdict": "approve"} for role in required_bench(bench_stage)},
    }


def _ladder(stage: str) -> dict:
    return {
        "sub_stages": [
            {"name": name, "produces": f"{name}_artifact", "owner_approved": True}
            for name in _required_ladder_sub_stages("zavod-reel", stage)
        ]
    }


def _checkpoint(stage: str, stage_artifact: dict) -> dict:
    artifacts = {
        "bench_report": _bench_report(stage),
        "production_ladder": _ladder(stage),
        "engine_lock": {"engine": "remotion", "compose_runtime": "remotion"},
    }
    artifacts.update(stage_artifact)
    return {"pipeline_type": "zavod-reel", "stage": stage, "status": "completed", "artifacts": artifacts}


def _asset_manifest(path: str) -> dict:
    return {"version": "1.0", "assets": [{
        "id": "a1", "type": "video", "path": path, "source_tool": "remotion", "scene_id": "s1",
    }]}


def _render_report(path: str) -> dict:
    return {"version": "1.0", "outputs": [{
        # Honest declaration for the tiny_mp4 fixture — declared-vs-actual is enforced (r6 #6).
        "path": path, "format": "mp4", "resolution": "64x64", "duration_seconds": 0.2,
    }]}


def test_assets_completed_checkpoint_blocks_phantom_manifest_path(tmp_path):
    cp = _checkpoint("assets", {"asset_manifest": _asset_manifest("assets/missing.mp4")})
    with pytest.raises(CheckpointValidationError) as exc:
        enforce_zavod_write_contracts(cp, project_dir=tmp_path)
    assert "assets/missing.mp4" in str(exc.value)


def test_assets_completed_checkpoint_passes_existing_manifest_path(tmp_path):
    path = tmp_path / "assets" / "real.mp4"
    path.parent.mkdir()
    tiny_mp4(path)
    cp = _checkpoint("assets", {"asset_manifest": _asset_manifest("assets/real.mp4")})
    seed_prior_stages(tmp_path, "zavod-reel", "assets")
    enforce_zavod_write_contracts(cp, project_dir=tmp_path)


def test_compose_completed_checkpoint_blocks_phantom_output_path(tmp_path):
    cp = _checkpoint("compose", {"render_report": _render_report("renders/missing.mp4")})
    with pytest.raises(CheckpointValidationError) as exc:
        enforce_zavod_write_contracts(cp, project_dir=tmp_path)
    assert "renders/missing.mp4" in str(exc.value)


def test_compose_completed_checkpoint_passes_existing_output_path(tmp_path):
    path = tmp_path / "renders" / "real.mp4"
    path.parent.mkdir()
    tiny_mp4(path)
    cp = _checkpoint("compose", {"render_report": _render_report("renders/real.mp4")})
    seed_prior_stages(tmp_path, "zavod-reel", "compose")
    enforce_zavod_write_contracts(cp, project_dir=tmp_path)