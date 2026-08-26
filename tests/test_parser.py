import pytest
from todus.parser import (
    parse_todus_message, parse_presence, parse_iq, parse_tdack,
    IncrementalParser, extract_all_stanzas, _attr,
)


STANZA_MSG = """<m f='5354123456@im.todus.cu' o='5398765432' i='abc123' t='c' xmlns='jc'><k xmlns='x8'/><b>Hola mundo</b></m>"""

STANZA_MSG_GROUP = """<m f='grp123@muclight.im.todus.cu/5354123456' o='' i='def456' t='gc' xmlns='jc'><b>Msg grupo</b></m>"""

STANZA_MSG_FILE = """<m f='5354123456@im.todus.cu' o='5398765432' i='file01' t='c' xmlns='jc'><k xmlns='x8'/><b>Ver archivo</b><file xmlns='file:n' i='fid1' mi='file01' n='doc.pdf' url='https://url/file' s='1024' h='hash1'/></m>"""

STANZA_MSG_IMAGE = """<m f='5354123456@im.todus.cu' o='5398765432' i='img01' t='c' xmlns='jc'><k xmlns='x8'/><b>Foto</b><image xmlns='image:n' i='iid1' mi='img01' url='https://url/img.jpg' n='foto.jpg' s='50000' h='' w='1920' he='1080' tnail='blur'/></m>"""

STANZA_MSG_VIDEO = """<m f='5354123456@im.todus.cu' o='5398765432' i='vid01' t='c' xmlns='jc'><k xmlns='x8'/><b>Video</b><video xmlns='video:n' i='vid1' mi='vid01' url='https://url/vid.mp4' s='5000000' h='' d='30' n='video.mp4' w='1280' he='720' tnail='tn'/></m>"""

STANZA_MSG_STICKER = """<m f='5354123456@im.todus.cu' o='5398765432' i='stk01' t='c' xmlns='jc'><k xmlns='x8'/><sticker xmlns='sticker:n' i='sid1' mi='stk01' n='sticker1' f='pack1' url='' s='0' h='shash' json=''/><b/></m>"""

STANZA_MSG_CONTACT = """<m f='5354123456@im.todus.cu' o='5398765432' i='ctc01' t='c' xmlns='jc'><k xmlns='x8'/><contact xmlns='contact:n' i='cid1' mi='ctc01' n='Juan' num='5351111111'/><b/></m>"""

STANZA_MSG_LOCATION = """<m f='5354123456@im.todus.cu' o='5398765432' i='loc01' t='c' xmlns='jc'><k xmlns='x8'/><location xmlns='location:n' i='lid1' mi='loc01' lat='23.1136' lon='-82.3666' z='15.0' t='La Habana'/><b/></m>"""

STANZA_MSG_EVENT = """<m f='5354123456@im.todus.cu' o='5398765432' i='evt01' t='c' xmlns='jc'><k xmlns='x8'/><event xmlns='event:n' i='eid1' mi='evt01' ti='Reunion' s='1700000000' e='1700003600' ad='false'><ics>DATA</ics></event><b/></m>"""

STANZA_MSG_EDITED = """<m f='5354123456@im.todus.cu' o='5398765432' i='orig01' t='c' xmlns='jc'><edited xmlns='edited:n' i='edit01' mi='orig01'/><k xmlns='x8'/><b>Texto editado</b></m>"""

STANZA_MSG_DELETED = """<m f='5354123456@im.todus.cu' o='5398765432' i='del01' t='c' xmlns='jc'><k xmlns='x8'/><deleted xmlns='deleted:n' i='did1' mi='del01'/><b/></m>"""

STANZA_MSG_COMPOSING = """<m f='5354123456@im.todus.cu' o='5398765432' i='csp01' t='c' xmlns='jc'><csp xmlns='uc1'/></m>"""

STANZA_MSG_DELIVERED = """<m f='5354123456@im.todus.cu' o='5398765432' i='dd01' t='c' xmlns='jc'><dd xmlns='x8' i='msg123'/></m>"""

STANZA_MSG_READ = """<m f='5354123456@im.todus.cu' o='5398765432' i='rd01' t='c' xmlns='jc'><rd xmlns='x8' i='msg456'/></m>"""

