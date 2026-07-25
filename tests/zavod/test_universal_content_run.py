from lib.bench_gate import required_bench
import copy
import json

import pytest

from lib.checkpoint import (
    CheckpointValidationError,
    _canonical_artifact_sha256,
    get_completed_stages,
    write_checkpoint,
)


PIPELINE = "zavod-content"
ORDER = ["idea", "script", "quality", "publish"]
RUNGS = {
    "idea": ["intake_or_writer_room", "concept_lock"],
    "script": ["structure_pass", "candidate_bakeoff", "authorial_voice_pass", "accuracy_pass", "final_draft_lock"],
    "quality": ["editorial_postproduction", "channel_adaptation", "evidence_review"],
    "publish": ["presentation_route"],
}


def _bench(stage):
    return {
        "stage": stage,
        "bench": {
            role: {
                "ruling": f"The {role} reviewed the {stage} evidence independently and confirms structure, language, rights, and delivery quality for specialist {index}.",
                "verdict": "approve",
            }
            for index, role in enumerate(required_bench(stage, PIPELINE))
        },
    }


def _ladder(stage):
    return {"sub_stages": [
        {"name": name, "produces": name, "owner_approved": stage == "publish"}
        for name in RUNGS[stage]
    ]}


def _spec():
    return {
        "version": "1.0",
        "content_format": "article",
        "primary_modality": "text",
        "language": "hy-AM",
        "channels": ["website"],
        "deliverables": [{
            "id": "master",
            "kind": "article",
            "target_length": {"unit": "words", "minimum": 700, "maximum": 900},
            "acceptance_criteria": ["A source-backed argument with a clear ending"],
        }],
        "automation_mode": "automatic",
    }


def _identity():
    return {
        "version": "1.0",
        "identity_id": "neutral-editorial",
        "brand_pack_id": None,
        "authorial_voice": {"mode": "neutral"},
        "visual_identity": {"mode": "neutral"},
    }


def _decision_log(project_id):
    return {"version": "1.0", "project_id": project_id, "decisions": [{
        "decision_id": "d-concept",
        "stage": "idea",
        "category": "concept_selection",
        "subject": "article direction",
        "options_considered": [
            {"option_id": "c1", "label": "one-object investigation", "score": 0.9, "reason": "A physical object reveals the argument through evidence."},
            {"option_id": "c2", "label": "chronological field diary", "score": 0.7, "reason": "A dated sequence shows change over time.", "rejected_because": "The chronology hides the central tension."},
            {"option_id": "c3", "label": "expert debate transcript", "score": 0.5, "reason": "Opposing voices expose tradeoffs.", "rejected_because": "The format weakens the owner's authorial point of view."},
        ],
        "selected": "c1",
        "reason": "It gives the argument the clearest evidence-bearing mechanism.",
    }]}


def _brief():
    return {
        "version": "1.0",
        "title": "Փորձնական հոդված",
        "hook": "Մի առարկա, որի մեջ ամբողջ պատմությունն է։",
        "key_points": ["Աղբյուր", "Հակափաստարկ", "Եզրակացություն"],
        "tone": "ճշգրիտ",
        "style": "editorial",
        "content_format": "article",
        "target_platform": "website",
        "target_length": {"unit": "words", "value": 800},
    }


def _script():
    return {
        "version": "1.0",
        "title": "Փորձնական հոդված",
        "content_format": "article",
        "language": "hy-AM",
        "blocks": [
            {"id": "h1", "type": "heading", "text": "Մի առարկայի պատմություն"},
            {"id": "p1", "type": "paragraph", "text": "Առարկան մնացել էր սեղանին, երբ բոլորը վաղուց գնացել էին։"},
            {"id": "p2", "type": "paragraph", "text": "Այդ լռությունից է սկսվում հարցը, ոչ թե պատրաստի պատասխանից։"},
        ],
    }


def _candidate_variant(script, text):
    draft = copy.deepcopy(script)
    block_sets = [draft.get("blocks") or []]
    block_sets.extend(
        item.get("blocks") or []
        for item in draft.get("deliverables") or []
        if isinstance(item, dict)
    )
    index = 0
    for blocks in block_sets:
        for block in blocks:
            if isinstance(block, dict):
                index += 1
                block["text"] = f"{text} Մաս {index}։"
    return draft


