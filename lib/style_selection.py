"""Per-role Style Radar selection for the creative-language council.

The creative-language council does not "decide a vibe" — it must choose a *named*
style per craft role, drawn from the Style Radar registry
(``library/style_radar.json``, mirrored from ``skills/zavod-craft/style-rider.md``).
Each role maps to one radar axis:

    director           ← directors
    cinematographer    ← cinematographers
    editor             ← montage
    production_designer← production_designers
    costume_designer   ← costume_designers
    colorist           ← color_luts

``candidate_styles`` surfaces options for the council to propose; ``validate_selections``
is the contract the checkpoint seam enforces — a completed ``scene_plan`` whose council
left any role unchosen is rejected, exactly like a failed glyph gate.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The radar registry lives in library/ (mirrors skills/zavod-craft/style-rider.md).
REGISTRY = os.path.join(ROOT, "library", "style_radar.json")

# Craft role -> Style Radar axis. These six roles are radar-backed; sound/composer
# are chosen too but have no taste axis, so they are not enforced here.
ROLE_AXIS: dict[str, str] = {
    "director": "directors",
    "cinematographer": "cinematographers",
    "editor": "montage",
    "production_designer": "production_designers",
    "costume_designer": "costume_designers",
    "colorist": "color_luts",
}


def required_roles() -> list[str]:
    """The craft roles the creative-language council must each pick a named style for."""
    return list(ROLE_AXIS)


def _load_registry(path: Optional[str] = None) -> dict[str, Any]:
    try:
        with open(path or REGISTRY, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def candidate_styles(
    role_or_axis: str, *, limit: int = 3, registry_path: Optional[str] = None
) -> list[dict[str, str]]:
    """Return up to ``limit`` named style candidates for a role (or raw axis).

    Best-effort: the council uses this to *propose*; enforcement only checks that a
    pick was made. Returns ``[{"id", "essence"}, ...]``.
    """
    axis = ROLE_AXIS.get(role_or_axis, role_or_axis)
    caps = _load_registry(registry_path).get("capabilities", {})
    items = caps.get(axis, []) or []
    out: list[dict[str, str]] = []
    for it in items[:limit]:
        if isinstance(it, dict) and it.get("id"):
            out.append({"id": it["id"], "essence": it.get("essence", "")})
    return out


def validate_selections(selections: Any) -> dict[str, Any]:
    """Check that the council chose a non-empty named style for every required role.

    Returns ``{"ok", "missing", "empty"}``. ``ok`` is True only when every role in
    :func:`required_roles` is present with a non-empty value.
    """
    sel = selections if isinstance(selections, dict) else {}
    missing = [r for r in ROLE_AXIS if r not in sel]
    empty = [
        r for r in ROLE_AXIS
        if r in sel and not str(_pick_name(sel[r])).strip()
    ]
    return {"ok": not missing and not empty, "missing": missing, "empty": empty}


def _pick_name(value: Any) -> str:
    """A selection may be a bare name string or a ``{"style"/"id"/"name": ...}`` dict."""
    if isinstance(value, dict):
        for key in ("style", "id", "name"):
            if value.get(key):
                return str(value[key])
        return ""
    return str(value or "")


if __name__ == "__main__":  # tiny self-test
    print("required roles:", required_roles())
    print("director candidates:", candidate_styles("director"))
    print("validate empty:", validate_selections({}))
    full = {r: f"pick-{r}" for r in required_roles()}
    print("validate full:", validate_selections(full))
