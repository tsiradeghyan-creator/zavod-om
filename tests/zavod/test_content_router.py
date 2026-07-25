import pytest

from lib.content_router import ContentRoutingError, route_content
from schemas.artifacts import validate_artifact


def _spec(content_format="article", modality="text", hint=None):
    spec = {
        "version": "1.0",
        "content_format": content_format,
        "primary_modality": modality,
        "language": "hy-AM",
        "channels": ["website"],
        "deliverables": [{
            "id": "master",
            "kind": content_format,
            "target_length": {"unit": "words", "minimum": 700, "maximum": 900},
            "acceptance_criteria": ["One clear argument with source-backed claims"],
        }],
        "automation_mode": "automatic",
    }
    if hint:
        spec["metadata"] = {"pipeline_hint": hint}
    return spec


def test_text_routes_to_format_neutral_pipeline():
    spec = _spec()
    validate_artifact("content_spec", spec)
    route = route_content(spec)
    assert route.primary_pipeline == "zavod-content"
    assert route.postproduction_contract == "content_quality_report"


def test_campaign_expands_to_explicit_bundle():
    spec = _spec("campaign_package", "mixed")
    spec["deliverables"] = [
        {
            "id": "article", "kind": "master article", "content_format": "article",
            "target_length": {"unit": "words", "minimum": 700},
            "acceptance_criteria": ["One source-backed master argument"],
        },
        {
            "id": "carousel", "kind": "carousel", "content_format": "carousel",
            "target_length": {"unit": "slides", "minimum": 6},
            "acceptance_criteria": ["A complete slide narrative"],
        },
        {
            "id": "reel", "kind": "short video", "content_format": "reel",
            "target_length": {"unit": "seconds", "minimum": 30, "maximum": 60},
            "acceptance_criteria": ["A complete vertical story"],
        },
        {
            "id": "promo", "kind": "campaign promo", "content_format": "promo",
            "target_length": {"unit": "seconds", "minimum": 15},
            "acceptance_criteria": ["A rights-cleared promotional cut"],
        },
    ]
    route = route_content(spec)
    assert route.primary_pipeline == "zavod-content"
    assert set(route.companion_pipelines) == {"zavod-carousel", "zavod-reel", "zavod-promo"}
    assert dict(route.deliverable_routes) == {
        "article": "zavod-content", "carousel": "zavod-carousel",
        "reel": "zavod-reel", "promo": "zavod-promo",
    }


def test_campaign_refuses_an_ambiguous_deliverable():
    spec = _spec("campaign_package", "mixed")
    spec["deliverables"][0]["target_length"] = {"unit": "words", "minimum": 100}
    with pytest.raises(ContentRoutingError, match="must declare content_format"):
        route_content(spec)


def test_incompatible_modality_fails_loudly():
    with pytest.raises(ContentRoutingError, match="cannot honestly"):
        route_content(_spec("screenplay", "video"))


def test_pipeline_hint_is_allowlisted():
    spec = _spec("long_video", "video", "animated-explainer")
    spec["deliverables"][0]["target_length"] = {"unit": "minutes", "minimum": 5}
    assert route_content(spec).primary_pipeline == "animated-explainer"

    with pytest.raises(ContentRoutingError, match="not allowed"):
        route_content(_spec("article", "text", "zavod-reel"))


def test_duplicate_deliverables_and_impossible_lengths_fail_before_production():
    duplicate = _spec()
    duplicate["deliverables"].append(dict(duplicate["deliverables"][0]))
    with pytest.raises(ContentRoutingError, match="unique"):
        route_content(duplicate)

    impossible = _spec()
    impossible["deliverables"][0]["target_length"] = {
        "unit": "words", "minimum": 900, "maximum": 700,
    }
    with pytest.raises(ContentRoutingError, match="above maximum"):
        route_content(impossible)


def test_target_length_units_and_channels_are_format_checked():
    wrong_unit = _spec("screenplay", "text")
    with pytest.raises(ContentRoutingError, match="target-length unit"):
        route_content(wrong_unit)

    unknown_channel = _spec()
    unknown_channel["deliverables"][0]["channel"] = "newsletter"
    with pytest.raises(ContentRoutingError, match="not declared"):
        route_content(unknown_channel)
