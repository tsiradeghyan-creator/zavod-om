import copy

import pytest

from lib.authorial_voice import (
    CRITERIA,
    load_profile,
    objective_signals,
    report_seed,
    script_text,
    validate_voice_report,
)
from lib.bench_gate import required_bench
from lib.checkpoint import CheckpointValidationError, _enforce_zavod_gates
from schemas.artifacts import validate_artifact
from tests.zavod.test_ideal_run import _story_bible


def _script():
    return {
        "version": "1.0",
        "title": "Փորձնական տեսարան",
        "content_format": "screenplay",
        "language": "hy-AM",
        "blocks": [
            {"id": "b1", "type": "scene_heading", "text": "1. ՏԵՍԱՐԱՆ"},
            {"id": "b2", "type": "action", "text": "Անին բաժակը դնում է սեղանին ու չի նայում Արմանին։"},
            {"id": "b3", "type": "dialogue", "speaker": "ԱՐՄԱՆ", "text": "Գնո՞ւմ ես։"},
            {"id": "b4", "type": "dialogue", "speaker": "ԱՆԻ", "text": "Դուռը բաց ա,,, եթե ուզում ես՝ դու գնա։"},
            {"id": "b5", "type": "action", "text": "Արմանը վերցնում է բաժակը, բայց չի խմում։"},
            {"id": "b6", "type": "dialogue", "speaker": "ԱՐՄԱՆ", "text": "Я не про дверь."},
            {"id": "b7", "type": "action", "text": "Անին ուղղում է ծաղկամանի թեքված ճյուղը։"},
            {"id": "b8", "type": "dialogue", "speaker": "ԱՆԻ", "text": "Ես էլ։"},
        ],
    }


def _report(script=None):
    script = script or _script()
    profile = load_profile()
    report = report_seed(script, profile=profile, register="A1")
    excerpts = [
        "Անին բաժակը դնում է սեղանին ու չի նայում Արմանին։",
        "Դուռը բաց ա,,, եթե ուզում ես՝ դու գնա։",
        "Անին ուղղում է ծաղկամանի թեքված ճյուղը։",
    ]
    corpus_refs = ["դու1.txt#voice-evidence", "դու2.txt#voice-evidence", "դու3.txt#voice-evidence"]
    report["criteria"] = [
        {
            "criterion": name,
            "score": 4,
            "evidence": [{
                "draft_excerpt": excerpts[index % len(excerpts)],
                "rationale": f"This concrete action supplies draft evidence for {name} without stated emotion.",
                "corpus_ref": corpus_refs[index % len(corpus_refs)],
            }],
        }
        for index, name in enumerate(CRITERIA)
    ]
    report["overall_score"] = 0.8
    report["verdict"] = "pass"
    report["blocking_issues"] = []
    return report


def test_evidence_backed_authorial_report_passes():
    script = _script()
    report = _report(script)
    validate_artifact("script", script)
    validate_artifact("authorial_voice_report", report)
    result = validate_voice_report(script, report, profile=load_profile(), register="A1")
    assert result["ok"], result["violations"]


def test_report_cannot_survive_draft_change():
    script = _script()
    report = _report(script)
    changed = copy.deepcopy(script)
    changed["blocks"][1]["text"] = "Անին հեռանում է։"
    result = validate_voice_report(changed, report, profile=load_profile(), register="A1")
    assert not result["ok"]
    assert any("draft_sha256" in item for item in result["violations"])


def test_fabricated_corpus_reference_is_rejected():
    report = _report()
    report["criteria"][0]["evidence"][0]["corpus_ref"] = "չգոյություն-ունեցող.txt#1"
    result = validate_voice_report(_script(), report, profile=load_profile(), register="A1")
    assert not result["ok"]
    assert any("outside the pinned profile" in item for item in result["violations"])


def test_one_reused_excerpt_cannot_fake_all_creative_criteria():
    report = _report()
    excerpt = report["criteria"][0]["evidence"][0]["draft_excerpt"]
    for item in report["criteria"]:
        item["evidence"][0]["draft_excerpt"] = excerpt
    result = validate_voice_report(_script(), report, profile=load_profile(), register="A1")
    assert not result["ok"]
    assert any("distinct excerpts" in item for item in result["violations"])


