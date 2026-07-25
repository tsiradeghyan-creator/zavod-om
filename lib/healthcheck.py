"""ZavodOM health-check — the council's #1 ask: a human-readable session-start signal.

Run at the top of any session: `./.venv/bin/python lib/healthcheck.py`.
Answers in ~seconds: is the brain present, are the gates live, do the manifests/schemas
validate, is render reachable, is the Scout registry there. Prints GREEN/RED per item so
failures are visible to a human instead of silently drifting.
"""

from __future__ import annotations

import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OK, BAD = "✅", "❌"


def _corpus():
    # the brain's voice source (style-profile.md derives from it)
    cands = [os.path.expanduser("~/Documents/Maghakian-Scripts/docx"),
             os.path.expanduser("~/Documents/Maghakian-Scripts/txt")]
    hit = [c for c in cands if os.path.isdir(c) and os.listdir(c)]
    return (bool(hit), f"{len(glob.glob(hit[0]+'/*'))} files in {hit[0]}" if hit else "NOT FOUND (style-profile source) — back it up")


def _brain():
    d = os.path.join(ROOT, "skills/zavod-craft")
    files = glob.glob(d + "/*.md")
    craft = [
        p for p in files
        if os.path.basename(p) not in {"SKILL.md", "INDEX.md"}
    ]
    return (
        len(craft) >= 40 and os.path.exists(d + "/INDEX.md"),
        f"{len(craft)} craft files + SKILL + INDEX" if craft else "missing",
    )


def _ffmpeg():
    from lib.continuity_checker import find_ffmpeg
    f = find_ffmpeg()
    return (bool(f), f or "NOT FOUND — render/continuity sampling will fail")


def _manifests():
    from lib.pipeline_loader import load_pipeline
    names = [os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, "pipeline_defs/zavod-*.yaml"))]
    bad = []
    for n in names:
        try:
            load_pipeline(n)
        except Exception as e:
            bad.append(f"{n}({e.__class__.__name__})")
    return (not bad and bool(names), f"{len(names)} zavod manifests valid" if not bad else f"INVALID: {bad}")


def _gates():
    from lib.armenian_glyph_gate import gate as glyph
    from lib.continuity_checker import verdict as cont
    from lib.brand_voice_check import check as voice
    g = glyph({"t": "Vanը"})["verdict"] == "fail"
    c = cont({"anchors": [{"name": "x", "kind": "object", "persists": False}]})["verdict"] == "fail"
    v = voice("unlock revolutionary cutting-edge seamless")["verdict"] == "revise"
    native = []
    for m in ("lib.delivery_promise", "lib.variation_checker", "lib.verify_scene_pacing"):
        __import__(m)
        native.append(m.split(".")[-1])
    from lib.gatechain import run_rights_gates
    rights_bad = {
        "version": "1.0", "project_id": "health", "entries": [{
            "asset_id": "x", "asset_type": "text", "status": "unknown",
            "source": "unknown", "evidence": ["pending"],
        }],
        "ai_disclosure": {"required": False, "decision": "not_required"},
    }
    r = run_rights_gates(rights_bad)["verdict"] == "fail"
    allok = g and c and v and r
    return (allok, f"glyph/continuity/brand_voice/rights live; native: {','.join(native)}" if allok else "a gate failed self-check")


def _authorial_voice():
    from lib.authorial_voice import DEFAULT_PROFILE_PATH, load_profile, profile_sha256
    if not DEFAULT_PROFILE_PATH.exists():
        return (False, f"missing {DEFAULT_PROFILE_PATH.name}")
    profile = load_profile()
    files = (profile.get("sources") or {}).get("files") or []
    registers = profile.get("registers") or {}
    quarantined = sorted(
        name for name, value in registers.items()
        if isinstance(value, dict) and value.get("status") == "quarantined_no_clean_sources"
    )
    extractor = os.path.join(ROOT, "scripts/voice_extractor.py")
    ok = (
        profile.get("profile_id") == "maghakian-script-v1"
        and len(files) >= 40
        and all(name in registers for name in ("A1", "A2", "A3", "A4", "A5", "A6", "B", "C"))
        and os.path.exists(extractor)
    )
    detail = (
        f"{profile.get('profile_id')} pinned to {len(files)} sources / {len(registers)} registers "
        f"({profile_sha256(profile)[:12]}); incremental extractor live"
        + (f"; quarantined register(s): {','.join(quarantined)}" if quarantined else "")
    )
    return (ok, detail if ok else f"invalid authorial profile: {detail}")


