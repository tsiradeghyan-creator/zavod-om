"""Universal content router for ZavodOM.

The old entry point claimed "any content" while its canonical brief and routing table were
mostly video-shaped.  This module makes the promise inspectable: a schema-valid content
specification maps to a real pipeline (or a loud error), and compound campaigns expand into
an explicit bundle instead of being squeezed through one video pipeline.

The router makes no creative decisions and calls no providers.  It is deterministic
infrastructure: format/modality compatibility, pipeline selection, and required preflight.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from schemas.artifacts import validate_artifact


class ContentRoutingError(ValueError):
    """Raised when a content request cannot be routed without changing its promise."""


@dataclass(frozen=True)
class RouteDecision:
    content_format: str
    primary_pipeline: str
    companion_pipelines: tuple[str, ...]
    reason: str
    required_inputs: tuple[str, ...]
    postproduction_contract: str
    deliverable_routes: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["companion_pipelines"] = list(self.companion_pipelines)
        data["required_inputs"] = list(self.required_inputs)
        data["deliverable_routes"] = [
            {"deliverable_id": deliverable_id, "pipeline": pipeline}
            for deliverable_id, pipeline in self.deliverable_routes
        ]
        return data


TEXT_FORMATS = frozenset({
    "social_post", "caption", "article", "newsletter", "screenplay",
    "series_episode", "stageplay",
})

FORMAT_MODALITIES: dict[str, frozenset[str]] = {
    **{name: frozenset({"text", "mixed"}) for name in TEXT_FORMATS},
    "carousel": frozenset({"image", "mixed"}),
    "reel": frozenset({"video", "mixed"}),
    "promo": frozenset({"video", "image", "mixed"}),
    "short_video": frozenset({"video", "mixed"}),
    "long_video": frozenset({"video", "mixed"}),
    "animated_explainer": frozenset({"video", "mixed"}),
    "talking_head": frozenset({"video", "mixed"}),
    "screen_demo": frozenset({"video", "mixed"}),
    "podcast_repurpose": frozenset({"audio", "video", "mixed"}),
    "localization": frozenset({"text", "audio", "video", "mixed"}),
    "documentary": frozenset({"video", "mixed"}),
    "character_animation": frozenset({"video", "mixed"}),
    "campaign_package": frozenset({"mixed"}),
}

FORMAT_LENGTH_UNITS: dict[str, frozenset[str]] = {
    "social_post": frozenset({"words", "characters"}),
    "caption": frozenset({"words", "characters"}),
    "article": frozenset({"words"}),
    "newsletter": frozenset({"words"}),
    "screenplay": frozenset({"pages", "minutes"}),
    "series_episode": frozenset({"pages", "minutes", "episodes"}),
    "stageplay": frozenset({"pages", "minutes"}),
    "carousel": frozenset({"slides"}),
    "reel": frozenset({"seconds"}),
    "promo": frozenset({"seconds", "minutes"}),
    "short_video": frozenset({"seconds", "minutes"}),
    "long_video": frozenset({"minutes", "seconds"}),
    "animated_explainer": frozenset({"minutes", "seconds"}),
    "talking_head": frozenset({"minutes", "seconds"}),
    "screen_demo": frozenset({"minutes", "seconds"}),
    "podcast_repurpose": frozenset({"minutes", "seconds"}),
    "localization": frozenset({"words", "characters", "minutes", "seconds"}),
    "documentary": frozenset({"minutes", "seconds"}),
    "character_animation": frozenset({"minutes", "seconds"}),
    "campaign_package": frozenset({"words", "characters", "seconds", "minutes", "slides", "pages", "episodes"}),
}

ROUTES: dict[str, RouteDecision] = {
    **{
        name: RouteDecision(
            content_format=name,
            primary_pipeline="zavod-content",
            companion_pipelines=(),
            reason="Text and narrative work uses the format-neutral draft, quality, and delivery path.",
            required_inputs=("content_spec", "creative_identity"),
            postproduction_contract="content_quality_report",
        )
        for name in TEXT_FORMATS
    },
    "carousel": RouteDecision("carousel", "zavod-carousel", (),
        "Slide-based visual storytelling needs carousel sequencing and per-slide checks.",
        ("content_spec", "creative_identity"), "render_report"),
    "reel": RouteDecision("reel", "zavod-reel", (),
        "A reel needs the full short-video production and continuity path.",
        ("content_spec", "creative_identity"), "render_report"),
    "short_video": RouteDecision("short_video", "zavod-reel", (),
        "Short-form video uses the full reel pipeline unless the owner explicitly selects the audited fast lane.",
        ("content_spec", "creative_identity"), "render_report"),
    "promo": RouteDecision("promo", "zavod-promo", (),
        "Promotional media requires source, style, people, storyboard, prompt, and rights locks.",
        ("content_spec", "creative_identity"), "render_report"),
    "long_video": RouteDecision("long_video", "cinematic", (),
        "Long-form authored video defaults to the cinematic pipeline; an explainer hint can override it.",
        ("content_spec",), "render_report"),
    "animated_explainer": RouteDecision("animated_explainer", "animated-explainer", (),
        "Explainers need research, timed narration, visual planning, and composition.",
        ("content_spec",), "render_report"),
    "talking_head": RouteDecision("talking_head", "talking-head", (),
        "Speaker-led source footage uses the talking-head review and edit path.",
        ("content_spec", "source_media_review"), "render_report"),
    "screen_demo": RouteDecision("screen_demo", "screen-demo", (),
        "Software demonstrations require capture-mode selection and UI-safe post-production.",
        ("content_spec",), "render_report"),
    "podcast_repurpose": RouteDecision("podcast_repurpose", "podcast-repurpose", (),
        "Podcast derivatives begin from source audio and create clip-level deliverables.",
        ("content_spec", "source_media_review"), "render_report"),
    "localization": RouteDecision("localization", "localization-dub", (),
        "Localization needs translation, consent-aware voice routing, sync, subtitle, and glyph QC.",
        ("content_spec", "source_media_review"), "render_report"),
    "documentary": RouteDecision("documentary", "documentary-montage", (),
        "Documentary work needs claim provenance and source-led montage governance.",
        ("content_spec", "source_media_review"), "render_report"),
    "character_animation": RouteDecision("character_animation", "character-animation", (),
        "Character animation needs identity, rig, pose, timeline, and character-QA stages.",
        ("content_spec",), "render_report"),
    "campaign_package": RouteDecision("campaign_package", "zavod-promo",
        ("zavod-content", "zavod-carousel", "zavod-reel"),
        "A campaign is a governed bundle: master promise plus text, carousel, and video derivatives.",
        ("content_spec", "creative_identity"), "content_quality_report + render_report"),
}

ALLOWED_HINTS: dict[str, frozenset[str]] = {
    "long_video": frozenset({"cinematic", "animated-explainer", "hybrid", "documentary-montage"}),
    "short_video": frozenset({"zavod-reel", "zavod-reel-fast", "cinematic", "hybrid"}),
    "promo": frozenset({"zavod-promo", "cinematic", "hybrid"}),
}


def route_content(spec: dict[str, Any]) -> RouteDecision:
    """Validate and route a universal content specification.

    A caller may provide ``metadata.pipeline_hint`` only for formats with an explicit
    allowlist.  The override changes the primary route but never suppresses the required
    inputs or post-production contract.
    """
    validate_artifact("content_spec", spec)
    content_format = spec["content_format"]
    modality = spec["primary_modality"]

    allowed_modalities = FORMAT_MODALITIES.get(content_format)
    if not allowed_modalities or modality not in allowed_modalities:
        raise ContentRoutingError(
            f"Format {content_format!r} cannot honestly be delivered as primary modality "
            f"{modality!r}; allowed: {sorted(allowed_modalities or [])}."
        )

    deliverables = spec.get("deliverables") or []
    ids = [item.get("id") for item in deliverables if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        raise ContentRoutingError("Every content_spec deliverable id must be unique.")
    channels = set(spec.get("channels") or [])
    for item in deliverables:
        deliverable_id = item.get("id", "deliverable")
        if content_format == "campaign_package" and not item.get("content_format"):
            raise ContentRoutingError(
                f"Campaign deliverable {deliverable_id!r} must declare content_format."
            )
        channel = item.get("channel")
        if channel and channel not in channels:
            raise ContentRoutingError(
                f"Deliverable {deliverable_id!r} references channel {channel!r}, "
                "which is not declared in content_spec.channels."
            )
        target = item.get("target_length") or {}
        unit = target.get("unit")
        unit_format = (
            item.get("content_format")
            if content_format == "campaign_package"
            else content_format
        )
        allowed_units = FORMAT_LENGTH_UNITS.get(unit_format, frozenset())
        if unit and unit not in allowed_units:
            raise ContentRoutingError(
                f"Deliverable {deliverable_id!r} uses target-length unit {unit!r}; "
                f"{unit_format!r} accepts {sorted(allowed_units)}."
            )
        minimum = target.get("minimum")
        maximum = target.get("maximum")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ContentRoutingError(
                f"Deliverable {deliverable_id!r} has minimum target length above maximum."
            )

    if content_format == "campaign_package":
        sub_routes: list[tuple[str, RouteDecision]] = []
        for item in deliverables:
            sub_format = item.get("content_format")
            if not sub_format:
                raise ContentRoutingError(
                    f"Campaign deliverable {item.get('id')!r} must declare content_format."
                )
            route = ROUTES.get(sub_format)
            if route is None or sub_format == "campaign_package":
                raise ContentRoutingError(
                    f"Campaign deliverable {item.get('id')!r} has no audited sub-route "
                    f"for {sub_format!r}."
                )
            sub_routes.append((item["id"], route))
        ordered_pipelines: list[str] = []
        for _, route in sub_routes:
            if route.primary_pipeline not in ordered_pipelines:
                ordered_pipelines.append(route.primary_pipeline)
        primary = ordered_pipelines[0]
        required_inputs = tuple(dict.fromkeys(
            value for _, route in sub_routes for value in route.required_inputs
        ))
        contracts = tuple(dict.fromkeys(
            route.postproduction_contract for _, route in sub_routes
        ))
        return RouteDecision(
            content_format="campaign_package",
            primary_pipeline=primary,
            companion_pipelines=tuple(ordered_pipelines[1:]),
            reason="Each campaign deliverable is mapped to its own audited production path.",
            required_inputs=required_inputs,
            postproduction_contract=" + ".join(contracts),
            deliverable_routes=tuple(
                (deliverable_id, route.primary_pipeline)
                for deliverable_id, route in sub_routes
            ),
        )

    base = ROUTES.get(content_format)
    if base is None:
        raise ContentRoutingError(
            f"No audited route exists for {content_format!r}; add a manifest and regression proof "
            "before promising production."
        )

    hint = (spec.get("metadata") or {}).get("pipeline_hint")
    if not hint:
        return RouteDecision(
            content_format=base.content_format,
            primary_pipeline=base.primary_pipeline,
            companion_pipelines=base.companion_pipelines,
            reason=base.reason,
            required_inputs=base.required_inputs,
            postproduction_contract=base.postproduction_contract,
            deliverable_routes=tuple(
                (item["id"], base.primary_pipeline) for item in deliverables
            ),
        )
    allowed = ALLOWED_HINTS.get(content_format, frozenset())
    if hint not in allowed:
        raise ContentRoutingError(
            f"Pipeline hint {hint!r} is not allowed for {content_format!r}; "
            f"audited options: {sorted(allowed)}."
        )
    return RouteDecision(
        content_format=base.content_format,
        primary_pipeline=hint,
        companion_pipelines=base.companion_pipelines,
        reason=f"Owner/brief selected audited route {hint!r}. {base.reason}",
        required_inputs=base.required_inputs,
        postproduction_contract=base.postproduction_contract,
        deliverable_routes=tuple((item["id"], hint) for item in deliverables),
    )


def route_file(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return route_content(json.load(handle)).to_dict()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Route a ZavodOM content_spec JSON file")
    parser.add_argument("spec")
    args = parser.parse_args()
    print(json.dumps(route_file(args.spec), ensure_ascii=False, indent=2))
