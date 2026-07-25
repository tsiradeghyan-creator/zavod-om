"""Deterministic relevance router and bounded handoff planner for ZavodOM agents.

The host model may extract semantic signals from an open-ended request, but it may not
silently decide which risk specialist can be skipped.  This router combines those structured
signals with multilingual lexical evidence, applies the typed registry, records every selected
and rejected agent, and emits a dependency graph with exact instruction hashes, budgets,
permissions, stop conditions, owner gates, and idempotency keys.

It plans work; platform adapters execute it.  Claude Code uses `.claude/agents`, Codex uses its
native collaboration tools, and API hosts can provide their own executor. A single-context
fallback must be labeled as simulation in the execution ledger and never counts as independent
review.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

import jsonschema

from lib.agent_registry import (
    AgentRegistry,
    content_hash,
    load_agent_registry,
    task_contract_hash,
)
from lib.agent_runtime import validate_activation_plan


ROOT = Path(__file__).resolve().parent.parent
REQUEST_SCHEMA = ROOT / "schemas" / "agents" / "agent_request.schema.json"
PLAN_SCHEMA = ROOT / "schemas" / "agents" / "activation_plan.schema.json"


class AgentRoutingError(ValueError):
    """Raised when a request or activation graph cannot be routed safely."""


INTENT_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("system_change", ("գործակալ", "ագենտ", "համակարգ", "ճարտարապետ", "երթուղիչ", "schema", "pipeline", "orchestrator", "agent system")),
    ("publishing", ("հրապարակ", "տեղադրիր", "publish", "distribution")),
    ("media_production", ("տեսանյութ", "ռենդեր", "մոնտաժ", "հետարտադր", "render", "edit video", "post-production")),
    ("research", ("հետազոտ", "աղբյուր", "վերջին", "համեմատ", "research", "benchmark", "latest source")),
    ("content_transformation", ("թարգման", "տեղայնաց", "վերաշարադր", "translation", "localize", "rewrite")),
    ("content_creation", ("գրիր", "ստեղծիր", "սցենար", "հոդված", "գրառում", "draft", "write", "create", "script")),
)

SIGNAL_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    "topics": {
        "agents": ("գործակալ", "ագենտ", "agent"),
        "architecture": ("ճարտարապետ", "համակարգ", "architecture", "orchestrator"),
        "tests": ("փորձարկ", "թեստ", "test", "eval"),
        "research": ("հետազոտ", "աղբյուր", "research", "source"),
        "benchmark": (
            "աշխարհում լավագույն",
            "աշխարհում ամենալավ",
            "հավասարը չունեն",
            "ամենալավը",
            "լավագույններից լավագույն",
            "համեմատ",
            "benchmark",
            "best in the world",
        ),
        "story": ("պատմություն", "սյուժե", "story", "plot"),
        "structure": ("կառուցվածք", "բիթ", "structure", "beat"),
        "dialogue": ("երկխոսություն", "խոսվածք", "dialogue"),
        "authorial_voice": ("ձեռագիր", "հեղինակային ձայն", "authorial voice", "script dna"),
        "maghakian": ("մաղակյան", "անի մաղաքյան", "maghakian"),
        "visuals": ("տեսողական", "կադր", "visual", "shot"),
        "rights": ("իրավունք", "լիցենզիա", "rights", "license"),
        "consent": ("համաձայնություն", "դեմք", "consent", "likeness"),
        "translation": ("թարգման", "տեղայնաց", "translation", "localization"),
        "subtitles": ("ենթագիր", "subtitle"),
        "render": ("ռենդեր", "render"),
        "edit": ("մոնտաժ", "edit"),
        "audio": ("ձայն", "միքս", "audio", "sound", "mix"),
        "distribution": ("հրապարակ", "հարթակ", "publish", "platform"),
        "analytics": ("վերլուծություն", "աճ", "analytics", "growth"),
    },
    "formats": {
        "screenplay": ("սցենար", "screenplay"),
        "series_episode": ("սերիա", "էպիզոդ", "episode"),
        "stageplay": ("թատերական պիես", "stageplay"),
        "article": ("հոդված", "article"),
        "newsletter": ("լրատու", "newsletter"),
        "social_post": ("գրառում", "social post"),
        "caption": ("նկարագրություն", "caption"),
        "carousel": ("կարուսել", "carousel"),
        "reel": ("ռիլ", "reel"),
        "promo": ("պրոմո", "promo"),
        "short_video": ("կարճ տեսանյութ", "short video"),
        "long_video": ("երկար տեսանյութ", "long video"),
        "documentary": ("վավերագրական", "documentary"),
        "localization": ("տեղայնաց", "localization"),
        "campaign_package": ("արշավ", "campaign"),
    },
    "risks": {
        "factual_claims": ("փաստ", "աղբյուր", "վերջին", "claim", "source", "latest"),
        "voice_drift": ("ձեռագիր", "հեղինակային ձայն", "authorial voice", "script dna"),
        "armenian_glyphs": ("հայերեն", "արևելահայերեն", "armenian"),
        "rights": ("իրավունք", "լիցենզիա", "rights", "license"),
        "likeness": ("դեմք", "նմանություն", "likeness", "face"),
        "publication": ("հրապարակ", "publish"),
        "paid_generation": ("վճարովի", "բյուջե", "paid", "budget"),
        "governance_bypass": ("շրջանց", "անվտանգ", "governance", "bypass"),
        "destructive_change": ("ջնջ", "վերանվան", "միգրացիա", "delete", "rename", "migration"),
    },
}

TOPIC_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "agents": ("agent_orchestration",),
    "architecture": ("system_architecture", "reliability"),
    "tests": ("testing", "adversarial_testing"),
    "research": ("current_research", "source_provenance"),
    "benchmark": ("competitive_benchmark",),
    "story": ("ideation", "story_structure"),
    "structure": ("story_structure", "serial_architecture"),
    "dialogue": ("dialogue", "dialogue_register"),
    "authorial_voice": ("authorial_voice",),
    "maghakian": ("maghakian_script_dna",),
    "visuals": ("visual_language", "directing"),
    "rights": ("rights_clearance", "provenance"),
    "consent": ("consent", "likeness_governance"),
    "translation": ("translation", "localization"),
    "subtitles": ("subtitles", "glyph_quality"),
    "render": ("video_generation", "mastering"),
    "edit": ("editing", "compositing"),
    "audio": ("sound_post",),
    "distribution": ("distribution", "publishing", "platform_adaptation"),
    "analytics": ("analytics", "experimentation"),
}

FORMAT_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "screenplay": ("screenwriting", "story_structure", "authorial_voice"),
    "series_episode": ("screenwriting", "serial_architecture", "authorial_voice"),
    "stageplay": ("screenwriting", "dialogue", "authorial_voice"),
    "article": ("narrative_draft",),
    "newsletter": ("narrative_draft", "marketing_copy"),
    "social_post": ("marketing_copy",),
    "caption": ("marketing_copy",),
    "carousel": ("visual_language", "marketing_copy"),
    "reel": ("visual_language", "video_generation", "editing"),
    "promo": ("visual_language", "video_generation", "rights_clearance"),
    "short_video": ("visual_language", "video_generation", "editing"),
    "long_video": ("visual_language", "video_generation", "editing", "mastering"),
    "documentary": ("factual_accuracy", "source_provenance", "rights_clearance", "editing"),
    "localization": ("translation", "localization", "glyph_quality"),
    "campaign_package": ("format_strategy", "platform_adaptation", "rights_clearance"),
}

# Explicit negative scope beats keyword inference. Without this rule, a phrase such as
# "only the script; visuals do not matter" both excludes the visual director and still asks
# the capability matcher for visual work, producing a falsely blocked plan.
NEGATED_SCOPE_RULES: dict[str, tuple[str, ...]] = {
    "visuals": (
        "տեսողականը կարևոր չէ",
        "տեսողական ոճը կարևոր չէ",
        "գույները հետաքրքիր չեն",
        "գույները կարևոր չեն",
        "visuals are not important",
        "visuals do not matter",
        "no visual work",
    ),
    "media_production": (
        "միայն սցենար",
        "միայն տեքստ",
        "only the script",
        "script only",
        "text only",
    ),
}

NEGATED_SCOPE_CAPABILITIES: dict[str, frozenset[str]] = {
    "visuals": frozenset({
        "visual_language", "directing", "cinematography", "storyboard",
        "production_design",
    }),
    "media_production": frozenset({
        "visual_language", "directing", "cinematography", "storyboard",
        "production_design", "asset_generation", "video_generation", "editing",
        "compositing", "sound_post", "mastering", "rights_clearance", "consent",
        "likeness_governance", "provenance", "ai_disclosure", "platform_adaptation",
        "distribution", "publishing", "analytics", "experimentation",
    }),
}


def _schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(instance: dict[str, Any], schema_path: Path, label: str) -> None:
    try:
        jsonschema.Draft202012Validator(_schema(schema_path)).validate(instance)
    except jsonschema.ValidationError as exc:
        where = ".".join(str(part) for part in exc.absolute_path) or "<root>"
        raise AgentRoutingError(f"Invalid {label} at {where}: {exc.message}") from exc


def _contains(text: str, needles: Iterable[str]) -> list[str]:
    return [needle for needle in needles if needle.casefold() in text]


def _infer_intent(text: str) -> str:
    for intent, keywords in INTENT_KEYWORDS:
        if _contains(text, keywords):
            return intent
    return "question"


def _infer_signals(text: str, field: str) -> list[str]:
    values: list[str] = []
    for value, keywords in SIGNAL_RULES[field].items():
        if _contains(text, keywords):
            values.append(value)
    return sorted(values)


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def build_agent_request(
    text: str,
    *,
    request_id: str | None = None,
    intent: str | None = None,
    topics: Iterable[str] = (),
    formats: Iterable[str] = (),
    languages: Iterable[str] = (),
    risks: Iterable[str] = (),
    required_capabilities: Iterable[str] = (),
    available_tools: Iterable[str] = (),
    input_artifacts: Iterable[str] = (),
    automation_mode: str = "supervised",
    owner_constraints: Iterable[str] = (),
) -> dict[str, Any]:
    """Build a schema-valid request, inferring only signals the text actually supports."""
    if not isinstance(text, str) or not text.strip():
        raise AgentRoutingError("Agent request text must be a non-empty string.")
    normalized = re.sub(r"\s+", " ", text).strip()
    folded = normalized.casefold()
    inferred_topics = _infer_signals(folded, "topics")
    inferred_formats = _infer_signals(folded, "formats")
    inferred_risks = _infer_signals(folded, "risks")
    inferred_languages: list[str] = []
    if re.search(r"[\u0531-\u058F]", normalized):
        inferred_languages.append("hy-AM")

    negated_scopes = {
        scope for scope, phrases in NEGATED_SCOPE_RULES.items() if _contains(folded, phrases)
    }
    if "visuals" in negated_scopes:
        inferred_topics = [topic for topic in inferred_topics if topic != "visuals"]
    all_topics = _unique([*inferred_topics, *topics])
    all_formats = _unique([*inferred_formats, *formats])
    inferred_capabilities = _unique([
        *(cap for topic in all_topics for cap in TOPIC_CAPABILITIES.get(topic, ())),
        *(cap for fmt in all_formats for cap in FORMAT_CAPABILITIES.get(fmt, ())),
    ])
    excluded_capabilities = {
        capability
        for scope in negated_scopes
        for capability in NEGATED_SCOPE_CAPABILITIES[scope]
    }
    inferred_capabilities = [
        capability for capability in inferred_capabilities
        if capability not in excluded_capabilities
    ]
    # Programmatically declared mandatory capabilities are explicit and therefore override a
    # coarse natural-language scope exclusion. Deterministic rights/safety callers can never
    # have their hard requirement erased by a nearby phrase such as "script only".
    all_capabilities = _unique([*inferred_capabilities, *required_capabilities])
    request = {
        "version": "1.0",
        "request_id": request_id or f"req-{hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]}",
        "text": normalized,
        "intent": intent or _infer_intent(folded),
        "topics": all_topics,
        "formats": all_formats,
        "languages": _unique([*inferred_languages, *languages]),
        "risks": _unique([*inferred_risks, *risks]),
        "required_capabilities": all_capabilities,
        "available_tools": _unique(available_tools),
        "input_artifacts": _unique(input_artifacts),
        "automation_mode": automation_mode,
        "owner_constraints": _unique([
            *owner_constraints,
            *(f"explicitly excludes {scope}" for scope in sorted(negated_scopes)),
        ]),
    }
    _validate(request, REQUEST_SCHEMA, "agent request")
    return request


def normalize_agent_request(value: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, str):
        return build_agent_request(value)
    if not isinstance(value, dict):
        raise AgentRoutingError("Agent request must be text or an object.")
    _validate(value, REQUEST_SCHEMA, "agent request")
    return dict(value)


def _score_agent(card: dict[str, Any], request: dict[str, Any]) -> tuple[float, list[str], bool]:
    text = request["text"].casefold()
    trigger = card["trigger"]
    excluded = _contains(text, trigger["keywords_none"])
    if excluded:
        return (-1.0, [f"excluded by request phrase {excluded[0]!r}"], True)

    explicit_scope_exclusions = {
        constraint.removeprefix("explicitly excludes ")
        for constraint in request["owner_constraints"]
        if constraint.startswith("explicitly excludes ")
    }
    requested_capabilities = set(request["required_capabilities"])
    for scope in sorted(explicit_scope_exclusions):
        scoped = NEGATED_SCOPE_CAPABILITIES.get(scope, frozenset())
        affected = set(card["capabilities"]) & scoped
        if affected and not (affected & requested_capabilities):
            return (-1.0, [f"excluded by explicit {scope} scope"], True)

    score = 0.0
    reasons: list[str] = []
    weighted = (
        ("intent", {request["intent"]}, set(trigger["intents_any"]), 2.0),
        ("topic", set(request["topics"]), set(trigger["topics_any"]), 2.0),
        ("format", set(request["formats"]), set(trigger["formats_any"]), 2.5),
        ("language", set(request["languages"]), set(trigger["languages_any"]), 1.0),
        ("risk", set(request["risks"]), set(trigger["risks_any"]), 4.0),
        (
            "capability",
            set(request["required_capabilities"]),
            set(trigger["capabilities_any"]) | set(card["capabilities"]),
            5.0,
        ),
    )
    for label, requested, declared, weight in weighted:
        matches = sorted(requested & declared)
        if matches:
            score += weight * len(matches)
            reasons.append(f"{label}: {', '.join(matches)}")
    keyword_matches = _contains(text, trigger["keywords_any"])
    if keyword_matches:
        score += min(3.0, 1.5 * len(keyword_matches))
        reasons.append(f"request phrase: {', '.join(repr(item) for item in keyword_matches[:3])}")
    return (score, reasons or ["no matching trigger"], False)


def _owner_gate_for(card: dict[str, Any]) -> tuple[str | None, str | None]:
    if card["external_side_effects"] != "approval_required":
        return (None, None)
    if card["id"] == "distribution-growth":
        return ("publication", "External publication requires approval bound to the exact payload hash.")
    if card["id"] == "media-producer":
        return ("cost-or-runtime-change", "Paid generation or a material runtime change requires owner approval.")
    return (f"external-action:{card['id']}", "External side effects require exact owner approval.")


def _task_idempotency_key(
    task: dict[str, Any],
) -> str:
    """Hash the complete executable task contract, not merely its label.

    Owner approval bound to this key becomes stale if instructions, adapter content, tools,
    evidence duties, dependencies, output contract, or side-effect policy change.
    """
    return task_contract_hash(task)


def _task(
    request: dict[str, Any],
    registry: AgentRegistry,
    card: dict[str, Any],
    *,
    task_id: str,
    phase: str,
    wave: int,
    depends_on: list[str],
    objective: str,
    required: bool,
) -> dict[str, Any]:
    request_hash = content_hash(request)
    gate_id, _ = _owner_gate_for(card)
    task = {
        "task_id": task_id,
        "agent_id": card["id"],
        "phase": phase,
        "wave": wave,
        "depends_on": depends_on,
        "required": required,
        "objective": objective,
        "input_hash": request_hash,
        "input_artifacts": _unique([*request["input_artifacts"], *card["input_artifacts"]]),
        "instruction_hashes": registry.instruction_hashes(card["id"]),
        "platform_adapter_hashes": registry.platform_adapter_hashes(card["id"]),
        "output_artifact": card["output_artifact"],
        "allowed_tools": list(card["allowed_tools"]),
        "evidence_required": list(card["evidence_required"]),
        "stop_conditions": list(card["stop_conditions"]),
        "budget": dict(card["budget"]),
        "prompt_version": card["prompt_version"],
        "lineage": None,
        "failure_policy": card["failure_policy"],
        "fallback_agent": card["fallback_agent"],
        "external_side_effects": card["external_side_effects"],
        "approval_gate": gate_id,
        "approval_binding": "idempotency_key" if gate_id else None,
        "fallback_for_task": None,
    }
    task["idempotency_key"] = _task_idempotency_key(task)
    return task


def route_agents(
    value: str | dict[str, Any],
    *,
    registry: AgentRegistry | None = None,
) -> dict[str, Any]:
    """Route a request into a bounded, dependency-aware multi-agent activation plan."""
    request = normalize_agent_request(value)
    registry = registry or load_agent_registry()
    policy = registry.policy
    coordinator_id = policy["coordinator"]
    verifier_id = policy["verifier"]

    scored: dict[str, tuple[float, list[str], bool]] = {
        card["id"]: _score_agent(card, request) for card in registry.cards()
    }
    selected_ids = {
        card["id"]
        for card in registry.cards()
        if card["always_selected"]
    }
    specialist_candidates: list[dict[str, Any]] = []
    for card in registry.cards(kinds={"specialist"}):
        if card["activation_mode"] == "fallback_only":
            continue
        score, reasons, excluded = scored[card["id"]]
        if not excluded and score >= float(policy["route_score_floor"]):
            specialist_candidates.append(card)

    specialist_candidates.sort(
        key=lambda card: (
            -scored[card["id"]][0],
            -card["priority"],
            card["execution_order"],
            card["id"],
        )
    )
    room = max(0, int(policy["max_agents"]) - len(selected_ids))
    selected_ids.update(card["id"] for card in specialist_candidates[:room])

    covered = {
        capability
        for agent_id in selected_ids
        for capability in registry.get(agent_id)["capabilities"]
    }
    unmatched = sorted(set(request["required_capabilities"]) - covered)

    def selection(agent_id: str, selected: bool) -> dict[str, Any]:
        score, reasons, _ = scored[agent_id]
        card = registry.get(agent_id)
        required = selected
        if selected and card["kind"] == "specialist":
            explicit = sorted(set(request["required_capabilities"]) & set(card["capabilities"]))
            if explicit:
                reasons = [*reasons, f"required capability coverage: {', '.join(explicit)}"]
        return {
            "agent_id": agent_id,
            "score": score,
            "reasons": _unique(reasons),
            "required": required,
        }

    selected_cards = [registry.get(agent_id) for agent_id in selected_ids]
    selected_cards.sort(
        key=lambda card: (
            0 if card["id"] == coordinator_id else 2 if card["id"] == verifier_id else 1,
            card["execution_order"],
            -card["priority"],
            card["id"],
        )
    )
    selected = [selection(card["id"], True) for card in selected_cards]
    rejected = [
        selection(card["id"], False)
        for card in registry.cards()
        if card["id"] not in selected_ids
    ]

    tasks: list[dict[str, Any]] = []
    waves: list[dict[str, Any]] = []
    route_id = f"{request['request_id']}:route"
    coordinator = registry.get(coordinator_id)
    route_task = _task(
        request,
        registry,
        coordinator,
        task_id=route_id,
        phase="route",
        wave=0,
        depends_on=[],
        objective=(
            "Lock the request decomposition, owner constraints, activation graph, and exact "
            "input snapshot before any specialist begins work."
        ),
        required=True,
    )
    tasks.append(route_task)
    waves.append({"wave": 0, "task_ids": [route_id], "parallel": False})

    specialists = [
        card for card in selected_cards if card["kind"] == "specialist"
    ]
    previous_wave = [route_id]
    wave_number = 1
    for order in sorted({card["execution_order"] for card in specialists}):
        group = [card for card in specialists if card["execution_order"] == order]
        group = sorted(group, key=lambda card: (-card["priority"], card["id"]))
        task_ids: list[str] = []
        for card in group:
            task_id = f"{request['request_id']}:{card['id']}"
            task_ids.append(task_id)
            required = next(item["required"] for item in selected if item["agent_id"] == card["id"])
            tasks.append(_task(
                request,
                registry,
                card,
                task_id=task_id,
                phase="specialist",
                wave=wave_number,
                depends_on=list(previous_wave),
                objective=(
                    f"Work only as {card['name']} on request {request['request_id']!r}. "
                    f"{card['description']} Return {card['output_artifact']} with the declared evidence."
                ),
                required=required,
            ))
        waves.append({
            "wave": wave_number,
            "task_ids": task_ids,
            "parallel": len(task_ids) > 1 and all(card["parallel_safe"] for card in group),
        })
        previous_wave = task_ids
        wave_number += 1

    synth_id = f"{request['request_id']}:synthesize"
    specialist_dependencies = [
        task["task_id"] for task in tasks if task["phase"] == "specialist"
    ] or [route_id]
    tasks.append(_task(
        request,
        registry,
        coordinator,
        task_id=synth_id,
        phase="synthesize",
        wave=wave_number,
        depends_on=specialist_dependencies,
        objective=(
            "Synthesize the hash-bound specialist contributions into one locked candidate, "
            "retain minority reports and blockers, and stop before any unresolved owner gate."
        ),
        required=True,
    ))
    waves.append({"wave": wave_number, "task_ids": [synth_id], "parallel": False})
    wave_number += 1

    owner_gates: list[dict[str, Any]] = []
    for card in selected_cards:
        gate_id, reason = _owner_gate_for(card)
        if gate_id and reason and gate_id not in {item["gate_id"] for item in owner_gates}:
            binding_task = next(
                task for task in tasks
                if task["agent_id"] == card["id"] and task["phase"] == "specialist"
            )
            owner_gates.append({
                "gate_id": gate_id,
                "reason": reason,
                "action_hash_required": True,
                "binding_task_id": binding_task["task_id"],
                "binding_source": "idempotency_key",
            })
    deferred_owner_gates: list[tuple[str, str]] = []
    if "rights" in request["risks"] or "likeness" in request["risks"]:
        deferred_owner_gates.append((
            "rights-or-likeness",
            "Rights and likeness decisions require approval bound to the exact final candidate.",
        ))
    if "destructive_change" in request["risks"]:
        deferred_owner_gates.append((
            "destructive-change",
            "Destructive repository changes require approval bound to the exact synthesized diff.",
        ))
    if "publication" in request["risks"]:
        deferred_owner_gates.append((
            "publication",
            "External publication requires approval bound to the exact synthesized payload.",
        ))

    owner_gate_task_ids: list[str] = []
    for gate_id, reason in deferred_owner_gates:
        task_id = f"{request['request_id']}:owner:{gate_id}"
        owner_task = _task(
            request,
            registry,
            coordinator,
            task_id=task_id,
            phase="owner_gate",
            wave=wave_number,
            depends_on=[synth_id],
            objective=(
                f"Pause for owner decision at gate {gate_id!r}. Bind approval to the exact "
                "synthesized candidate output hash; do not broaden or reuse the approval."
            ),
            required=True,
        )
        owner_task.update({
            "output_artifact": "owner_approval_receipt",
            "evidence_required": [
                "owner identity and approval timestamp",
                "exact dependency output hash approved",
            ],
            "stop_conditions": [
                "stop until the owner approves the exact dependency output hash",
                "stop if the candidate changes after approval",
            ],
            "external_side_effects": "approval_required",
            "approval_gate": gate_id,
            "approval_binding": "dependency_output_hash",
            "failure_policy": "fail_closed",
            "fallback_agent": None,
        })
        owner_task["idempotency_key"] = _task_idempotency_key(owner_task)
        tasks.append(owner_task)
        owner_gate_task_ids.append(task_id)
        owner_gates.append({
            "gate_id": gate_id,
            "reason": reason,
            "action_hash_required": True,
            "binding_task_id": synth_id,
            "binding_source": "output_hash",
        })
    if owner_gate_task_ids:
        waves.append({
            "wave": wave_number,
            "task_ids": owner_gate_task_ids,
            "parallel": False,
        })
        wave_number += 1

    verifier = registry.get(verifier_id)
    verify_id = f"{request['request_id']}:verify"
    tasks.append(_task(
        request,
        registry,
        verifier,
        task_id=verify_id,
        phase="verify",
        wave=wave_number,
        depends_on=owner_gate_task_ids or [synth_id],
        objective=(
            "Independently attack the final locked candidate, verify every specialist receipt, "
            "exact hash, promised criterion, owner approval, and preserved objection, then return "
            "a structured pass, revise, or reject verdict."
        ),
        required=True,
    ))
    waves.append({"wave": wave_number, "task_ids": [verify_id], "parallel": False})

    plan = {
        "version": "1.0",
        "request_id": request["request_id"],
        "request_hash": content_hash(request),
        "registry_version": registry.version,
        "registry_hash": registry.registry_hash,
        "routing_status": "blocked" if unmatched else "ready",
        "supersedes_plan_hash": None,
        "replan_reason": None,
        "signals": {
            "intent": request["intent"],
            "topics": request["topics"],
            "formats": request["formats"],
            "languages": request["languages"],
            "risks": request["risks"],
            "required_capabilities": request["required_capabilities"],
            "automation_mode": request["automation_mode"],
            "owner_constraints": request["owner_constraints"],
        },
        "selected_agents": selected,
        "rejected_agents": rejected,
        "tasks": tasks,
        "waves": waves,
        "owner_gates": owner_gates,
        "unmatched_capabilities": unmatched,
        "policy": {
            key: policy[key]
            for key in (
                "max_parallel", "max_agents", "max_depth", "max_retries",
                "max_wall_time_seconds", "preserve_dissent"
            )
        },
    }
    _validate(plan, PLAN_SCHEMA, "activation plan")
    if plan["routing_status"] == "ready":
        validate_activation_plan(plan)
    return plan


def route_text(text: str, **request_overrides: Any) -> dict[str, Any]:
    return route_agents(build_agent_request(text, **request_overrides))


def replan_with_fallback(
    plan: dict[str, Any],
    failed_task_id: str,
    *,
    registry: AgentRegistry | None = None,
) -> dict[str, Any]:
    """Create one hash-linked replacement plan after an allowlisted recoverable failure.

    The failed task remains terminal and immutable in its original execution ledger. The new
    plan replaces it with a new task id, identical input hash, original output contract,
    original side-effect policy, and original approval gate. Critical specialists deliberately
    have no fallback, and a fallback cannot recursively fall back again.
    """
    _validate(plan, PLAN_SCHEMA, "activation plan")
    registry = registry or load_agent_registry()
    if plan["registry_hash"] != registry.registry_hash:
        raise AgentRoutingError("Fallback refused: activation plan registry hash is stale.")
    matches = [task for task in plan["tasks"] if task["task_id"] == failed_task_id]
    if len(matches) != 1:
        raise AgentRoutingError(f"Fallback requires one known task, got {failed_task_id!r}.")
    primary = matches[0]
    if primary["phase"] != "specialist":
        raise AgentRoutingError("Control, verification, and synthesis tasks cannot fall back.")
    if primary["failure_policy"] != "fallback" or not primary["fallback_agent"]:
        raise AgentRoutingError(
            f"Task {failed_task_id!r} is {primary['failure_policy']!r}, not fallback-eligible."
        )
    fallback_id = primary["fallback_agent"]
    fallback_card = registry.get(fallback_id)
    primary_card = registry.get(primary["agent_id"])
    missing = sorted(set(primary_card["capabilities"]) - set(fallback_card["capabilities"]))
    if missing:
        raise AgentRoutingError(
            f"Fallback {fallback_id!r} cannot preserve required capabilities: {missing}"
        )

    missing_tools = sorted(
        set(primary["allowed_tools"]) - set(fallback_card["allowed_tools"])
    )
    if missing_tools:
        raise AgentRoutingError(
            f"Fallback {fallback_id!r} cannot preserve exact tool permissions for "
            f"{primary['agent_id']!r}: {missing_tools}."
        )
    replacement_id = f"{failed_task_id}:fallback"
    replacement = copy.deepcopy(primary)
    replacement.update({
        "task_id": replacement_id,
        "agent_id": fallback_id,
        "objective": (
            f"Fallback for failed task {failed_task_id!r}. Preserve the exact input hash, "
            f"permissions, output contract {primary['output_artifact']!r}, evidence duties, "
            "and owner gates; do not broaden scope or reinterpret the request."
        ),
        "instruction_hashes": registry.instruction_hashes(fallback_id),
        "platform_adapter_hashes": registry.platform_adapter_hashes(fallback_id),
        "prompt_version": fallback_card["prompt_version"],
        "lineage": {
            "supersedes_plan_hash": content_hash(plan),
            "primary_task": failed_task_id,
        },
        "allowed_tools": list(primary["allowed_tools"]),
        "budget": {
            "max_turns": min(primary["budget"]["max_turns"], fallback_card["budget"]["max_turns"]),
            "max_seconds": min(primary["budget"]["max_seconds"], fallback_card["budget"]["max_seconds"]),
        },
        "failure_policy": "fail_closed",
        "fallback_agent": None,
        "fallback_for_task": failed_task_id,
    })
    replacement["idempotency_key"] = _task_idempotency_key(replacement)

    new_plan = copy.deepcopy(plan)
    new_plan["supersedes_plan_hash"] = content_hash(plan)
    new_plan["replan_reason"] = (
        f"Allowlisted fallback {fallback_id!r} replaces terminal failed task {failed_task_id!r}."
    )
    new_plan["tasks"] = [
        replacement if task["task_id"] == failed_task_id else task
        for task in new_plan["tasks"]
    ]
    for task in new_plan["tasks"]:
        dependency_changed = failed_task_id in task["depends_on"]
        task["depends_on"] = [
            replacement_id if dependency == failed_task_id else dependency
            for dependency in task["depends_on"]
        ]
        if dependency_changed and task["task_id"] != replacement_id:
            task["lineage"] = {"supersedes_plan_hash": content_hash(plan)}
            task["idempotency_key"] = _task_idempotency_key(task)
    for wave in new_plan["waves"]:
        wave["task_ids"] = [
            replacement_id if task_id == failed_task_id else task_id
            for task_id in wave["task_ids"]
        ]
    for gate in new_plan["owner_gates"]:
        if gate["binding_task_id"] == failed_task_id:
            gate["binding_task_id"] = replacement_id

    previous_selection = next(
        item for item in new_plan["selected_agents"] if item["agent_id"] == primary["agent_id"]
    )
    new_plan["selected_agents"] = [
        item for item in new_plan["selected_agents"] if item["agent_id"] != primary["agent_id"]
    ]
    if fallback_id not in {item["agent_id"] for item in new_plan["selected_agents"]}:
        new_plan["selected_agents"].append({
            "agent_id": fallback_id,
            "score": previous_selection["score"],
            "reasons": [f"allowlisted fallback for {failed_task_id}"],
            "required": previous_selection["required"],
        })
    new_plan["rejected_agents"] = [
        item for item in new_plan["rejected_agents"] if item["agent_id"] != fallback_id
    ]
    new_plan["rejected_agents"].append({
        "agent_id": primary["agent_id"],
        "score": previous_selection["score"],
        "reasons": [f"terminal failure recorded in superseded plan for {failed_task_id}"],
        "required": False,
    })
    new_plan["selected_agents"].sort(key=lambda item: item["agent_id"])
    new_plan["rejected_agents"].sort(key=lambda item: item["agent_id"])
    _validate(new_plan, PLAN_SCHEMA, "fallback activation plan")
    validate_activation_plan(new_plan)
    return new_plan


__all__ = [
    "AgentRoutingError",
    "build_agent_request",
    "normalize_agent_request",
    "replan_with_fallback",
    "route_agents",
    "route_text",
]