def _universal_router():
    from lib.content_router import route_content
    spec = {
        "version": "1.0", "content_format": "article", "primary_modality": "text",
        "language": "hy-AM", "channels": ["website"], "automation_mode": "automatic",
        "deliverables": [{"id": "master", "kind": "article",
                          "acceptance_criteria": ["evidence-backed article"]}],
    }
    route = route_content(spec)
    ok = route.primary_pipeline == "zavod-content"
    return (ok, f"article → {route.primary_pipeline}; format/modality contracts live")


def _agent_activation():
    import tempfile
    from pathlib import Path

    from lib.agent_registry import content_hash, load_agent_registry
    from lib.agent_router import build_agent_request, route_agents
    from lib.agent_runtime import TaskLedger
    from lib.orchestrator import execute_agent_run, initialize_agent_run

    registry = load_agent_registry()
    system_plan = route_agents(
        "Գործակալների համակարգը համեմատի՛ր աշխարհի լավագույն լուծումների հետ և ամրացրու այն",
        registry=registry,
    )
    script_plan = route_agents(
        "Գրիր հայկական սցենար իմ հեղինակային ձեռագրով։ Միայն սցենար․ գույները կարևոր չեն։",
        registry=registry,
    )
    system_agents = {item["agent_id"] for item in system_plan["selected_agents"]}
    script_agents = {item["agent_id"] for item in script_plan["selected_agents"]}
    expected_system = {
        "executive-producer", "system-architect", "research-accuracy", "quality-auditor",
    }
    expected_script = {
        "executive-producer", "story-architect", "authorial-voice-guardian",
        "scriptwriter", "quality-auditor",
    }
    phases = [
        next(task["phase"] for task in system_plan["tasks"] if task["task_id"] == wave["task_ids"][0])
        for wave in system_plan["waves"]
    ]
    route_ok = (
        system_plan["routing_status"] == "ready"
        and script_plan["routing_status"] == "ready"
        and system_agents == expected_system
        and script_agents == expected_script
        and "resilience-generalist" not in system_agents | script_agents
        and phases[0] == "route"
        and phases[-2:] == ["synthesize", "verify"]
        and max(len(wave["task_ids"]) for wave in system_plan["waves"])
        <= registry.policy["max_parallel"]
    )
    with tempfile.TemporaryDirectory() as directory:
        ledger = TaskLedger.create(Path(directory) / "ledger.json", system_plan)
        ledger_ok = ledger.completion_report()["status"] == "running"
    with tempfile.TemporaryDirectory() as directory:
        request = build_agent_request(
            "Կատարիր գործակալ համակարգի ճարտարապետական թեստ և աուդիտ։",
            request_id="health-agent-dispatch",
        )
        initialize_agent_run(Path(directory), "health-project", request)

        def host(task, _context):
            output = {"health-task": task["task_id"]}
            return {
                "status": "completed",
                "executor": {
                    "type": "api_agent",
                    "run_id": f"health:{task['task_id']}",
                    "model": "health-contract-agent",
                    "prompt_version": task["prompt_version"],
                },
                "output_artifact": task["output_artifact"],
                "output": output,
                "output_hash": content_hash(output),
                "evidence": [f"health-receipt:{task['task_id']}"],
                "verdict": "pass" if task["phase"] == "verify" else None,
                "reason": "Health-check host completed the exact task contract.",
            }

        dispatch_state = execute_agent_run(
            Path(directory), "health-project", request["request_id"], host
        )
        dispatcher_ok = dispatch_state["completion"]["status"] == "complete"
    adapters = [
        card["platform"]["claude_agent_file"]
        for card in registry.cards()
        if card["platform"]["claude_agent_file"]
    ]
    ok = route_ok and ledger_ok and dispatcher_ok and len(adapters) == len(registry.agents) == 13
    detail = (
        "13 typed cards/adapters; exact routing, automatic host-dispatch loop, bounded waves, immutable receipts, "
        "fallback-only reserve, and independent final verification live; host execution "
        "is proven per run by receipts"
    )
    return (ok, detail if ok else "agent registry/router/ledger self-check failed")


def _provenance_integrity():
    import tempfile
    from pathlib import Path

    from lib.provenance import sha256_file, verify_rights_files

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        payload = root / "final.txt"
        payload.write_text("approved payload", encoding="utf-8")
        rights = {
            "entries": [{
                "asset_id": "final", "artifact_path": "final.txt",
                "artifact_sha256": sha256_file(payload),
            }],
        }
        publish = {"entries": [{
            "status": "published", "export_path": "final.txt",
            "url": "https://example.com/final",
        }]}
        clean = verify_rights_files(rights, publish, root).get("ok") is True
        payload.write_text("changed payload", encoding="utf-8")
        changed = verify_rights_files(rights, publish, root).get("ok") is False
    ok = clean and changed
    return (
        ok,
        "final payload hashes and returned publication URLs are fail-closed"
        if ok else "final payload provenance self-check failed",
    )