STANZA_MSG_BUTTONS = """<m f='5354123456@im.todus.cu' o='5398765432' i='btn01' t='c' xmlns='jc'><k xmlns='x8'/><b>Elige:</b><button xmlns='button:n' btn_t='Opcion 1' btn_cmd='cmd_type_send' btn_msg_c='1' btn_size='0.5'/><button xmlns='button:n' btn_t='Opcion 2' btn_cmd='cmd_type_send' btn_msg_c='2' btn_size='0.5'/></m>"""

STANZA_MSG_REPLY = """<m f='5354123456@im.todus.cu' o='5398765432' i='rep01' t='c' xmlns='jc'><k xmlns='x8'/><reply xmlns='reply:n' mi='original_id'/><b>Respuesta</b></m>"""

STANZA_PRESENCE = """<p f='5354123456@im.todus.cu' o='' i='p1' xmlns='jc'><show>away</show><status>Ausente</status><priority>1</priority></p>"""

STANZA_IQ = """<iq f='im.todus.cu' o='5354123456@im.todus.cu' i='iq1' t='result'><query xmlns='todus:purl' put='https://upload.url' get='https://download.url'/></iq>"""

STANZA_TDACK = """<tdack xmlns='x8' mi='msg123'/>"""


# --- parse_todus_message ---

class TestParseMessage:
    def test_basic_fields(self):
        r = parse_todus_message(STANZA_MSG)
        assert r["from"] == "5354123456@im.todus.cu"
        assert r["id"] == "abc123"
        assert r["body"] == "Hola mundo"
        assert r["is_group"] is False

    def test_group_detection(self):
        r = parse_todus_message(STANZA_MSG_GROUP)
        assert r["is_group"] is True
        assert r["group_id"] == "grp123"
        assert r["sender_phone"] == "5354123456"
        assert r["body"] == "Msg grupo"

    def test_file_attachment(self):
        r = parse_todus_message(STANZA_MSG_FILE)
        assert r["file_id"] == "fid1"
        assert r["file_name"] == "doc.pdf"
        assert r["url"] == "https://url/file"
        assert r["file_size"] == 1024

    def test_image_attachment(self):
        r = parse_todus_message(STANZA_MSG_IMAGE)
        assert r["file_id"] == "iid1"
        assert r["image_width"] == 1920
        assert r["image_height"] == 1080
        assert r["image_thumbnail"] == "blur"

    def test_video_attachment(self):
        r = parse_todus_message(STANZA_MSG_VIDEO)
        assert r["video_id"] == "vid1"
        assert r["video_duration"] == 30
        assert r["video_width"] == 1280
        assert r["video_height"] == 720

    def test_sticker_attachment(self):
        r = parse_todus_message(STANZA_MSG_STICKER)
        assert r["sticker_id"] == "sid1"
        assert r["sticker_name"] == "sticker1"
        assert r["sticker_pack"] == "pack1"

    def test_contact_attachment(self):
        r = parse_todus_message(STANZA_MSG_CONTACT)
        assert r["contact_id"] == "cid1"
        assert r["contact_name"] == "Juan"
        assert r["contact_phone"] == "5351111111"

    def test_location_attachment(self):
        r = parse_todus_message(STANZA_MSG_LOCATION)
        assert r["location_lat"] == 23.1136
        assert r["location_lon"] == -82.3666
        assert r["location_text"] == "La Habana"

    def test_event_attachment(self):
        r = parse_todus_message(STANZA_MSG_EVENT)
        assert r["event_title"] == "Reunion"
        assert r["event_start"] == 1700000000
        assert r["event_end"] == 1700003600
        assert r["event_all_day"] is False
        assert r["event_ics"] == "DATA"

    def test_edited(self):
        r = parse_todus_message(STANZA_MSG_EDITED)
        assert r["edited"] == "edit01"
        assert r["body"] == "Texto editado"

    def test_deleted(self):
        r = parse_todus_message(STANZA_MSG_DELETED)
        assert r["deleted"] == "del01"

    def test_chat_state_composing(self):
        r = parse_todus_message(STANZA_MSG_COMPOSING)
        assert r["chat_state"] == "composing"

    def test_delivery_receipt(self):
        r = parse_todus_message(STANZA_MSG_DELIVERED)
        assert r["receipt"] == "msg123"
        assert r["receipt_type"] == "delivered"

    def test_read_receipt(self):
        r = parse_todus_message(STANZA_MSG_READ)
        assert r["receipt"] == "msg456"
        assert r["receipt_type"] == "read"

    def test_buttons(self):
        r = parse_todus_message(STANZA_MSG_BUTTONS)
        assert len(r["buttons"]) == 2
        assert r["buttons"][0]["text"] == "Opcion 1"
        assert r["buttons"][1]["data"] == "2"

    def test_reply_to(self):
        r = parse_todus_message(STANZA_MSG_REPLY)
        assert r["reply_to"] == "original_id"

    def test_has_key(self):
        r = parse_todus_message(STANZA_MSG)
        assert r["has_key"] is True

    def test_default_fields(self):
        r = parse_todus_message(STANZA_MSG)
        assert r["url"] == ""
        assert r["file_size"] == 0
        assert r["deleted"] == ""
        assert r["buttons"] == []


