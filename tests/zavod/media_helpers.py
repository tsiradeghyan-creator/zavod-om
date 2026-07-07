"""Real tiny media generators for tests that must pass the #5 content-validation gate.

The artifact-existence gate now probes files with ffprobe, so tests that legitimately
close an asset/compose stage need genuine (if tiny) decodable media, not placeholder bytes.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def tiny_mp4(path: Path, seconds: float = 0.2) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", f"color=c=black:s=64x64:d={seconds}:r=10",
         "-pix_fmt", "yuv420p", str(path)],
        check=True, capture_output=True,
    )
    return path


def tiny_wav(path: Path, seconds: float = 0.2) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", f"sine=frequency=440:duration={seconds}", str(path)],
        check=True, capture_output=True,
    )
    return path


def tiny_png(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "color=c=red:s=32x32:d=0.1", "-frames:v", "1", str(path)],
        check=True, capture_output=True,
    )
    return path


def seed_prior_stages(project_dir: Path, pipeline_type: str, stage: str) -> None:
    """Drop minimal completed-checkpoint markers for every stage before ``stage`` in the
    pipeline's manifest order, so a test that writes/validates a single later-stage
    checkpoint in isolation satisfies the manifest-order gate (#7 ordering, 2026-07-06)."""
    import json
    from lib.checkpoint import get_pipeline_stages
    order = get_pipeline_stages(pipeline_type)
    Path(project_dir).mkdir(parents=True, exist_ok=True)
    for prior in order[:order.index(stage)]:
        # Schema-valid marker: the ordering gate schema-validates each prior (not a bare status
        # field), so these markers must be full schema-shaped checkpoints of that stage.
        (Path(project_dir) / f"checkpoint_{prior}.json").write_text(
            json.dumps({
                "version": "1.0",
                "project_id": Path(project_dir).name,
                "pipeline_type": pipeline_type,
                "stage": prior,
                "status": "completed",
                "timestamp": "2026-07-06T00:00:00+00:00",
                "artifacts": {},
            })
        )


def degenerate_mp4(path: Path) -> Path:
    """A perfectly decodable but production-useless video: 8x8, one black frame (audit №5)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "color=c=black:s=8x8:d=0.1:r=10", "-frames:v", "1",
         "-pix_fmt", "yuv420p", str(path)],
        check=True, capture_output=True,
    )
    return path
