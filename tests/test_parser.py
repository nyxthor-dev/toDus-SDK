from todus.parser import parse_todus_message, IncrementalParser


def test_parse_simple_message():
    stanza = "<m f='5312345678@im.todus.cu' o='5312345679@im.todus.cu' i='msg1' t='c' xmlns='jc'><k xmlns='x8'/><b>Hola &amp; Bienvenid\'o</b></m>"
    parsed = parse_todus_message(stanza)

    assert parsed["from"].startswith("5312345678")
    assert parsed["to"].startswith("5312345679")
    assert parsed["id"] == "msg1"
    assert parsed["body"] == "Hola & Bienvenid'o"
    assert parsed["is_group"] is False


def test_incremental_parser_handles_chunks():
    parser = IncrementalParser()
    chunks = ["<m f='5312'", "345678@im.todus.cu' o='5312345679@im.todus.cu' i='msg2' t='c' xmlns='jc'><k xmlns='x8'/><b>Chunked</b></m>"]
    results = []
    for c in chunks:
        results.extend(parser.feed(c))
    assert any(r.get("id") == "msg2" for r in results)
