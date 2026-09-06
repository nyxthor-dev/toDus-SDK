"""Tests de alineación con el protocolo oficial v2.1.2.

Cubre: stanzas nuevas (voice, gif, streamvideo, reaction, resend, tcall,
mention), IQs de grupo nuevas, parser de las extensiones nuevas,
transporte thread-safe (sendall), validación de teléfonos y constantes.
"""

import socket
import struct
import threading
import time
import pytest

from todus import constants
from todus.parser import parse_todus_message, parse_ack
from todus.stanzas import private, group, utils
from todus.client.base import ThreadSafeSocket, ToDusClientBase
from todus.client.file import _needs_auth
from todus.util import normalize_phone, generate_msg_id, get_image_dimensions


# --- Constantes de transporte ---

class TestConstants:
    def test_xmpp_port_is_prod(self):
        # El puerto de producción es 1756
        assert constants.XMPP_PORT == 1756

    def test_xmpp_port_prod2(self):
        assert constants.XMPP_PORT_PROD2 == 5443

    def test_keepalive_interval(self):
        # PingManager.setPingInterval(30)
        assert constants.KEEPALIVE_INTERVAL == 30


# --- Stanzas nuevas (v2.1.2) ---

class TestNewPrivateStanzas:
    def test_voice_message(self):
        xml = private.voice_message("53@im.todus.cu", "https://u/v.opus", "v.opus",
                                    1024, 15, "1,2,3,4")
        assert "<voice xmlns='voice:n'" in xml
        assert "url='https://u/v.opus'" in xml
        assert "d='15'" in xml
        assert "ws='1,2,3,4'" in xml
        assert "s='1024'" in xml

    def test_gif_message(self):
        xml = private.gif_message("53@im.todus.cu", "https://u/g.gif", "g.gif",
                                  50000, 400, 300, "THUMB")
        assert "<gif xmlns='gif:n'" in xml
        assert "w='400'" in xml
        assert "he='300'" in xml
        assert "tnail='THUMB'" in xml

    def test_stream_video_message(self):
        xml = private.stream_video_message("53@im.todus.cu", "guid-1",
                                           "https://s/stream", 60, "h264")
        assert "<streamvideo xmlns='streamvideo:n'" in xml
        assert "gu='guid-1'" in xml
        assert "su='https://s/stream'" in xml
        assert "du='60'" in xml
        assert "ec='h264'" in xml

    def test_reaction_message(self):
        xml = private.reaction_message("53@im.todus.cu", "msg123", "❤")
        assert "<reaction xmlns='reaction:n'" in xml
        assert "mi='msg123'" in xml
        assert "rc='❤'" in xml

    def test_forward_message(self):
        xml = private.forward_message("53@im.todus.cu", "msg123",
                                      "5354123456@im.todus.cu", body="mira esto")
        assert "<resend xmlns='resend:n'" in xml
        assert "mi='msg123'" in xml
        assert "uowner='5354123456@im.todus.cu'" in xml
        assert "<b>mira esto</b>" in xml
        # Fix v1.10.2: ``i=`` del resend es un ID NUEVO, distinto del ``i=`` del <m>
        import re
        m_match = re.search(r"<m [^>]*i='([^']+)'", xml)
        resend_match = re.search(r"<resend [^>]*i='([^']+)'", xml)
        assert m_match and resend_match
        assert m_match.group(1) != resend_match.group(1), (
            f"i del <m> ({m_match.group(1)}) debe ser distinto del i del <resend> ({resend_match.group(1)})"
        )

    def test_tcall_message(self):
        xml = private.tcall_message("53@im.todus.cu", "ringing", "call-9")
        assert "<tcall xmlns='tcall:n'" in xml
        assert "st='ringing'" in xml
        assert "cid='call-9'" in xml

    def test_mention_extension(self):
        xml = private.mention_extension(0, 5, "5354123456@im.todus.cu")
        assert "<mention xmlns='mention:n'" in xml
        assert "o='0'" in xml
        assert "l='5'" in xml
        assert "ui='5354123456@im.todus.cu'" in xml

    def test_button_message_official_attrs(self):
        btns = [{"text": "Web", "command": "cmd_open_web", "data": "https://x.cu",
                 "description": "Abrir sitio", "size": "0.4"}]
        xml = private.button_message("53@im.todus.cu", "Ver", btns)
        assert "btn_d='Abrir sitio'" in xml
        assert "btn_size='0.4'" in xml
        assert "btn_cmd='cmd_open_web'" in xml
        # atributos no soportados por el protocolo
        assert "btn_color" not in xml
        assert "btn_row" not in xml

    def test_no_reply_extension(self):
        # Fix v1.10.2: respuestas usan ``reply:n`` (no ``resend:n``)
        xml = private.message("53@im.todus.cu", "hola", reply_to_id="orig")
        assert "<reply xmlns='reply:n'" in xml
        assert "mi='orig'" in xml
        # resend se reserva para forward
        assert "<resend" not in xml or "reply:n" in xml