# --- parse_presence ---

class TestParsePresence:
    def test_basic(self):
        r = parse_presence(STANZA_PRESENCE)
        assert r["from"] == "5354123456@im.todus.cu"
        assert r["show"] == "away"
        assert r["status"] == "Ausente"
        assert r["priority"] == 1


# --- parse_iq ---

class TestParseIq:
    def test_upload_urls(self):
        r = parse_iq(STANZA_IQ)
        assert r["upload_url"] == "https://upload.url"
        assert r["download_url"] == "https://download.url"

    def test_error_iq(self):
        stanza = """<iq i='err1' t='error'><error><text>not allowed</text></error></iq>"""
        r = parse_iq(stanza)
        assert r["type"] == "error"
        assert "not allowed" in r["error"]


# --- parse_tdack ---

class TestParseTdack:
    def test_basic(self):
        r = parse_tdack(STANZA_TDACK)
        assert r["type"] == "tdack"
        assert r["message_id"] == "msg123"


# --- IncrementalParser ---

class TestIncrementalParser:
    def test_single_message(self):
        p = IncrementalParser()
        results = p.feed(STANZA_MSG)
        assert len(results) == 1
        assert results[0]["body"] == "Hola mundo"

    def test_multiple_stanzas(self):
        p = IncrementalParser()
        results = p.feed(STANZA_MSG + STANZA_TDACK)
        assert len(results) == 2

    def test_fragmented_chunk(self):
        p = IncrementalParser()
        chunk1 = STANZA_MSG[:50]
        chunk2 = STANZA_MSG[50:]
        r1 = p.feed(chunk1)
        r2 = p.feed(chunk2)
        assert len(r1) == 0
        assert len(r2) == 1
        assert r2[0]["body"] == "Hola mundo"

    def test_dedup_by_id(self):
        p = IncrementalParser()
        results = p.feed(STANZA_MSG + STANZA_MSG)
        assert len(results) == 1

    def test_reset(self):
        p = IncrementalParser()
        p.feed(STANZA_MSG[:20])
        p.reset()
        assert p._buffer == ""

    def test_empty_feed(self):
        p = IncrementalParser()
        assert p.feed("") == []
        assert p.feed(None) == []


# --- extract_all_stanzas ---

class TestExtractAllStanzas:
    def test_extracts_all_types(self):
        xml = STANZA_MSG + STANZA_PRESENCE + STANZA_TDACK
        r = extract_all_stanzas(xml)
        assert len(r["messages"]) == 1
        assert len(r["presences"]) == 1
        assert len(r["tdacks"]) == 1


# --- _attr ---

class TestAttr:
    def test_double_quotes(self):
        assert _attr("<m i='abc123'/>", "i") == "abc123"

    def test_single_quotes(self):
        assert _attr("<m i=\"abc123\"/>", "i") == "abc123"

    def test_missing_attr(self):
        assert _attr("<m/>", "i") == ""
