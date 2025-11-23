from gitvisioncli.core.provider_normalizer import ProviderNormalizer


def test_normalize_fences_collapses_json_variants():
    norm = ProviderNormalizer()
    text = "```JSON\n{\"a\":1}\n```"
    out = norm.normalize_fences(text)
    assert "```json" in out


def test_extract_json_blocks_ignores_invalid():
    norm = ProviderNormalizer()
    text = """```json
{"ok": true}
```

```json
{not valid}
```"""
    blocks = norm.extract_json_blocks(text)
    assert len(blocks) == 1
    assert blocks[0]["ok"] is True

