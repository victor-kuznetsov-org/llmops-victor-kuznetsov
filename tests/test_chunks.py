from pkgscout.chunks import fixed_windows, split_by_headings


def test_split_by_headings() -> None:
    md = (
        "intro text that is long enough to stay a chunk of its own\n# A\n"
        + "a" * 50
        + "\n## B\n"
        + "b" * 50
    )
    chunks = split_by_headings(md)
    assert [c["heading"] for c in chunks] == ["", "A", "B"]


def test_code_fence_hash_is_not_a_heading() -> None:
    md = "# A\n```\n# comment\n```\n" + "x" * 50
    assert len(split_by_headings(md)) == 1


def test_empty() -> None:
    assert split_by_headings(None) == []
    assert fixed_windows("") == []


def test_fixed_windows_overlap() -> None:
    w = fixed_windows("x" * 1000)
    assert [len(c) for c in w] == [800, 300]
