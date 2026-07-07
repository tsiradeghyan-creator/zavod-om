"""Test-suite isolation.

The performance loop reads the account-level performance directory
(`library/performance/`, env-overridable). Tests must never see REAL published
briefs — otherwise the "concept decisions must reference the latest 3 results"
rule would start failing unrelated tests the day the third real brief lands.
Point every test at an empty per-session directory; tests that exercise the
loop set their own directory explicitly.
"""
import pytest


@pytest.fixture(autouse=True)
def _isolated_performance_dir(tmp_path_factory, monkeypatch):
    monkeypatch.setenv(
        "ZAVOD_PERFORMANCE_DIR",
        str(tmp_path_factory.mktemp("performance-isolated")),
    )
