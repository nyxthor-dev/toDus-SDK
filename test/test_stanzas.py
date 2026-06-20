"""Tests para todus.stanza (builders XML)."""

from todus import stanza


class TestMessage:
    def test_contains_body(self):
        xml = stanza.message("user@im.todus.cu", "hola", msg_id="test123")
        assert "test123" in xml
        assert "hola" in xml
        assert "<b>" in xml
        assert "to='user@im.todus.cu'" in xml

    def test_escapes_body(self):
        xml = stanza.message("user@im.todus.cu", "a<b&c", msg_id="id1")
        assert "a&lt;b&amp;c" in xml

    def test_auto_generates_id(self):
        xml = stanza.message("user@im.todus.cu", "test")
        assert "i='" in xml


class TestEditMessage:
    def test_contains_edited_tag(self):
        xml = stanza.edit_message("user@im.todus.cu", "nuevo", "orig123", edit_id="e1")
        assert "edited xmlns='edited:n'" in xml
        assert "mi='orig123'" in xml
        assert "nuevo" in xml


class TestFileMessage:
    def test_contains_file_tag(self):
        xml = stanza.file_message(
            "user@im.todus.cu", "https://url.com/f", 0,
            caption="doc", msg_id="m1", file_name="test.pdf", file_size=1024,
        )
        assert "file xmlns='file:n'" in xml
        assert "url='https://url.com/f'" in xml
        assert "n='test.pdf'" in xml
        assert "s='1024'" in xml


class TestImageMessage:
    def test_contains_image_tag(self):
        xml = stanza.image_message(
            "user@im.todus.cu", "https://url.com/i", "photo.jpg", 2048,
            msg_id="m2",
        )
        assert "image xmlns='image:n'" in xml
        assert "n='photo.jpg'" in xml
        assert "s='2048'" in xml

    def test_with_dimensions(self):
        xml = stanza.image_message(
            "user@im.todus.cu", "https://url.com/i", "p.jpg", 100,
            width=640, height=480, msg_id="m3",
        )
        assert "w='640'" in xml
        assert "he='480'" in xml


class TestVideoMessage:
    def test_contains_video_tag(self):
        xml = stanza.video_message(
            "user@im.todus.cu", "https://url.com/v", "vid1",
            "video.mp4", 5000, 30, 1920, 1080, "tnail",
            msg_id="m4",
        )
        assert "video xmlns='video:n'" in xml
        assert "d='30'" in xml
        assert "w='1920'" in xml
        assert "he='1080'" in xml


class TestDeleteMessage:
    def test_contains_deleted_tag(self):
        xml = stanza.delete_message("user@im.todus.cu", "msg123", msg_id="msg123")
        assert "deleted xmlns='deleted:n'" in xml
        assert "mi='msg123'" in xml


class TestLocationMessage:
    def test_contains_location_tag(self):
        xml = stanza.location_message("user@im.todus.cu", 23.1, -82.3, msg_id="l1")
        assert "location xmlns='location:n'" in xml
        assert "lat='23.1'" in xml
        assert "lon='-82.3'" in xml


class TestPing:
    def test_format(self):
        xml = stanza.ping("ping1")
        assert xml == "<iq i='ping1' t='get'><ping xmlns='urn:xmpp:ping'/></iq>"


class TestKeepalive:
    def test_is_space(self):
        assert stanza.keepalive() == " "


class TestStreamOpen:
    def test_default_host(self):
        xml = stanza.stream_open()
        assert "o='im.todus.cu'" in xml
        assert "xmlns='jc'" in xml
        assert "v='1.0'" in xml

    def test_custom_host(self):
        xml = stanza.stream_open("custom.host")
        assert "o='custom.host'" in xml


class TestStreamClose:
    def test_format(self):
        assert stanza.stream_close() == "</stream:stream>"


class TestBind:
    def test_format(self):
        xml = stanza.bind("bind1")
        assert "<iq i='bind1' t='set'>" in xml
        assert "b1 xmlns='x4'" in xml


class TestAck:
    def test_format(self):
        xml = stanza.ack("msg999")
        assert "mi='msg999'" in xml
        assert "tdack" in xml


class TestUploadQuery:
    def test_basic(self):
        xml = stanza.upload_query("q1", 1024, 4)
        assert "todus:purl" in xml
        assert "size='1024'" in xml
        assert "type='4'" in xml

    def test_with_filename(self):
        xml = stanza.upload_query("q2", 500, 0, file_name="doc.pdf")
        assert "n='doc.pdf'" in xml


class TestDownloadQuery:
    def test_basic(self):
        xml = stanza.download_query("q1", "https://cdn.todus.cu/f/abc")
        assert "todus:gurl" in xml
        assert "url='https://cdn.todus.cu/f/abc'" in xml


class TestChatState:
    def test_composing(self):
        xml = stanza.chat_state("user@im.todus.cu", "composing", msg_id="cs1")
        assert "csp xmlns='uc1'" in xml

    def test_paused(self):
        xml = stanza.chat_state("user@im.todus.cu", "paused", msg_id="cs2")
        assert "csc xmlns='uc1'" in xml


class TestReceipt:
    def test_delivery(self):
        xml = stanza.receipt("user@im.todus.cu", "msg1", receipt_id="r1")
        assert "dd xmlns='x8'" in xml
        assert "i='msg1'" in xml

    def test_read(self):
        xml = stanza.read_receipt("user@im.todus.cu", "msg2", receipt_id="r2")
        assert "rd xmlns='x8'" in xml
        assert "i='msg2'" in xml
