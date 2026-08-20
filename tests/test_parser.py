"""Tests para el parser incremental y deduplicación por ID."""
import pytest
from todus.parser import IncrementalParser, parse_todus_message


class TestIncrementalParser:
    def test_feed_simple_message(self):
        p = IncrementalParser()
        xml = "<m f='5312345678@im.todus.cu' i='abc123' t='c' xmlns='jc'><k xmlns='x8'/><b>Hola</b></m>"
        results = p.feed(xml)
        assert len(results) == 1
        assert results[0]["body"] == "Hola"
        assert results[0]["id"] == "abc123"

    def test_dedup_by_id(self):
        """Mismo ID no debería duplicarse."""
        p = IncrementalParser()
        xml1 = "<m f='5312345678@im.todus.cu' i='abc123' t='c' xmlns='jc'><k xmlns='x8'/><b>Hola</b></m>"
        xml2 = "<m f='5312345678@im.todus.cu' i='abc123' t='c' xmlns='jc'><k xmlns='x8'/><b>Hola</b></m>"
        results = p.feed(xml1 + xml2)
        assert len(results) == 1

    def test_different_ids_not_deduped(self):
        """IDs diferentes deberían pasar."""
        p = IncrementalParser()
        xml1 = "<m f='5312345678@im.todus.cu' i='aaa' t='c' xmlns='jc'><k xmlns='x8'/><b>Msg1</b></m>"
        xml2 = "<m f='5312345678@im.todus.cu' i='bbb' t='c' xmlns='jc'><k xmlns='x8'/><b>Msg2</b></m>"
        results = p.feed(xml1 + xml2)
        assert len(results) == 2

    def test_fragmented_message(self):
        """Mensaje partido en dos chunks."""
        p = IncrementalParser()
        full = "<m f='5312345678@im.todus.cu' i='abc' t='c' xmlns='jc'><k xmlns='x8'/><b>Hola mundo</b></m>"
        chunk1 = full[:50]
        chunk2 = full[50:]
        r1 = p.feed(chunk1)
        assert len(r1) == 0  # Incompleto
        r2 = p.feed(chunk2)
        assert len(r2) == 1
        assert r2[0]["body"] == "Hola mundo"

    def test_buffer_cleanup(self):
        """Buffer no debería crecer infinito."""
        p = IncrementalParser()
        # Alimentar basura que no es XML válido
        for _ in range(10):
            p.feed("x" * 3000)
        assert len(p._buffer) < 20000

    def test_reset(self):
        p = IncrementalParser()
        p.feed("some data")
        p.reset()
        assert p._buffer == ""


