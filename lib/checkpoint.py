"""Checkpoint writer/reader for pipeline state persistence.

Each stage writes a checkpoint after completion. The orchestrator uses
checkpoints to resume pipelines and to present state at human checkpoints.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import unicodedata
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


def _merge_manifest_stage_artifacts() -> None:
    """Make the checkpoint spine manifest-driven: extend CANONICAL_STAGE_ARTIFACTS with every
    stage declared in any pipeline manifest (canonical artifact = the stage's first ``produces``).
    Without this the spine only knew a hardcoded 9 stages, so pipelines with extra stages —
    character-animation's character_design/rig_plan — could not be checkpoint-written at all
    (KeyError), which also left character_id referential integrity with nothing to resolve
    against (#B, 2026-07-06). Hardcoded entries win; an unloadable manifest is skipped."""
    import glob
    try:
        from lib.pipeline_loader import load_pipeline
    except Exception:
        return
    pdefs = Path(__file__).resolve().parent.parent / "pipeline_defs"
    for path in sorted(glob.glob(str(pdefs / "*.yaml"))):
        try:
            manifest = load_pipeline(Path(path).stem)
        except Exception:
            continue
        for st in manifest.get("stages", []):
            produces = st.get("produces") or []
            if st.get("name") and produces:
                CANONICAL_STAGE_ARTIFACTS.setdefault(st["name"], produces[0])


# The hardcoded core, kept so the spine can be rebuilt from scratch (manifest add AND remove).
_CORE_STAGE_ARTIFACTS = dict(CANONICAL_STAGE_ARTIFACTS)
_merge_manifest_stage_artifacts()

# Now that the spine knows every pipeline's stages, the "all known stages" fallback set
# (used when a write/validate has no explicit pipeline_type) covers them too.
ALL_KNOWN_STAGES = frozenset(CANONICAL_STAGE_ARTIFACTS)


def reset_pipeline_caches() -> None:
    """Rebuild all manifest-derived state from disk. Call after adding OR removing a pipeline
    manifest at runtime (e.g. the capability-extension flow) so the structural gates —
    ordering, artifact-existence, canonical-artifact presence, manifest membership — see the
    change immediately instead of after a process restart (#4 round-5). Without this the
    lru_cached manifest set and the import-time stage map go split-brain: a freshly added
    pipeline would bypass the whole structural spine until restart.
    """
    global ALL_KNOWN_STAGES
    _manifest_pipeline_types.cache_clear()
    CANONICAL_STAGE_ARTIFACTS.clear()          # in place — external imports keep their ref
    CANONICAL_STAGE_ARTIFACTS.update(_CORE_STAGE_ARTIFACTS)
    _merge_manifest_stage_artifacts()
    ALL_KNOWN_STAGES = frozenset(CANONICAL_STAGE_ARTIFACTS)

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
    except CheckpointValidationError:
        raise
    except Exception as exc:
        # A manifest that EXISTS but fails to load (schema-invalid, unparseable) is a
        # CONFIGURATION ERROR — fail closed. Silently substituting the generic stage order
        # mis-sequences the real pipeline and false-blocks its true first stage (#2 round-5:
        # documentary-montage / screen-demo both start at 'idea', not research/proposal).
        # A zavod pipeline additionally NEVER falls back — its manifest is its allowlist
        # entry, so a deleted/renamed zavod manifest is a downgrade attempt, not a generic
        # pipeline (round-6 #1, external audit №2). Only a non-zavod pipeline with NO
        # manifest at all gets the lenient generic fallback.
        if is_zavod or _is_manifest_pipeline(pipeline_type):
            raise CheckpointValidationError(
                f"Pipeline {pipeline_type!r} has (or must have) a manifest that failed to "
                f"load — fix/restore the manifest; the generic stage order will not be "
                f"substituted. ({exc})"
            ) from exc
        return list(STAGES)

CHECKPOINT_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "checkpoints"
    / "checkpoint.schema.json"
)


ZAVOD_PIPELINE_TYPES = frozenset({
    "zavod-reel",
    "zavod-reel-fast",
    "zavod-carousel",
    "zavod-promo",
    "zavod-content",
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


@lru_cache(maxsize=1)
def _manifest_pipeline_types() -> frozenset[str]:
    """Every pipeline that has a manifest in pipeline_defs/ — the set whose runs are
    structurally governed (stage order, artifact existence), zavod or not."""
    pdefs = Path(__file__).resolve().parent.parent / "pipeline_defs"
    return frozenset(p.stem for p in pdefs.glob("*.yaml"))


def _is_manifest_pipeline(pipeline_type: str | None) -> bool:
    """True when pipeline_type names a manifest-driven pipeline (canonical form).

    Round-4 (#11.1): ordering and artifact-existence were zavod-only, so a
    character-animation compose could be completed first, with a phantom render, and resume.
    Structural run-integrity applies to every manifest pipeline; brand-specific gates
    (glyph/bench/ladder/engine) stay scoped to their packs.
    """
    if not pipeline_type:
        return False
    return pipeline_type.strip().casefold() in _manifest_pipeline_types()


def _manifest_pin(pipeline_type: str | None) -> dict[str, Any] | None:
    """Pin of the manifest a checkpoint is being written under (round-6 #1, audit №2).

    The manifest-pipeline set is a live filesystem glob, so deleting/renaming a manifest
    between runs silently reclassified the pipeline as generic and downgraded its stage
    order — the write-time fail-closed rule never fired because, to a fresh process, the
    pipeline never "had" a manifest. The checkpoint itself is the durable witness: it
    records the manifest's content hash and the stage order it was written under, and
    _enforce_manifest_pin() refuses navigation/resume when that witness no longer matches.
    """
    if not _is_manifest_pipeline(pipeline_type):
        return None
    canonical = pipeline_type.strip().casefold()
    manifest_path = Path(__file__).resolve().parent.parent / "pipeline_defs" / f"{canonical}.yaml"
    return {
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "stage_order": get_pipeline_stages(canonical),
    }


def _enforce_manifest_pin(checkpoint: dict[str, Any]) -> None:
    """A pinned checkpoint refuses to advance under a vanished or re-sequenced manifest.

    Presence is mandatory: the pipeline must still resolve as a manifest pipeline. Ordering
    is mandatory: the current manifest's stage order must equal the pinned one — a mid-project
    re-sequencing is an owner decision, not a silent resume. The content hash is recorded for
    provenance but not enforced alone, so a cosmetic manifest edit does not block projects.
    Checkpoints written before pinning existed carry no pin and stay loadable (legacy).
    """
    pin = checkpoint.get("manifest_pin")
    if not isinstance(pin, dict):
        return
    ptype = checkpoint.get("pipeline_type")
    if not _is_manifest_pipeline(ptype):
        raise CheckpointValidationError(
            f"checkpoint for {checkpoint.get('project_id')!r}/{checkpoint.get('stage')!r} was "
            f"written under a manifest for pipeline {ptype!r} that no longer exists — restore "
            f"pipeline_defs/{ptype}.yaml; the generic stage order will not be substituted."
        )
    current = get_pipeline_stages(ptype)
    if current != pin.get("stage_order"):
        raise CheckpointValidationError(
            f"pipeline {ptype!r} manifest stage order changed since checkpoint "
            f"{checkpoint.get('stage')!r} was written (pinned {pin.get('stage_order')}, "
            f"now {current}) — mid-project re-sequencing requires an explicit owner "
            f"decision, not a silent resume."
        )


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
    if canonical in ZAVOD_PIPELINE_TYPES or canonical in _manifest_pipeline_types():
        return canonical
    return pipeline_type


class CheckpointValidationError(ValueError):
    """Raised when a checkpoint or its canonical artifacts are invalid."""


@lru_cache(maxsize=1)
def _load_checkpoint_schema() -> dict[str, Any]:
    with open(CHECKPOINT_SCHEMA_PATH) as f:
        return json.load(f)


def _stage_declared_produces(pipeline_type: str | None, stage: str) -> list[str]:
    """The artifacts a pipeline manifest declares a stage produces (empty when no manifest)."""
    if not pipeline_type:
        return []
    try:
        from lib.pipeline_loader import load_pipeline
        manifest = load_pipeline(_canonical_pipeline_type(pipeline_type))
    except Exception:
        return []
    for st in manifest.get("stages", []):
        if st.get("name") == stage:
            return list(st.get("produces") or [])
    return []


def _validate_artifacts_for_stage(
    stage: str,
    status: str,
    artifacts: dict[str, Any],
    pipeline_type: str | None = None,
) -> None:
    required_artifact = CANONICAL_STAGE_ARTIFACTS.get(stage)
    if required_artifact and status in {"completed", "awaiting_human"}:
        if required_artifact not in artifacts:
            raise CheckpointValidationError(
                f"Stage {stage!r} with status {status!r} must include "
                f"canonical artifact {required_artifact!r}"
            )
        # Fail-closed on ANY declared-but-unschematized produce, not just the canonical (first)
        # one. A manifest with produces:[script, unregistered_blob] otherwise smuggles the
        # 'unregistered_blob' payload past the validation loop below, which skips unknown names
        # (#3 round-5). An artifact that cannot be validated cannot close the stage.
        for produced in (_stage_declared_produces(pipeline_type, stage) or [required_artifact]):
            if produced not in ARTIFACT_NAMES:
                raise CheckpointValidationError(
                    f"Stage {stage!r} declares artifact {produced!r} which has no registered "
                    "schema — it cannot be validated, so the stage cannot close."
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
    creative_identity = artifacts.get("creative_identity") or {}
    authorial_voice = creative_identity.get("authorial_voice") or {}
    strict_authorial_voice = (
        stage == "script"
        and authorial_voice.get("mode") == "strict"
    )

    # Glyph gate on EVERY text surface of EVERY artifact, not just the stage-specific fields
    # (#8, 2026-07-05). An invisible/zero-width or homoglyph character hiding in a
    # metadata.caption, an asset filename, a prompt, or a subtitle must be caught wherever it
    # appears — the per-field checks (scene_plan text_policy.text, script strings) left the
    # other surfaces open. The gate is a no-op on pure-ASCII/single-script strings (paths,
    # ids, enums), so sweeping every string leaf is safe and closes the gap.
    from lib.armenian_glyph_gate import gate as _glyph_gate
    if strict_authorial_voice:
        # Ani's screenplay registers intentionally contain genuine Russian code-switching.
        # Keep mixed-token/transliteration/invisible-character failures, but do not mistake
        # every whole Russian word for an Armenian homoglyph attack.
        from lib.authorial_voice import authorial_glyph_gate as _authorial_glyph_gate
    else:
        _authorial_glyph_gate = None
    for _name, _art in artifacts.items():
        # Check the artifact NAME (top-level key) too, not only its contents — a poisoned
        # artifact name rode along unchecked otherwise (2026-07-06 dry re-probe).
        _viol = list(_glyph_gate(_name)["violations"]) if isinstance(_name, str) else []
        _gate = _authorial_glyph_gate if _authorial_glyph_gate else _glyph_gate
        _viol += _gate(_art)["violations"]  # walks keys AND values of the whole artifact
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
        run_rights_gates,
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
    bench_result = run_bench_gates(bench_stage, bench_report, pipeline_type=ptype)
    if not bench_result.get("ok"):
        detail = bench_result.get("violations") or bench_result
        raise CheckpointValidationError(
            f"Gate block at stage {stage!r} ({ptype}): {detail}"
        )

    result: dict[str, Any] | None = None
    if stage == "script":
        story_bible = artifacts.get("story_bible")
        content_spec = artifacts.get("content_spec") if ptype == "zavod-content" else None
        narrative_content = (
            isinstance(content_spec, dict)
            and content_spec.get("content_format") in {"screenplay", "series_episode", "stageplay"}
        )
        story_bible_required = ptype != "zavod-content" or narrative_content
        if (checkpoint.get("status") == "completed" and story_bible_required
                and not isinstance(story_bible, dict)):
            raise CheckpointValidationError(
                f"Gate block at stage {stage!r} ({ptype}): missing artifacts.story_bible — "
                "a Zavod script stage cannot close without the dramaturgy story bible."
            )
        if isinstance(story_bible, dict):
            result = run_story_gates(story_bible)
        if result is not None and not result.get("ok"):
            pass
        elif "script" in artifacts:
            result = run_script_gates(
                "\n".join(_all_strings(artifacts["script"])),
                allow_cyrillic_code_switch=strict_authorial_voice,
            )
        if (result is None or result.get("ok")) and strict_authorial_voice:
            report = artifacts.get("authorial_voice_report")
            if not isinstance(report, dict):
                raise CheckpointValidationError(
                    f"Gate block at stage {stage!r} ({ptype}): strict authorial voice is locked "
                    "but artifacts.authorial_voice_report is missing."
                )
            from lib.authorial_voice import (
                load_profile, profile_path, validate_voice_report,
            )
            try:
                profile = load_profile(profile_path(authorial_voice.get("profile_id", "")))
                result = validate_voice_report(
                    artifacts["script"], report,
                    profile=profile,
                    register=str(authorial_voice.get("register")),
                    minimum_score=float(authorial_voice.get("minimum_score", 0.8)),
                )
            except (OSError, ValueError, TypeError) as exc:
                raise CheckpointValidationError(
                    f"Gate block at stage {stage!r} ({ptype}): authorial voice profile/report "
                    f"cannot be verified ({exc})."
                ) from exc
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
            # Coverage, not just presence (round-6 #2, audit №7): N outputs with one report
            # closed with N-1 clips never checked. Every output must have a report matching
            # its clip basename — the name the documented builder writes.
            covered = {str(r.get("clip")) for r in reports_list if isinstance(r, dict)}
            uncovered = sorted(
                {os.path.basename(str(o.get("path") or "")) for o in outputs if isinstance(o, dict)}
                - covered
            )
            if uncovered:
                raise CheckpointValidationError(
                    f"Gate block at stage {stage!r} ({ptype}): output(s) {uncovered} have no "
                    "continuity report — every rendered output must be continuity-checked by clip name."
                )
        reports = _continuity_reports(artifacts)
        if reports:
            result = run_compose_gates(reports)
    elif stage == "publish":
        publish_log = artifacts.get("publish_log") or {}
        final_entries = [
            entry for entry in publish_log.get("entries") or []
            if isinstance(entry, dict) and entry.get("status") in {"published", "exported"}
        ]
        if final_entries:
            rights_manifest = artifacts.get("rights_manifest")
            if not isinstance(rights_manifest, dict):
                raise CheckpointValidationError(
                    f"Gate block at stage {stage!r} ({ptype}): final publish/export requires "
                    "artifacts.rights_manifest; draft and pending-review runs may omit it."
                )
            result = run_rights_gates(rights_manifest, publish_log)

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
VALID_ENGINES = {"none", "remotion", "higgsfield"}
LANE_COMPOSE_RUNTIMES = {
    "none": {"none"},                    # written content: no media-generation lane
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
    allowed_engines = {"none"} if ptype == "zavod-content" else {"remotion", "higgsfield"}

    if engine not in allowed_engines:
        raise CheckpointValidationError(
            f"Engine lane not locked at stage {stage!r} ({ptype}): artifacts.engine_lock.engine "
            f"must be one of {sorted(allowed_engines)}. Written content locks the no-render lane; "
            f"media pipelines ask Remotion vs Higgsfield and carry the lock forward. Got {engine!r}."
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


def _stage_artifact(
    project_dir: Path | str | None, stage: str, name: str,
) -> Any:
    if project_dir is None:
        return None
    path = Path(project_dir) / f"checkpoint_{stage}.json"
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            checkpoint = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    return (checkpoint.get("artifacts") or {}).get(name)


def _idea_artifact(project_dir: Path | str | None, name: str) -> Any:
    return _stage_artifact(project_dir, "idea", name)


def _enforce_creative_identity(
    checkpoint: dict[str, Any], project_dir: Path | str | None,
) -> None:
    """Lock authorial handwriting separately from optional visual branding.

    New Zavod runs must choose an identity at idea.  The script stage must carry the exact
    same lock, so a strict Maghakian profile cannot be silently omitted to bypass its report.
    Legacy projects whose old idea checkpoint predates this artifact remain resumable.
    """
    ptype = checkpoint.get("pipeline_type") or ""
    if not _is_zavod_pipeline(ptype) or checkpoint.get("status") != "completed":
        return
    stage = checkpoint.get("stage")
    artifacts = checkpoint.get("artifacts") or {}
    current = artifacts.get("creative_identity")

    if stage == "idea":
        if not isinstance(current, dict):
            if ptype == "zavod-content":
                raise CheckpointValidationError(
                    f"Creative identity not locked at idea ({ptype}): add "
                    "artifacts.creative_identity. Authorial handwriting and visual branding "
                    "must be explicit, even when both are neutral."
                )
            return  # existing media pipelines opt in; backward-compatible
        voice = current.get("authorial_voice") or {}
        if voice.get("mode") in {"reference", "strict"}:
            from lib.authorial_voice import load_profile, profile_path
            try:
                path = profile_path(str(voice.get("profile_id") or ""))
            except ValueError as exc:
                raise CheckpointValidationError(str(exc)) from exc
            if not path.exists():
                raise CheckpointValidationError(
                    f"Creative identity references missing authorial profile {path.name!r}."
                )
            if voice.get("mode") == "strict":
                profile = load_profile(path)
                register = str(voice.get("register") or "")
                register_profile = (profile.get("registers") or {}).get(register)
                if not isinstance(register_profile, dict):
                    raise CheckpointValidationError(
                        f"Strict authorial register {register!r} is absent from profile {path.name!r}."
                    )
                if register_profile.get("status") != "active":
                    raise CheckpointValidationError(
                        f"Strict authorial register {register!r} is quarantined until a glyph-clean "
                        "owner source is reviewed; reference mode remains available."
                    )
        return

    if stage != "script":
        return
    locked = _idea_artifact(project_dir, "creative_identity")
    if locked is None:
        return  # backward-compatible legacy run
    if not isinstance(current, dict):
        raise CheckpointValidationError(
            f"Script stage ({ptype}) dropped the idea-stage creative_identity lock; "
            "carry it unchanged so strict authorial voice cannot be bypassed."
        )
    if _canonical_json_for_lock(current) != _canonical_json_for_lock(locked):
        raise CheckpointValidationError(
            f"Script stage ({ptype}) changed the locked creative_identity. Supersede the "
            "idea decision explicitly instead of drifting the authorial profile mid-run."
        )


def _canonical_json_for_lock(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _canonical_artifact_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json_for_lock(value).encode("utf-8")).hexdigest()


def _enforce_universal_content_contract(
    checkpoint: dict[str, Any], project_dir: Path | str | None,
) -> None:
    """Contracts specific to the format-neutral ``zavod-content`` route."""
    if checkpoint.get("pipeline_type") != "zavod-content":
        return
    if checkpoint.get("status") != "completed":
        return
    stage = checkpoint.get("stage")
    artifacts = checkpoint.get("artifacts") or {}

    if stage == "idea":
        spec = artifacts.get("content_spec")
        if not isinstance(spec, dict):
            raise CheckpointValidationError(
                "zavod-content idea must carry artifacts.content_spec; a universal claim "
                "without a typed format/modality/deliverable contract is not routable."
            )
        from lib.content_router import ContentRoutingError, route_content
        try:
            route = route_content(spec)
        except ContentRoutingError as exc:
            raise CheckpointValidationError(f"content_spec route failed: {exc}") from exc
        if route.primary_pipeline != "zavod-content":
            raise CheckpointValidationError(
                f"content_spec format {spec.get('content_format')!r} routes to "
                f"{route.primary_pipeline!r}, not 'zavod-content'. Use the audited route."
            )
        if spec.get("automation_mode") != artifacts.get("run_mode"):
            raise CheckpointValidationError(
                "content_spec.automation_mode must equal the locked artifacts.run_mode."
            )
        return

    if stage == "script":
        locked = _idea_artifact(project_dir, "content_spec")
        current = artifacts.get("content_spec")
        if locked is not None and _canonical_json_for_lock(current) != _canonical_json_for_lock(locked):
            raise CheckpointValidationError(
                "zavod-content script changed or dropped the idea-stage content_spec; "
                "deliverable scope must be superseded explicitly, not drift mid-run."
            )
        script = artifacts.get("script") or {}
        if isinstance(locked, dict):
            expected = locked.get("deliverables") or []
            package = script.get("deliverables")
            if isinstance(package, list):
                expected_by_id = {item.get("id"): item for item in expected}
                actual_by_id = {item.get("deliverable_id"): item for item in package}
                if len(actual_by_id) != len(package) or set(actual_by_id) != set(expected_by_id):
                    raise CheckpointValidationError(
                        "zavod-content script deliverable ids must cover the locked content_spec "
                        "exactly once."
                    )
                for deliverable_id, item in actual_by_id.items():
                    spec_item = expected_by_id[deliverable_id]
                    if item.get("kind") != spec_item.get("kind"):
                        raise CheckpointValidationError(
                            f"zavod-content script deliverable {deliverable_id!r} changed its locked kind."
                        )
                    if item.get("language") != locked.get("language"):
                        raise CheckpointValidationError(
                            f"zavod-content script deliverable {deliverable_id!r} changed its locked language."
                        )
            else:
                if len(expected) != 1:
                    raise CheckpointValidationError(
                        "A multi-deliverable content_spec requires script.deliverables; one flat "
                        "draft cannot prove coverage of several promised outputs."
                    )
                if script.get("content_format") != locked.get("content_format"):
                    raise CheckpointValidationError(
                        "zavod-content script.content_format does not match the locked "
                        "content_spec.content_format."
                    )
                if script.get("language") != locked.get("language"):
                    raise CheckpointValidationError(
                        "zavod-content script.language does not match the locked "
                        "content_spec.language."
                    )
        bakeoff = artifacts.get("candidate_bakeoff")
        if not isinstance(bakeoff, dict):
            raise CheckpointValidationError(
                "zavod-content script cannot close without artifacts.candidate_bakeoff; "
                "the three-draft comparison must be evidence, not a checked box."
            )
        from lib.candidate_bakeoff import validate_candidate_bakeoff
        bakeoff_result = validate_candidate_bakeoff(script, bakeoff)
        if not bakeoff_result.get("ok"):
            raise CheckpointValidationError(
                f"zavod-content candidate bakeoff failed: "
                f"{bakeoff_result.get('violations') or bakeoff_result}"
            )
        return

    if stage == "quality":
        report = artifacts.get("content_quality_report") or {}
        spec = _idea_artifact(project_dir, "content_spec") or {}
        script = _stage_artifact(project_dir, "script", "script")
        if not isinstance(script, dict):
            raise CheckpointValidationError(
                "zavod-content quality cannot bind its evidence: the script checkpoint is missing."
            )
        expected_ids = [item.get("id") for item in spec.get("deliverables") or []]
        results = report.get("deliverables") or []
        actual_ids = [item.get("deliverable_id") for item in results if isinstance(item, dict)]
        if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != set(expected_ids):
            raise CheckpointValidationError(
                "content_quality_report must cover every locked deliverable exactly once."
            )
        script_package = script.get("deliverables")
        if isinstance(script_package, list):
            payloads = {item.get("deliverable_id"): item for item in script_package}
        elif len(expected_ids) == 1:
            payloads = {expected_ids[0]: script}
        else:
            payloads = {}
        required_checks = {
            "structure", "accuracy", "authorial_voice", "language",
            "channel_fit", "rights", "accessibility", "delivery",
        }
        violations: list[str] = []
        for item in results:
            deliverable_id = item.get("deliverable_id")
            checks = item.get("checks") or []
            names = [check.get("name") for check in checks if isinstance(check, dict)]
            if len(names) != len(set(names)) or set(names) != required_checks:
                violations.append(f"{deliverable_id}: incomplete or duplicate quality checks")
            failed = [
                check.get("name") for check in checks
                if isinstance(check, dict) and check.get("status") == "revise"
            ]
            if item.get("verdict") != "pass" or item.get("open_issues") or failed:
                violations.append(f"{deliverable_id}: unresolved quality result")
            payload = payloads.get(deliverable_id)
            expected_sha = _canonical_artifact_sha256(payload) if payload is not None else None
            if item.get("artifact_sha256") != expected_sha:
                violations.append(f"{deliverable_id}: quality evidence is bound to the wrong draft hash")
        if report.get("verdict") != "pass" or report.get("open_issues") or violations:
            raise CheckpointValidationError(
                f"zavod-content quality stage cannot close: verdict={report.get('verdict')!r}, "
                f"open={report.get('open_issues') or []}, violations={violations}."
            )


def _enforce_final_provenance(
    checkpoint: dict[str, Any], project_dir: Path | str | None,
) -> None:
    """Verify that the exact final payload is file-backed and hash-covered.

    ``run_rights_gates`` closes the declarations plane.  This structural gate closes the
    evidence plane: the final local payload must still exist, its SHA-256 must match the
    approved rights row, and a claimed C2PA manifest must itself be hash-verifiable.
    """
    ptype = checkpoint.get("pipeline_type") or ""
    if not _is_zavod_pipeline(ptype):
        return
    if checkpoint.get("stage") != "publish" or checkpoint.get("status") != "completed":
        return
    artifacts = checkpoint.get("artifacts") or {}
    publish_log = artifacts.get("publish_log") or {}
    final_entries = [
        item for item in publish_log.get("entries") or []
        if isinstance(item, dict) and item.get("status") in {"published", "exported"}
    ]
    if not final_entries:
        return
    if project_dir is None:
        raise CheckpointValidationError(
            "Final publish/export provenance cannot be verified without a project directory."
        )
    rights_manifest = artifacts.get("rights_manifest")
    if not isinstance(rights_manifest, dict):
        # The content gate normally catches this first; keep the structural seam fail-closed.
        raise CheckpointValidationError(
            "Final publish/export provenance requires artifacts.rights_manifest."
        )
    from lib.provenance import verify_rights_files
    result = verify_rights_files(rights_manifest, publish_log, project_dir)
    if not result.get("ok"):
        raise CheckpointValidationError(
            f"Final provenance block at publish ({ptype}): {result.get('violations') or result}"
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

    _validate_artifacts_for_stage(stage, status, artifacts, pipeline_type)

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


# Round-6 #6 (external audit №5): "readable media" and "usable production asset" are not the
# same thing. A 1×1, single-black-frame, 0.04s H.264 decodes fine and passed as a video.
# Floor thresholds block degenerate assets outright; compose outputs additionally must match
# what the render_report DECLARES (resolution exact, duration within tolerance) — a report
# that lies about its own output is a defect, not a formality.
_MIN_MEDIA_SIDE_PX = 32
_MIN_MEDIA_SECONDS = 0.1


def _media_defect(path: Path, kind: str, declared: dict[str, Any] | None = None) -> str | None:
    """Return a problem description if `path` is not valid media of `kind`, else None.

    Uses ffprobe to inspect real streams. Callers must confirm ffprobe is available first.
    ``declared`` (compose outputs) enables the declared-vs-actual check.
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
        w, h = int(s0.get("width") or 0), int(s0.get("height") or 0)
        if not (w > 0 and h > 0):
            return "video stream has no dimensions"
        if min(w, h) < _MIN_MEDIA_SIDE_PX:
            return f"degenerate video canvas {w}x{h} (min side {_MIN_MEDIA_SIDE_PX}px)"
        duration = max(_safe_float(fmt.get("duration")), _safe_float(s0.get("duration")))
        if duration <= 0:
            return "video has zero/unknown duration"
        if duration < _MIN_MEDIA_SECONDS:
            return f"degenerate video duration {duration}s (min {_MIN_MEDIA_SECONDS}s)"
        frames = int(_safe_float(s0.get("nb_frames")))
        if 0 < frames < 2:
            return "single-frame video (a still passed off as motion)"
        if declared:
            m = re.fullmatch(r"(\d+)x(\d+)", str(declared.get("resolution") or ""))
            if m and (int(m.group(1)), int(m.group(2))) != (w, h):
                return (f"render_report declares {declared['resolution']} but the file "
                        f"is {w}x{h}")
            want = _safe_float(declared.get("duration_seconds"))
            if want > 0 and abs(duration - want) > max(0.5, 0.1 * want):
                return (f"render_report declares {want}s but the file runs {duration:.2f}s")
        return None
    if kind in _PROBE_AUDIO:
        if not audio:
            return "declared audio but ffprobe found no audio stream"
        duration = max(_safe_float(fmt.get("duration")), _safe_float(audio[0].get("duration")))
        if duration <= 0:
            return "audio has zero/unknown duration"
        if duration < _MIN_MEDIA_SECONDS:
            return f"degenerate audio duration {duration}s (min {_MIN_MEDIA_SECONDS}s)"
        return None
    if kind in _PROBE_IMAGE:
        # A still decodes as a single-frame video stream (png/mjpeg/webp); require dimensions,
        # not duration.
        if not video:
            return "declared image but ffprobe could not decode it"
        s0 = video[0]
        w, h = int(s0.get("width") or 0), int(s0.get("height") or 0)
        if not (w > 0 and h > 0):
            return "image has no dimensions"
        if min(w, h) < _MIN_MEDIA_SIDE_PX:
            return f"degenerate image canvas {w}x{h} (min side {_MIN_MEDIA_SIDE_PX}px)"
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
    # Structural gate: applies to every manifest-driven pipeline, not only zavod (#11.1 r4).
    # _is_zavod_pipeline still runs first so an unknown zavod-* keeps failing closed.
    if not (_is_zavod_pipeline(ptype) or _is_manifest_pipeline(ptype)) or project_dir is None:
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
            # Compose outputs also carry their own declaration (resolution/duration) —
            # verified against the actual file (round-6 #6).
            declared = entry if stage == "compose" else None
            probe_targets.append(
                (entry["path"], _resolve_artifact_path(project_dir_p, entry["path"]), kind, declared))

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
    for raw, resolved, kind, declared in probe_targets:
        defect = _media_defect(resolved, kind, declared)
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


def _known_character_ids(project_dir: Path) -> set[str] | None:
    """Character ids declared by the project's character_design checkpoint (None when absent —
    e.g. zavod-reel has no character_design stage, so there is nothing to resolve against)."""
    cd_path = project_dir / "checkpoint_character_design.json"
    if not cd_path.exists():
        return None
    try:
        with open(cd_path) as f:
            cp = json.load(f)
    except Exception:
        return None
    cd = (cp.get("artifacts") or {}).get("character_design")
    if not isinstance(cd, dict):
        return None
    return {c.get("id") for c in cd.get("characters", []) if isinstance(c, dict)}


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
    if project_dir is None:
        return
    project_dir = Path(project_dir)
    stage = checkpoint.get("stage")
    artifacts = checkpoint.get("artifacts") or {}

    # character_id -> character_design.characters[].id. Scoped by the MANIFEST (does this
    # pipeline declare a character_design stage?), not by file presence — a stale
    # checkpoint_character_design.json dropped into e.g. a zavod-reel project must not
    # false-block its scene_plan on an unrelated character_id-shaped field (#6 round-4).
    if stage == "scene_plan" and "character_design" in get_pipeline_stages(
        checkpoint.get("pipeline_type")
    ):
        scene_plan = artifacts.get("scene_plan")
        if isinstance(scene_plan, dict):
            char_ids = _known_character_ids(project_dir)
            if char_ids is not None:
                for ref in _collect_by_key(scene_plan, "character_id"):
                    if ref not in char_ids:
                        raise CheckpointValidationError(
                            f"Referential integrity: scene_plan references character_id {ref!r} which "
                            f"is not in the character_design (known: {sorted(x for x in char_ids if x)})."
                        )

    # scene_id / asset_id checks stay scoped to zavod pipelines.
    if not _is_zavod_pipeline(checkpoint.get("pipeline_type") or ""):
        return

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


def _enforce_stage_order(checkpoint: dict[str, Any], project_dir: Path | str | None) -> None:
    """A zavod stage may only close — OR pause at an owner checkpoint (awaiting_human) — after
    every earlier stage in the pipeline's manifest order has itself completed (#7 ordering).

    Prior stages are verified as structurally-real completed checkpoints *for that stage of this
    pipeline*, not a bare status field, so a hand-dropped ``{"status":"completed"}`` marker
    cannot forge the run's history (#2/#5 round-4). This also gates awaiting_human, so a bogus
    late-stage owner-pause cannot be created out of order (#1 round-4).

    NOTE: this raises the forgery bar to a full schema-shaped checkpoint and matches the
    orchestrator's validated view; it cannot stop an attacker who can write arbitrary
    valid-looking checkpoints into the project dir — the whole spine trusts on-disk checkpoints.
    """
    _pt = checkpoint.get("pipeline_type") or ""
    if project_dir is None or not (_is_zavod_pipeline(_pt) or _is_manifest_pipeline(_pt)):
        return
    if checkpoint.get("status") not in {"completed", "awaiting_human"}:
        return
    ptype = checkpoint.get("pipeline_type")
    stage = checkpoint.get("stage")
    order = get_pipeline_stages(ptype)
    if stage not in order:
        return
    canonical_pt = _canonical_pipeline_type(ptype)
    project_dir = Path(project_dir)
    for prior in order[:order.index(stage)]:
        p = project_dir / f"checkpoint_{prior}.json"
        ok = False
        if p.exists():
            try:
                cp = json.load(open(p))
                # The prior must be a schema-valid checkpoint (not a bare status marker):
                # jsonschema rejects the forged {"status":"completed"} / garbage-artifacts /
                # extra-field markers the round-5 audit walked through write+resume, raising the
                # bar to a full schema-shaped checkpoint of this exact stage/pipeline.
                jsonschema.validate(instance=cp, schema=_load_checkpoint_schema())
                ok = (
                    cp.get("status") == "completed"
                    and cp.get("stage") == prior
                    and _canonical_pipeline_type(cp.get("pipeline_type")) == canonical_pt
                )
            except Exception:
                ok = False
        if not ok:
            raise CheckpointValidationError(
                f"Stage order violation: cannot advance {stage!r} before earlier stage {prior!r} "
                f"is a completed checkpoint of this pipeline (manifest order: {order})."
            )


def _enforce_concept_lock(checkpoint: dict[str, Any]) -> None:
    """Zavod idea closure requires a recorded concept_selection decision (round-6 #4).

    The proposal ritual — several directions, one chosen, the rest rejected with reasons —
    only binds later stages if it is RECORDED. An idea stage that closes without a
    concept_selection decision leaves no trace of what was considered, so rejected
    directions can silently return and the choice rationale is lost. The decision itself
    is validated by _validate_concept_selection at merge time; this seam only refuses
    closure without one.
    """
    if not _is_zavod_pipeline(checkpoint.get("pipeline_type") or ""):
        return
    if checkpoint.get("stage") != "idea" or checkpoint.get("status") != "completed":
        return
    dl = (checkpoint.get("artifacts") or {}).get("decision_log") or {}
    if not any(isinstance(d, dict) and d.get("category") == "concept_selection"
               for d in dl.get("decisions", [])):
        raise CheckpointValidationError(
            "Gate block at stage 'idea': a Zavod idea stage cannot close without a "
            "concept_selection decision in artifacts.decision_log — at least three "
            "directions with recorded rejections (round-6 #4)."
        )


def _enforce_fast_lane_eligibility(checkpoint: dict[str, Any]) -> None:
    """The fast lane's own failure mode is 'run everything through the fast lane'.

    A manifest that declares ``metadata.fast_lane.max_duration_seconds`` gets a duration
    guard: the idea stage cannot close with a brief whose target duration exceeds the
    limit — long-form work belongs in the standard pipeline with its full bench and ladder.

    Round-7.1 (re-audit №5, MERJEL — the original had no code for this): a manifest may
    also declare ``metadata.fast_lane.owner_override_required_if``, a list of risk
    categories (paid_client_delivery, new_series_launch, legal_or_sensitive_topic, …).
    That list was documentation only — nothing read it. Now: if the brief's
    ``risk_flags`` intersects that list, the idea stage cannot close without a structured
    ``brief.owner_override`` whose ``covers`` includes every matched flag. A brief that
    declares no risk_flags is unaffected — the guard only fires on what the brief itself
    admits to.
    """
    ptype = checkpoint.get("pipeline_type") or ""
    if not _is_zavod_pipeline(ptype):
        return
    if checkpoint.get("stage") != "idea" or checkpoint.get("status") != "completed":
        return
    try:
        from lib.pipeline_loader import load_pipeline
        limits = (load_pipeline(ptype).get("metadata") or {}).get("fast_lane") or {}
    except Exception:
        return  # manifest problems are the manifest gates' job
    if not limits:
        return
    brief = (checkpoint.get("artifacts") or {}).get("brief") or {}

    max_s = limits.get("max_duration_seconds")
    want = brief.get("target_duration_seconds")
    if max_s and isinstance(want, (int, float)) and want > max_s:
        raise CheckpointValidationError(
            f"Fast-lane eligibility: {ptype!r} allows at most {max_s}s, the brief asks "
            f"for {want}s — use the standard pipeline for long-form work."
        )

    gated = set(limits.get("owner_override_required_if") or [])
    flagged = {f for f in (brief.get("risk_flags") or []) if isinstance(f, str)}
    matched = sorted(gated & flagged)
    if matched:
        override = brief.get("owner_override")
        covers = set((override or {}).get("covers") or [])
        if not isinstance(override, dict) or not set(matched).issubset(covers):
            raise CheckpointValidationError(
                f"Fast-lane eligibility: brief risk_flags {matched} require a structured "
                "brief.owner_override whose 'covers' includes every matched flag — the "
                "fast lane does not skip owner sign-off on flagged work."
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
    _enforce_no_history_rewrite(checkpoint, project_dir)  # approved history is append-only
    _enforce_production_ladder(checkpoint)   # specialist ladder is non-collapsible
    _enforce_engine_lane(checkpoint)         # Remotion and Higgsfield lanes stay separate
    _enforce_run_mode(checkpoint)            # supervised vs automatic stay separated
    _enforce_creative_identity(checkpoint, project_dir)  # authorial voice cannot disappear
    _enforce_universal_content_contract(checkpoint, project_dir)  # typed any-content route
    _enforce_final_provenance(checkpoint, project_dir)  # exact final payload is hash-covered
    _enforce_concept_lock(checkpoint)        # idea closes only with a recorded concept choice (r6 #4)
    _enforce_fast_lane_eligibility(checkpoint)  # fast lane stays short-form (strategy audit)
    _enforce_canon_guard(checkpoint, project_dir)  # mid-pipeline canon drift requires revalidation
    _enforce_artifact_path_existence(checkpoint, project_dir)  # manifests must point at real files
    _enforce_referential_integrity(checkpoint, project_dir)  # cross-artifact links must resolve (#7)
    _enforce_stage_order(checkpoint, project_dir)  # completed stages follow manifest order (#7)
    _enforce_checkpoint_chain(checkpoint, project_dir)  # prior approvals remain byte-identical


def _enforce_resume_contracts(checkpoint: dict[str, Any], project_dir: Path | str | None) -> None:
    """Fail-closed re-validation for RESUME (not plain read).

    A completed checkpoint being resumed from must still satisfy the same structural contracts
    it satisfied at write time — otherwise a hand-edited, downgraded, or drifted checkpoint (or
    one whose artifacts were deleted after the fact) could silently continue a run. Unlike the
    write contracts, this path is side-effect free: the canon check is read-only (no lock write),
    so resuming/inspecting never mutates project state.
    """
    _enforce_manifest_pin(checkpoint)               # manifest still present + same order (r6 #1)
    _enforce_stage_order(checkpoint, project_dir)   # run structure first: manifest order holds (#7 r4)
    _enforce_production_ladder(checkpoint)          # specialist ladder still non-collapsed
    _enforce_engine_lane(checkpoint)                # engine lane still consistent
    _enforce_run_mode(checkpoint)                   # run mode still consistent
    _enforce_creative_identity(checkpoint, project_dir)  # identity lock still present
    _enforce_universal_content_contract(checkpoint, project_dir)  # deliverables still match
    _enforce_final_provenance(checkpoint, project_dir)  # final bytes still match approval
    _enforce_concept_lock(checkpoint)               # concept choice still recorded (r6 #4)
    _check_canon_guard_readonly(checkpoint, project_dir)      # canon drift — read-only
    _enforce_artifact_path_existence(checkpoint, project_dir)  # files real + valid media (#5)
    _enforce_referential_integrity(checkpoint, project_dir)   # cross-artifact links still resolve (#7)
    _enforce_checkpoint_chain(checkpoint, project_dir)        # prior checkpoints did not drift


def _checkpoint_path(pipeline_dir: Path, project_id: str, stage: str) -> Path:
    return pipeline_dir / project_id / f"checkpoint_{stage}.json"


def _decision_log_path(pipeline_dir: Path, project_id: str) -> Path:
    return pipeline_dir / project_id / "decision_log.json"


def _checkpoint_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _attach_checkpoint_chain(checkpoint: dict[str, Any], project_dir: Path) -> None:
    """Attach the exact previous-checkpoint hash to new Zavod writes.

    Legacy checkpoints remain resumable. The first newly written stage after a legacy checkpoint
    records ``legacy_anchor`` and pins that exact file; all later new checkpoints form a complete
    recursive chain back to that anchor.
    """
    if not _is_zavod_pipeline(checkpoint.get("pipeline_type") or ""):
        return
    order = get_pipeline_stages(checkpoint.get("pipeline_type"))
    stage = checkpoint.get("stage")
    if stage not in order:
        return
    position = order.index(stage)
    if position == 0:
        checkpoint["checkpoint_chain"] = {"position": 0}
        return
    previous_stage = order[position - 1]
    previous_path = project_dir / f"checkpoint_{previous_stage}.json"
    if not previous_path.is_file():
        return  # the existing stage-order gate emits the canonical failure
    try:
        with open(previous_path, encoding="utf-8") as handle:
            previous = json.load(handle)
    except (OSError, json.JSONDecodeError):
        previous = {}
    checkpoint["checkpoint_chain"] = {
        "position": position,
        "previous_stage": previous_stage,
        "previous_checkpoint_sha256": _checkpoint_file_sha256(previous_path),
        "legacy_anchor": not isinstance(previous.get("checkpoint_chain"), dict),
    }


def _enforce_checkpoint_chain(
    checkpoint: dict[str, Any], project_dir: Path | str | None,
) -> None:
    """Recursively verify a new Zavod checkpoint's immutable history links.

    This detects accidental/manual changes after approval. It deliberately does not claim to
    resist an attacker who can rewrite every file and recompute hashes; signed attestations are a
    separate future capability.
    """
    if not _is_zavod_pipeline(checkpoint.get("pipeline_type") or ""):
        return
    chain = checkpoint.get("checkpoint_chain")
    if not isinstance(chain, dict):
        return  # pre-chain checkpoint: backward-compatible legacy read/resume
    if project_dir is None:
        raise CheckpointValidationError("Checkpoint integrity chain requires a project directory.")

    order = get_pipeline_stages(checkpoint.get("pipeline_type"))
    current = checkpoint
    current_stage = current.get("stage")
    if current_stage not in order:
        return
    expected_position = order.index(current_stage)
    project_dir = Path(project_dir)

    while True:
        current_chain = current.get("checkpoint_chain")
        if not isinstance(current_chain, dict):
            raise CheckpointValidationError(
                f"Checkpoint integrity chain breaks at stage {current.get('stage')!r}."
            )
        if current_chain.get("position") != expected_position:
            raise CheckpointValidationError(
                f"Checkpoint integrity chain position mismatch at stage {current.get('stage')!r}."
            )
        if expected_position == 0:
            if current_chain.get("previous_stage") or current_chain.get("previous_checkpoint_sha256"):
                raise CheckpointValidationError(
                    "Checkpoint integrity genesis must not claim a previous checkpoint."
                )
            return

        previous_stage = order[expected_position - 1]
        if current_chain.get("previous_stage") != previous_stage:
            raise CheckpointValidationError(
                f"Checkpoint integrity chain expected previous stage {previous_stage!r}."
            )
        previous_path = project_dir / f"checkpoint_{previous_stage}.json"
        if not previous_path.is_file():
            raise CheckpointValidationError(
                f"Checkpoint integrity chain is missing {previous_path.name}."
            )
        actual_sha = _checkpoint_file_sha256(previous_path)
        if current_chain.get("previous_checkpoint_sha256") != actual_sha:
            raise CheckpointValidationError(
                f"Checkpoint integrity chain hash mismatch for {previous_path.name}; "
                "an approved earlier checkpoint changed after the next stage was linked."
            )
        try:
            with open(previous_path, encoding="utf-8") as handle:
                previous = json.load(handle)
            jsonschema.validate(instance=previous, schema=_load_checkpoint_schema())
        except (OSError, json.JSONDecodeError, jsonschema.ValidationError) as exc:
            raise CheckpointValidationError(
                f"Checkpoint integrity chain cannot validate {previous_path.name}: {exc}"
            ) from exc
        if (
            previous.get("project_id") != checkpoint.get("project_id")
            or _canonical_pipeline_type(previous.get("pipeline_type"))
            != _canonical_pipeline_type(checkpoint.get("pipeline_type"))
            or previous.get("stage") != previous_stage
        ):
            raise CheckpointValidationError(
                f"Checkpoint integrity chain points to the wrong run at {previous_path.name}."
            )
        previous_has_chain = isinstance(previous.get("checkpoint_chain"), dict)
        if current_chain.get("legacy_anchor"):
            if previous_has_chain:
                raise CheckpointValidationError(
                    "Checkpoint integrity chain falsely marks a chained checkpoint as legacy."
                )
            return
        if not previous_has_chain:
            raise CheckpointValidationError(
                f"Checkpoint integrity chain silently drops history at {previous_stage!r}."
            )
        current = previous
        expected_position -= 1


def _enforce_no_history_rewrite(
    checkpoint: dict[str, Any], project_dir: Path | str | None,
) -> None:
    """Do not replace an approved stage while later checkpoints depend on it."""
    if not _is_zavod_pipeline(checkpoint.get("pipeline_type") or ""):
        return
    if checkpoint.get("status") != "completed" or project_dir is None:
        return
    order = get_pipeline_stages(checkpoint.get("pipeline_type"))
    stage = checkpoint.get("stage")
    if stage not in order:
        return
    root = Path(project_dir)
    later = [
        name for name in order[order.index(stage) + 1:]
        if (root / f"checkpoint_{name}.json").is_file()
    ]
    if later:
        raise CheckpointValidationError(
            f"Checkpoint history rewrite blocked: stage {stage!r} already has later linked "
            f"checkpoint(s) {later}. Fork/supersede the run instead of replacing approved history."
        )


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


def _read_decision_log(pipeline_dir: Path, project_id: str) -> dict[str, Any]:
    path = _decision_log_path(pipeline_dir, project_id)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"version": "1.0", "project_id": project_id, "decisions": []}


def active_decisions(log: dict[str, Any]) -> list[dict[str, Any]]:
    """The decisions currently in force, derived unambiguously from history (round-6 #3).

    A decision is active unless another decision supersedes it. History is append-only:
    superseded entries stay in the log, they just stop being the answer.
    """
    superseded = {d.get("supersedes") for d in log.get("decisions", []) if d.get("supersedes")}
    return [d for d in log.get("decisions", []) if d.get("decision_id") not in superseded]


_LABEL_PUNCT = re.compile(r"[^\w\s]", flags=re.UNICODE)
_LABEL_WS = re.compile(r"\s+")


def _normalize_concept_label(label: Any) -> str:
    """Canonical form for duplicate-label comparison (round-7.1 #8).

    strip().casefold() alone let 'Pool Party.' and 'pool party' pass as "different"
    directions — only casing/edge-whitespace was covered, not punctuation or internal
    whitespace. NFKC first (width/compatibility forms), then drop all punctuation, then
    collapse internal whitespace, then casefold.
    """
    s = unicodedata.normalize("NFKC", str(label or ""))
    s = _LABEL_PUNCT.sub(" ", s)  # a space, not "" — "Pool-Party" must stay two words
    s = _LABEL_WS.sub(" ", s).strip()
    return s.casefold()


def _validate_concept_selection(decision: dict[str, Any]) -> None:
    """Anti-mediocrity contract for a concept_selection decision (round-6 #4, audit №12).

    Claiming the category means meeting the bar: at least three directions that are not
    the same idea in different words, the selection actually among them, and every
    rejected direction carrying its rejection rationale — that record is what keeps a
    rejected idea from silently returning in a later stage.
    """
    did = decision.get("decision_id")
    opts = [o for o in decision.get("options_considered") or [] if isinstance(o, dict)]
    if len(opts) < 3:
        raise CheckpointValidationError(
            f"decision_log: concept_selection {did!r} offers only {len(opts)} option(s) — "
            "at least three genuinely different directions are required."
        )
    if decision.get("selected") not in {o.get("option_id") for o in opts}:
        raise CheckpointValidationError(
            f"decision_log: concept_selection {did!r} selects "
            f"{decision.get('selected')!r} which is not among its options."
        )
    # Similarity is a SIGNAL, not a judge (strategy audit №17): the token threshold both
    # false-blocked legitimately close directions and passed reworded duplicates, so it
    # was demoted from hard block to a loud warning for the reviewer/bench. Only literal
    # label equality remains a hard block — the same name twice is never two directions.
    from lib.bench_gate import _similarity
    import logging
    for i in range(len(opts)):
        for j in range(i + 1, len(opts)):
            a, b = opts[i], opts[j]
            la = _normalize_concept_label(a.get("label"))
            lb = _normalize_concept_label(b.get("label"))
            if la and la == lb:
                raise CheckpointValidationError(
                    f"decision_log: concept_selection {did!r} lists the same label "
                    f"({a.get('label')!r} / {b.get('label')!r}) twice — punctuation and "
                    "casing don't make it a different direction."
                )
            ta = f"{a.get('label', '')} {a.get('reason', '')}"
            tb = f"{b.get('label', '')} {b.get('reason', '')}"
            if _similarity(ta, tb) >= 0.85:
                msg = (
                    f"options {a.get('option_id')!r} and {b.get('option_id')!r} read as "
                    "the same direction in different words (similarity signal) — "
                    "reviewer should confirm they differ in mechanism, not phrasing."
                )
                logging.getLogger(__name__).warning("concept_selection %s: %s", did, msg)
                # Round-7.1 (re-audit №7): a log line is not an audit trail — a rotated
                # log or an unwatched stdout makes the signal disappear. Attach it to the
                # decision ITSELF (mutates the same dict object that gets persisted into
                # decision_log.json), so it survives independent of any log stream.
                decision.setdefault("warnings", [])
                if msg not in decision["warnings"]:
                    decision["warnings"].append(msg)
    for o in opts:
        if o.get("option_id") != decision.get("selected") and not str(o.get("rejected_because") or "").strip():
            raise CheckpointValidationError(
                f"decision_log: concept_selection {did!r} rejects option "
                f"{o.get('option_id')!r} without rejected_because — the rejection "
                "rationale must survive for later stages."
            )


def _validate_decision_log_merge(
    existing: dict[str, Any], new_log: dict[str, Any]
) -> None:
    """Lifecycle invariants for the combined decision history (round-6 #3, audit №11).

    The old merge appended by id and silently DROPPED a re-submitted id with different
    content — a history-rewrite attempt vanished without a trace — and let two active
    decisions on the same (category, subject) contradict each other, so 'the current
    decision' was whichever a consumer happened to read (day-4 Remotion vs day-18 FFmpeg).
    Invariants, order-independent over existing ∪ new:
      1. a decision_id is immutable — same id with different content is a rewrite, blocked;
      2. every ``supersedes`` names a known decision, and a decision is superseded at most
         once (no forked history);
      3. active decisions never disagree: same (category, subject) with a different
         ``selected`` requires ``supersedes`` on the newcomer — an explicit re-decision,
         never a silent contradiction.
    """
    # Concept validation/mutation (structural checks + the similarity-warning attachment)
    # runs BEFORE the equality check below, not after: the warning attachment mutates the
    # decision dict deterministically from its own content, so an identical resubmission
    # gets the identical mutation on both calls and the equality check still sees matching
    # dicts. Running it after would compare an unmutated resubmission against an
    # already-mutated persisted copy and false-fire "re-submitted with different content"
    # (round-7.1 #7 follow-through).
    for d in new_log.get("decisions", []):
        if d.get("category") == "concept_selection":
            _validate_concept_selection(d)
            from lib.performance_loop import concept_refs_violation
            viol = concept_refs_violation(d)
            if viol:
                raise CheckpointValidationError(f"decision_log: {viol}")

    combined: dict[str, dict[str, Any]] = {}
    for d in existing.get("decisions", []):
        combined[d["decision_id"]] = d
    for d in new_log.get("decisions", []):
        did = d.get("decision_id")
        prev = combined.get(did)
        if prev is not None and prev != d:
            raise CheckpointValidationError(
                f"decision_log: decision {did!r} was re-submitted with different content — "
                "history is append-only; supersede it with a new decision instead."
            )
        combined[did] = d

    superseded_by: dict[str, str] = {}
    for d in combined.values():
        target = d.get("supersedes")
        if not target:
            continue
        if target not in combined:
            raise CheckpointValidationError(
                f"decision_log: decision {d['decision_id']!r} supersedes unknown "
                f"decision {target!r}."
            )
        if target in superseded_by:
            raise CheckpointValidationError(
                f"decision_log: decision {target!r} is superseded by both "
                f"{superseded_by[target]!r} and {d['decision_id']!r} — forked history."
            )
        superseded_by[target] = d["decision_id"]

    active_by_subject: dict[tuple[str, str], dict[str, Any]] = {}
    for d in combined.values():
        if d.get("decision_id") in superseded_by:
            continue
        key = (str(d.get("category")), str(d.get("subject")))
        other = active_by_subject.get(key)
        if other is not None and other.get("selected") != d.get("selected"):
            raise CheckpointValidationError(
                f"decision_log: active decisions {other['decision_id']!r} "
                f"(selected {other.get('selected')!r}) and {d['decision_id']!r} "
                f"(selected {d.get('selected')!r}) contradict on {key} — re-deciding "
                "requires supersedes; two active answers must never coexist."
            )
        active_by_subject.setdefault(key, d)

    # Round-6 #4 (audit №12): concept contract + forbidden directions.
    # (Concept structural validation + performance-refs check already ran above, BEFORE
    # the equality check — see the round-7.1 #7 note.)
    #
    # A direction an ACTIVE decision explicitly rejected must not return by name in a new
    # decision of the same category — reopening it requires superseding the decision that
    # rejected it, so the rejection (and its rationale) leaves history explicitly.
    # Label matching uses the same punctuation/whitespace-aware normalization as the
    # duplicate-label check (round-7.1 #8) — a reworded-punctuation label must not bypass
    # this either.
    for d in new_log.get("decisions", []):
        sel_label = next(
            (_normalize_concept_label(o.get("label"))
             for o in d.get("options_considered") or [] if isinstance(o, dict)
             and o.get("option_id") == d.get("selected")),
            "",
        )
        if not sel_label:
            continue
        for other in combined.values():
            if other.get("decision_id") == d.get("decision_id"):
                continue
            if other.get("decision_id") in superseded_by:
                continue
            if other.get("category") != d.get("category"):
                continue
            rejected_labels = {
                _normalize_concept_label(o.get("label"))
                for o in other.get("options_considered") or [] if isinstance(o, dict)
                and o.get("option_id") != other.get("selected")
            }
            if sel_label in rejected_labels:
                raise CheckpointValidationError(
                    f"decision_log: decision {d['decision_id']!r} selects "
                    f"{sel_label!r}, which active decision {other['decision_id']!r} "
                    "explicitly rejected — a rejected direction must not return without "
                    "superseding the decision that rejected it."
                )


def _merge_decision_log(
    pipeline_dir: Path, project_id: str, new_log: dict[str, Any]
) -> None:
    """Append new decisions to the project-level decision log.

    Each stage may produce decisions. This function merges them into a
    single cumulative file so reviewers and the bench can inspect the
    full audit trail. Lifecycle invariants were already validated pre-persist
    (_validate_decision_log_merge), so identical re-submissions are the only
    duplicates left to skip here.
    """
    existing = _read_decision_log(pipeline_dir, project_id)
    existing_ids = {d["decision_id"] for d in existing.get("decisions", [])}
    for decision in new_log.get("decisions", []):
        if decision.get("decision_id") not in existing_ids:
            existing["decisions"].append(decision)

    _atomic_write_json(_decision_log_path(pipeline_dir, project_id), existing)


def _identity_lock_path(pipeline_dir: Path, project_id: str) -> Path:
    return pipeline_dir / project_id / ".pipeline_identity.json"


def _enforce_project_pipeline_identity(
    pipeline_dir: Path, project_id: str, pipeline_type: str | None
) -> None:
    """Pipeline identity is a PROJECT property, not a per-checkpoint field (round-7 #1,
    external audit №8 — code-confirmed bypass; hardened round-7.1 per re-audit №1/№2).

    Every gate is keyed off the checkpoint's own pipeline_type, so a project that started
    as zavod-reel could close its next stage as 'animation' and silently shed bench,
    ladder, glyph, and engine-lane enforcement — a full governance bypass with one field.

    Round-7.1: the original version derived identity by scanning every checkpoint_*.json —
    O(n) per write, and only as trustworthy as those files staying intact (deleting or
    renaming the one typed checkpoint silently un-locked the project, re-audit №1). Identity
    now lives in its own append-once file, ``.pipeline_identity.json`` — one O(1) read on the
    common path. The checkpoint scan still runs, but only as a tamper-evidence fallback when
    the lock file is missing: a project with typed checkpoint history but no lock file means
    either a pre-lock-file legacy project (self-heals: the lock is written from that history)
    or the lock file was deleted (still caught, because the reconstructed identity is then
    compared against the incoming write exactly as before). A CORRUPTED lock file is never
    silently trusted or silently ignored — it blocks until repaired, since a bad lock file is
    itself tamper evidence.
    """
    # No early return on a not-yet-existing project directory: that is exactly the FIRST
    # write, which must reach the "first typed write" branch below and create the lock
    # (_atomic_write_json creates the directory). Round-7.1: the earlier version returned
    # here, so no project ever got a lock file until its SECOND write.
    project_dir = pipeline_dir / project_id
    new = _canonical_pipeline_type(pipeline_type) or "unknown"
    lock_path = _identity_lock_path(pipeline_dir, project_id)

    if lock_path.exists():
        try:
            with open(lock_path) as f:
                locked = json.load(f).get("pipeline_type")
        except Exception as exc:
            raise CheckpointValidationError(
                f"Pipeline identity lock file for project {project_id!r} is unreadable "
                f"({exc}) — a corrupted lock is treated as tamper evidence, not as absence; "
                "repair or restore it before writing."
            ) from exc
        if not locked:
            raise CheckpointValidationError(
                f"Pipeline identity lock file for project {project_id!r} has no "
                "pipeline_type — repair or restore it before writing."
            )
        # An untyped ('unknown') write into an already-typed project IS the downgrade —
        # writing 'unknown' does not require gates, so it is not special-cased here.
        if new != locked:
            raise CheckpointValidationError(
                f"Pipeline identity lock: project {project_id!r} is locked to "
                f"{locked!r} (see {lock_path.name}); writing stage {new!r}-typed "
                "checkpoints into it would shed that pipeline's gates. One project, "
                "one pipeline."
            )
        return

    # No lock file — tamper-evidence fallback: does typed checkpoint history exist anyway?
    reconstructed: str | None = None
    for path in sorted(project_dir.glob("checkpoint_*.json")):
        try:
            with open(path) as f:
                existing = json.load(f).get("pipeline_type") or "unknown"
        except Exception:
            continue
        if existing != "unknown":
            reconstructed = existing
            break

    if reconstructed is not None:
        if new != reconstructed:
            raise CheckpointValidationError(
                f"Pipeline identity lock: project {project_id!r} has typed checkpoint "
                f"history ({reconstructed!r}) but no lock file — writing "
                f"{new!r}-typed checkpoints into it would shed that pipeline's gates. "
                "One project, one pipeline."
            )
        _write_identity_lock(lock_path, reconstructed)  # self-heal for legacy projects
        return

    if new != "unknown":
        _write_identity_lock(lock_path, new)  # first typed write — lock it now


def _write_identity_lock(lock_path: Path, pipeline_type: str) -> None:
    _atomic_write_json(lock_path, {
        "version": "1.0",
        "pipeline_type": pipeline_type,
        "locked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })


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
    if status == "awaiting_human":
        # A pause is an owner gate by definition. Normalize legacy callers so the persisted
        # checkpoint cannot claim it is awaiting a human while approval is not required.
        human_approval_required = True
        human_approved = False
    if status == "completed" and human_approval_required and not human_approved:
        raise CheckpointValidationError(
            f"Stage {stage!r} requires human approval and cannot close unapproved."
        )
    # Canonicalize at the source so a stray-cased / whitespace-padded zavod type is never
    # persisted raw — every downstream consumer then sees the canonical id (#11).
    pipeline_type = _canonical_pipeline_type(pipeline_type)
    _enforce_project_pipeline_identity(pipeline_dir, project_id, pipeline_type)
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
    pin = _manifest_pin(pipeline_type)
    if pin is not None:
        checkpoint["manifest_pin"] = pin
    _attach_checkpoint_chain(checkpoint, pipeline_dir / project_id)
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
        # Lifecycle invariants run BEFORE the checkpoint persists (round-6 #3): a history
        # rewrite or a contradiction with an active decision must block the whole write,
        # not surface after the carrying checkpoint is already on disk.
        _validate_decision_log_merge(
            _read_decision_log(pipeline_dir, project_id), decision_log
        )
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
        if not cp:
            continue
        # A pinned checkpoint blocks ALL navigation once its manifest vanishes or
        # re-sequences — otherwise stage navigation would quietly proceed on the generic
        # fallback order the pin exists to forbid (round-6 #1).
        _enforce_manifest_pin(cp)
        if cp.get("status") == "completed":
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