def _schemas():
    import jsonschema
    files = glob.glob(os.path.join(ROOT, "schemas/artifacts/*.json"))
    bad = []
    for f in files:
        try:
            jsonschema.Draft202012Validator.check_schema(json.load(open(f)))
        except Exception:
            bad.append(os.path.basename(f))
    return (not bad, f"{len(files)} artifact schemas valid" if not bad else f"INVALID: {bad}")


def _enforcement():
    # the wiring that makes gates non-bypassable: a dirty zavod checkpoint MUST be blocked.
    from lib.checkpoint import _enforce_zavod_gates, CheckpointValidationError
    # reports ride the ONE valid route: render_report.continuity_reports (schema field)
    _bad_rr = {"version": "1.0",
               "outputs": [{"path": "/tmp/c.mp4", "format": "mp4",
                            "resolution": "1080x1920", "duration_seconds": 5.0}],
               "continuity_reports": [{"clip": "c.mp4",
                  "anchors": [{"name": "glass", "kind": "object", "persists": False}]}]}
    dirty = {"pipeline_type": "zavod-reel", "stage": "compose", "status": "completed",
             "artifacts": {"render_report": _bad_rr}}
    try:
        _enforce_zavod_gates(dirty)
        return (False, "NOT WIRED — a broken zavod checkpoint was NOT blocked")
    except CheckpointValidationError:
        # and an upstream pipeline must remain ungated
        ok_up = {"pipeline_type": "cinematic", "stage": "compose", "status": "completed",
                 "artifacts": {"render_report": _bad_rr}}
        _enforce_zavod_gates(ok_up)  # must NOT raise
        return (True, "checkpoint seam blocks dirty zavod artifacts; upstream untouched")


def _scout():
    p = os.path.join(ROOT, "library/known_capabilities.json")
    if not os.path.exists(p):
        return (False, "known_capabilities.json missing")
    reg = json.load(open(p))
    n = sum(len(v) for v in reg.get("capabilities", {}).values())
    if n == 0:
        return (False, "0 known capabilities")
    # Round-6 #5: an adoption without owner approval, rollback anchor, or green post-change
    # suite turns the tree RED — which also blocks the next Scout run (wake-safe gate).
    from lib.scout import adoption_ledger_violations
    bad = adoption_ledger_violations()
    if bad:
        return (False, f"adoption ledger violations: {bad}")
    return (True, f"{n} known capabilities (Scout dedup ready; adoption ledger clean)")


def _style_radar():
    # the living visual-taste registry (style Scout dedups against it)
    p = os.path.join(ROOT, "library/style_radar.json")
    if not os.path.exists(p):
        return (False, "style_radar.json missing")
    reg = json.load(open(p))
    axes = reg.get("capabilities", {})
    n = sum(len(v) for v in axes.values())
    cards = len(glob.glob(os.path.join(ROOT, "skills/zavod-craft/style-library/*.md")))
    return (n > 0, f"{n} styles across {len(axes)} axes, {cards} matured cards (Style Radar ready)")


def _memo_inbox():
    # Decision-debt visibility (2026-07-02 council): an undecided GATED memo must be LOUD at
    # every session start, but must not block production (it is taste/capability debt, not a
    # broken tree) — so this check stays green with a shouting detail line. The hard failure
    # lives in the scan drivers themselves (scout_run / style_radar exit 2 on undecided memos).
    from lib.scout import undecided_memos
    pending = undecided_memos()
    if pending:
        return (True, f"⚠️  {len(pending)} UNDECIDED memo(s) — owner review required: {', '.join(pending)}")
    return (True, "0 undecided memos (decision ledger clean)")


def _production_sequence():
    from lib.pipeline_loader import load_pipeline, get_stage_order

    required = {
        "zavod-reel": {
            "idea.intake_or_writer_room",
            "script.expanded_story_structure",
            "scene_plan.creative_language_council",
            "scene_plan.technical_preparation",
            "scene_plan.preproduction_plan",
            "assets.prompt_pack_or_shoot_pack_approval",
            "edit.story_cut",
            "compose.color_vfx_master_qc",
        },
        "zavod-promo": {
            "idea.intake_or_writer_room",
            "script.expanded_story_structure",
            "scene_plan.creative_language_council",
            "scene_plan.source_frame_selection",
            "scene_plan.technical_preparation",
            "assets.prompt_pack_approval",
            "edit.story_cut",
            "compose.color_vfx_master_qc",
        },
        "zavod-content": {
            "idea.intake_or_writer_room",
            "idea.concept_lock",
            "script.structure_pass",
            "script.candidate_bakeoff",
            "script.authorial_voice_pass",
            "quality.editorial_postproduction",
            "quality.channel_adaptation",
            "quality.evidence_review",
            "publish.presentation_route",
        },
    }
    problems = []
    for name, expected in required.items():
        manifest = load_pipeline(name)
        order = set(get_stage_order(manifest, include_sub_stages=True))
        problems.extend(f"{name}:{item} missing" for item in sorted(expected - order))
        # Every owner-gated sub-stage must be artifact-backed (produces) so the ladder
        # is enforceable at the checkpoint seam, not merely named in prose.
        for stage in manifest["stages"]:
            for ss in stage.get("sub_stages", []):
                if ss.get("human_approval_default", True) and not ss.get("produces"):
                    problems.append(f"{name}:{stage['name']}.{ss['name']} not artifact-backed")
    msg = (
        "reel/promo/content specialist ladders wired + artifact-backed (non-collapsible)"
        if not problems else f"{problems}"
    )
    return (not problems, msg)


