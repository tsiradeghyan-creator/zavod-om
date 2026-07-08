"""Performance loop (2026-07-07 strategy audit №9): publish+48h results become a
STRUCTURAL input to the next concept decision, not a "we learned" sentence."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from lib.checkpoint import CheckpointValidationError, write_checkpoint  # noqa: E402
from lib.performance_loop import (  # noqa: E402
    latest_performance_ids, save_performance_brief,
)
from tests.zavod.test_redteam_hardening import _concept, _log  # noqa: E402


def _brief(pid, published_at):
    return {"version": "1.0", "performance_id": pid, "project_id": "p",
            "published_at": published_at, "platform": "instagram", "format": "reel",
            "metrics_48h": {"views": 100, "saves": 5},
            "verdict": {"keep_hook_type": True, "repeat_topic": False}}


def _warm_loop(monkeypatch, tmp_path, n=3):
    monkeypatch.setenv("ZAVOD_PERFORMANCE_DIR", str(tmp_path / "perf"))
    for i in range(n):
        save_performance_brief(_brief(f"perf_{i:03d}", f"2026-07-0{i + 1}T10:00:00+00:00"))


def test_brief_saved_and_ordered(monkeypatch, tmp_path):
    _warm_loop(monkeypatch, tmp_path)
    assert latest_performance_ids() == ["perf_002", "perf_001", "perf_000"]


def test_duplicate_performance_id_refused(monkeypatch, tmp_path):
    _warm_loop(monkeypatch, tmp_path, n=1)
    with pytest.raises(ValueError, match="append-only"):
        save_performance_brief(_brief("perf_000", "2026-07-05T10:00:00+00:00"))


def test_concept_without_refs_blocks_once_loop_is_warm(monkeypatch, tmp_path):
    _warm_loop(monkeypatch, tmp_path)
    with pytest.raises(CheckpointValidationError, match="performance"):
        write_checkpoint(tmp_path, "p", "idea", "in_progress",
                         {"decision_log": _log(_concept())}, pipeline_type=None)


def test_concept_with_full_refs_passes(monkeypatch, tmp_path):
    _warm_loop(monkeypatch, tmp_path)
    c = _concept()
    c["performance_refs"] = [
        {"performance_id": "perf_002", "used_for": "repeat_hook_type", "signal": "high_saves"},
        {"performance_id": "perf_001", "used_for": "avoid_topic", "signal": "low_completion"},
        {"performance_id": "perf_000", "used_for": "adapt_cta", "signal": "comment_question"},
    ]
    p = write_checkpoint(tmp_path, "p", "idea", "in_progress",
                         {"decision_log": _log(c)}, pipeline_type=None)
    assert p.exists()


def test_partial_refs_still_block(monkeypatch, tmp_path):
    _warm_loop(monkeypatch, tmp_path)
    c = _concept()
    c["performance_refs"] = [
        {"performance_id": "perf_002", "used_for": "repeat_hook_type"}]
    with pytest.raises(CheckpointValidationError, match="perf_00"):
        write_checkpoint(tmp_path, "p", "idea", "in_progress",
                         {"decision_log": _log(c)}, pipeline_type=None)


def test_rule_dormant_below_three_briefs(monkeypatch, tmp_path):
    _warm_loop(monkeypatch, tmp_path, n=2)
    p = write_checkpoint(tmp_path, "p", "idea", "in_progress",
                         {"decision_log": _log(_concept())}, pipeline_type=None)
    assert p.exists()


# ── Round 7.1 (2026-07-08 re-audit №9/№10) ──────────────────────────────────────────
from lib.performance_loop import _parse_dt  # noqa: E402


def test_save_rejects_unparseable_timestamp(monkeypatch, tmp_path):
    monkeypatch.setenv("ZAVOD_PERFORMANCE_DIR", str(tmp_path / "perf"))
    with pytest.raises(ValueError, match="ISO-8601"):
        save_performance_brief(_brief("perf_bad", "not-a-timestamp"))


def test_sorting_uses_parsed_time_not_lexicographic_string(monkeypatch, tmp_path):
    # 'Z' suffix and a numeric-offset timestamp for the SAME instant must compare equal in
    # ORDER even though the strings differ lexicographically ("2026-07-05T10:00:00+02:00"
    # sorts differently as a string than "...Z" for an equivalent/later real UTC instant).
    monkeypatch.setenv("ZAVOD_PERFORMANCE_DIR", str(tmp_path / "perf"))
    save_performance_brief(_brief("perf_early", "2026-07-01T10:00:00Z"))
    save_performance_brief(_brief("perf_late", "2026-07-01T09:00:00-02:00"))  # = 11:00 UTC, LATER
    # Lexicographically "09:00...-02:00" < "10:00...Z", but 11:00 UTC is actually later.
    assert latest_performance_ids(n=2) == ["perf_late", "perf_early"]


def test_corrupted_stored_timestamp_raises_not_silently_dropped(monkeypatch, tmp_path):
    monkeypatch.setenv("ZAVOD_PERFORMANCE_DIR", str(tmp_path / "perf"))
    save_performance_brief(_brief("perf_ok", "2026-07-01T10:00:00Z"))
    bad = (tmp_path / "perf" / "perf_hand_edited.json")
    bad.write_text('{"performance_id": "perf_hand_edited", "published_at": "garbage"}')
    with pytest.raises(ValueError, match="unparseable"):
        latest_performance_ids()


def _refs(latest, extra=None):
    out = [{"performance_id": pid, "used_for": "repeat_hook_type", "signal": "high_saves"}
           for pid in latest]
    if extra:
        out += extra
    return out


def test_padding_with_all_known_ids_still_requires_signal_on_latest(monkeypatch, tmp_path):
    # Gaming attempt: dump every known id into performance_refs so the subset check
    # trivially passes. The latest-3 entries still need a real 'signal', not just an id.
    _warm_loop(monkeypatch, tmp_path)
    c = _concept()
    latest = latest_performance_ids()
    c["performance_refs"] = (
        [{"performance_id": pid, "used_for": "x"} for pid in latest]  # no signal!
        + [{"performance_id": f"pad_{i}", "used_for": "x", "rationale": "padding"} for i in range(20)]
    )
    with pytest.raises(CheckpointValidationError, match="signal"):
        write_checkpoint(tmp_path, "p", "idea", "in_progress",
                         {"decision_log": _log(c)}, pipeline_type=None)


def test_extra_ref_without_rationale_blocks(monkeypatch, tmp_path):
    _warm_loop(monkeypatch, tmp_path)
    c = _concept()
    latest = latest_performance_ids()
    c["performance_refs"] = _refs(latest, extra=[
        {"performance_id": "perf_ancient", "used_for": "x"}])  # no rationale
    with pytest.raises(CheckpointValidationError, match="rationale"):
        write_checkpoint(tmp_path, "p", "idea", "in_progress",
                         {"decision_log": _log(c)}, pipeline_type=None)


def test_extra_ref_with_rationale_passes(monkeypatch, tmp_path):
    _warm_loop(monkeypatch, tmp_path)
    c = _concept()
    latest = latest_performance_ids()
    c["performance_refs"] = _refs(latest, extra=[
        {"performance_id": "perf_ancient", "used_for": "x", "rationale": "same topic worked before"}])
    p = write_checkpoint(tmp_path, "p", "idea", "in_progress",
                         {"decision_log": _log(c)}, pipeline_type=None)
    assert p.exists()
