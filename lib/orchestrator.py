"""Minimal production orchestrator — the executable runtime that drives a pipeline through
its stages, wiring get_next_stage -> write_checkpoint -> resume_checkpoint into a real run.

Until this module existed, every gate in lib/checkpoint.py was an *enforceable library* with
no production caller: nothing sequenced an actual run, so the gates were only ever exercised
by tests. This is that spine — deliberately thin. It does NOT generate creative content
(agents/skills do that); it decides which stage runs next, gates each stage completion through
write_checkpoint (so every contract — ordering, referential integrity, glyph, continuity,
ladder — fires on the real path), stops at owner checkpoints, and resumes fail-closed.

Owner law (Mozg): the orchestrator advances one stage at a time and never skips ahead. A
stage may pause the run for the owner by completing as ``awaiting_human`` instead of
``completed``; the run does not proceed past it until the owner supplies the completed write.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from lib.checkpoint import (
    CheckpointValidationError,
    _canonical_pipeline_type,
    get_completed_stages,
    get_next_stage,
    get_pipeline_stages,
    read_checkpoint,
    resume_checkpoint,
    write_checkpoint,
)


class OrchestratorError(RuntimeError):
    """Raised when a run is driven incorrectly — e.g. an out-of-order advance."""


def run_state(pipeline_dir: Path, project_id: str, pipeline_type: str) -> dict[str, Any]:
    """The current state of a run.

    Returns the completed stages, the next stage to run (None when finished), whether the run
    is paused at an owner checkpoint, and a ``done`` flag.
    """
    # Canonicalize at the public boundary: a stray-cased/whitespace pipeline_type must resolve
    # to the real manifest, or get_pipeline_stages returns the generic order and the orchestrator
    # drives e.g. character-animation without its character_design/rig_plan stages (#round-5).
    pipeline_type = _canonical_pipeline_type(pipeline_type)
    completed = get_completed_stages(pipeline_dir, project_id, pipeline_type)
    next_stage = get_next_stage(pipeline_dir, project_id, pipeline_type)
    awaiting_human: Optional[str] = None
    for stage in get_pipeline_stages(pipeline_type):
        cp = read_checkpoint(pipeline_dir, project_id, stage)
        if cp and cp.get("status") == "awaiting_human":
            awaiting_human = stage
            break
    return {
        "pipeline_type": pipeline_type,
        "completed": completed,
        "next_stage": next_stage,
        "awaiting_human": awaiting_human,
        "done": next_stage is None,
    }


def advance(
    pipeline_dir: Path,
    project_id: str,
    pipeline_type: str,
    *,
    stage: str,
    artifacts: dict[str, Any],
    status: str = "completed",
    **write_kwargs: Any,
) -> dict[str, Any]:
    """Advance the run by writing ``stage``'s checkpoint, and return the new run state.

    A ``completed`` write must target the next expected stage — no skipping ahead, no
    re-completing a finished stage. The ordering the checkpoint spine already enforces is
    surfaced here as a loud runtime error *before* anything is written, so a caller cannot
    drive the run out of order. Every gate runs inside write_checkpoint; a gate violation
    propagates as CheckpointValidationError.
    """
    pipeline_type = _canonical_pipeline_type(pipeline_type)  # resolve to the real manifest
    if status == "completed":
        expected = get_next_stage(pipeline_dir, project_id, pipeline_type)
        if expected is None:
            raise OrchestratorError(
                f"Run {project_id!r} is already complete — nothing left to advance."
            )
        if stage != expected:
            raise OrchestratorError(
                f"Out-of-order advance: run {project_id!r} expects stage {expected!r} next, "
                f"not {stage!r}."
            )
    write_checkpoint(
        pipeline_dir, project_id, stage, status, artifacts,
        pipeline_type=pipeline_type, **write_kwargs,
    )
    return run_state(pipeline_dir, project_id, pipeline_type)


def resume(pipeline_dir: Path, project_id: str, stage: str | None = None) -> Optional[dict[str, Any]]:
    """Resume a run fail-closed.

    Delegates to resume_checkpoint, which re-runs the structural contracts, a read-only canon
    check, artifact existence/media validation, and referential integrity before handing back
    the state to continue from. A hand-edited, drifted, or dangling checkpoint is refused, not
    silently continued.
    """
    return resume_checkpoint(pipeline_dir, project_id, stage)