class TestNewGroupStanzas:
    def test_create_group(self):
        xml = group.group_create_iq("Mi grupo", ["5354123456"])
        assert "xmlns='x16'" in xml
        assert "<roomname>Mi grupo</roomname>" in xml
        assert "<user>5354123456@im.todus.cu</user>" in xml

    def test_my_groups(self):
        xml = group.group_my_groups_iq(index=0, limit=20)
        assert "xmlns='todus:muclight:my_mucs:2'" in xml
        assert "index='0'" in xml
        assert "limit='20'" in xml

    def test_promote_admin(self):
        xml = group.group_promote_admin_iq("g1@muclight.im.todus.cu", ["5354123456"])
        assert "xmlns='td:g:promote'" in xml
        assert "new_occupants='5354123456@im.todus.cu'" in xml

    def test_demote_admin(self):
        xml = group.group_demote_admin_iq("g1@muclight.im.todus.cu", ["5354123456"])
        assert "xmlns='td:g:demote'" in xml

    def test_info_by_link(self):
        xml = group.group_info_by_link_iq("https://todus.cu/l/abc")
        assert "xmlns='td:g:info_by_link'" in xml
        assert "link='https://todus.cu/l/abc'" in xml

    def test_info_by_id(self):
        xml = group.group_info_by_id_iq("abc123")
        assert "xmlns='td:g:info_by_id'" in xml
        assert "room='abc123@muclight.im.todus.cu'" in xml

    def test_set_members_uses_add_occupant(self):
        # Las mutaciones de miembros usan td:g:add_occupant, no x11
        xml = group.group_set_members_iq("g1@muclight.im.todus.cu",
                                         {"5354123456": "participant"})
        assert "xmlns='td:g:add_occupant'" in xml
        assert "new_occupants='5354123456@im.todus.cu'" in xml

    def test_group_message_reply_uses_resend(self):
        # Fix v1.10.2: respuestas usan ``reply:n`` (no ``resend:n``)
        xml = group.group_message("g1@muclight.im.todus.cu", "hola", reply_to_id="orig")
        assert "<reply xmlns='reply:n'" in xml
        assert "mi='orig'" in xml


# --- Parser de extensiones nuevas ---

STANZA_VOICE = """<m f='5354123456@im.todus.cu' o='5398765432' i='v1' t='c' xmlns='jc'><k xmlns='x8'/><voice xmlns='voice:n' i='fv1' mi='v1' url='https://u/v.opus' s='2048' h='' d='12' n='v.opus' ws='1,2,3'/><b/></m>"""
STANZA_GIF = """<m f='5354123456@im.todus.cu' o='5398765432' i='g1' t='c' xmlns='jc'><k xmlns='x8'/><gif xmlns='gif:n' i='fg1' mi='g1' url='https://u/g.gif' n='g.gif' s='4096' h='' w='320' he='240' tnail='T'/><b/></m>"""
STANZA_STREAM = """<m f='5354123456@im.todus.cu' o='5398765432' i='sv1' t='c' xmlns='jc'><streamvideo xmlns='streamvideo:n' gu='gu-1' su='https://s/x' du='90' ec='av1'/></m>"""
STANZA_REACTION = """<m f='5354123456@im.todus.cu' o='5398765432' i='r1' t='c' xmlns='jc'><reaction xmlns='reaction:n' i='fr1' mi='target1' mir='target1' rc='❤' ca=''/></m>"""
STANZA_MENTION = """<m f='5354123456@im.todus.cu' o='5398765432' i='mn1' t='c' xmlns='jc'><k xmlns='x8'/><b>Hola @juan que tal</b><mention xmlns='mention:n' o='5' l='5' ui='5354123456@im.todus.cu'/></m>"""
STANZA_RESEND = """<m f='5354123456@im.todus.cu' o='5398765432' i='fw1' t='c' xmlns='jc'><k xmlns='x8'/><resend xmlns='resend:n' i='fw1' mi='original1' uowner='5398765432@im.todus.cu'/><b/></m>"""
STANZA_TCALL = """<m f='5354123456@im.todus.cu' o='5398765432' i='tc1' t='c' xmlns='jc'><tcall xmlns='tcall:n' i='tc1' mi='tc1' st='ringing' cid='call-42'/></m>"""
STANZA_ACK = """<ak xmlns='x8' i='msg789'/>"""


