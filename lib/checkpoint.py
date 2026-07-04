"""Checkpoint writer/reader for pipeline state persistence.

Each stage writes a checkpoint after completion. The orchestrator uses
checkpoints to resume pipelines and to present state at human checkpoints.
"""

from __future__ import annotations

import json
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import jsonschema

from schemas.artifacts import ARTIFACT_NAMES, validate_artifact

# All known stages across all pipelines (used only for artifact name lookup).
ALL_KNOWN_STAGES = frozenset([
    "research", "proposal", "idea", "script", "scene_plan",
    "assets", "edit", "compose", "publish",
])

# Backward-compatible alias — existing code / tests that import STAGES still work.
# New code should use get_pipeline_stages(pipeline_type) instead.
STAGES = ["research", "proposal", "idea", "script", "scene_plan",
          "assets", "edit", "compose", "publish"]

CANONICAL_STAGE_ARTIFACTS = {
    "research": "research_brief",
    "proposal": "proposal_packet",
    "idea": "brief",
    "script": "script",
    "scene_plan": "scene_plan",
    "assets": "asset_manifest",
    "edit": "edit_decisions",
    "compose": "render_report",
    "publish": "publish_log",
}

# Additional artifacts that may be produced alongside canonical ones.
# These are not stage-defining but are required by governance contracts.
SUPPLEMENTARY_ARTIFACTS = {
    "source_media_review",  # Required before first planning stage when user media exists
    "final_review",         # Required by compose stage before presenting to user
    "video_analysis_brief", # Reference-video grounding artifact carried alongside stages
}


def get_pipeline_stages(pipeline_type: str | None) -> list[str]:
    """Return the ordered stage list for a specific pipeline.

    Falls back to STAGES (deterministic canonical order) when pipeline_type
    is not provided or the manifest cannot be loaded.

    Previous versions used a set intersection here, which produced
    nondeterministic ordering. The fallback now uses a stable list.
    """
    if pipeline_type is None:
        # Deterministic canonical fallback — sorted to ensure stable ordering
        import logging
        logging.getLogger(__name__).warning(
            "get_pipeline_stages called without pipeline_type — "
            "using canonical fallback order. Pass pipeline_type for correctness."
        )
        return list(STAGES)

    try:
        from lib.pipeline_loader import load_pipeline, get_stage_order
        manifest = load_pipeline(pipeline_type)
        return get_stage_order(manifest)
    except (FileNotFoundError, Exception):
        # Graceful fallback: return all known stages in canonical order
        return list(STAGES)

CHECKPOINT_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "checkpoints"
    / "checkpoint.schema.json"
)


class CheckpointValidationError(ValueError):
    """Raised when a checkpoint or its canonical artifacts are invalid."""


@lru_cache(maxsize=1)
def _load_checkpoint_schema() -> dict[str, Any]:
    with open(CHECKPOINT_SCHEMA_PATH) as f:
        return json.load(f)


def _validate_artifacts_for_stage(
    stage: str,
    status: str,
    artifacts: dict[str, Any],
) -> None:
    required_artifact = CANONICAL_STAGE_ARTIFACTS[stage]
    if status in {"completed", "awaiting_human"} and required_artifact not in artifacts:
        raise CheckpointValidationError(
            f"Stage {stage!r} with status {status!r} must include "
            f"canonical artifact {required_artifact!r}"
        )

    for artifact_name, artifact_data in artifacts.items():
        if artifact_name not in ARTIFACT_NAMES:
            continue
        if not isinstance(artifact_data, dict):
            raise CheckpointValidationError(
                f"Artifact {artifact_name!r} must be a JSON object matching its schema"
            )
        try:
            validate_artifact(artifact_name, artifact_data)
        except Exception as exc:
            raise CheckpointValidationError(
                f"Artifact {artifact_name!r} failed schema validation: {exc}"
            ) from exc