def test_pass_verdict_cannot_hide_a_blocking_issue():
    report = _report()
    report["blocking_issues"] = ["The protagonist's motive is still unclear."]
    result = validate_voice_report(_script(), report, profile=load_profile(), register="A1")
    assert not result["ok"]
    assert any("blocking_issues" in item for item in result["violations"])


def test_legitimate_russian_code_switch_does_not_break_authorial_glyph_signal():
    result = validate_voice_report(_script(), _report(), profile=load_profile(), register="A1")
    assert result["objective"]["glyph_pass"] is True


def test_multi_deliverable_draft_is_not_invisible_to_voice_gate():
    package = {
        "version": "1.0", "title": "Փաթեթ",
        "deliverables": [{
            "deliverable_id": "scene", "kind": "screenplay", "language": "hy-AM",
            "blocks": _script()["blocks"],
        }],
    }
    text = script_text(package)
    assert "Անին բաժակը դնում է" in text
    signals = objective_signals(package, "A1", load_profile())
    assert signals["format_signal"] >= 0.66


def test_generic_explanatory_melodrama_misses_a1_register_signal():
    generic = {
        "version": "1.0", "title": "Ընդհանուր տեսարան",
        "content_format": "screenplay", "language": "hy-AM",
        "blocks": [
            {"id": "b1", "type": "scene_heading", "text": "1. ՏԵՍԱՐԱՆ"},
            {"id": "b2", "type": "action", "text": "Աննան մտնում է սենյակ և տխուր նայում պատուհանին։"},
            {"id": "b3", "type": "dialogue", "speaker": "ԱՆՆԱ", "text": "Ես շատ տխուր եմ, որովհետև դու հեռացար։"},
        ],
    }
    profile = load_profile()
    signals = objective_signals(generic, "A1", profile)
    floor = profile["registers"]["A1"]["minimum_signal"]
    assert signals["register_signal"] < floor


def _script_bench():
    return {
        "stage": "script",
        "bench": {
            role: {
                "ruling": f"The {role} reviewed dialogue, structure, register fidelity, and evidence independently for specialist position {index}.",
                "verdict": "approve",
            }
            for index, role in enumerate(required_bench("script", "zavod-content"))
        },
    }


def _strict_checkpoint(report=None):
    return {
        "pipeline_type": "zavod-content",
        "stage": "script",
        "status": "completed",
        "artifacts": {
            "script": _script(),
            "content_spec": {
                "version": "1.0", "content_format": "screenplay", "primary_modality": "text",
                "language": "hy-AM", "channels": ["production"], "automation_mode": "automatic",
                "deliverables": [{"id": "master", "kind": "screenplay",
                                  "acceptance_criteria": ["A complete scene"]}],
            },
            "creative_identity": {
                "version": "1.0", "identity_id": "ani-screenplay",
                "authorial_voice": {"mode": "strict", "profile_id": "maghakian-script-v1",
                                     "register": "A1", "minimum_score": 0.8},
            },
            "story_bible": _story_bible(),
            "authorial_voice_report": report if report is not None else _report(),
            "bench_report": _script_bench(),
        },
    }


def test_strict_voice_report_is_wired_into_checkpoint_seam():
    _enforce_zavod_gates(_strict_checkpoint())


def test_strict_voice_cannot_close_without_report():
    checkpoint = _strict_checkpoint()
    del checkpoint["artifacts"]["authorial_voice_report"]
    with pytest.raises(CheckpointValidationError, match="authorial_voice_report"):
        _enforce_zavod_gates(checkpoint)


def test_strict_voice_rejects_self_declared_pass_with_wrong_hash():
    report = _report()
    report["draft_sha256"] = "0" * 64
    with pytest.raises(CheckpointValidationError, match="draft_sha256"):
        _enforce_zavod_gates(_strict_checkpoint(report))