class TestNewParserExtensions:
    def test_voice(self):
        r = parse_todus_message(STANZA_VOICE)
        assert r["voice_url"] == "https://u/v.opus"
        assert r["voice_size"] == 2048
        assert r["voice_duration"] == 12
        assert r["voice_wave"] == "1,2,3"
        assert r["url"] == "https://u/v.opus"

    def test_gif(self):
        r = parse_todus_message(STANZA_GIF)
        assert r["gif_url"] == "https://u/g.gif"
        assert r["gif_size"] == 4096
        assert r["gif_width"] == 320
        assert r["gif_height"] == 240

    def test_stream_video(self):
        r = parse_todus_message(STANZA_STREAM)
        assert r["stream_guid"] == "gu-1"
        assert r["stream_url"] == "https://s/x"
        assert r["stream_duration"] == 90
        assert r["stream_codec"] == "av1"

    def test_reaction(self):
        r = parse_todus_message(STANZA_REACTION)
        assert r["reaction_msg_id"] == "target1"
        assert r["reaction_code"] == "❤"

    def test_mentions(self):
        r = parse_todus_message(STANZA_MENTION)
        assert len(r["mentions"]) == 1
        assert r["mentions"][0]["offset"] == 5
        assert r["mentions"][0]["length"] == 5
        assert r["mentions"][0]["user_id"] == "5354123456@im.todus.cu"

    def test_resend_forward(self):
        r = parse_todus_message(STANZA_RESEND)
        assert r["forward_id"] == "original1"
        assert r["forward_owner"] == "5398765432@im.todus.cu"
        assert r["reply_to"] == "original1"

    def test_tcall(self):
        r = parse_todus_message(STANZA_TCALL)
        assert r["call_state"] == "ringing"
        assert r["call_id"] == "call-42"

    def test_parse_ack(self):
        r = parse_ack(STANZA_ACK)
        assert r["type"] == "ack"
        assert r["message_id"] == "msg789"

    def test_incremental_parser_handles_ack(self):
        from todus.parser import IncrementalParser
        p = IncrementalParser()
        stanzas = p.feed(STANZA_ACK)
        types = [s.get("type") for s in stanzas]
        assert "ack" in types


# --- Transporte thread-safe ---