def _all_strings(obj: Any) -> list[str]:
    """Collect every string leaf of an artifact (for text-based gates)."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in _all_strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in _all_strings(v)]
    return []


def _continuity_reports(artifacts: dict[str, Any]) -> list[dict[str, Any]]:
    """The ONE valid route for compose-stage continuity reports:
    ``render_report.continuity_reports`` — schema-validated as part of the render_report
    artifact (see render_report.schema.json). The old loose ``artifacts.continuity_report``
    / ``artifacts.continuity_reports`` keys were closed 2026-07-02: they escaped schema
    validation entirely (not in ARTIFACT_NAMES), so any garbage could ride in them.
    """
    rr = artifacts.get("render_report")
    if not isinstance(rr, dict):
        return []
    cr = rr.get("continuity_reports")
    if cr is None:
        return []
    return cr if isinstance(cr, list) else [cr]


def _enforce_zavod_gates(checkpoint: dict[str, Any]) -> None:
    """Hard-gate enforcement at the checkpoint seam — the wiring that makes the code
    gates non-bypassable instead of prose the agent can skip.

    Only ``zavod-*`` pipelines are gated, so upstream OpenMontage behavior is byte-for-byte
    unchanged. A stage cannot persist a ``completed`` / ``awaiting_human`` checkpoint whose
    artifacts fail their gate. A hard ``fail`` always blocks; ``needs_human`` is allowed only
    while ``awaiting_human`` (it must never reach ``completed`` unjudged).
    """
    ptype = checkpoint.get("pipeline_type") or ""
    if not ptype.startswith("zavod"):
        return
    if checkpoint.get("status") not in {"completed", "awaiting_human"}:
        return

    stage = checkpoint.get("stage")
    artifacts = checkpoint.get("artifacts") or {}

    # Lazy import: keeps the spine importable without the gate libs, and avoids any cycle.
    from lib.gatechain import (
        run_bench_gates,
        run_script_gates,
        run_scene_plan_gates,
        run_edit_gates,
        run_compose_gates,
    )

    # Owner standing order (2026-07-03): every Zavod stage closes only after
    # its full specialist bench has left substantive rulings. Missing the
    # report is itself a hard gate failure; otherwise an agent could simply
    # omit the artifact and bypass lib/bench_gate.py.
    bench_stage = {"scene_plan": "scene", "assets": "asset"}.get(stage, stage)
    bench_report = artifacts.get("bench_report")
    if not isinstance(bench_report, dict):
        raise CheckpointValidationError(
            f"Gate block at stage {stage!r} ({ptype}): missing artifacts.bench_report — "
            "every zavod stage requires a full bench_report before it can close."
        )
    bench_result = run_bench_gates(bench_stage, bench_report)
    if not bench_result.get("ok"):
        detail = bench_result.get("violations") or bench_result
        raise CheckpointValidationError(
            f"Gate block at stage {stage!r} ({ptype}): {detail}"
        )

    result: dict[str, Any] | None = None
    if stage == "script" and "script" in artifacts:
        result = run_script_gates("\n".join(_all_strings(artifacts["script"])))
    elif stage == "scene_plan" and "scene_plan" in artifacts:
        result = run_scene_plan_gates(artifacts["scene_plan"])
    elif stage == "edit" and "edit_decisions" in artifacts:
        # Delivery-promise preservation: a motion-led promise must not silently become
        # a slideshow. The locked promise travels in artifacts.delivery_promise.
        result = run_edit_gates(artifacts["edit_decisions"], artifacts.get("delivery_promise"))
    elif stage == "compose":
        reports = _continuity_reports(artifacts)
        if reports:
            result = run_compose_gates(reports)

    if result is None or result.get("ok"):
        return

    if result.get("verdict") == "needs_human" and checkpoint.get("status") == "awaiting_human":
        return  # legitimate pause at the human checkpoint

    detail = result.get("violations") or result.get("pending") or result
    raise CheckpointValidationError(
        f"Gate block at stage {stage!r} ({ptype}): {detail}"
    )


def _required_ladder_sub_stages(pipeline_type: str, stage: str) -> list[str]:
    """Owner-gated sub-stages that declare a ``produces`` artifact for this stage.

    These are the non-collapsible rungs: every one must be recorded in
    ``artifacts.production_ladder`` before the stage may close.
    """
    try:
        from lib.pipeline_loader import load_pipeline
        manifest = load_pipeline(pipeline_type)
    except Exception:
        return []
    for st in manifest.get("stages", []):
        if st.get("name") != stage:
            continue
        return [
            ss["name"]
            for ss in st.get("sub_stages", [])
            if ss.get("human_approval_default", True) and ss.get("produces")
        ]
    return []


def _enforce_production_ladder(checkpoint: dict[str, Any]) -> None:
    """Make the specialist ladder non-collapsible at the checkpoint seam.

    A ``zavod-*`` stage cannot persist a ``completed`` checkpoint unless every
    owner-gated sub-stage that declares ``produces`` is recorded in
    ``artifacts.production_ladder.sub_stages``. This is what stops the Executive
    Producer from silently squeezing five specialists into one answer — the same
    failure mode that motivated the ladder. The creative-language council carries
    the extra contract that every craft role has a named Style Radar pick.

    Only fires on ``completed`` (the stage is fully done); ``awaiting_human`` is a
    legitimate mid-ladder pause and is left alone.
    """
    ptype = checkpoint.get("pipeline_type") or ""
    if not ptype.startswith("zavod"):
        return
    if checkpoint.get("status") != "completed":
        return

    stage = checkpoint.get("stage")
    required = _required_ladder_sub_stages(ptype, stage)
    if not required:
        return

    artifacts = checkpoint.get("artifacts") or {}
    ladder = artifacts.get("production_ladder") or {}
    recorded = {
        entry["name"]: entry
        for entry in (ladder.get("sub_stages") or [])
        if isinstance(entry, dict) and entry.get("name")
    }

    missing = [name for name in required if name not in recorded]
    if missing:
        raise CheckpointValidationError(
            f"Production ladder collapsed at stage {stage!r} ({ptype}): completed without "
            f"owner-gated sub-stage(s) {missing}. Each specialist sub-stage must run and be "
            f"recorded in artifacts.production_ladder.sub_stages before the stage can close."
        )

    # Per-role Style Radar selection is mandatory on the creative-language council.
    if "creative_language_council" in recorded:
        from lib.style_selection import validate_selections, required_roles
        verdict = validate_selections(recorded["creative_language_council"].get("style_selections"))
        if not verdict["ok"]:
            raise CheckpointValidationError(
                f"Creative-language council at stage {stage!r} ({ptype}) left craft roles without "
                f"a named Style Radar pick — missing {verdict['missing']}, empty {verdict['empty']}. "
                f"Every role must be chosen: {required_roles()}."
            )


# Two mutually-exclusive production lanes. The EP asks Remotion vs Higgsfield at the
# idea stage; the lock is carried in artifacts.engine_lock and the lanes never mix.
VALID_ENGINES = {"remotion", "higgsfield"}
LANE_COMPOSE_RUNTIMES = {
    "remotion": {"remotion", "hyperframes"},  # programmatic build, zero AI footage
    "higgsfield": {"ffmpeg"},                  # AI footage + ffmpeg overlay, zero Remotion
}
# Stages where the engine actually drives the toolchain.
_ENGINE_RELEVANT_STAGES = {"idea", "assets", "compose"}

# Two run modes. Same structure either way; only the stopping behavior differs.
VALID_RUN_MODES = {"supervised", "automatic"}
# Even an automatic run must stop for the owner at these irreversible external gates.
_OWNER_ALWAYS_RUNGS = {"presentation_route"}  # final delivery / publish


def _asset_uses_higgsfield(asset: dict[str, Any]) -> bool:
    blob = " ".join(
        str(asset.get(k, "")) for k in ("source_tool", "provider", "model")
    ).lower()
    return "higgsfield" in blob


def _enforce_engine_lane(checkpoint: dict[str, Any]) -> None:
    """Keep the Remotion and Higgsfield lanes from interfering.

    The owner picks ONE engine at the idea stage; `artifacts.engine_lock.engine` carries it.
    - idea:    the lane must be locked (forces the upfront Remotion-vs-Higgsfield question).
    - assets:  a Remotion-lane manifest may not contain Higgsfield-generated assets.
    - compose: the compose runtime must match the lane — Remotion lane renders via
               remotion/hyperframes, Higgsfield lane composes via ffmpeg (zero Remotion).
    Only zavod pipelines, only on `completed`.
    """
    ptype = checkpoint.get("pipeline_type") or ""
    if not ptype.startswith("zavod"):
        return
    if checkpoint.get("status") != "completed":
        return
    stage = checkpoint.get("stage")
    if stage not in _ENGINE_RELEVANT_STAGES:
        return

    artifacts = checkpoint.get("artifacts") or {}
    lock = artifacts.get("engine_lock") or {}
    engine = lock.get("engine")

    if engine not in VALID_ENGINES:
        raise CheckpointValidationError(
            f"Engine lane not locked at stage {stage!r} ({ptype}): artifacts.engine_lock.engine "
            f"must be one of {sorted(VALID_ENGINES)}. The Executive Producer asks Remotion vs "
            f"Higgsfield at the idea stage and carries the lock forward. Got {engine!r}."
        )

    if stage == "assets" and engine == "remotion":
        bad = [
            a.get("id")
            for a in (artifacts.get("asset_manifest") or {}).get("assets", [])
            if isinstance(a, dict) and _asset_uses_higgsfield(a)
        ]
        if bad:
            raise CheckpointValidationError(
                f"Remotion lane ({ptype}) forbids Higgsfield-generated assets, but {bad} were "
                f"produced with Higgsfield. The Remotion and Higgsfield lanes must not mix."
            )

    if stage == "compose":
        runtime = lock.get("compose_runtime")
        allowed = LANE_COMPOSE_RUNTIMES[engine]
        if runtime not in allowed:
            raise CheckpointValidationError(
                f"{engine!r} lane ({ptype}) must compose via {sorted(allowed)} with zero cross-lane "
                f"tooling, but engine_lock.compose_runtime={runtime!r}. "
                f"(Remotion lane → remotion/hyperframes; Higgsfield lane → ffmpeg only.)"
            )


def _enforce_run_mode(checkpoint: dict[str, Any]) -> None:
    """Keep supervised and automatic runs cleanly separated — both ideal, different stops.

    `artifacts.run_mode` is chosen at the idea stage and carried forward. Both modes must
    produce the same structure (the ladder/engine/style gates apply equally); the ONLY
    difference is the stopping behavior:
    - idea:     the run mode must be locked (supervised|automatic).
    - supervised: every owner-gated rung in this stage must be recorded `owner_approved`
                  (proof the freeze happened).
    - any mode: the irreversible external gates (final delivery / publish) still require
                owner approval even in an automatic run.
    Only zavod pipelines, only on `completed`.
    """
    ptype = checkpoint.get("pipeline_type") or ""
    if not ptype.startswith("zavod"):
        return
    if checkpoint.get("status") != "completed":
        return

    stage = checkpoint.get("stage")
    artifacts = checkpoint.get("artifacts") or {}
    mode = artifacts.get("run_mode")
    recorded = {
        e["name"]: e
        for e in ((artifacts.get("production_ladder") or {}).get("sub_stages") or [])
        if isinstance(e, dict) and e.get("name")
    }

    if stage == "idea" and mode not in VALID_RUN_MODES:
        raise CheckpointValidationError(
            f"Run mode not locked at stage {stage!r} ({ptype}): artifacts.run_mode must be one of "
            f"{sorted(VALID_RUN_MODES)}. The Executive Producer asks supervised vs automatic up front "
            f"and carries it forward. Got {mode!r}."
        )

    # External gates: owner approval is mandatory in BOTH modes (automatic still stops here).
    for rung in _OWNER_ALWAYS_RUNGS:
        if rung in recorded and not recorded[rung].get("owner_approved"):
            raise CheckpointValidationError(
                f"Final delivery gate at stage {stage!r} ({ptype}): rung {rung!r} must be "
                f"owner_approved even in an automatic run (publish/spend/rights/delivery never auto-approve)."
            )

    # Supervised runs must show the per-rung freeze; automatic runs are exempt (they don't stop).
    if mode == "supervised":
        required = _required_ladder_sub_stages(ptype, stage)
        not_approved = [n for n in required if not recorded.get(n, {}).get("owner_approved")]
        if not_approved:
            raise CheckpointValidationError(
                f"Supervised run at stage {stage!r} ({ptype}) is missing owner approval on rung(s) "
                f"{not_approved}. In supervised mode every owner-gated sub-stage freezes for the owner; "
                f"record owner_approved: true once approved (or switch run_mode to automatic)."
            )


def validate_checkpoint(checkpoint: dict[str, Any]) -> None:
    """Validate checkpoint structure and canonical artifact payloads.

    Uses pipeline_type (if present) to resolve the valid stage list.
    Falls back to ALL_KNOWN_STAGES when pipeline_type is absent.
    """
    stage = checkpoint.get("stage")
    status = checkpoint.get("status")
    artifacts = checkpoint.get("artifacts")
    pipeline_type = checkpoint.get("pipeline_type")

    valid_stages = (
        set(get_pipeline_stages(pipeline_type)) if pipeline_type
        else ALL_KNOWN_STAGES
    )

    if not isinstance(stage, str) or stage not in valid_stages:
        raise CheckpointValidationError(
            f"Invalid stage: {stage!r} for pipeline {pipeline_type!r}. "
            f"Valid stages: {sorted(valid_stages)}"
        )
    if not isinstance(status, str):
        raise CheckpointValidationError(f"Invalid status: {status!r}")
    if not isinstance(artifacts, dict):
        raise CheckpointValidationError("Checkpoint artifacts must be a dictionary")

    _validate_artifacts_for_stage(stage, status, artifacts)

    try:
        jsonschema.validate(instance=checkpoint, schema=_load_checkpoint_schema())
    except jsonschema.ValidationError as exc:
        raise CheckpointValidationError(f"Checkpoint failed schema validation: {exc.message}") from exc

    # Content gates (glyph/continuity/brand-voice) run on BOTH read and write — they judge
    # the artifact itself, so a dirty payload is caught even when re-reading old data.
    _enforce_zavod_gates(checkpoint)


def enforce_zavod_write_contracts(checkpoint: dict[str, Any]) -> None:
    """Structural production contracts enforced only when WRITING a new checkpoint.

    Backward-compat: these contracts (ladder non-collapse, engine lane, run mode) describe
    how a stage may be *completed*, so they are write-time gates. Re-reading a legacy
    checkpoint written before these rules existed must NOT be retroactively rejected —
    `read_checkpoint` runs `validate_checkpoint` (schema + content gates) but not these.
    """
    _enforce_production_ladder(checkpoint)   # specialist ladder is non-collapsible
    _enforce_engine_lane(checkpoint)         # Remotion and Higgsfield lanes stay separate
    _enforce_run_mode(checkpoint)            # supervised vs automatic stay separated


def _checkpoint_path(pipeline_dir: Path, project_id: str, stage: str) -> Path:
    return pipeline_dir / project_id / f"checkpoint_{stage}.json"


def _decision_log_path(pipeline_dir: Path, project_id: str) -> Path:
    return pipeline_dir / project_id / "decision_log.json"


def _merge_decision_log(
    pipeline_dir: Path, project_id: str, new_log: dict[str, Any]
) -> None:
    """Append new decisions to the project-level decision log.

    Each stage may produce decisions. This function merges them into a
    single cumulative file so reviewers and the bench can inspect the
    full audit trail.
    """
    path = _decision_log_path(pipeline_dir, project_id)
    if path.exists():
        with open(path) as f:
            existing = json.load(f)
    else:
        existing = {
            "version": "1.0",
            "project_id": project_id,
            "decisions": [],
        }

    existing_ids = {d["decision_id"] for d in existing.get("decisions", [])}
    for decision in new_log.get("decisions", []):
        if decision.get("decision_id") not in existing_ids:
            existing["decisions"].append(decision)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)


def write_checkpoint(
    pipeline_dir: Path,
    project_id: str,
    stage: str,
    status: str,
    artifacts: dict[str, Any],
    *,
    pipeline_type: Optional[str] = None,
    style_playbook: Optional[str] = None,
    checkpoint_policy: str = "guided",
    human_approval_required: bool = False,
    human_approved: bool = False,
    review: Optional[dict] = None,
    cost_snapshot: Optional[dict] = None,
    error: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Path:
    """Write a checkpoint file for a pipeline stage."""
    valid_stages = (
        set(get_pipeline_stages(pipeline_type)) if pipeline_type
        else ALL_KNOWN_STAGES
    )
    if stage not in valid_stages:
        raise ValueError(
            f"Invalid stage: {stage!r} for pipeline {pipeline_type!r}. "
            f"Valid stages: {sorted(valid_stages)}"
        )

    checkpoint = {
        "version": "1.0",
        "project_id": project_id,
        "pipeline_type": pipeline_type or "unknown",
        "stage": stage,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checkpoint_policy": checkpoint_policy,
        "human_approval_required": human_approval_required,
        "human_approved": human_approved,
        "artifacts": artifacts,
    }
    if style_playbook is not None:
        checkpoint["style_playbook"] = style_playbook
    if review is not None:
        checkpoint["review"] = review
    if cost_snapshot is not None:
        checkpoint["cost_snapshot"] = cost_snapshot
    if error is not None:
        checkpoint["error"] = error
    if metadata is not None:
        checkpoint["metadata"] = metadata

    # If this checkpoint carries new decisions, prepare the reference before
    # validation, but do not write the project-level decision log until the
    # checkpoint itself has passed every schema and gate. This keeps failed
    # checkpoints from leaving half-accepted audit trails on disk.
    decision_log = artifacts.get("decision_log")
    if isinstance(decision_log, dict):
        log_ref = str(_decision_log_path(pipeline_dir, project_id))

        # Write decision_log_ref into proposal_packet and render_report
        # artifacts if they are present in this checkpoint.
        for artifact_key in ("proposal_packet", "render_report"):
            if artifact_key in artifacts and isinstance(artifacts[artifact_key], dict):
                plan_or_top = artifacts[artifact_key]
                # proposal_packet stores it under production_plan
                if artifact_key == "proposal_packet":
                    plan = plan_or_top.get("production_plan")
                    if isinstance(plan, dict):
                        plan["decision_log_ref"] = log_ref
                else:
                    plan_or_top["decision_log_ref"] = log_ref

    validate_checkpoint(checkpoint)
    # Write-time only: a new completed stage must satisfy the structural contracts.
    # (read_checkpoint deliberately does not, so legacy checkpoints still load.)
    enforce_zavod_write_contracts(checkpoint)

    if isinstance(decision_log, dict):
        _merge_decision_log(pipeline_dir, project_id, decision_log)

    path = _checkpoint_path(pipeline_dir, project_id, stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(checkpoint, f, indent=2)

    return path


def read_checkpoint(
    pipeline_dir: Path, project_id: str, stage: str
) -> Optional[dict[str, Any]]:
    """Read a checkpoint file. Returns None if not found."""
    path = _checkpoint_path(pipeline_dir, project_id, stage)
    if not path.exists():
        return None
    with open(path) as f:
        checkpoint = json.load(f)
    validate_checkpoint(checkpoint)
    return checkpoint


def get_latest_checkpoint(
    pipeline_dir: Path, project_id: str
) -> Optional[dict[str, Any]]:
    """Find the most recent checkpoint for a project (by file mtime)."""
    project_dir = pipeline_dir / project_id
    if not project_dir.exists():
        return None

    checkpoints = sorted(
        project_dir.glob("checkpoint_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not checkpoints:
        return None

    with open(checkpoints[0]) as f:
        checkpoint = json.load(f)
    validate_checkpoint(checkpoint)
    return checkpoint


def get_completed_stages(
    pipeline_dir: Path, project_id: str, pipeline_type: str | None = None
) -> list[str]:
    """Return list of stages that have a completed checkpoint.

    When pipeline_type is provided, only checks stages defined in that
    pipeline's manifest — preventing false positives from leftover
    checkpoints of a different pipeline type.
    """
    stages_to_check = get_pipeline_stages(pipeline_type)
    completed = []
    for stage in stages_to_check:
        cp = read_checkpoint(pipeline_dir, project_id, stage)
        if cp and cp.get("status") == "completed":
            completed.append(stage)
    return completed


def get_next_stage(
    pipeline_dir: Path, project_id: str, pipeline_type: str | None = None
) -> Optional[str]:
    """Determine the next stage to run based on completed checkpoints.

    Uses pipeline-specific stage order so that pipelines with different
    stage sequences (e.g. cinematic vs explainer) progress correctly.
    """
    stages = get_pipeline_stages(pipeline_type) if pipeline_type else STAGES
    completed = set(get_completed_stages(pipeline_dir, project_id, pipeline_type))
    for stage in stages:
        if stage not in completed:
            return stage
    return None
