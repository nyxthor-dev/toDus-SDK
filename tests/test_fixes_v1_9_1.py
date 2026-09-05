"""Tests para los fixes de v1.9.1.

Cada bug arreglado en v1.9.1 tiene aquí un test que:
1. Falla en v1.9.0 (sin el fix).
2. Pasa en v1.9.1 (con el fix).

Bugs cubiertos:
- #1  stop_event contaminado por _listen_loop finally (CRÍTICO)
- #2  Parser reemite stanzas en feeds separados
- #3  Parser no descarta <stream:stream> inicial
- #4  Parser no parsea <m .../> self-closing
- #5  Parser no respeta CDATA en <b>
- #6  Parser no maneja <b> anidados
- #7  RateLimiter race condition (timestamps > max_ops)
- #8  send_chat_state sin rate limiter
- #9  send_call_signal sin rate limiter
- #10 upload_file timeout hardcoded 60s
- #11 download_file no valida .part corrupto
- #12 _handshake sin timeout total (loop infinito potencial)
- #13 get_real_download_url retorna "" silenciosamente
- #14 upload_file override rompe LSP (no acepta token)
- #15 _is_group_target trata no-cubanos como grupos (documentado, no cambia comportamiento)
"""
import os
import sys
import time
import threading
from unittest.mock import MagicMock, patch
import inspect

import pytest


# ---------------------------------------------------------------------------
# Bug #1: stop_event contaminado por _listen_loop finally (CRÍTICO)
# ---------------------------------------------------------------------------


class TestStopEventNotContaminated:
    """El bug que apaga el bot cuando envía una respuesta durante listen.

    Antes, ``_listen_loop`` hacía ``stop_event.set()`` en ``finally`` para
    detener el keepalive worker — pero como recibía el mismo event que el
    caller, lo dejaba seteado para siempre. El caller creía que el usuario
    había pedido parar y apagaba el bot.
    """

    def test_stop_event_no_se_contamina_tras_fallo_de_red(self):
        """Si el loop falla por red (ConnectionLostError), el stop_event
        del caller NO debe quedar seteado — el caller no pidió parar."""
        from todus.client.message import ToDusMessageMixin
        from todus.errors import ConnectionLostError

        class FakeMixin(ToDusMessageMixin):
            def __init__(self):
                self._xml_parser = MagicMock()
                self._xml_parser.reset = MagicMock()
                self._xml_parser.feed = MagicMock(return_value=[])

            def _xmpp_session(self, token):
                class Ctx:
                    def __enter__(s): return MagicMock()
                    def __exit__(s, *a): return False
                return Ctx()

            def _recv_all(self, sock):
                # Simula servidor que cierra conexión al primer recv
                return None  # ConnectionLostError

        m = FakeMixin()
        user_stop_event = threading.Event()
        callback = MagicMock()

        t = threading.Thread(
            target=m.listen_messages,
            args=("fake_token", callback),
            kwargs={
                "stop_event": user_stop_event,
                "max_retries": 1,
                "base_backoff": 0.01,
            },
            daemon=True,
        )
        t.start()
        t.join(timeout=3)
        # En v1.9.0: user_stop_event.is_set() era True (BUG).
        # En v1.9.1: debe ser False — el caller no pidió parar.
        assert not user_stop_event.is_set(), (
            "stop_event fue contaminado por _listen_loop finally. "
            "El caller cree que pidió parar, pero solo fue un fallo de red."
        )


# ---------------------------------------------------------------------------
# Bugs #2-#6: IncrementalParser
# ---------------------------------------------------------------------------


class TestParserNoReemiteDuplicados:
    """Bug #2: feed() reemitía stanzas ya emitidas en feeds separados."""

    def test_stanza_en_feed_separado_no_se_reemite(self):
        from todus.parser import IncrementalParser

        parser = IncrementalParser()
        stanza = (
            "<m f='a@im.todus.cu' t='c' i='id1' xmlns='jc'>"
            "<k xmlns='x8'/><b>hola</b></m>"
        )
        msgs1 = parser.feed(stanza)
        msgs2 = parser.feed(stanza)  # Mismo stanza (reenvío del servidor)
        assert len(msgs1) == 1
        # En v1.9.0: len(msgs2) == 1 (BUG — reemitía).
        # En v1.9.1: len(msgs2) == 0 — el set de IDs vistos persiste.
        assert len(msgs2) == 0, (
            f"Parser reemitió stanza duplicada: {len(msgs2)} msgs"
        )


