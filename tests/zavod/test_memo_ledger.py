"""Loud-fail on undecided memos (2026-07-02 council ruling).

A GATED memo without an owner decision in library/memo_decisions.json is decision-debt:
the next scheduled Scout/Style-Radar run must refuse to duplicate the memo and exit loudly,
and the ledger must resolve today's real memos as decided.
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from lib.scout import undecided_memos  # noqa: E402


def test_undecided_memo_is_detected(tmp_path):
    (tmp_path / "scout_memo_2099-01-01.md").write_text("# memo")
    dec = tmp_path / "memo_decisions.json"
    dec.write_text(json.dumps({"decisions": {}}))
    assert undecided_memos(str(tmp_path), str(dec)) == ["scout_memo_2099-01-01.md"]


def test_decided_memo_is_not_flagged(tmp_path):
    (tmp_path / "style_memo_2099-01-01.md").write_text("# memo")
    dec = tmp_path / "memo_decisions.json"
    dec.write_text(json.dumps({"decisions": {"style_memo_2099-01-01.md": {"decided": "2099-01-02"}}}))
    assert undecided_memos(str(tmp_path), str(dec)) == []


def test_missing_ledger_means_everything_undecided(tmp_path):
    (tmp_path / "scout_memo_2099-01-01.md").write_text("# memo")
    assert undecided_memos(str(tmp_path), str(tmp_path / "nope.json")) == ["scout_memo_2099-01-01.md"]


def test_real_ledger_has_no_undecided_memos():
    # The 2026-07-02 review closed all pending memos; new memos must be decided or the scans go loud.
    assert undecided_memos() == []
