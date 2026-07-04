"""Static regressions for portable runtime commands and gate coverage docs."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent


def test_makefile_has_no_bare_python_or_pip_invocations():
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    bare = []
    for lineno, line in enumerate(makefile.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("python ") or stripped.startswith("python -"):
            bare.append((lineno, stripped))
        if stripped.startswith("pip ") or stripped.startswith("pip install"):
            bare.append((lineno, stripped))
    assert bare == []


def test_zavodom_delivery_promise_doc_matches_required_edit_seam():
    doc = (ROOT / "ZAVODOM.md").read_text(encoding="utf-8")
    assert "Delivery promise | checkpoint-enforced, required at edit seam" in doc
    assert "reviewer-invoked, not checkpoint seam yet" not in doc