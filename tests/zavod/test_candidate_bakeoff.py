import copy

from lib.candidate_bakeoff import canonical_sha256, validate_candidate_bakeoff
from tests.zavod.test_universal_content_run import _bakeoff, _script


def test_complete_blind_bakeoff_passes():
    script = _script()
    result = validate_candidate_bakeoff(script, _bakeoff(script))
    assert result["ok"], result["violations"]


def test_duplicate_draft_cannot_pose_as_an_alternative():
    script = _script()
    bakeoff = _bakeoff(script)
    bakeoff["candidates"][1]["draft"] = copy.deepcopy(script)
    bakeoff["candidates"][1]["draft_sha256"] = canonical_sha256(script)
    result = validate_candidate_bakeoff(script, bakeoff)
    assert not result["ok"]
    assert any("not unique" in item for item in result["violations"])


def test_cosmetic_rewrite_is_not_a_material_candidate():
    script = _script()
    bakeoff = _bakeoff(script)
    almost_same = copy.deepcopy(script)
    almost_same["blocks"][-1]["text"] += " Իսկ հետո՝ լռություն։"
    bakeoff["candidates"][1]["draft"] = almost_same
    bakeoff["candidates"][1]["draft_sha256"] = canonical_sha256(almost_same)
    result = validate_candidate_bakeoff(script, bakeoff)
    assert not result["ok"]
    assert any("not a material alternative" in item for item in result["violations"])


def test_every_rejected_candidate_needs_one_reason():
    script = _script()
    bakeoff = _bakeoff(script)
    fourth = copy.deepcopy(bakeoff["candidates"][2])
    fourth["candidate_id"] = "c4"
    fourth["difference_axes"] = ["narrator"]
    fourth["draft"] = copy.deepcopy(fourth["draft"])
    fourth["draft"]["blocks"][0]["text"] = "Պատմողը բացում է չորրորդ, ամբողջովին առանձին կառուցվածքը։"
    fourth["draft_sha256"] = canonical_sha256(fourth["draft"])
    bakeoff["candidates"].append(fourth)
    result = validate_candidate_bakeoff(script, bakeoff)
    assert not result["ok"]
    assert any("every unselected candidate exactly once" in item for item in result["violations"])
