"""Typed, versioned registry for ZavodOM's real specialist agents.

The craft bench used to be a list of role names backed only by prose.  This module turns
the roster into executable infrastructure: every specialist has declared capabilities,
triggers, permissions, budgets, failure policy, instruction files, and a platform adapter.
The loader validates all references and hashes the exact registry/instructions so a later
execution receipt can prove what the specialist was asked to follow.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY_PATH = ROOT / "agents" / "registry.yaml"
REGISTRY_SCHEMA_PATH = ROOT / "schemas" / "agents" / "agent_registry.schema.json"
COMMON_AGENT_INSTRUCTIONS = ("skills/meta/agent-routing.md",)


class AgentRegistryError(ValueError):
    """Raised when agent discovery is ambiguous, unsafe, or internally inconsistent."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def task_contract_hash(task: dict[str, Any]) -> str:
    """Hash the complete executable task contract, excluding only its own hash field."""
    contract = {key: value for key, value in task.items() if key != "idempotency_key"}
    return content_hash({"task_contract": contract})


def _validate_claude_adapter(path: Path, agent_id: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise AgentRegistryError(f"Claude adapter has no YAML frontmatter: {path}")
    boundary = text.find("\n---\n", 4)
    try:
        frontmatter = yaml.safe_load(text[4:boundary])
    except yaml.YAMLError as exc:
        raise AgentRegistryError(f"Claude adapter frontmatter is invalid: {path}") from exc
    if not isinstance(frontmatter, dict):
        raise AgentRegistryError(f"Claude adapter frontmatter must be an object: {path}")
    required = {"name", "description", "tools", "model"}
    missing = sorted(required - set(frontmatter))
    if missing:
        raise AgentRegistryError(f"Claude adapter {path} misses frontmatter fields: {missing}")
    if frontmatter["name"] != path.stem:
        raise AgentRegistryError(
            f"Claude adapter name {frontmatter['name']!r} must match file stem {path.stem!r}."
        )
    if frontmatter["model"] != "inherit":
        raise AgentRegistryError(f"Claude adapter {path} must use model: inherit.")
    if len(str(frontmatter["description"]).strip()) < 20:
        raise AgentRegistryError(f"Claude adapter {path} needs a precise discovery description.")
    if not str(frontmatter["tools"]).strip():
        raise AgentRegistryError(f"Claude adapter {path} needs an explicit minimal tool set.")
    body = text[boundary + 5:]
    if f"registry agent `{agent_id}`" not in body:
        raise AgentRegistryError(
            f"Claude adapter {path} is not bound to registry agent {agent_id!r}."
        )


def _safe_repo_path(raw: str, *, suffix: str | None = None) -> Path:
    candidate = (ROOT / raw).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError as exc:
        raise AgentRegistryError(f"Agent registry path escapes repository: {raw!r}") from exc
    if suffix and candidate.suffix != suffix:
        raise AgentRegistryError(f"Agent registry path {raw!r} must end in {suffix!r}.")
    if not candidate.is_file():
        raise AgentRegistryError(f"Agent registry references missing file: {raw!r}")
    return candidate


@dataclass(frozen=True)
class AgentRegistry:
    raw: dict[str, Any]
    path: Path
    agents: dict[str, dict[str, Any]]
    registry_hash: str

    @property
    def version(self) -> str:
        return str(self.raw["version"])

    @property
    def policy(self) -> dict[str, Any]:
        return dict(self.raw["policy"])

    def get(self, agent_id: str) -> dict[str, Any]:
        try:
            return self.agents[agent_id]
        except KeyError as exc:
            raise AgentRegistryError(f"Unknown agent id: {agent_id!r}") from exc

    def capability_index(self) -> dict[str, tuple[str, ...]]:
        grouped: dict[str, list[str]] = {}
        for agent_id, card in self.agents.items():
            for capability in card["capabilities"]:
                grouped.setdefault(capability, []).append(agent_id)
        return {key: tuple(sorted(values)) for key, values in sorted(grouped.items())}

    def instruction_hashes(self, agent_id: str) -> dict[str, str]:
        card = self.get(agent_id)
        return {
            raw: file_hash(_safe_repo_path(raw, suffix=".md"))
            for raw in dict.fromkeys([*COMMON_AGENT_INSTRUCTIONS, *card["skills"]])
        }

    def platform_adapter_hashes(self, agent_id: str) -> dict[str, str]:
        card = self.get(agent_id)
        raw = card["platform"]["claude_agent_file"]
        if not raw:
            return {}
        return {raw: file_hash(_safe_repo_path(raw, suffix=".md"))}

    def cards(self, *, kinds: Iterable[str] | None = None) -> list[dict[str, Any]]:
        allowed = set(kinds or ())
        cards = list(self.agents.values())
        if allowed:
            cards = [card for card in cards if card["kind"] in allowed]
        return sorted(cards, key=lambda card: (-card["priority"], card["id"]))


def load_agent_registry(
    path: str | Path | None = None,
    *,
    verify_platform_adapters: bool = True,
) -> AgentRegistry:
    registry_path = Path(path or DEFAULT_REGISTRY_PATH).resolve()
    if not registry_path.is_file():
        raise AgentRegistryError(f"Agent registry not found: {registry_path}")

    raw = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AgentRegistryError("Agent registry root must be an object.")
    schema = json.loads(REGISTRY_SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        jsonschema.Draft202012Validator(schema).validate(raw)
    except jsonschema.ValidationError as exc:
        where = ".".join(str(part) for part in exc.absolute_path) or "<root>"
        raise AgentRegistryError(f"Invalid agent registry at {where}: {exc.message}") from exc

    cards = raw["agents"]
    for instruction in COMMON_AGENT_INSTRUCTIONS:
        _safe_repo_path(instruction, suffix=".md")
    ids = [card["id"] for card in cards]
    if len(ids) != len(set(ids)):
        duplicates = sorted({agent_id for agent_id in ids if ids.count(agent_id) > 1})
        raise AgentRegistryError(f"Duplicate agent ids: {duplicates}")
    by_id = {card["id"]: card for card in cards}

    policy = raw["policy"]
    coordinator = by_id.get(policy["coordinator"])
    verifier = by_id.get(policy["verifier"])
    if not coordinator or coordinator["kind"] != "coordinator":
        raise AgentRegistryError("policy.coordinator must reference a coordinator agent.")
    if not verifier or verifier["kind"] != "verifier":
        raise AgentRegistryError("policy.verifier must reference a verifier agent.")
    if coordinator["id"] == verifier["id"]:
        raise AgentRegistryError("Coordinator and independent verifier must be different agents.")

    for card in cards:
        if card["activation_mode"] == "always" and not card["always_selected"]:
            raise AgentRegistryError(
                f"Always-active agent {card['id']!r} must set always_selected=true."
            )
        if card["activation_mode"] != "always" and card["always_selected"]:
            raise AgentRegistryError(
                f"Agent {card['id']!r} cannot be always_selected in "
                f"activation mode {card['activation_mode']!r}."
            )
        if card["activation_mode"] == "fallback_only" and card["failure_policy"] != "fail_closed":
            raise AgentRegistryError(
                f"Fallback-only agent {card['id']!r} must fail closed after one attempt."
            )
        for skill in card["skills"]:
            _safe_repo_path(skill, suffix=".md")
        fallback = card["fallback_agent"]
        if fallback is not None and fallback not in by_id:
            raise AgentRegistryError(
                f"Agent {card['id']!r} references unknown fallback {fallback!r}."
            )
        if fallback == card["id"]:
            raise AgentRegistryError(f"Agent {card['id']!r} cannot fall back to itself.")
        if card["failure_policy"] == "fail_closed" and fallback is not None:
            raise AgentRegistryError(
                f"Fail-closed agent {card['id']!r} cannot declare a fallback."
            )
        if card["failure_policy"] == "fallback" and fallback is None:
            raise AgentRegistryError(
                f"Fallback agent {card['id']!r} must name fallback_agent."
            )
        if card["failure_policy"] == "fallback" and fallback is not None:
            if by_id[fallback]["activation_mode"] != "fallback_only":
                raise AgentRegistryError(
                    f"Fallback {fallback!r} must declare activation_mode='fallback_only'."
                )
            missing = sorted(set(card["capabilities"]) - set(by_id[fallback]["capabilities"]))
            if missing:
                raise AgentRegistryError(
                    f"Fallback {fallback!r} cannot preserve {card['id']!r} capabilities: {missing}"
                )
            missing_tools = sorted(
                set(card["allowed_tools"]) - set(by_id[fallback]["allowed_tools"])
            )
            if missing_tools:
                raise AgentRegistryError(
                    f"Fallback {fallback!r} cannot preserve {card['id']!r} tool permissions: "
                    f"{missing_tools}"
                )
        adapter = card["platform"]["claude_agent_file"]
        if verify_platform_adapters and adapter:
            adapter_path = _safe_repo_path(adapter, suffix=".md")
            _validate_claude_adapter(adapter_path, card["id"])

    registry = AgentRegistry(
        raw=raw,
        path=registry_path,
        agents=by_id,
        registry_hash=content_hash(raw),
    )

    # A capability that exists only on a coordinator or verifier is not dispatchable as
    # specialist work. This is allowed for control-only capabilities but must never shadow
    # a declared specialist need.
    specialist_caps = {
        capability
        for card in registry.cards(kinds={"specialist"})
        for capability in card["capabilities"]
    }
    if not specialist_caps:
        raise AgentRegistryError("Agent registry has no specialist capabilities.")
    return registry


__all__ = [
    "AgentRegistry",
    "AgentRegistryError",
    "COMMON_AGENT_INSTRUCTIONS",
    "DEFAULT_REGISTRY_PATH",
    "canonical_bytes",
    "content_hash",
    "file_hash",
    "load_agent_registry",
    "task_contract_hash",
]