class TestParseTodusMessage:
    def test_group_message_detection(self):
        xml = "<m f='grupo123@muclight.im.todus.cu/53123@im.todus.cu' i='abc' t='gc' xmlns='jc'><k xmlns='x8'/><b>Hola grupo</b></m>"
        result = parse_todus_message(xml)
        assert result["is_group"] is True
        assert result["group_id"] == "grupo123"
        assert result["sender_phone"] == "53123"

    def test_reply_to(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><reply xmlns='reply:n' mi='msg_original'/><k xmlns='x8'/><b>Respuesta</b></m>"
        result = parse_todus_message(xml)
        assert result["reply_to"] == "msg_original"

    def test_edited(self):
        xml = "<m f='53@im.todus.cu' i='edit_id' t='c' xmlns='jc'><edited xmlns='edited:n' i='edit_id' mi='original_id'/><k xmlns='x8'/><b>Nuevo texto</b></m>"
        result = parse_todus_message(xml)
        assert result["edited"] == "edit_id"  # El parser extrae el ID del edit (atributo 'i')

    def test_deleted(self):
        xml = "<m f='53@im.todus.cu' i='del_id' t='c' xmlns='jc'><deleted xmlns='deleted:n' i='del_id' mi='msg_borrado'/><k xmlns='x8'/><b>Eliminado</b></m>"
        result = parse_todus_message(xml)
        assert result["deleted"] == "msg_borrado"

    def test_buttons(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><button xmlns='button:n' btn_t='Opcion 1' btn_cmd='cmd_type_send' btn_msg_c='dato1' btn_size='0.82'/><button xmlns='button:n' btn_t='Opcion 2' btn_cmd='cmd_type_url' btn_msg_c='https://ejemplo.com' btn_size='0.5'/><k xmlns='x8'/><b>Elige:</b></m>"
        result = parse_todus_message(xml)
        assert len(result["buttons"]) == 2
        assert result["buttons"][0]["text"] == "Opcion 1"
        assert result["buttons"][1]["command"] == "cmd_type_url"

    def test_location(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><location xmlns='location:n' i='loc1' mi='abc' lat='23.1136' lon='-82.3666' z='15.0' t='La Habana'/><k xmlns='x8'/><b/></m>"
        result = parse_todus_message(xml)
        assert result["location_lat"] == 23.1136
        assert result["location_lon"] == -82.3666
        assert result["location_text"] == "La Habana"

    def test_chat_state_composing(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><csp xmlns='uc1'/></m>"
        result = parse_todus_message(xml)
        assert result["chat_state"] == "composing"

    def test_chat_state_paused(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><csc xmlns='uc1'/></m>"
        result = parse_todus_message(xml)
        assert result["chat_state"] == "paused"

    def test_receipt_delivered(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><dd xmlns='x8' i='msg_id'/></m>"
        result = parse_todus_message(xml)
        assert result["receipt"] == "msg_id"
        assert result["receipt_type"] == "delivered"

    def test_receipt_read(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><rd xmlns='x8' i='msg_id'/></m>"
        result = parse_todus_message(xml)
        assert result["receipt"] == "msg_id"
        assert result["receipt_type"] == "read"

    def test_image_metadata(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><image xmlns='image:n' i='fid' mi='abc' url='https://example.com/img.jpg' n='foto.jpg' s='102400' h='hash123' w='800' he='600' tnail='thumb_hash'/><k xmlns='x8'/><b>Una foto</b></m>"
        result = parse_todus_message(xml)
        assert result["image_width"] == 800
        assert result["image_height"] == 600
        assert result["file_size"] == 102400
        assert result["url"] == "https://example.com/img.jpg"
        assert result["body"] == "Una foto"

    def test_video_metadata(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><video xmlns='video:n' i='vid1' mi='abc' url='https://example.com/vid.mp4' s='5000000' h='vhash' d='120' n='video.mp4' w='1920' he='1080' tnail='tnail_hash'/><k xmlns='x8'/><b/></m>"
        result = parse_todus_message(xml)
        assert result["video_duration"] == 120
        assert result["video_width"] == 1920
        assert result["video_height"] == 1080
        assert result["video_size"] == 5000000

    def test_event_metadata(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><event xmlns='event:n' i='evt1' mi='abc' ti='Reunion' s='1700000000' e='1700003600' ad='false'><ics>ICS_DATA</ics></event><k xmlns='x8'/><b/></m>"
        result = parse_todus_message(xml)
        assert result["event_title"] == "Reunion"
        assert result["event_start"] == 1700000000
        assert result["event_end"] == 1700003600
        assert result["event_all_day"] is False
        assert result["event_ics"] == "ICS_DATA"

    def test_has_format(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><k xmlns='x8'/><b>Visita <linkInfo url='https://ejemplo.com'>este enlace</linkInfo></b></m>"
        result = parse_todus_message(xml)
        assert result["has_format"] is True

    def test_offline_timestamp(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><todus_offline ts='1700000000'/><k xmlns='x8'/><b>Mensaje offline</b></m>"
        result = parse_todus_message(xml)
        assert result["offline_ts"] == "1700000000"

    def test_sticker(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><sticker xmlns='sticker:n' i='stk1' mi='abc' n='Happy' f='pack1' url='' s='0' h='shash' json=''/><k xmlns='x8'/><b/></m>"
        result = parse_todus_message(xml)
        assert result["sticker_id"] == "stk1"
        assert result["sticker_name"] == "Happy"
        assert result["sticker_pack"] == "pack1"
        assert result["sticker_hash"] == "shash"

    def test_contact(self):
        xml = "<m f='53@im.todus.cu' i='abc' t='c' xmlns='jc'><contact xmlns='contact:n' i='cid1' mi='abc' n='Juan' num='5300000000'/><k xmlns='x8'/><b/></m>"
        result = parse_todus_message(xml)
        assert result["contact_id"] == "cid1"
        assert result["contact_name"] == "Juan"
        assert result["contact_phone"] == "5300000000"