def _bakeoff(final_script):
    alternatives = [
        final_script,
        _candidate_variant(
            final_script,
            "Պատմությունը սկսվում է հակափաստարկից և հետո վերադառնում է առարկային։",
        ),
        _candidate_variant(
            final_script,
            "Վերջին պատկերը բացում է սկզբի թաքնված իմաստը և փոխում հիմնական հարցը։",
        ),
    ]
    axes = ["structure", "perspective", "ending"]
    candidates = []
    for index, (draft, axis) in enumerate(zip(alternatives, axes), start=1):
        candidates.append({
            "candidate_id": f"c{index}",
            "draft": draft,
            "draft_sha256": _canonical_artifact_sha256(draft),
            "difference_axes": [axis],
            "differentiator": f"Candidate {index} uses a materially different {axis} mechanism throughout the complete draft.",
            "scores": {
                "brief_fit": 9 if index == 1 else 7,
                "authorial_voice_fit": 9 if index == 1 else 7,
                "structure": 9 if index == 1 else 8,
                "originality": 8,
                "accuracy_confidence": 9,
            },
        })
    return {
        "version": "1.0",
        "blind_review": {"labels_hidden": True, "system_preference_hidden": True},
        "candidates": candidates,
        "selection": {
            "selected_candidate_id": "c1",
            "reason": "The selected draft best preserves the locked promise, evidence, and authorial restraint.",
            "rejected": [
                {"candidate_id": "c2", "rejected_because": "Its reverse argument delays the central dramatic question too long."},
                {"candidate_id": "c3", "rejected_because": "Its ending-first mechanism weakens the concrete opening and subtext."},
            ],
        },
    }


def _quality(script):
    names = ["structure", "accuracy", "authorial_voice", "language", "channel_fit", "rights", "accessibility", "delivery"]
    return {
        "version": "1.0",
        "deliverables": [{
            "deliverable_id": "master",
            "artifact_sha256": _canonical_artifact_sha256(script),
            "checks": [{"name": name, "status": "pass", "evidence": f"Verified {name} against the locked specification."} for name in names],
            "open_issues": [],
            "verdict": "pass",
        }],
        "open_issues": [],
        "verdict": "pass",
    }


def test_automatic_article_runs_idea_to_draft_postproduction_and_delivery(tmp_path):
    project = "article-run"
    spec = _spec()
    identity = _identity()
    script = _script()

    writes = {
        "idea": {
            "brief": _brief(), "content_spec": spec, "creative_identity": identity,
            "engine_lock": {"engine": "none", "compose_runtime": "none"},
            "run_mode": "automatic", "decision_log": _decision_log(project),
        },
        "script": {
            "script": script, "candidate_bakeoff": _bakeoff(script),
            "content_spec": spec, "creative_identity": identity,
            "run_mode": "automatic",
        },
        "quality": {"content_quality_report": _quality(script), "run_mode": "automatic"},
        "publish": {
            "publish_log": {"version": "1.0", "entries": [{
                "platform": "website", "status": "draft", "timestamp": "2026-07-13T00:00:00Z",
            }]},
            "run_mode": "automatic",
        },
    }
    for stage in ORDER:
        artifacts = writes[stage] | {
            "production_ladder": _ladder(stage),
            "bench_report": _bench(stage),
        }
        path = write_checkpoint(
            tmp_path, project, stage, "completed", artifacts, pipeline_type=PIPELINE,
        )
        assert path.exists()

    assert get_completed_stages(tmp_path, project, PIPELINE) == ORDER


def test_script_cannot_change_locked_format_or_language(tmp_path):
    project = "locked-script"
    spec = _spec()
    identity = _identity()
    idea = {
        "brief": _brief(), "content_spec": spec, "creative_identity": identity,
        "engine_lock": {"engine": "none", "compose_runtime": "none"},
        "run_mode": "automatic", "decision_log": _decision_log(project),
        "production_ladder": _ladder("idea"), "bench_report": _bench("idea"),
    }
    write_checkpoint(tmp_path, project, "idea", "completed", idea, pipeline_type=PIPELINE)

    changed = _script()
    changed["language"] = "en-US"
    artifacts = {
        "script": changed, "candidate_bakeoff": _bakeoff(changed),
        "content_spec": spec, "creative_identity": identity,
        "run_mode": "automatic", "production_ladder": _ladder("script"),
        "bench_report": _bench("script"),
    }
    with pytest.raises(CheckpointValidationError, match="script.language"):
        write_checkpoint(tmp_path, project, "script", "completed", artifacts, pipeline_type=PIPELINE)


