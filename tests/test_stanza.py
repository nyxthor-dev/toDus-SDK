from todus import stanza, util


def test_message_builder_and_escape():
    body = "Hello <user> & 'world'"
    msg = stanza.message("5312345678@im.todus.cu", body, msg_id="m1")
    assert "i='m1'" in msg
    # Body should be XML-escaped
    assert "&lt;user&gt;" in msg or "&amp;" in msg


def test_image_message_includes_attrs():
    msg = stanza.image_message("5312345678@im.todus.cu", "https://cdn.example/img.jpg", "img.jpg", 12345, width=100, height=200, msg_id="mimg")
    assert "i='mimg'" in msg
    assert "w='100'" in msg or "he='200'" in msg
