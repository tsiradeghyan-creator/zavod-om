"""Checkpoint writer/reader for pipeline state persistence.

Each stage writes a checkpoint after completion. The orchestrator uses
checkpoints to resume pipelines and to present state at human checkpoints.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
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

    # Fail-closed: a zavod-prefixed but unknown/malformed pipeline_type (casing, whitespace,
    # zero-width, homoglyph) must BLOCK here, not silently fall back to the generic stage
    # list — that fallback is the side door that bypasses the pipeline allowlist through
    # stage navigation (#1). For a valid zavod type we also look it up by its canonical form
    # so stray casing/whitespace still resolves to the real manifest, not the fallback.
    is_zavod = _is_zavod_pipeline(pipeline_type)  # raises CheckpointValidationError on unknown zavod-*
    lookup = pipeline_type.strip().casefold() if is_zavod else pipeline_type

    try:
        from lib.pipeline_loader import load_pipeline, get_stage_order
        manifest = load_pipeline(lookup)
        return get_stage_order(manifest)
    except Exception:
        # Graceful fallback only for a genuinely non-zavod pipeline whose manifest is absent.
        return list(STAGES)

CHECKPOINT_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "checkpoints"
    / "checkpoint.schema.json"
)


ZAVOD_PIPELINE_TYPES = frozenset({
    "zavod-reel",
    "zavod-carousel",
    "zavod-promo",
})


def _is_zavod_pipeline(pipeline_type: str | None) -> bool:
    """Canonical test for whether zavod gates apply to a pipeline_type.

    The 2026-07-04 red-team showed the bare ``ptype.startswith("zavod")`` guard was
    case-sensitive and whitespace-sensitive: ``"Zavod-reel"``, ``"ZAVOD-reel"`` or
    ``" zavod-reel"`` silently disabled EVERY gate. Canonicalize (strip + casefold)
    before the prefix test so those variants of a real zavod pipeline are still gated.
    Non-zavod pipelines (animation, cinematic, …) correctly remain ungated.
    """
    if not pipeline_type:
        return False
    canonical = pipeline_type.strip().casefold()
    if canonical in ZAVOD_PIPELINE_TYPES:
        return True
    if canonical.startswith("zavod"):
        raise CheckpointValidationError(
            f"unknown Zavod pipeline {pipeline_type!r}; expected one of {sorted(ZAVOD_PIPELINE_TYPES)}")
    return False


def _canonical_pipeline_type(pipeline_type: str | None) -> str | None:
    """Canonical storage form of a pipeline_type.

    A valid zavod pipeline is stored by its canonical id (strip + casefold) so a stray-cased
    or whitespace-padded variant (``" zavod-reel "``) can never persist raw. Otherwise every
    downstream consumer that looks the manifest up by the stored value — the production ladder
    requirement most dangerously — fails the lookup, silently gets an empty result, and the
    stage closes without its specialist ladder (#11, 2026-07-05). Non-zavod types are returned
    unchanged; an unknown zavod-* is left for _is_zavod_pipeline to reject at the gate.
    """
    if not pipeline_type:
        return pipeline_type
    canonical = pipeline_type.strip().casefold()
    return canonical if canonical in ZAVOD_PIPELINE_TYPES else pipeline_type


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
    if not _is_zavod_pipeline(ptype):
        return
    if checkpoint.get("status") not in {"completed", "awaiting_human"}:
        return

    stage = checkpoint.get("stage")
    artifacts = checkpoint.get("artifacts") or {}

    # Glyph gate on EVERY text surface of EVERY artifact, not just the stage-specific fields
    # (#8, 2026-07-05). An invisible/zero-width or homoglyph character hiding in a
    # metadata.caption, an asset filename, a prompt, or a subtitle must be caught wherever it
    # appears — the per-field checks (scene_plan text_policy.text, script strings) left the
    # other surfaces open. The gate is a no-op on pure-ASCII/single-script strings (paths,
    # ids, enums), so sweeping every string leaf is safe and closes the gap.
    from lib.armenian_glyph_gate import gate as _glyph_gate
    for _name, _art in artifacts.items():
        # Check the artifact NAME (top-level key) too, not only its contents — a poisoned
        # artifact name rode along unchecked otherwise (2026-07-06 dry re-probe).
        _viol = list(_glyph_gate(_name)["violations"]) if isinstance(_name, str) else []
        _viol += _glyph_gate(_art)["violations"]  # walks keys AND values of the whole artifact
        if _viol:
            _detail = "; ".join(x["reason"] for x in _viol)
            raise CheckpointValidationError(
                f"Gate block at stage {stage!r} ({ptype}): glyph violation in "
                f"artifacts.{_name}: {_detail}"
            )

    # Lazy import: keeps the spine importable without the gate libs, and avoids any cycle.
    from lib.gatechain import (
        run_bench_gates,
        run_story_gates,
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
    if stage == "script":
        story_bible = artifacts.get("story_bible")
        if checkpoint.get("status") == "completed" and not isinstance(story_bible, dict):
            raise CheckpointValidationError(
                f"Gate block at stage {stage!r} ({ptype}): missing artifacts.story_bible — "
                "a Zavod script stage cannot close without the dramaturgy story bible."
            )
        if isinstance(story_bible, dict):
            result = run_story_gates(story_bible)
        if result is not None and not result.get("ok"):
            pass
        elif "script" in artifacts:
            result = run_script_gates("\n".join(_all_strings(artifacts["script"])))
    elif stage == "scene_plan" and "scene_plan" in artifacts:
        result = run_scene_plan_gates(artifacts["scene_plan"])
    elif stage == "edit" and "edit_decisions" in artifacts:
        # Delivery-promise preservation: a motion-led promise must not silently become
        # a slideshow. The locked promise travels in artifacts.delivery_promise and is
        # mandatory for Zavod edit-stage closure; omission must not become a bypass.
        if not isinstance(artifacts.get("delivery_promise"), dict):
            raise CheckpointValidationError(
                f"Gate block at stage {stage!r} ({ptype}): missing artifacts.delivery_promise — "
                "Zavod edit checkpoints must carry the locked delivery promise."
            )
        result = run_edit_gates(artifacts["edit_decisions"], artifacts.get("delivery_promise"))
    elif stage == "compose":
        # Continuity proof is mandatory to CLOSE a Zavod compose stage. The
        # render_report.continuity_reports field must be present as a list (a silently-absent
        # field must not become a bypass, mirroring the edit-stage delivery_promise rule).
        # Tightened 2026-07-06 (#5): if the render produced outputs, the list must be
        # NON-empty — every rendered clip has to be continuity-checked, so "5 clips, zero
        # continuity reports" no longer closes. An empty list is allowed only when there are
        # no outputs. awaiting_human may still be mid-flight, so only completion is gated.
        rr = artifacts.get("render_report")
        has_reports_field = isinstance(rr, dict) and isinstance(rr.get("continuity_reports"), list)
        if checkpoint.get("status") == "completed":
            if not has_reports_field:
                raise CheckpointValidationError(
                    f"Gate block at stage {stage!r} ({ptype}): missing render_report.continuity_reports — "
                    "a Zavod compose stage cannot close without a continuity report list."
                )
            outputs = rr.get("outputs") or []
            reports_list = rr.get("continuity_reports") or []
            if outputs and not reports_list:
                raise CheckpointValidationError(
                    f"Gate block at stage {stage!r} ({ptype}): render_report declares {len(outputs)} "
                    "output(s) but no continuity_reports — every rendered output must be continuity-checked."
                )
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
        # Fail-closed for zavod: a zavod pipeline whose manifest cannot be resolved must not
        # silently yield an empty ladder requirement — that would let the stage close without
        # its specialist rungs. Non-zavod pipelines keep the lenient empty default.
        if _is_zavod_pipeline(pipeline_type):
            raise CheckpointValidationError(
                f"cannot resolve production-ladder requirements for zavod pipeline "
                f"{pipeline_type!r}: manifest unavailable"
            )
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
    if not _is_zavod_pipeline(ptype):
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
    if not _is_zavod_pipeline(ptype):
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
    if not _is_zavod_pipeline(ptype):
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


def _enforce_canon_guard(checkpoint: dict[str, Any], project_dir: Path | str | None) -> None:
    """Wire lib/canon_guard.py into the write seam.

    The script stage freezes the current canon snapshot. After that, any changed
    bible/look/canon-secret file blocks stage closure until canon-revalidation.md
    is newer than the drift. This is write-time only because it depends on the
    project directory and should not retroactively reject legacy reads.
    """
    ptype = checkpoint.get("pipeline_type") or ""
    if not _is_zavod_pipeline(ptype) or project_dir is None:
        return
    if checkpoint.get("status") != "completed":
        return

    stage = checkpoint.get("stage")
    from lib.canon_guard import FREE_STAGES, check as canon_check, lock as canon_lock

    project_dir_s = str(project_dir)
    if stage in FREE_STAGES:
        canon_lock(project_dir_s)
        return

    result = canon_check(project_dir_s, stage)
    if not result.get("ok"):
        raise CheckpointValidationError(
            f"Canon guard block at stage {stage!r} ({ptype}): {result.get('action') or result}"
        )
    # After a clean post-script closure, refresh the lock to the validated canon state.
    canon_lock(project_dir_s)


def _check_canon_guard_readonly(checkpoint: dict[str, Any], project_dir: Path | str | None) -> None:
    """Read-only canon drift check for the RESUME path.

    Same block condition as _enforce_canon_guard, but it must never call canon_lock():
    resuming/inspecting a checkpoint must not mutate the canon snapshot. Turning a read into
    a lock write would let a resume silently 'bless' drifted canon (the #6 side-effect trap).
    """
    ptype = checkpoint.get("pipeline_type") or ""
    if not _is_zavod_pipeline(ptype) or project_dir is None:
        return
    if checkpoint.get("status") != "completed":
        return
    stage = checkpoint.get("stage")
    from lib.canon_guard import FREE_STAGES, check as canon_check

    if stage in FREE_STAGES:
        return
    result = canon_check(str(project_dir), stage)
    if not result.get("ok"):
        raise CheckpointValidationError(
            f"Canon guard block on resume at stage {stage!r} ({ptype}): {result.get('action') or result}"
        )


def _resolve_artifact_path(project_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    return path if path.is_absolute() else project_dir / path


# #5 content validation: an existing, non-empty file is not proof of real media. A .mp4 full
# of garbage bytes, a text file renamed .mp4, or a truncated render must not close a stage.
# We probe the actual content with ffprobe, keyed on the asset's declared type.
_PROBE_VIDEO = frozenset({"video", "animation"})
_PROBE_AUDIO = frozenset({"audio", "narration", "music", "sfx"})
_PROBE_IMAGE = frozenset({"image", "diagram"})
_PROBE_KINDS = _PROBE_VIDEO | _PROBE_AUDIO | _PROBE_IMAGE
# subtitle / code_snippet / font / lut are data files — the non-empty regular-file check is the
# right bar for them; they carry no decodable A/V stream to probe.


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _media_defect(path: Path, kind: str) -> str | None:
    """Return a problem description if `path` is not valid media of `kind`, else None.

    Uses ffprobe to inspect real streams. Callers must confirm ffprobe is available first.
    """
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-show_format", str(path)],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"ffprobe failed to run: {exc}"
    if proc.returncode != 0:
        return "not decodable by ffprobe (corrupt or not real media)"
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return "ffprobe returned unreadable output"

    streams = data.get("streams") or []
    fmt = data.get("format") or {}
    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]

    if kind in _PROBE_VIDEO:
        if not video:
            return "declared video but ffprobe found no video stream"
        s0 = video[0]
        if not (int(s0.get("width") or 0) > 0 and int(s0.get("height") or 0) > 0):
            return "video stream has no dimensions"
        if _safe_float(fmt.get("duration")) <= 0 and _safe_float(s0.get("duration")) <= 0:
            return "video has zero/unknown duration"
        return None
    if kind in _PROBE_AUDIO:
        if not audio:
            return "declared audio but ffprobe found no audio stream"
        if _safe_float(fmt.get("duration")) <= 0 and _safe_float(audio[0].get("duration")) <= 0:
            return "audio has zero/unknown duration"
        return None
    if kind in _PROBE_IMAGE:
        # A still decodes as a single-frame video stream (png/mjpeg/webp); require dimensions,
        # not duration.
        if not video:
            return "declared image but ffprobe could not decode it"
        s0 = video[0]
        if not (int(s0.get("width") or 0) > 0 and int(s0.get("height") or 0) > 0):
            return "image has no dimensions"
        return None
    return None


def _enforce_artifact_path_existence(
    checkpoint: dict[str, Any],
    project_dir: Path | str | None,
) -> None:
    """Reject completed asset/render checkpoints that point at phantom files.

    This deliberately lives in the checkpoint seam rather than the JSON schemas:
    schemas can require a path field, but only the write seam knows the project
    directory where relative paths must physically exist.
    """
    ptype = checkpoint.get("pipeline_type") or ""
    if not _is_zavod_pipeline(ptype) or project_dir is None:
        return
    if checkpoint.get("status") != "completed":
        return

    stage = checkpoint.get("stage")
    artifacts = checkpoint.get("artifacts") or {}
    project_dir_p = Path(project_dir)

    if stage == "assets":
        manifest = artifacts.get("asset_manifest") or {}
        entries = manifest.get("assets") or []
        label = "asset_manifest.assets"
    elif stage == "compose":
        report = artifacts.get("render_report") or {}
        entries = report.get("outputs") or []
        label = "render_report.outputs"
    else:
        return

    # An empty entry list means the stage closed without a single real artifact — that is
    # itself a phantom completion, not a pass. (2026-07-04 red-team: empty asset list slid by.)
    real_entries = [e for e in entries if isinstance(e, dict) and isinstance(e.get("path"), str)]
    if not real_entries:
        raise CheckpointValidationError(
            f"Artifact existence gate at stage {stage!r} ({ptype}): {label} declares no real "
            "artifact path — a stage cannot close 'completed' with zero produced files."
        )

    try:
        project_root = project_dir_p.resolve()
    except OSError:
        project_root = project_dir_p

    missing: list[str] = []
    degenerate: list[str] = []
    for entry in real_entries:
        raw = entry["path"]
        resolved = _resolve_artifact_path(project_dir_p, raw)
        # Require a real, non-empty regular file — not just .exists().
        # 2026-07-04 red-team: a 0-byte file, a symlink to /dev/null, or a directory all
        # passed the bare exists() check.
        if not resolved.exists():
            missing.append(raw)
        elif not resolved.is_file():
            degenerate.append(f"{raw} (not a regular file)")
        elif resolved.stat().st_size == 0:
            degenerate.append(f"{raw} (0 bytes)")
        else:
            # Provenance: a symlink whose real target escapes the project directory is not a
            # pipeline-produced asset (2026-07-04 probe: a link to /etc/hosts was accepted).
            real = resolved.resolve()
            if resolved.is_symlink() and project_root not in (real, *real.parents):
                degenerate.append(f"{raw} (symlink escapes project dir → {real})")

    problems = missing + degenerate
    if problems:
        raise CheckpointValidationError(
            f"Artifact existence gate at stage {stage!r} ({ptype}): {label} path(s) not real "
            f"non-empty files: {problems}"
        )

    # #5: content validation. Every real file above still has to BE what it claims — a decodable
    # video/audio/image of its declared type. Data types (subtitle/font/lut/code) carry no stream
    # and are covered by the non-empty check above.
    probe_targets = []
    for entry in real_entries:
        kind = (entry.get("type") if stage == "assets" else "video") or "video"
        if kind in _PROBE_KINDS:
            probe_targets.append((entry["path"], _resolve_artifact_path(project_dir_p, entry["path"]), kind))

    if probe_targets and shutil.which("ffprobe") is None:
        # A final render must never be accepted unverified. Upstream asset stages degrade to the
        # existence checks so a probe-less box can still draft — the compose gate is the backstop.
        if stage == "compose":
            raise CheckpointValidationError(
                f"Media validation gate at stage 'compose' ({ptype}): ffprobe not found — a final "
                "render cannot be accepted without content verification. Install ffmpeg/ffprobe."
            )
        return

    invalid = []
    for raw, resolved, kind in probe_targets:
        defect = _media_defect(resolved, kind)
        if defect:
            invalid.append(f"{raw} ({kind}: {defect})")
    if invalid:
        raise CheckpointValidationError(
            f"Media validation gate at stage {stage!r} ({ptype}): declared media is not valid "
            f"content of its type: {invalid}"
        )


def _known_scene_ids(project_dir: Path) -> set[str] | None:
    """Scene ids declared by the project's completed scene_plan checkpoint.

    Returns None when there is no scene_plan to check against — a partial run or an
    isolated stage write — so referential integrity is only enforced where it is
    actually verifiable, never fabricated.
    """
    sp_path = project_dir / "checkpoint_scene_plan.json"
    if not sp_path.exists():
        return None
    try:
        with open(sp_path) as f:
            sp = json.load(f)
    except Exception:
        return None
    scene_plan = (sp.get("artifacts") or {}).get("scene_plan")
    if not isinstance(scene_plan, dict):
        return None
    return {s.get("id") for s in scene_plan.get("scenes", []) if isinstance(s, dict)}


def _known_asset_ids(project_dir: Path) -> set[str] | None:
    """Asset ids declared by the project's assets checkpoint (None when absent — see
    _known_scene_ids for why unverifiable state is skipped, not fabricated)."""
    ap = project_dir / "checkpoint_assets.json"
    if not ap.exists():
        return None
    try:
        with open(ap) as f:
            cp = json.load(f)
    except Exception:
        return None
    manifest = (cp.get("artifacts") or {}).get("asset_manifest")
    if not isinstance(manifest, dict):
        return None
    return {a.get("id") for a in manifest.get("assets", []) if isinstance(a, dict)}


# Free-form subtrees that carry arbitrary user data — an ``asset_id`` there is a label
# (e.g. an analytics tag), NOT a pipeline reference, so it must not be resolved as one.
_REF_FREEFORM_KEYS = frozenset({"metadata"})


def _collect_by_key(obj: Any, key: str) -> list[str]:
    """Every string value stored under ``key`` anywhere in a nested structure, excluding
    free-form subtrees (see _REF_FREEFORM_KEYS) where the same key name is not a reference."""
    found: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _REF_FREEFORM_KEYS:
                continue  # arbitrary user data — not a semantic reference surface
            if k == key and isinstance(v, str):
                found.append(v)
            else:
                found += _collect_by_key(v, key)
    elif isinstance(obj, list):
        for v in obj:
            found += _collect_by_key(v, key)
    return found


def _enforce_referential_integrity(checkpoint: dict[str, Any], project_dir: Path | str | None) -> None:
    """Cross-artifact referential integrity (write-time, zavod only).

    A schema-valid artifact can still reference entities that do not exist: an asset_manifest
    asset naming a scene_id absent from the scene_plan, or an edit naming an asset_id absent
    from the asset_manifest (#7). JSON Schema validates each artifact in isolation; this checks
    the links between them. Scoped to what persisted state can prove — when the referenced prior
    checkpoint exists — so an unverifiable partial run is skipped, never fabricated.
    """
    if project_dir is None or not _is_zavod_pipeline(checkpoint.get("pipeline_type") or ""):
        return
    project_dir = Path(project_dir)
    stage = checkpoint.get("stage")
    artifacts = checkpoint.get("artifacts") or {}

    if stage == "assets":
        manifest = artifacts.get("asset_manifest")
        if not isinstance(manifest, dict):
            return
        scene_ids = _known_scene_ids(project_dir)
        if scene_ids is None:
            return
        for asset in manifest.get("assets", []):
            if not isinstance(asset, dict):
                continue
            sid = asset.get("scene_id")
            if sid not in scene_ids:
                raise CheckpointValidationError(
                    f"Referential integrity: asset {asset.get('id')!r} references scene_id {sid!r} "
                    f"which is not in the scene_plan (known: {sorted(x for x in scene_ids if x)})."
                )

    elif stage == "edit":
        edits = artifacts.get("edit_decisions")
        if not isinstance(edits, dict):
            return
        asset_ids = _known_asset_ids(project_dir)
        if asset_ids is None:
            return
        # Explicit asset_id references (overlays, audio, subtitles, …) must resolve. cuts[].source
        # is overloaded (file path OR asset id), so it is left out to avoid false positives.
        for ref in _collect_by_key(edits, "asset_id"):
            if ref not in asset_ids:
                raise CheckpointValidationError(
                    f"Referential integrity: edit_decisions references asset_id {ref!r} which is "
                    f"not in the asset_manifest (known: {sorted(x for x in asset_ids if x)})."
                )


def enforce_zavod_write_contracts(
    checkpoint: dict[str, Any],
    *,
    project_dir: Path | str | None = None,
) -> None:
    """Structural production contracts enforced only when WRITING a new checkpoint.

    Backward-compat: these contracts (ladder non-collapse, engine lane, run mode) describe
    how a stage may be *completed*, so they are write-time gates. Re-reading a legacy
    checkpoint written before these rules existed must NOT be retroactively rejected —
    `read_checkpoint` runs `validate_checkpoint` (schema + content gates) but not these.
    """
    _enforce_production_ladder(checkpoint)   # specialist ladder is non-collapsible
    _enforce_engine_lane(checkpoint)         # Remotion and Higgsfield lanes stay separate
    _enforce_run_mode(checkpoint)            # supervised vs automatic stay separated
    _enforce_canon_guard(checkpoint, project_dir)  # mid-pipeline canon drift requires revalidation
    _enforce_artifact_path_existence(checkpoint, project_dir)  # manifests must point at real files
    _enforce_referential_integrity(checkpoint, project_dir)  # cross-artifact links must resolve (#7)


def _enforce_resume_contracts(checkpoint: dict[str, Any], project_dir: Path | str | None) -> None:
    """Fail-closed re-validation for RESUME (not plain read).

    A completed checkpoint being resumed from must still satisfy the same structural contracts
    it satisfied at write time — otherwise a hand-edited, downgraded, or drifted checkpoint (or
    one whose artifacts were deleted after the fact) could silently continue a run. Unlike the
    write contracts, this path is side-effect free: the canon check is read-only (no lock write),
    so resuming/inspecting never mutates project state.
    """
    _enforce_production_ladder(checkpoint)          # specialist ladder still non-collapsed
    _enforce_engine_lane(checkpoint)                # engine lane still consistent
    _enforce_run_mode(checkpoint)                   # run mode still consistent
    _check_canon_guard_readonly(checkpoint, project_dir)      # canon drift — read-only
    _enforce_artifact_path_existence(checkpoint, project_dir)  # files real + valid media (#5)
    _enforce_referential_integrity(checkpoint, project_dir)   # cross-artifact links still resolve (#7)


def _checkpoint_path(pipeline_dir: Path, project_id: str, stage: str) -> Path:
    return pipeline_dir / project_id / f"checkpoint_{stage}.json"


def _decision_log_path(pipeline_dir: Path, project_id: str) -> Path:
    return pipeline_dir / project_id / "decision_log.json"


def _atomic_write_json(path: Path, data: Any) -> None:
    """Persist ``data`` as JSON atomically.

    Serialize to a temp file in the same directory, fsync it, then ``os.replace()``
    onto the destination. Because the destination is only ever swapped by an atomic
    rename — never opened with ``"w"`` (which truncates in place) — a crash mid-write
    leaves the previous valid file fully intact instead of a truncated/corrupt one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # Unique temp name (pid + uuid): pid alone collides when two threads of the SAME process
    # write the same project/stage concurrently — they clobbered one temp file and most
    # writes died with FileNotFoundError (2026-07-06 dry re-probe).
    tmp = path.parent / f".{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}"
    try:
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # atomic on the same filesystem
        # Durability: fsync the parent directory so the rename itself survives a crash/power
        # loss, not just the file contents. Best-effort — some platforms cannot fsync a dir.
        try:
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    finally:
        if tmp.exists():
            tmp.unlink()


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

    _atomic_write_json(path, existing)


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
    # Canonicalize at the source so a stray-cased / whitespace-padded zavod type is never
    # persisted raw — every downstream consumer then sees the canonical id (#11).
    pipeline_type = _canonical_pipeline_type(pipeline_type)
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
    enforce_zavod_write_contracts(checkpoint, project_dir=pipeline_dir / project_id)

    # Persist the carrying checkpoint FIRST, and atomically. The stage's decision is
    # already embedded in checkpoint["artifacts"]["decision_log"], so the project-level
    # decision_log.json is a derived aggregate. Writing the checkpoint first means a crash
    # between the two writes can at worst drop an audit-log projection (rebuildable from the
    # checkpoint) — never leave a decision recorded with no carrying checkpoint (the
    # split-brain failure mode). Both writes are atomic, so neither can be left truncated.
    path = _checkpoint_path(pipeline_dir, project_id, stage)
    _atomic_write_json(path, checkpoint)

    if isinstance(decision_log, dict):
        _merge_decision_log(pipeline_dir, project_id, decision_log)

    return path


def read_checkpoint(
    pipeline_dir: Path, project_id: str, stage: str,
    *, verify_artifacts: bool = False,
) -> Optional[dict[str, Any]]:
    """Read a checkpoint file. Returns None if not found.

    ``verify_artifacts=True`` additionally re-checks that a completed asset/compose
    checkpoint's declared files still physically exist — used on the resume path so a
    checkpoint written when a file existed (then deleted), or a hand-edited checkpoint
    file, cannot silently resume with phantom artifacts (2026-07-04 red-team, angle 2).
    Plain reads (inspection, get_completed_stages) stay lenient so legacy checkpoints load.
    """
    path = _checkpoint_path(pipeline_dir, project_id, stage)
    if not path.exists():
        return None
    with open(path) as f:
        checkpoint = json.load(f)
    validate_checkpoint(checkpoint)
    if verify_artifacts:
        _enforce_artifact_path_existence(checkpoint, pipeline_dir / project_id)
    return checkpoint


def get_latest_checkpoint(
    pipeline_dir: Path, project_id: str, *, strict_resume: bool = False
) -> Optional[dict[str, Any]]:
    """Find the most recent checkpoint for a project (by file mtime).

    ``strict_resume=True`` runs the full fail-closed resume re-validation (structural
    contracts + read-only canon drift + artifact existence/media) instead of the artifact
    check alone. See resume_checkpoint() for the recommended resume entry point.
    """
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
    # Resume entry point: re-verify the state before handing it back as the point to resume
    # from (2026-07-04 red-team). strict_resume adds structural + read-only canon re-checks (#6).
    if strict_resume:
        _enforce_resume_contracts(checkpoint, project_dir)
    else:
        _enforce_artifact_path_existence(checkpoint, project_dir)
    return checkpoint


def resume_checkpoint(
    pipeline_dir: Path, project_id: str, stage: str | None = None
) -> Optional[dict[str, Any]]:
    """Load a checkpoint to RESUME from, fully re-validated and fail-closed.

    This is the entry point a runtime should use to continue a run: it re-runs the structural
    contracts (ladder, engine lane, run mode), a read-only canon drift check, and the artifact
    existence/media checks against the persisted state. A hand-edited, downgraded, canon-drifted,
    or artifact-missing checkpoint is refused rather than silently resumed. Side-effect free —
    unlike write contracts, it never writes a canon lock.

    stage=None resumes from the most recent checkpoint; passing a stage resumes that specific one.
    """
    project_dir = pipeline_dir / project_id
    if stage is not None:
        path = _checkpoint_path(pipeline_dir, project_id, stage)
        if not path.exists():
            return None
        with open(path) as f:
            checkpoint = json.load(f)
        validate_checkpoint(checkpoint)
        _enforce_resume_contracts(checkpoint, project_dir)
        return checkpoint
    return get_latest_checkpoint(pipeline_dir, project_id, strict_resume=True)


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