def _engine_lanes():
    """Both lanes declared and mutually exclusive: Remotion (no AI footage) vs Higgsfield
    (zero Remotion, ffmpeg compose). Mirrors lib/checkpoint.LANE_COMPOSE_RUNTIMES."""
    from lib.pipeline_loader import load_pipeline
    problems = []
    for name in ("zavod-reel", "zavod-promo"):
        pe = load_pipeline(name).get("metadata", {}).get("production_engine", {})
        lanes = pe.get("lanes", {})
        if not pe.get("ask_at_start"):
            problems.append(f"{name}: production_engine.ask_at_start not set")
        for lane in ("remotion", "higgsfield"):
            if lane not in lanes:
                problems.append(f"{name}: lane {lane!r} missing")
        if lanes.get("higgsfield", {}).get("compose_runtime") != ["ffmpeg"]:
            problems.append(f"{name}: higgsfield lane must compose via [ffmpeg] (zero Remotion)")
        if "higgsfield" not in (lanes.get("remotion", {}).get("forbids") or []):
            problems.append(f"{name}: remotion lane must forbid higgsfield")
    content_engine = load_pipeline("zavod-content").get("metadata", {}).get("production_engine", {})
    if content_engine.get("lane") != "none" or content_engine.get("compose_runtime") != "none":
        problems.append("zavod-content: written content must lock the no-render lane")
    return (not problems, "remotion/higgsfield lanes separated (ask-first, no cross-lane)" if not problems else f"{problems}")


# Named checks (label, fn) — the full production profile, in display order.
_ALL_CHECKS = [
    ("corpus (voice source)", _corpus),
    ("brain (craft files)", _brain),
    ("render (ffmpeg)", _ffmpeg),
    ("pipelines", _manifests),
    ("gates", _gates),
    ("authorial voice", _authorial_voice),
    ("universal router", _universal_router),
    ("agent activation", _agent_activation),
    ("provenance", _provenance_integrity),
    ("enforcement seam", _enforcement),
    ("schemas", _schemas),
    ("scout registry", _scout),
    ("style radar", _style_radar),
    ("memo inbox", _memo_inbox),
    ("production sequence", _production_sequence),
    ("engine lanes", _engine_lanes),
]

# What a trend-scan actually needs. The Scout / Style-Radar weekly scans only web-scan and
# write a GATED memo — they touch neither the corpus nor the render binary — so excluding the
# TCC-protected corpus (~/Documents) and ffmpeg lets the launchd scan run GREEN even before
# Full Disk Access is granted, while still refusing to act on a genuinely broken tree
# (gates / schemas / enforcement / registries must still pass).
_SCAN_EXCLUDE = {"corpus (voice source)", "render (ffmpeg)"}


def evaluate(checks: list | None = None) -> list[tuple[bool, str]]:
    out: list[tuple[bool, str]] = []
    for label, fn in (checks if checks is not None else _ALL_CHECKS):
        try:
            ok, detail = fn()
        except Exception as e:  # never let the health-check itself crash
            ok, detail = False, f"error: {e}"
        out.append((ok, f"{label}: {detail}"))
    return out


def scan_safe_ok() -> tuple[bool, list[str]]:
    """Lighter gate for the weekly scans: full profile minus the TCC-gated corpus and the
    render binary. Returns (ok, [red lines])."""
    res = evaluate([c for c in _ALL_CHECKS if c[0] not in _SCAN_EXCLUDE])
    reds = [line for ok, line in res if not ok]
    return (not reds, reds)


if __name__ == "__main__":
    results = evaluate()
    print("\n  ZavodOM health-check\n  " + "-" * 24)
    for ok, line in results:
        print(f"  {OK if ok else BAD} {line}")
    reds = [l for ok, l in results if not ok]
    print("  " + "-" * 24)
    print(f"  {'ALL GREEN' if not reds else str(len(reds)) + ' RED — fix before producing'}\n")
    sys.exit(0 if not reds else 1)
