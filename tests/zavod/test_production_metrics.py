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
    MetricsError, gate_block_summary, gate_report, record_gate_block,
    record_production_row, stopping_criterion_met,
)


def _block(pdir, cls="real_defect", gate="glyph", minutes=5):
    return record_gate_block(
        pdir, gate=gate, stage="cut", classification=cls, classifier="agent",
        evidence="visible subtitle had Latin-script Armenian",
        resolution_action="rewrote in Armenian Unicode", duration_minutes=minutes)


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
    a, b = tmp_path / "a", tmp_path / "b"
    _block(a, "blocked_formality", gate="bench")
    _block(b, "blocked_formality", gate="bench")
    _block(b, "real_defect", gate="glyph")
    report = gate_report([a, b])
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
