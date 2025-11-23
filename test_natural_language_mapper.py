from gitvisioncli.core.natural_language_mapper import (
    NaturalLanguageEditMapper,
    FileContext,
)


def test_insert_after_line_with_block_maps_to_insert_after():
    mapper = NaturalLanguageEditMapper()
    ctx = FileContext(path="foo.py", content="a\nb\nc\n")
    res = mapper.map_instruction(
        "add this line after line 2",
        active_file=ctx,
        attached_block="print('hi')",
    )
    assert not res.error
    assert not res.clarification
    assert len(res.intents) == 1
    intent = res.intents[0]
    assert intent.type == "InsertAfterLine"
    assert intent.params["path"] == "foo.py"
    assert intent.params["line_number"] == 2
    assert "text" in intent.params


def test_delete_line_range_from_instruction():
    mapper = NaturalLanguageEditMapper()
    ctx = FileContext(path="foo.py", content="a\nb\nc\nd\n")
    res = mapper.map_instruction(
        "remove lines 2-3", active_file=ctx, attached_block=None
    )
    assert not res.error
    assert len(res.intents) == 1
    intent = res.intents[0]
    assert intent.type == "DeleteLineRange"
    assert intent.params["start_line"] == 2
    assert intent.params["end_line"] == 3


def test_insert_into_function_mapping():
    mapper = NaturalLanguageEditMapper()
    ctx = FileContext(path="foo.py", content="def foo():\n    pass\n")
    res = mapper.map_instruction(
        "Add this inside the function foo()", active_file=ctx, attached_block="x = 1"
    )
    assert not res.error
    assert not res.clarification
    assert len(res.intents) == 1
    intent = res.intents[0]
    assert intent.type == "InsertIntoFunction"
    assert intent.params["function_name"] == "foo"


def test_add_import_mapping():
    mapper = NaturalLanguageEditMapper()
    ctx = FileContext(path="foo.py", content="")
    res = mapper.map_instruction(
        "Import datetime if missing", active_file=ctx, attached_block=None
    )
    assert not res.error
    assert len(res.intents) == 1
    intent = res.intents[0]
    assert intent.type == "AddImport"
    assert intent.params["symbol"] == "datetime"


def test_ambiguous_instruction_requests_clarification():
    mapper = NaturalLanguageEditMapper()
    ctx = FileContext(path="foo.py", content="a\nb\nc\n")
    res = mapper.map_instruction("please fix this", active_file=ctx, attached_block=None)
    assert not res.error
    assert res.clarification is not None
    assert res.intents == []
