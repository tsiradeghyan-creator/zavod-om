from lib.authorial_voice import (
    build_profile,
    discover_corpus,
    evidence_source_id,
    resolve_evidence_source,
)
from scripts.voice_extractor import scan


def test_extractor_builds_profile_and_excludes_contracts(tmp_path):
    corpus = tmp_path / "txt"
    corpus.mkdir()
    (corpus / "դու1.txt").write_text(
        ("1. ՏԵՍԱՐԱՆ\nԱնի\nԴուռը բաց ա,,, բայց նա չի գնում։\n" * 20),
        encoding="utf-8",
    )
    (corpus / "Պայմանագիր.txt").write_text("Պայմանագրային տեքստ " * 30, encoding="utf-8")

    files, excluded = discover_corpus(corpus)
    assert [item.name for item in files] == ["դու1.txt"]
    assert "Պայմանագիր.txt" in excluded

    profile = build_profile(corpus)
    assert profile["sources"]["file_count"] == 1
    assert profile["registers"]["A1"]["sample_count"] == 1
    assert profile["registers"]["C"]["status"] == "quarantined_no_clean_sources"


def test_mixed_script_filename_is_excluded_without_propagating_corrupt_text(tmp_path):
    corpus = tmp_path / "txt"
    corpus.mkdir()
    unsafe_name = "".join(chr(codepoint) for codepoint in (
        0x0531, 0x0550, 0x041C, 0x0418, 0x041D, 0x0415,
    )) + "_Concept.txt"
    (corpus / unsafe_name).write_text("Տեքստ " * 100, encoding="utf-8")
    files, excluded = discover_corpus(corpus)
    assert files == []
    assert len(excluded) == 1
    assert excluded[0].startswith("unsafe-filename-sha256-")
    assert unsafe_name not in excluded[0]


def test_corrupt_source_content_is_quarantined_without_copying_its_name(tmp_path):
    corpus = tmp_path / "txt"
    corpus.mkdir()
    path = corpus / "վնասված.txt"
    invisible = chr(0x200E)
    path.write_text((f"1. ՏԵՍԱՐԱՆ\nԱն{invisible}ի չի գնում։\n" * 30), encoding="utf-8")
    files, excluded = discover_corpus(corpus)
    assert files == []
    assert len(excluded) == 1
    assert excluded[0].startswith("content-glyph-failure-sha256-")
    assert path.name not in excluded[0]


def test_incremental_scan_emits_only_changed_files(tmp_path):
    corpus = tmp_path / "txt"
    corpus.mkdir()
    path = corpus / "դու1.txt"
    path.write_text("1. ՏԵՍԱՐԱՆ\nԴուռը բաց ա,,, բայց նա չի գնում։\n" * 20, encoding="utf-8")

    state, first, removed = scan(corpus, {"version": "1.0", "files": {}})
    assert len(first) == 1 and removed == []
    _, second, removed = scan(corpus, state)
    assert second == [] and removed == []

    path.write_text(path.read_text(encoding="utf-8") + "2. ՏԵՍԱՐԱՆ\n", encoding="utf-8")
    _, third, _ = scan(corpus, state)
    assert len(third) == 1 and third[0]["change"] == "changed"


def test_latin_source_filename_is_stored_only_as_an_opaque_id(tmp_path):
    corpus = tmp_path / "txt"
    corpus.mkdir()
    path = corpus / "source-one.txt"
    path.write_text("1. ՏԵՍԱՐԱՆ\nԴուռը բաց ա,,, բայց նա չի գնում։\n" * 20, encoding="utf-8")
    state, changed, _ = scan(corpus, {"version": "1.0", "files": {}})
    source_id = evidence_source_id(path.name)
    assert source_id.startswith("source-filename-sha256-")
    assert set(state["files"]) == {source_id}
    assert changed[0]["file"] == source_id
    assert path.name not in str(state)
    assert resolve_evidence_source(source_id, corpus) == path
