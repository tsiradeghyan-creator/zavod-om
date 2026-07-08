"""Measurement layer (2026-07-07 strategy audit): gate-block log + production CSV.

Governance earns its keep with evidence — every hard block is classified, block totals
flow into the per-production row, and the hardening-stop rule is computable.
"""
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from lib.production_metrics import (  # noqa: E402
    MetricsError, gate_block_summary, gate_report, gate_sample_sizes,
    record_gate_block, record_production_row, stopping_criterion_met,
)


def _block(pdir, cls="real_defect", gate="glyph", minutes=5):
    # blocked_formality/false_block need owner_confirmed when classifier="agent"
    # (round-7.1 #3) — the test helper supplies it so existing fixtures keep working.
    needs_confirm = cls in ("blocked_formality", "false_block")
    return record_gate_block(
        pdir, gate=gate, stage="cut", classification=cls, classifier="agent",
        evidence="visible subtitle had Latin-script Armenian",
        resolution_action="rewrote in Armenian Unicode", duration_minutes=minutes,
        owner_confirmed=needs_confirm)


def test_unclassified_block_is_rejected(tmp_path):
    with pytest.raises(MetricsError, match="classification"):
        record_gate_block(tmp_path, gate="glyph", stage="cut",
                          classification="dunno", classifier="agent", evidence="x")


def test_block_without_evidence_is_rejected(tmp_path):
    with pytest.raises(MetricsError, match="evidence"):
        record_gate_block(tmp_path, gate="glyph", stage="cut",
                          classification="real_defect", classifier="agent", evidence="  ")


def test_summary_derives_from_log(tmp_path):
    _block(tmp_path, "real_defect", minutes=5)
    _block(tmp_path, "false_block", minutes=14)
    s = gate_block_summary(tmp_path)
    assert s["gate_blocks_total"] == 2 and s["false_block_minutes"] == 14.0


def test_csv_row_uses_log_totals_not_hand_entry(tmp_path):
    _block(tmp_path, "false_block", minutes=10)
    csv_path = tmp_path / "metrics.csv"
    row = record_production_row(
        project_id="p1", format="reel", idea_to_first_preview_minutes=120,
        owner_revision_rounds=1, missed_defects_count=0, first_preview_accepted=True,
        project_dir=tmp_path, csv_path=csv_path)
    assert row["gate_blocks_total"] == 1 and row["false_block_minutes"] == 10.0
    rows = list(csv.DictReader(open(csv_path)))
    assert rows[0]["project_id"] == "p1" and rows[0]["first_preview_accepted"] == "True"


def test_formality_heavy_gate_is_flagged_for_simplification(tmp_path):
    # min_n=1 isolates the >=50%-share LOGIC from the round-7.1 #4 sample-size floor,
    # which has its own tests below.
    a, b = tmp_path / "a", tmp_path / "b"
    _block(a, "blocked_formality", gate="bench")
    _block(b, "blocked_formality", gate="bench")
    _block(b, "real_defect", gate="glyph")
    report = gate_report([a, b], min_n=1)
    assert any(r.startswith("bench:") for r in report)
    assert not any(r.startswith("glyph:") for r in report)


def test_stopping_criterion(tmp_path):
    csv_path = tmp_path / "metrics.csv"
    assert stopping_criterion_met(csv_path)["met"] is False  # nothing measured
    for i in range(5):
        record_production_row(
            project_id=f"p{i}", format="reel", idea_to_first_preview_minutes=100,
            owner_revision_rounds=1, missed_defects_count=0,
            first_preview_accepted=(i != 0),  # 4/5 accepted = 80%
            csv_path=csv_path)
    out = stopping_criterion_met(csv_path)
    assert out["met"] is True and out["acceptance"] == 0.8


# ── Round 7.1 (2026-07-08 re-audit №3): agent can't self-classify formality/false ──
def test_agent_self_classifying_formality_without_confirmation_blocks(tmp_path):
    with pytest.raises(MetricsError, match="owner_confirmed"):
        record_gate_block(tmp_path, gate="bench", stage="idea",
                          classification="blocked_formality", classifier="agent",
                          evidence="6th bench role missing but 3 completed")


def test_agent_self_classifying_false_block_without_confirmation_blocks(tmp_path):
    with pytest.raises(MetricsError, match="owner_confirmed"):
        record_gate_block(tmp_path, gate="glyph", stage="cut",
                          classification="false_block", classifier="agent",
                          evidence="brand word Instagram flagged")


def test_agent_classification_with_owner_confirmation_passes(tmp_path):
    e = record_gate_block(tmp_path, gate="bench", stage="idea",
                          classification="blocked_formality", classifier="agent",
                          evidence="6th bench role missing but 3 completed",
                          owner_confirmed=True)
    assert e["owner_confirmed"] is True


def test_agent_real_defect_needs_no_confirmation(tmp_path):
    # real_defect never favors the reporter, so it is not gated the same way.
    e = record_gate_block(tmp_path, gate="glyph", stage="cut",
                          classification="real_defect", classifier="agent",
                          evidence="Latin-script Armenian in subtitle")
    assert e["owner_confirmed"] is False


def test_owner_classification_needs_no_separate_confirmation(tmp_path):
    e = record_gate_block(tmp_path, gate="bench", stage="idea",
                          classification="false_block", classifier="owner",
                          evidence="owner reviewed and disagreed with the block")
    assert e["owner_confirmed"] is False  # owner classifying IS the confirmation


# ── Round 7.1 (2026-07-08 re-audit №4): min-N floor for simplification candidates ──
def test_two_of_two_formality_does_not_trigger_below_min_n(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _block(a, "blocked_formality", gate="bench")
    _block(b, "blocked_formality", gate="bench")
    assert gate_report([a, b]) == []  # n=2 < min_n=10, no false trend


def test_min_n_met_still_flags(tmp_path):
    dirs = [tmp_path / f"p{i}" for i in range(10)]
    for d in dirs:
        _block(d, "blocked_formality", gate="bench")
    report = gate_report(dirs)
    assert any(r.startswith("bench:") for r in report)


def test_gate_sample_sizes_shows_low_n_transparently(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _block(a, "blocked_formality", gate="bench")
    _block(b, "blocked_formality", gate="bench")
    sizes = gate_sample_sizes([a, b])
    assert sizes["bench"]["n"] == 2 and sizes["bench"]["min_n_met"] is False
    assert sizes["bench"]["blocked_formality_share"] == 1.0