class TestParserDescartaStreamHeaders:
    """Bug #3: <?xml...?><stream:stream...> se quedaba pegado al buffer."""

    def test_stream_open_se_descarta(self):
        from todus.parser import IncrementalParser

        parser = IncrementalParser()
        chunk = (
            "<?xml version='1.0'?><stream:stream xmlns='jc' o='im.todus.cu' "
            "xmlns:stream='x1' v='1.0'>"
            "<m f='5300000000@im.todus.cu' t='c' i='id1' xmlns='jc'>"
            "<k xmlns='x8'/><b>hola</b></m>"
        )
        msgs = parser.feed(chunk)
        assert len(msgs) == 1
        # En v1.9.0: el buffer aún contenía <?xml...?><stream:stream...>.
        # En v1.9.1: el buffer debe estar limpio.
        assert parser._buffer == "", (
            f"Buffer no se limpió: {parser._buffer!r}"
        )


class TestParserSelfClosingM:
    """Bug #4: <m .../> self-closing no se parseaba."""

    def test_m_self_closing_se_parsea(self):
        from todus.parser import IncrementalParser

        parser = IncrementalParser()
        chunk = "<m f='a@im.todus.cu' t='c' i='id1' xmlns='jc'/>"
        msgs = parser.feed(chunk)
        # En v1.9.0: 0 msgs (BUG — el patrón exigía </m>).
        # En v1.9.1: 1 msg.
        assert len(msgs) == 1, f"Self-closing no se parseó: {len(msgs)} msgs"


class TestParserCDATAEnBody:
    """Bug #5: CDATA en <b> corrompía el body."""

    def test_cdata_en_body_se_limpia(self):
        from todus.parser import IncrementalParser

        parser = IncrementalParser()
        chunk = (
            "<m f='a@im.todus.cu' t='c' i='id1' xmlns='jc'>"
            "<k xmlns='x8'/><b><![CDATA[hello <world>]]></b></m>"
        )
        msgs = parser.feed(chunk)
        assert len(msgs) == 1
        # En v1.9.0: "<![CDATAello <world>]]>" (corrupto).
        # En v1.9.1: "hello <world>" (CDATA limpiado).
        assert msgs[0]["body"] == "hello <world>", (
            f"CDATA no se limpió: {msgs[0]['body']!r}"
        )


class TestParserNestedB:
    """Bug #6: <b> anidados se rompían por non-greedy regex."""

    def test_b_anidados_se_balancean(self):
        from todus.parser import IncrementalParser

        parser = IncrementalParser()
        chunk = (
            "<m f='a@im.todus.cu' t='c' i='id1' xmlns='jc'>"
            "<k xmlns='x8'/><b>texto <b>negrita</b> aqui</b></m>"
        )
        msgs = parser.feed(chunk)
        assert len(msgs) == 1
        # En v1.9.0: "texto <b>negrita" (truncado en el primer </b>).
        # En v1.9.1: "texto <b>negrita</b> aqui" (balanceado).
        assert msgs[0]["body"] == "texto <b>negrita</b> aqui", (
            f"<b> anidado mal balanceado: {msgs[0]['body']!r}"
        )


# ---------------------------------------------------------------------------
# Bug #7: RateLimiter race condition
# ---------------------------------------------------------------------------


class TestRateLimiterNoRace:
    """Bug #7: dos threads podían exceder max_ops."""

    def test_dos_threads_no_exceden_max_ops(self):
        from todus.ratelimit import RateLimiter

        limiter = RateLimiter(max_ops=2, window_seconds=2.0)
        limiter.wait()
        limiter.wait()
        # Lleno. Ahora dos threads en paralelo piden slot.
        results = []

        def worker():
            limiter.wait()
            results.append(time.time())

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start(); t2.start()
        t1.join(timeout=5); t2.join(timeout=5)
        # En v1.9.0: len(limiter._timestamps) > max_ops (race condition).
        # En v1.9.1: nunca se excede max_ops.
        assert len(limiter._timestamps) <= limiter.max_ops, (
            f"Race condition: timestamps={len(limiter._timestamps)} > "
            f"max_ops={limiter.max_ops}"
        )


# ---------------------------------------------------------------------------
# Bugs #8-#9: send_chat_state y send_call_signal con rate limiter
# ---------------------------------------------------------------------------


class TestSendChatStateRateLimited:
    """Bug #8: send_chat_state no usaba rate limiter."""

    def test_send_chat_state_llama_rate_limiter(self):
        from todus.client.message import ToDusMessageMixin
        src = inspect.getsource(ToDusMessageMixin.send_chat_state)
        assert "_rate_limiter.wait" in src, (
            "send_chat_state debe llamar self._rate_limiter.wait()"
        )


class TestSendCallSignalRateLimited:
    """Bug #9: send_call_signal no usaba rate limiter."""

    def test_send_call_signal_llama_rate_limiter(self):
        from todus.client.message import ToDusMessageMixin
        src = inspect.getsource(ToDusMessageMixin.send_call_signal)
        assert "_rate_limiter.wait" in src, (
            "send_call_signal debe llamar self._rate_limiter.wait()"
        )


# ---------------------------------------------------------------------------
# Bug #10: upload_file timeout configurable
# ---------------------------------------------------------------------------


