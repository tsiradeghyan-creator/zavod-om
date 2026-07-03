"""Full-bench gate — owner standing order 2026-07-03 («հազար ագենտ կա, ուզում եմ բոլորը՝ իրենց ժամանակին»)."""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
from lib.bench_gate import run_bench_gates, required_bench, RULING_MIN  # noqa: E402

FULL = lambda roles: {"bench": {r: {"ruling": "x" * (RULING_MIN + 5)} for r in roles}}

def test_full_bench_passes():
    assert run_bench_gates("scene", FULL(required_bench("scene")))["ok"]

def test_missing_specialist_blocks():
    roles = required_bench("scene")
    rep = FULL([r for r in roles if r != "costume-designer"])  # the Moratsoghy case
    r = run_bench_gates("scene", rep)
    assert not r["ok"] and any("costume-designer" in v for v in r["violations"])

def test_rubber_stamp_blocks():
    rep = FULL(required_bench("asset"))
    rep["bench"]["identity-guard"]["ruling"] = "ok"
    assert not run_bench_gates("asset", rep)["ok"]

def test_reviewer_always_required():
    for stage in ("idea", "script", "scene", "asset", "edit", "compose", "publish", "unknown"):
        assert "reviewer" in required_bench(stage)
