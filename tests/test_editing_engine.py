from gitvisioncli.core.editing_engine import EditingEngine, EditingError


def test_insert_before_after_and_delete_line_range_basic():
    engine = EditingEngine()
    original = "a\nb\nc"

    # Insert before line 2
    r1 = engine.insert_before_line(original, line_number=2, text="X")
    assert r1.content.split("\n") == ["a", "X", "b", "c"]

    # Insert after line 1
    r2 = engine.insert_after_line(original, line=1, text="Y")
    assert r2.content.split("\n") == ["a", "Y", "b", "c"]

    # Delete lines 2-3
    r3 = engine.delete_line_range(original, start_line=2, end_line=3)
    assert r3.content.split("\n") == ["a"]


def test_line_range_validation_and_aliases():
    engine = EditingEngine()
    content = "a\nb\nc"

    # Aliases start/end
    r = engine.delete_line_range(content, start=1, end=2)
    assert r.content.split("\n") == ["c"]

    # Out-of-bounds should raise
    try:
        engine.delete_line_range(content, start_line=5, end_line=6)
    except EditingError as e:
        assert "beyond file length" in str(e)
    else:
        assert False, "Expected EditingError for out-of-range start_line"


def test_replace_by_exact_match_and_pattern():
    engine = EditingEngine()
    content = "foo bar foo"

    r1 = engine.replace_by_exact_match(content, old="foo", new="X", count=1)
    assert r1.content == "X bar foo"

    r2 = engine.replace_by_pattern(content, pattern=r"foo", replacement="Y")
    assert r2.content == "Y bar Y"

    # Missing pattern should raise
    try:
        engine.replace_by_pattern(content, pattern="zzz", replacement="Q")
    except EditingError as e:
        assert "Pattern not found" in str(e)
    else:
        assert False, "Expected EditingError for missing pattern"


def test_update_json_key_nested_path():
    engine = EditingEngine()
    content = '{"a": {"b": 1}}'

    r = engine.update_json_key(content, key_path="a.c", value=42)
    assert '"c": 42' in r.content