def test_multi_deliverable_package_gets_exact_quality_coverage(tmp_path):
    project = "content-package"
    spec = _spec()
    spec["deliverables"] = [
        {
            "id": "body", "kind": "article",
            "target_length": {"unit": "words", "minimum": 700, "maximum": 900},
            "acceptance_criteria": ["Complete source-backed article"],
        },
        {
            "id": "teaser", "kind": "social_teaser", "channel": "website",
            "target_length": {"unit": "words", "minimum": 20, "maximum": 40},
            "acceptance_criteria": ["Accurate teaser without revealing the ending"],
        },
    ]
    identity = _identity()
    idea = {
        "brief": _brief(), "content_spec": spec, "creative_identity": identity,
        "engine_lock": {"engine": "none", "compose_runtime": "none"},
        "run_mode": "automatic", "decision_log": _decision_log(project),
        "production_ladder": _ladder("idea"), "bench_report": _bench("idea"),
    }
    write_checkpoint(tmp_path, project, "idea", "completed", idea, pipeline_type=PIPELINE)
    package = {
        "version": "1.0", "title": "Փաթեթ",
        "deliverables": [
            {
                "deliverable_id": "body", "kind": "article", "language": "hy-AM",
                "blocks": [{"id": "p1", "type": "paragraph", "text": "Հիմնական հոդվածի ճշգրիտ տեքստը։"}],
            },
            {
                "deliverable_id": "teaser", "kind": "social_teaser", "language": "hy-AM",
                "channel": "website",
                "blocks": [{"id": "p1", "type": "caption", "text": "Կարդացեք ամբողջ պատմությունը։"}],
            },
        ],
    }
    script_artifacts = {
        "script": package, "candidate_bakeoff": _bakeoff(package),
        "content_spec": spec, "creative_identity": identity,
        "run_mode": "automatic", "production_ladder": _ladder("script"),
        "bench_report": _bench("script"),
    }
    write_checkpoint(tmp_path, project, "script", "completed", script_artifacts, pipeline_type=PIPELINE)

    checks = ["structure", "accuracy", "authorial_voice", "language", "channel_fit", "rights", "accessibility", "delivery"]
    quality = {
        "version": "1.0",
        "deliverables": [
            {
                "deliverable_id": item["deliverable_id"],
                "artifact_sha256": _canonical_artifact_sha256(item),
                "checks": [{"name": name, "status": "pass", "evidence": f"Verified {name} with concrete evidence."} for name in checks],
                "open_issues": [], "verdict": "pass",
            }
            for item in package["deliverables"]
        ],
        "open_issues": [], "verdict": "pass",
    }
    quality_artifacts = {
        "content_quality_report": quality, "run_mode": "automatic",
        "production_ladder": _ladder("quality"), "bench_report": _bench("quality"),
    }
    write_checkpoint(tmp_path, project, "quality", "completed", quality_artifacts, pipeline_type=PIPELINE)

    tampered = json.loads(json.dumps(quality))
    tampered["deliverables"][1]["artifact_sha256"] = "0" * 64
    quality_artifacts["content_quality_report"] = tampered
    with pytest.raises(CheckpointValidationError, match="wrong draft hash"):
        write_checkpoint(tmp_path, project, "quality", "completed", quality_artifacts, pipeline_type=PIPELINE)


def test_candidate_bakeoff_selected_draft_must_equal_final_script(tmp_path):
    project = "bakeoff-mismatch"
    spec = _spec()
    identity = _identity()
    idea = {
        "brief": _brief(), "content_spec": spec, "creative_identity": identity,
        "engine_lock": {"engine": "none", "compose_runtime": "none"},
        "run_mode": "automatic", "decision_log": _decision_log(project),
        "production_ladder": _ladder("idea"), "bench_report": _bench("idea"),
    }
    write_checkpoint(tmp_path, project, "idea", "completed", idea, pipeline_type=PIPELINE)
    final_script = _script()
    bakeoff = _bakeoff(final_script)
    bakeoff["selection"]["selected_candidate_id"] = "c2"
    artifacts = {
        "script": final_script, "candidate_bakeoff": bakeoff,
        "content_spec": spec, "creative_identity": identity, "run_mode": "automatic",
        "production_ladder": _ladder("script"), "bench_report": _bench("script"),
    }
    with pytest.raises(CheckpointValidationError, match="not byte-for-structure identical"):
        write_checkpoint(tmp_path, project, "script", "completed", artifacts, pipeline_type=PIPELINE)


def test_quarantined_authorial_register_fails_at_idea_not_after_drafting(tmp_path):
    project = "quarantined-register"
    identity = _identity()
    identity["authorial_voice"] = {
        "mode": "strict", "profile_id": "maghakian-script-v1",
        "register": "C", "minimum_score": 0.8,
    }
    artifacts = {
        "brief": _brief(), "content_spec": _spec(), "creative_identity": identity,
        "engine_lock": {"engine": "none", "compose_runtime": "none"},
        "run_mode": "automatic", "decision_log": _decision_log(project),
        "production_ladder": _ladder("idea"), "bench_report": _bench("idea"),
    }
    with pytest.raises(CheckpointValidationError, match="quarantined"):
        write_checkpoint(tmp_path, project, "idea", "completed", artifacts, pipeline_type=PIPELINE)