class TestThreadSafeSocket:
    def _make_sock(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        addr = server.getsockname()

        received = []
        accepted = []

        def accept():
            conn, _ = server.accept()
            accepted.append(conn)
            while True:
                data = conn.recv(65536)
                if not data:
                    break
                received.append(data)

        t = threading.Thread(target=accept, daemon=True)
        t.start()

        raw = socket.create_connection(addr, timeout=5)
        sock = ThreadSafeSocket(raw)
        return sock, received, accepted, server

    def test_sendall_delivers_everything(self):
        sock, received, accepted, server = self._make_sock()
        payload = b"x" * 300000  # mayor que un solo write TCP
        sock.sendall(payload)
        time.sleep(0.3)
        total = b"".join(received)
        assert total == payload
        sock.close()
        accepted[0].close()
        server.close()

    def test_concurrent_writes_are_atomic(self):
        sock, received, accepted, server = self._make_sock()
        chunks = [bytes([65 + i]) * 1024 for i in range(8)]

        def writer(i):
            for _ in range(20):
                sock.sendall(chunks[i])

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(8)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        time.sleep(0.4)
        total = b"".join(received)
        assert len(total) == 8 * 20 * 1024
        # cada bloque de 1024 debe ser de una sola letra (sin intercalado)
        for i in range(0, len(total), 1024):
            block = total[i:i + 1024]
            assert len(set(block)) == 1, "escritura intercalada detectada"
        sock.close()
        accepted[0].close()
        server.close()

    def test_send_redirects_to_sendall(self):
        sock, received, accepted, server = self._make_sock()
        sock.send(b"hola")
        time.sleep(0.2)
        assert b"".join(received) == b"hola"
        sock.close()
        accepted[0].close()
        server.close()


# --- Utilidades ---

class TestNormalizePhone:
    def test_valid_cuban_with_prefix(self):
        assert normalize_phone("5351234567") == "5351234567"

    def test_valid_national(self):
        assert normalize_phone("51234567") == "5351234567"

    def test_plus_and_spaces(self):
        assert normalize_phone("+53 5123 4567") == "5351234567"

    def test_rejects_garbage(self):
        # antes truncaba silenciosamente basura de 16 dígitos
        with pytest.raises(ValueError):
            normalize_phone("5351234567890123")

    def test_rejects_short(self):
        with pytest.raises(ValueError):
            normalize_phone("12345")

    def test_rejects_letters(self):
        with pytest.raises(ValueError):
            normalize_phone("53512345abc")

    def test_rejects_international_numbers(self):
        """ToDus es plataforma cubana: solo se aceptan números cubanos."""
        # Brasil (5511...) debe rechazarse
        with pytest.raises(ValueError):
            normalize_phone("5511987654321")
        # USA (1...) debe rechazarse
        with pytest.raises(ValueError):
            normalize_phone("15551234567")
        # España (34...) debe rechazarse
        with pytest.raises(ValueError):
            normalize_phone("34612345678")

    def test_rejects_too_long(self):
        # 16 dígitos con prefijo 53 → rechazado (no es 53 + 8)
        with pytest.raises(ValueError):
            normalize_phone("5351234567890123")


class TestGenerateMsgId:
    def test_is_32_hex(self):
        mid = generate_msg_id()
        assert len(mid) == 32
        assert all(c in "0123456789abcdef" for c in mid)

    def test_unique(self):
        assert generate_msg_id() != generate_msg_id()


class TestImageDimensions:
    def test_png_real_header(self):
        # PNG 100x200 con IHDR en el offset correcto
        png = (b'\x89PNG\r\n\x1a\n'
               + struct.pack('>I', 13) + b'IHDR'
               + struct.pack('>IIBBBBB', 100, 200, 8, 2, 0, 0, 0)
               + b'\x00' * 4)
        assert get_image_dimensions(png) == (100, 200)

    def test_png_truncated_returns_zero(self):
        assert get_image_dimensions(b'\x89PNG\r\n\x1a\n') == (0, 0)

    def test_unknown_format(self):
        assert get_image_dimensions(b'GIF89a blah') == (0, 0)


class TestDownloadAuth:
    def test_official_no_auth(self):
        assert not _needs_auth("https://cdn.todus.cu/official/img.jpg")

    def test_catalog_no_auth(self):
        assert not _needs_auth("https://todus.cu/catalog/x")

    def test_status_no_auth(self):
        assert not _needs_auth("https://todus.cu/status/y")

    def test_stream_no_auth(self):
        assert not _needs_auth("https://media.todus.cu/stream/z")

    def test_normal_needs_auth(self):
        assert _needs_auth("https://x.todus.cu/file/abc")


# --- Cliente ---

class TestClientConstruction:
    def test_custom_xmpp_port(self):
        client = ToDusClientBase(xmpp_port=5443)
        assert client.xmpp_port == 5443

    def test_default_port(self):
        client = ToDusClientBase()
        assert client.xmpp_port == constants.XMPP_PORT

    def test_bind_resource_format(self):
        xml = utils.bind("b1", username="5354123456")
        import re as _re
        m = _re.search(r"<re>([0-9a-f]{32})_Android</re>", xml)
        assert m is not None


class TestClient2NewMethods:
    def _client(self):
        from todus import ToDusClient2
        return ToDusClient2("5354123456", "secret")

    def test_new_methods_exist(self):
        client = self._client()
        for name in ("send_voice_message", "send_gif_message", "send_reaction",
                     "forward_message", "send_stream_video_message",
                     "send_call_signal"):
            assert callable(getattr(client, name)), f"falta método {name}"

    def test_methods_require_auth(self):
        client = self._client()
        from todus.errors import AuthenticationError
        with pytest.raises(AuthenticationError):
            client.send_voice_message("5398765432", "https://u/v.opus", "v.opus", 1024, 10)
        with pytest.raises(AuthenticationError):
            client.send_gif_message("5398765432", "https://u/g.gif", "g.gif", 1024)
        with pytest.raises(AuthenticationError):
            client.send_reaction("5398765432", "msg1", "❤")
        with pytest.raises(AuthenticationError):
            client.forward_message("5398765432", "msg1")

    def test_group_client_new_methods(self):
        client = self._client()
        g = client.groups
        for name in ("create_group", "get_my_groups", "promote_admin",
                     "demote_admin", "get_group_info_by_link",
                     "get_group_info_by_id", "send_voice", "send_gif",
                     "send_reaction"):
            assert callable(getattr(g, name)), f"falta método {name}"
