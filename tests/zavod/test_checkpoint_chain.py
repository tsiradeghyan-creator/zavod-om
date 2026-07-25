import hashlib
import json

import pytest

from lib.checkpoint import CheckpointValidationError, resume_checkpoint, write_checkpoint
from tests.zavod.test_universal_content_run import (
    PIPELINE,
    _bakeoff,
    _bench,
    _brief,
    _decision_log,
    _identity,
    _ladder,
    _script,
    _spec,
)


def _write_idea_and_script(tmp_path, project="chain-run"):
    spec = _spec()
    identity = _identity()
    idea = {
        "brief": _brief(), "content_spec": spec, "creative_identity": identity,
        "engine_lock": {"engine": "none", "compose_runtime": "none"},
        "run_mode": "automatic", "decision_log": _decision_log(project),
        "production_ladder": _ladder("idea"), "bench_report": _bench("idea"),
    }
    idea_path = write_checkpoint(
        tmp_path, project, "idea", "completed", idea, pipeline_type=PIPELINE,
    )
    script = _script()
    script_artifacts = {
        "script": script, "candidate_bakeoff": _bakeoff(script),
        "content_spec": spec, "creative_identity": identity, "run_mode": "automatic",
        "production_ladder": _ladder("script"), "bench_report": _bench("script"),
    }
    script_path = write_checkpoint(
        tmp_path, project, "script", "completed", script_artifacts, pipeline_type=PIPELINE,
    )
    return idea_path, script_path


def test_new_zavod_checkpoints_form_an_exact_hash_chain(tmp_path):
    idea_path, script_path = _write_idea_and_script(tmp_path)
    idea = json.loads(idea_path.read_text(encoding="utf-8"))
    script = json.loads(script_path.read_text(encoding="utf-8"))
    assert idea["checkpoint_chain"] == {"position": 0}
    assert script["checkpoint_chain"]["previous_stage"] == "idea"
    assert script["checkpoint_chain"]["previous_checkpoint_sha256"] == hashlib.sha256(
        idea_path.read_bytes()
    ).hexdigest()
    assert script["checkpoint_chain"]["legacy_anchor"] is False


def test_resume_blocks_a_schema_valid_change_to_approved_history(tmp_path):
    idea_path, _ = _write_idea_and_script(tmp_path)
    idea = json.loads(idea_path.read_text(encoding="utf-8"))
    idea["timestamp"] = "2026-07-13T01:00:00+00:00"
    idea_path.write_text(json.dumps(idea, ensure_ascii=False, indent=2), encoding="utf-8")
    with pytest.raises(CheckpointValidationError, match="integrity chain hash mismatch"):
        resume_checkpoint(tmp_path, "chain-run", "script")


def test_earlier_stage_cannot_be_rewritten_after_later_approval(tmp_path):
    _write_idea_and_script(tmp_path)
    project = "chain-run"
    spec = _spec()
    artifacts = {
        "brief": _brief(), "content_spec": spec, "creative_identity": _identity(),
        "engine_lock": {"engine": "none", "compose_runtime": "none"},
        "run_mode": "automatic", "decision_log": _decision_log(project),
        "production_ladder": _ladder("idea"), "bench_report": _bench("idea"),
    }
    with pytest.raises(CheckpointValidationError, match="history rewrite blocked"):
        write_checkpoint(
            tmp_path, project, "idea", "completed", artifacts, pipeline_type=PIPELINE,
        )
