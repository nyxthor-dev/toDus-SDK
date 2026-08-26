import pytest
from todus.stanzas.private import (
    message, edit_message, file_message, image_message, image_message_simple,
    button_message, contact_message, sticker_message, video_message,
    delete_message, location_message, event_message, _generate_msg_id,
)
from todus.stanzas.utils import (
    iq, ping, chat_state, receipt, read_receipt, ack, keepalive,
    stream_open, stream_close, sasl_auth, bind, mam_query,
    upload_query, download_query,
)
from todus.stanzas.group import group_message, group_file_message, group_image_message
from todus.stanzas.presence import presence, muc_presence, muc_unavailable


# --- Private stanzas ---

class TestPrivateMessage:
    def test_basic_message(self):
        xml = message("5354123456@im.todus.cu", "Hola")
        assert "to='5354123456@im.todus.cu'" in xml
        assert "<b>Hola</b>" in xml
        assert "<k xmlns='x8'/>" in xml

    def test_custom_id(self):
        xml = message("5354123456@im.todus.cu", "x", msg_id="custom123")
        assert "i='custom123'" in xml

    def test_edit_message(self):
        xml = edit_message("5354123456@im.todus.cu", "nuevo texto", "original_id")
        assert "<edited" in xml
        assert "mi='original_id'" in xml
        assert "nuevo texto" in xml

    def test_file_message(self):
        xml = file_message("53@im.todus.cu", "https://url/f", 0, "pdf", msg_id="f1", file_name="doc.pdf", file_size=1024)
        assert "<file" in xml
        assert "n='doc.pdf'" in xml
        assert "s='1024'" in xml
        assert "pdf" in xml

    def test_image_message(self):
        xml = image_message("53@im.todus.cu", "https://url/img.jpg", "img.jpg", 50000, 1920, 1080, msg_id="im1")
        assert "<image" in xml
        assert "w='1920'" in xml
        assert "he='1080'" in xml

    def test_image_message_simple(self):
        xml = image_message_simple("53@im.todus.cu", "https://url/i.jpg", "i.jpg", 50000)
        assert "<image" in xml
        assert "<b/>" in xml

    def test_button_message(self):
        btns = [{"text": "Si", "command": "cmd_type_send", "data": "si", "size": "0.5"}]
        xml = button_message("53@im.todus.cu", "Pregunta?", btns)
        assert "<button" in xml
        assert "btn_t='Si'" in xml
        assert "Pregunta?" in xml

    def test_contact_message(self):
        xml = contact_message("53@im.todus.cu", "cid1", "Juan", "5351111111")
        assert "<contact" in xml
        assert "n='Juan'" in xml
        assert "num='5351111111'" in xml

    def test_sticker_message(self):
        xml = sticker_message("53@im.todus.cu", "sid1", "fuego", "pack1", "h1")
        assert "<sticker" in xml
        assert "f='pack1'" in xml

    def test_video_message(self):
        xml = video_message("53@im.todus.cu", "https://url/v.mp4", "vid1", "v.mp4", 5000000, 30, 1280, 720, "tn")
        assert "<video" in xml
        assert "d='30'" in xml
        assert "w='1280'" in xml

    def test_delete_message(self):
        xml = delete_message("53@im.todus.cu", "msg_to_del")
        assert "<deleted" in xml
        assert "mi='msg_to_del'" in xml

    def test_location_message(self):
        xml = location_message("53@im.todus.cu", 23.1, -82.3)
        assert "<location" in xml
        assert "lat='23.1'" in xml
        assert "lon='-82.3'" in xml

    def test_event_message(self):
        xml = event_message("53@im.todus.cu", "e1", "Reunion", 1000, 2000, False, "ICS_DATA")
        assert "<event" in xml
        assert "ti='Reunion'" in xml
        assert "ad='false'" in xml

    def test_reply_to_in_message(self):
        xml = message("53@im.todus.cu", "resp", reply_to_id="original")
        assert "<reply" in xml
        assert "mi='original'" in xml

    def test_generate_msg_id_is_hex(self):
        mid = _generate_msg_id()
        assert len(mid) == 32
        assert all(c in "0123456789abcdef" for c in mid)


# --- Utility stanzas ---

class TestUtilityStanzas:
    def test_iq(self):
        xml = iq("get", "iq1", "<payload/>", "target")
        assert "i='iq1'" in xml
        assert "t='get'" in xml
        assert "to='target'" in xml

    def test_ping(self):
        xml = ping("p1")
        assert "urn:xmpp:ping" in xml

    def test_chat_state_composing(self):
        xml = chat_state("53@im.todus.cu", "composing")
        assert "<csp" in xml

    def test_chat_state_paused(self):
        xml = chat_state("53@im.todus.cu", "paused")
        assert "<csc" in xml

    def test_receipt(self):
        xml = receipt("53@im.todus.cu", "msg1")
        assert "<dd" in xml
        assert "i='msg1'" in xml

    def test_read_receipt(self):
        xml = read_receipt("53@im.todus.cu", "msg1")
        assert "<rd" in xml

    def test_ack(self):
        xml = ack("msg1")
        assert "<tdack" in xml
        assert "mi='msg1'" in xml

    def test_keepalive(self):
        assert keepalive() == " "

    def test_stream_open(self):
        xml = stream_open()
        assert "<stream:stream" in xml
        assert "im.todus.cu" in xml

    def test_stream_close(self):
        assert stream_close() == "</stream:stream>"

    def test_sasl_auth(self):
        result = sasl_auth(b"authdata")
        assert b"<ah" in result
        assert b"PLAIN" in result
        assert b"authdata" in result

    def test_bind(self):
        xml = bind("b1")
        assert "<b1" in xml

    def test_mam_query(self):
        xml = mam_query("q1", since="2024-01-01T00:00:00Z", limit=20)
        assert "todus:mam" in xml
        assert "2024-01-01T00:00:00Z" in xml
        assert "<max>20</max>" in xml

    def test_upload_query(self):
        xml = upload_query("u1", 5000, 4, file_name="foto.jpg")
        assert "todus:purl" in xml
        assert "size='5000'" in xml
        assert "n='foto.jpg'" in xml

    def test_download_query(self):
        xml = download_query("d1", "https://some.url")
        assert "todus:gurl" in xml
        assert "some.url" in xml


# --- Group stanzas ---

class TestGroupStanzas:
    def test_group_message(self):
        xml = group_message("grp1@muclight.im.todus.cu", "Hola grupo")
        assert "<m" in xml
        assert "Hola grupo" in xml

    def test_group_file_message(self):
        xml = group_file_message("grp1@muclight.im.todus.cu", "https://url/f", "doc.pdf", 1024, caption="archivo")
        assert "<file" in xml
        assert "archivo" in xml

    def test_group_image_message(self):
        xml = group_image_message("grp1@muclight.im.todus.cu", "https://url/i.jpg", "i.jpg", 50000, 800, 600)
        assert "<image" in xml
        assert "w='800'" in xml


# --- Presence stanzas ---

class TestPresenceStanzas:
    def test_presence(self):
        xml = presence("available")
        assert "<p" in xml

    def test_muc_presence(self):
        xml = muc_presence("grp1@muclight.im.todus.cu", "BotNick")
        assert "<p" in xml
        assert "BotNick" in xml

    def test_muc_unavailable(self):
        xml = muc_unavailable("grp1@muclight.im.todus.cu")
        assert "<p" in xml
