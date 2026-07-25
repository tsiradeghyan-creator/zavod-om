import pytest

from lib.bench_gate import required_bench
from lib.checkpoint import (
    CheckpointValidationError,
    _enforce_final_provenance,
    _enforce_zavod_gates,
)
from lib.gatechain import run_rights_gates
from lib.provenance import sha256_file, verify_rights_files
from schemas.artifacts import validate_artifact


def _rights(status="controlled", *, asset_type="text"):
    return {
        "version": "1.0",
        "project_id": "p",
        "entries": [{
            "asset_id": "master",
            "asset_type": asset_type,
            "status": status,
            "source": "Owner-authored draft",
            "owner_or_licensor": "Owner",
            "license_or_basis": "Original work",
            "artifact_sha256": "a" * 64,
            "evidence": ["Project authorship record"],
        }],
        "ai_disclosure": {"required": False, "decision": "not_required"},
        "approved_by": "owner",
        "approved_at": "2026-07-13T00:00:00Z",
    }


def _publish():
    return {"version": "1.0", "entries": [{
        "platform": "website",
        "status": "published",
        "timestamp": "2026-07-13T00:00:00Z",
    }]}


def test_controlled_original_work_passes_rights_gate():
    manifest = _rights()
    validate_artifact("rights_manifest", manifest)
    assert run_rights_gates(manifest, _publish())["ok"]


def test_unknown_rights_block_final_delivery():
    result = run_rights_gates(_rights("unknown"), _publish())
    assert not result["ok"]
    assert any("unknown" in item for item in result["violations"])


def test_likeness_requires_consent_id():
    result = run_rights_gates(_rights(asset_type="likeness"), _publish())
    assert not result["ok"]
    assert any("consent id" in item for item in result["violations"])


def test_required_ai_disclosure_needs_label_text():
    manifest = _rights()
    manifest["ai_disclosure"] = {"required": True, "decision": "label"}
    result = run_rights_gates(manifest, _publish())
    assert not result["ok"]
    assert any("label_text" in item for item in result["violations"])


def test_ai_model_requires_terms_source_and_pinned_snapshot():
    manifest = _rights()
    manifest["entries"][0]["model"] = "example-model-v1"
    result = run_rights_gates(manifest, _publish())
    assert not result["ok"]
    assert any("terms source URL" in item for item in result["violations"])
    assert any("terms snapshot hash" in item for item in result["violations"])


def test_final_rights_approval_requires_actor_and_timestamp():
    manifest = _rights()
    del manifest["approved_at"]
    result = run_rights_gates(manifest, _publish())
    assert not result["ok"]
    assert any("approved_at" in item for item in result["violations"])


def _publish_bench():
    return {
        "stage": "publish",
        "bench": {
            role: {
                "ruling": f"The {role} independently verified final publication rights, metadata, disclosure, and delivery evidence for specialist {index}.",
                "verdict": "approve",
            }
            for index, role in enumerate(required_bench("publish", "zavod-content"))
        },
    }


def _checkpoint(rights=None):
    artifacts = {"publish_log": _publish(), "bench_report": _publish_bench()}
    if rights is not None:
        artifacts["rights_manifest"] = rights
    return {
        "pipeline_type": "zavod-content",
        "stage": "publish",
        "status": "completed",
        "artifacts": artifacts,
    }


def test_final_publish_cannot_bypass_rights_manifest_at_checkpoint_seam():
    with pytest.raises(CheckpointValidationError, match="rights_manifest"):
        _enforce_zavod_gates(_checkpoint())


def test_passing_rights_manifest_closes_checkpoint_content_gate():
    _enforce_zavod_gates(_checkpoint(_rights()))


def _file_backed_checkpoint(tmp_path, *, status="exported"):
    payload = tmp_path / "final.txt"
    payload.write_text("Approved final payload", encoding="utf-8")
    rights = _rights()
    rights["entries"][0]["artifact_path"] = "final.txt"
    rights["entries"][0]["artifact_sha256"] = sha256_file(payload)
    publish = {
        "version": "1.0",
        "entries": [{
            "platform": "website",
            "status": status,
            "export_path": "final.txt",
            "timestamp": "2026-07-13T00:00:00Z",
            **({"url": "https://example.com/final"} if status == "published" else {}),
        }],
    }
    checkpoint = _checkpoint(rights)
    checkpoint["artifacts"]["publish_log"] = publish
    return checkpoint, payload


def test_final_export_is_bound_to_hash_verified_rights_row(tmp_path):
    checkpoint, _ = _file_backed_checkpoint(tmp_path)
    _enforce_final_provenance(checkpoint, tmp_path)


def test_changed_final_bytes_block_publish_seam(tmp_path):
    checkpoint, payload = _file_backed_checkpoint(tmp_path, status="published")
    payload.write_text("Changed after approval", encoding="utf-8")
    with pytest.raises(CheckpointValidationError, match="hash mismatch"):
        _enforce_final_provenance(checkpoint, tmp_path)


def test_published_entry_requires_exact_local_payload_and_returned_url(tmp_path):
    checkpoint, _ = _file_backed_checkpoint(tmp_path, status="published")
    del checkpoint["artifacts"]["publish_log"]["entries"][0]["export_path"]
    del checkpoint["artifacts"]["publish_log"]["entries"][0]["url"]
    result = verify_rights_files(
        checkpoint["artifacts"]["rights_manifest"],
        checkpoint["artifacts"]["publish_log"],
        tmp_path,
    )
    assert not result["ok"]
    assert any("exact local payload" in item for item in result["violations"])
    assert any("returned URL" in item for item in result["violations"])


def test_claimed_c2pa_manifest_is_hash_verified(tmp_path):
    checkpoint, _ = _file_backed_checkpoint(tmp_path)
    manifest = tmp_path / "content-credentials.c2pa"
    manifest.write_bytes(b"signed-manifest")
    checkpoint["artifacts"]["rights_manifest"]["c2pa"] = {
        "status": "signed",
        "manifest_path": "content-credentials.c2pa",
        "manifest_sha256": "0" * 64,
    }
    with pytest.raises(CheckpointValidationError, match="C2PA manifest hash mismatch"):
        _enforce_final_provenance(checkpoint, tmp_path)
