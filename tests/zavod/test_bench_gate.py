"""Full-bench gate — owner standing order 2026-07-03 («հազար ագենտ կա, ուզում եմ բոլորը՝ իրենց ժամանակին»)."""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from lib.bench_gate import run_bench_gates, required_bench, RULING_MIN  # noqa: E402

# Substantive, role-distinct rulings: long, >=8 distinct tokens, unique per role so the
# 2026-07-04 hardening (filler + independence checks) is satisfied for genuine pass cases.
FULL = lambda stage, roles: {"stage": stage, "bench": {
    r: {"ruling": f"The {r} reviewed this stage in depth and confirms the craft bar is met "
                  f"across staging, continuity, palette, and delivery quality.",
        "verdict": "approve"}
    for r in roles}}

def test_full_bench_passes():
    assert run_bench_gates("scene", FULL("scene", required_bench("scene")))["ok"]

def test_missing_specialist_blocks():
    roles = required_bench("scene")
    rep = FULL("scene", [r for r in roles if r != "costume-designer"])  # the Moratsoghy case
    r = run_bench_gates("scene", rep)
    assert not r["ok"] and any("costume-designer" in v for v in r["violations"])

def test_rubber_stamp_blocks():
    rep = FULL("asset", required_bench("asset"))
    rep["bench"]["identity-guard"]["ruling"] = "ok"
    assert not run_bench_gates("asset", rep)["ok"]

def test_reviewer_always_required():
    for stage in ("idea", "script", "scene", "asset", "edit", "compose", "publish", "unknown"):
        assert "reviewer" in required_bench(stage)


def test_wrong_stage_report_is_rejected():
    report = FULL("idea", required_bench("script"))
    result = run_bench_gates("script", report)
    assert not result["ok"]
    assert any("expected 'script'" in item for item in result["violations"])


def test_unplanned_extra_role_is_rejected():
    report = FULL("script", required_bench("script"))
    report["bench"]["unrelated-colorist"] = {
        "ruling": "This unrelated role supplied a long but unplanned opinion that must not be silently accepted by the routed stage.",
        "verdict": "approve",
    }
    result = run_bench_gates("script", report)
    assert not result["ok"]
    assert any("unexpected roles" in item for item in result["violations"])