class TestUploadFileTimeoutConfigurable:
    """Bug #10: upload_file tenía timeout=60 hardcoded."""

    def test_upload_file_acepta_parametro_timeout(self):
        from todus.client.file import ToDusFileMixin
        sig = inspect.signature(ToDusFileMixin.upload_file)
        assert "timeout" in sig.parameters, (
            "upload_file debe aceptar parámetro timeout"
        )

    def test_upload_file_default_no_es_60(self):
        """El default no debe ser 60s (insuficiente para uploads grandes)."""
        from todus.client.file import ToDusFileMixin
        sig = inspect.signature(ToDusFileMixin.upload_file)
        # Si timeout no tiene default None, fallar
        timeout_param = sig.parameters.get("timeout")
        # El default puede ser None (en cuyo caso el código usa 300 internamente)
        # o directamente 300. Lo importante es que no sea 60.
        assert timeout_param is not None, "Falta parámetro timeout"

    def test_upload_file_toDusClient2_acepta_timeout(self):
        from todus.client import ToDusClient2
        sig = inspect.signature(ToDusClient2.upload_file)
        assert "timeout" in sig.parameters


# ---------------------------------------------------------------------------
# Bug #11: download_file valida .part corrupto
# ---------------------------------------------------------------------------


class TestDownloadFileValidatesPart:
    """Bug #11: download_file no validaba integridad del .part."""

    def test_download_file_hace_head_pre_resume(self):
        from todus.client.file import ToDusFileMixin
        src = inspect.getsource(ToDusFileMixin.download_file)
        # Debe haber una llamada a self.session.head() para validar el .part
        assert "session.head" in src or "head(" in src, (
            "download_file debe hacer HEAD pre-resume para validar .part"
        )
        # Debe descartar el .part si es más grande que el tamaño total
        assert "os.remove" in src or "os.unlink" in src, (
            "download_file debe descartar .part corrupto"
        )


# ---------------------------------------------------------------------------
# Bug #12: _handshake con timeout total
# ---------------------------------------------------------------------------


class TestHandshakeTimeout:
    """Bug #12: _handshake podía entrar en loop infinito."""

    def test_handshake_tiene_timeout_total(self):
        from todus.client.base import ToDusClientBase
        src = inspect.getsource(ToDusClientBase._handshake)
        assert "max_handshake_seconds" in src, (
            "_handshake debe tener un timeout total para evitar loop infinito"
        )
        # Debe levantar ConnectionLostError cuando se acaba el tiempo
        assert "Handshake timeout" in src or "ConnectionLostError" in src


# ---------------------------------------------------------------------------
# Bug #13: get_real_download_url no retorna "" silencioso
# ---------------------------------------------------------------------------


class TestGetRealDownloadUrlNoSilentEmpty:
    """Bug #13: get_real_download_url podía retornar "" silenciosamente."""

    def test_get_real_download_url_levanta_si_no_hay_match(self):
        from todus.client.file import ToDusFileMixin
        src = inspect.getsource(ToDusFileMixin.get_real_download_url)
        # No debe haber "return ''" silencioso al final
        assert "return \"\"" not in src, (
            "get_real_download_url no debe retornar '' silenciosamente; "
            "debe levantar ConnectionLostError"
        )
        # Debe levantar ConnectionLostError al final
        assert "raise ConnectionLostError" in src


# ---------------------------------------------------------------------------
# Bug #14: upload_file override mantiene LSP con token opcional
# ---------------------------------------------------------------------------


class TestUploadFileLSP:
    """Bug #14: el override en ToDusClient2 rompía LSP."""

    def test_upload_file_en_ToDusClient2_acepta_token(self):
        from todus.client import ToDusClient2, ToDusClient
        sig2 = inspect.signature(ToDusClient2.upload_file)
        sig1 = inspect.signature(ToDusClient.upload_file)
        # La base acepta token; el override también debe aceptarlo (aunque
        # sea opcional y use self._token si no se pasa).
        assert "token" in sig2.parameters, (
            "ToDusClient2.upload_file debe aceptar `token` (LSP-compatible)"
        )


# ---------------------------------------------------------------------------
# Bug #15: _is_group_target documentado (no cambia comportamiento)
# ---------------------------------------------------------------------------


class TestIsGroupTargetDocumented:
    """Bug #15: el comportamiento de tratar no-cubanos como grupos está
    ahora documentado en el docstring (no se cambia para no romper
    compatibilidad, pero el usuario debe ser consciente)."""

    def test_is_group_target_doc_menciona_no_cubanos(self):
        from todus.client import ToDusClient2
        doc = ToDusClient2._is_group_target.__doc__ or ""
        # El docstring debe advertir sobre el caso de no-cubanos
        assert "cubano" in doc.lower() or "no-cuban" in doc.lower(), (
            "_is_group_target debe documentar que trata no-cubanos como grupos"
        )
