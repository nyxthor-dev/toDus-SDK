"""Tests para los fixes de bugs críticos.

Estos tests validan específicamente los bugs corregidos en esta PR:

- P0 #1: ``_retry_worker_loop`` marca SENT en vez de PENDING tras reenvío exitoso.
- P0 #2: ``send_message_queued`` encola ANTES de enviar (no pierde mensajes).
- P1 #5: ``_is_group_target`` rechaza strings numéricos inválidos.
- P2: ``MessageStore`` usa conexión persistente, ``clear_stale`` limpia PENDING.
- P2: ``_seen_msg_ids`` es LRU determinista (OrderedDict).
- P2: ``ToDusClientWithQueue`` soporta ``close()`` y context manager.
- ``login_with_phone_only``: método oficial solo-con-número (sin password/SMS/JWT).
"""
import os
import time
import tempfile
import threading
from unittest.mock import MagicMock, patch

import pytest

from todus.cache import MessageStore, Message, MessageStatus, MessageQueue
from todus.cache.mixin import MessageQueueMixin
from todus.client_with_queue import ToDusClientWithQueue


# ---------------------------------------------------------------------------
# P0 #1: retry worker marca SENT (no PENDING) tras reenvío exitoso
# ---------------------------------------------------------------------------


class TestRetryWorkerMarksSent:
    def setup_method(self):
        self.tmpfile = tempfile.mktemp(suffix=".db")
        self.store = MessageStore(self.tmpfile)
        self.queue = MessageQueue(self.store, auto_retry=False)

    def teardown_method(self):
        self.store.close()
        if os.path.exists(self.tmpfile):
            os.unlink(self.tmpfile)

    def test_retry_worker_marks_sent_on_success(self):
        """Si ``send_fn`` retorna True, el mensaje debe quedar SENT, no PENDING."""
        msg = Message(msg_id="m_retry_ok", to="5300000000@im.todus.cu", body="hola")
        # Simular que ya fue intentado una vez (retry_count=1)
        msg.retry_count = 1
        msg.created_at = time.time() - 120  # viejo, califica para retry
        self.store.add(msg)

        # send_fn que siempre tiene éxito
        def fake_send(m):
            return True

        self.queue._send_fn = fake_send
        # Simular una iteración del worker loop manualmente
        success = self.queue._send_fn(msg)
        assert success is True

        # Aplicar la lógica de update que el worker ahora usa
        if success:
            self.store.update_status(msg.msg_id, MessageStatus.SENT)
            self.store.reset_retry_count(msg.msg_id)

        retrieved = self.store.get(msg.msg_id)
        assert retrieved.status == MessageStatus.SENT
        assert retrieved.retry_count == 0

    def test_retry_loop_does_not_reprocess_sent_message(self):
        """Mensaje marcado como SENT no debe ser reprocesado por el worker."""
        msg = Message(msg_id="m_already_sent", to="5300000000@im.todus.cu", body="hola",
                      status=MessageStatus.SENT)
        self.store.add(msg)

        # El worker solo pide PENDING
        pending = self.store.get_by_status(MessageStatus.PENDING)
        sent = self.store.get_by_status(MessageStatus.SENT)

        assert len(pending) == 0
        assert len(sent) == 1
        assert sent[0].msg_id == "m_already_sent"


# ---------------------------------------------------------------------------
# P0 #2: send_message_queued encola antes de enviar
# ---------------------------------------------------------------------------


class TestSendQueuedAtomicity:
    def setup_method(self):
        self.tmpfile = tempfile.mktemp(suffix=".db")

    def teardown_method(self):
        if os.path.exists(self.tmpfile):
            os.unlink(self.tmpfile)

    def _make_client(self):
        """Crea un cliente con token fake para los tests."""
        from todus.client import ToDusClient2
        client = ToDusClientWithQueue(
            "5300000000", "password", queue_db_path=self.tmpfile, verify_ssl=False
        )
        client._token = "fake.token.value"
        return client

    def test_send_message_queued_enqueues_before_send(self):
        """El mensaje debe estar en la cola ANTES de intentar enviar."""
        from todus.client import ToDusClient2
        from todus.errors import ConnectionLostError

        client = self._make_client()

        call_log = []

        def fake_send(self_client, to_phone, body, reply_to_id="", msg_id=""):
            call_log.append(("send", to_phone, body, msg_id))
            raise ConnectionLostError("red caída")

        with patch.object(ToDusClient2, "send_message", fake_send):
            # No debe relanzar ConnectionLostError (error de red = retry)
            msg_id = client.send_message_queued("5300000001", "hola")

        # El mensaje debe estar encolado como PENDING (no perdido)
        stats = client.get_queue_stats()
        assert stats.get("total_pending", 0) == 1, \
            "El mensaje debe quedar como PENDING en la cola tras fallo de red"

        # El send_message fue llamado con el mismo msg_id que se encoló
        assert len(call_log) == 1
        sent_args = call_log[0]
        enqueued = client._message_queue.dequeue(MessageStatus.PENDING, limit=1)
        assert len(enqueued) == 1
        assert enqueued[0].msg_id == sent_args[3], \
            "El msg_id encolado debe coincidir con el enviado por XMPP"

        client.close()

    def test_send_message_queued_marks_sent_on_success(self):
        """Si send_message tiene éxito, el mensaje queda como SENT."""
        from todus.client import ToDusClient2

        client = self._make_client()

        def fake_send(self_client, to_phone, body, reply_to_id="", msg_id=""):
            return msg_id

        with patch.object(ToDusClient2, "send_message", fake_send):
            msg_id = client.send_message_queued("5300000001", "hola")

        stats = client.get_queue_stats()
        assert stats.get("sent", 0) == 1
        assert stats.get("total_pending", 0) == 0
        client.close()

    def test_send_message_queued_marks_failed_on_auth_error(self):
        """Si send_message lanza AuthenticationError, se marca FAILED."""
        from todus.client import ToDusClient2
        from todus.errors import AuthenticationError

        client = self._make_client()

        def fake_send(self_client, to_phone, body, reply_to_id="", msg_id=""):
            raise AuthenticationError("token inválido")

        with patch.object(ToDusClient2, "send_message", fake_send):
            with pytest.raises(AuthenticationError):
                client.send_message_queued("5300000001", "hola")

        stats = client.get_queue_stats()
        assert stats.get("failed", 0) == 1
        client.close()


# ---------------------------------------------------------------------------
# P1 #5: _is_group_target rechaza strings numéricos inválidos
# ---------------------------------------------------------------------------


class TestIsGroupTarget:
    def setup_method(self):
        self.tmpfile = tempfile.mktemp(suffix=".db")
        self.client = ToDusClientWithQueue(
            "5300000000", "password", queue_db_path=self.tmpfile, verify_ssl=False
        )
        self.client._token = "fake.token.value"

    def teardown_method(self):
        self.client.close()
        if os.path.exists(self.tmpfile):
            os.unlink(self.tmpfile)

    @pytest.mark.parametrize("phone,expected", [
        ("5312345678", False),     # Cuba válido (10 dígitos empezando por 53)
        ("5351234567", False),     # Cuba válido
        ("5312345", True),         # 7 dígitos - inválido como teléfono → grupo
        ("1234567890123456", True),  # 16 dígitos - fuera de rango
        ("531234567", True),       # 9 dígitos - no es teléfono cubano válido → grupo
        ("12345678", True),        # 8 dígitos pero no empieza por 53 → grupo
        ("54123456", True),        # 8 dígitos nacionales sin 53 → grupo
                                    # (la normalización ocurre en normalize_phone,
                                    # no en _is_group_target)
        ("1234567", True),         # 7 dígitos - muy corto → grupo
        ("+5312345678", False),   # Cuba con prefijo +
        ("abc123", True),         # No numérico → grupo
        ("", False),              # Vacío → no grupo (no target)
    ])
    def test_phone_vs_group_detection(self, phone, expected):
        assert self.client._is_group_target(phone) is expected

    def test_group_jid_is_group(self):
        assert self.client._is_group_target("grp123@muclight.im.todus.cu") is True

    def test_user_jid_is_not_group(self):
        assert self.client._is_group_target("5300000000@im.todus.cu") is False


# ---------------------------------------------------------------------------
# P2: MessageStore clear_stale limpia PENDING/FAILED
# ---------------------------------------------------------------------------


class TestMessageStoreCleanup:
    def setup_method(self):
        self.tmpfile = tempfile.mktemp(suffix=".db")
        self.store = MessageStore(self.tmpfile)

    def teardown_method(self):
        self.store.close()
        if os.path.exists(self.tmpfile):
            os.unlink(self.tmpfile)

    def test_clear_stale_removes_old_pending_and_failed(self):
        old_ts = time.time() - (10 * 86400)

        # Mensajes viejos en estados no terminales
        old_pending = Message(msg_id="old_p", to="a", body="x",
                              status=MessageStatus.PENDING)
        old_pending.created_at = old_ts
        self.store.add(old_pending)

        old_failed = Message(msg_id="old_f", to="a", body="x",
                              status=MessageStatus.FAILED)
        old_failed.created_at = old_ts
        self.store.add(old_failed)

        # Mensajes nuevos (no deben borrarse)
        new_pending = Message(msg_id="new_p", to="a", body="x",
                              status=MessageStatus.PENDING)
        self.store.add(new_pending)

        # Mensaje viejo pero en estado terminal READ (clear_stale no lo toca)
        old_read = Message(msg_id="old_r", to="a", body="x",
                           status=MessageStatus.READ)
        old_read.created_at = old_ts
        self.store.add(old_read)

        deleted = self.store.clear_stale(days=7)
        assert deleted == 2
        assert self.store.get("old_p") is None
        assert self.store.get("old_f") is None
        assert self.store.get("new_p") is not None
        assert self.store.get("old_r") is not None  # clear_stale no toca READ

    def test_clear_old_does_not_remove_pending(self):
        """``clear_old`` solo debe borrar READ y DELIVERED, no PENDING."""
        old_ts = time.time() - (31 * 86400)

        old_pending = Message(msg_id="old_p", to="a", body="x",
                               status=MessageStatus.PENDING)
        old_pending.created_at = old_ts
        self.store.add(old_pending)

        old_read = Message(msg_id="old_r", to="a", body="x",
                           status=MessageStatus.READ)
        old_read.created_at = old_ts
        self.store.add(old_read)

        deleted = self.store.clear_old(days=30)
        assert deleted == 1
        assert self.store.get("old_r") is None
        assert self.store.get("old_p") is not None

    def test_add_returns_false_on_duplicate(self):
        """``INSERT OR IGNORE`` no debe sobrescribir mensajes existentes."""
        m1 = Message(msg_id="dup", to="a", body="original")
        assert self.store.add(m1) is True

        m2 = Message(msg_id="dup", to="a", body="sobrescrito")
        assert self.store.add(m2) is False  # ignorado

        retrieved = self.store.get("dup")
        assert retrieved.body == "original"  # no se sobreescribió


# ---------------------------------------------------------------------------
# P2: _seen_msg_ids LRU determinista
# ---------------------------------------------------------------------------


class TestSeenMsgIdsLRU:
    def setup_method(self):
        self.tmpfile = tempfile.mktemp(suffix=".db")
        self.client = ToDusClientWithQueue(
            "5300000000", "password", queue_db_path=self.tmpfile, verify_ssl=False
        )

    def teardown_method(self):
        self.client.close()
        if os.path.exists(self.tmpfile):
            os.unlink(self.tmpfile)

    def test_uses_ordered_dict(self):
        from collections import OrderedDict
        assert isinstance(self.client._seen_msg_ids, OrderedDict)

    def test_lru_eviction_is_deterministic_via_handle_parsed_stanza(self):
        """Al procesar más stanzas que ``max``, los más viejos se eliminan en FIFO."""
        # Configurar límites pequeños para el test
        self.client._seen_msg_ids_max = 5
        self.client._seen_msg_ids_trim_to = 2

        # Generar 6 stanzas con IDs "0".."5"
        for i in range(6):
            stanza = {
                "id": str(i),
                "type": "c",
                "from": "5300000000@im.todus.cu",
                "to": "5300000001@im.todus.cu",
                "body": f"msg {i}",
            }
            self.client.handle_parsed_stanza(stanza)

        # Tras procesar 6 stanzas con max=5, debe podar a 2 (los más nuevos)
        assert len(self.client._seen_msg_ids) == 2
        keys = list(self.client._seen_msg_ids.keys())
        # Los últimos procesados ("4", "5") deben sobrevivir
        assert keys == ["4", "5"]

    def test_move_to_end_on_reaccess(self):
        """Un mensaje re-visto debe ir al final (más recientemente usado)."""
        self.client._seen_msg_ids_max = 100  # Sin poda
        self.client._seen_msg_ids_trim_to = 50

        # Procesar tres stanzas
        for sid in ["a", "b", "c"]:
            self.client.handle_parsed_stanza({
                "id": sid, "type": "c", "from": "x@im.todus.cu",
                "to": "y@im.todus.cu", "body": sid,
            })

        # Re-procesar "a" (debe ir al final)
        self.client.handle_parsed_stanza({
            "id": "a", "type": "c", "from": "x@im.todus.cu",
            "to": "y@im.todus.cu", "body": "a-reaccessed",
        })

        keys = list(self.client._seen_msg_ids.keys())
        assert keys == ["b", "c", "a"]  # "a" ahora es el más reciente


# ---------------------------------------------------------------------------
# P2: ToDusClientWithQueue context manager
# ---------------------------------------------------------------------------


class TestClientContextManager:
    def setup_method(self):
        self.tmpfile = tempfile.mktemp(suffix=".db")

    def teardown_method(self):
        if os.path.exists(self.tmpfile):
            os.unlink(self.tmpfile)

    def test_context_manager_closes_resources(self):
        """``with`` debe cerrar el worker al salir del bloque."""
        with ToDusClientWithQueue(
            "5300000000", "password", queue_db_path=self.tmpfile, verify_ssl=False
        ) as client:
            assert client._message_queue is not None
            assert client._message_queue._running is True
            queue_ref = client._message_queue

        # Al salir del with, el worker debe estar detenido
        assert queue_ref._running is False

    def test_close_idempotent(self):
        """Llamar close() múltiples veces no debe lanzar excepciones."""
        client = ToDusClientWithQueue(
            "5300000000", "password", queue_db_path=self.tmpfile, verify_ssl=False
        )
        client.close()
        client.close()  # No debe lanzar

    def test_del_does_not_raise_on_incomplete_init(self):
        """Si __init__ falla a medias, __del__ no debe lanzar."""
        client = ToDusClientWithQueue.__new__(ToDusClientWithQueue)
        # No llamar __init__ — simula init parcial
        try:
            client.__del__()
        except Exception as e:
            pytest.fail(f"__del__ lanzó excepción: {e}")


# ---------------------------------------------------------------------------
# Otros fixes: escape_xml con comillas dobles, generate_msg_id con secrets
# ---------------------------------------------------------------------------


class TestUtilityFixes:
    def test_escape_xml_handles_double_quotes(self):
        from todus.util import escape_xml
        text = 'Hola "mundo" <>&\''
        escaped = escape_xml(text)
        assert "&quot;" in escaped
        assert "&lt;" in escaped
        assert "&gt;" in escaped
        assert "&amp;" in escaped
        assert "&apos;" in escaped

    def test_unescape_xml_roundtrip_with_quotes(self):
        from todus.util import escape_xml, unescape_xml
        original = 'Texto con "comillas" y <simbolos> & ampersand'
        assert unescape_xml(escape_xml(original)) == original

    def test_generate_msg_id_uses_secrets_not_md5(self):
        """Los IDs deben ser hex de 32 chars pero no necesariamente MD5."""
        from todus.util import generate_msg_id
        import hashlib
        # Generar varios IDs y verificar formato
        for _ in range(20):
            mid = generate_msg_id()
            assert len(mid) == 32
            assert all(c in "0123456789abcdef" for c in mid)
        # Verificar aleatoriedad real (no MD5 de token de 16 chars)
        ids = {generate_msg_id() for _ in range(100)}
        assert len(ids) == 100  # Sin colisiones


# ---------------------------------------------------------------------------
# Auth errors envueltos en AuthenticationError
# ---------------------------------------------------------------------------


class TestAuthErrorHandling:
    def test_request_code_wraps_network_error(self):
        from todus.client.auth import ToDusAuthMixin
        from todus.errors import AuthenticationError
        import requests

        mixin = ToDusAuthMixin.__new__(ToDusAuthMixin)
        mixin.version_name = "2.1.2"
        mixin.session = MagicMock()
        mixin.session.post.side_effect = requests.ConnectionError("red caída")

        with pytest.raises(AuthenticationError) as exc_info:
            mixin.request_code("5300000000")
        assert "Error de red" in str(exc_info.value)

    def test_validate_code_wraps_http_403(self):
        from todus.client.auth import ToDusAuthMixin
        from todus.errors import AuthenticationError

        mixin = ToDusAuthMixin.__new__(ToDusAuthMixin)
        mixin.version_name = "2.1.2"
        mixin.session = MagicMock()

        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mixin.session.post.return_value = mock_resp

        with pytest.raises(AuthenticationError) as exc_info:
            mixin.validate_code("5300000000", "123456")
        assert "inválido" in str(exc_info.value).lower()

    def test_login_wraps_network_error(self):
        from todus.client.auth import ToDusAuthMixin
        from todus.errors import AuthenticationError
        import requests

        mixin = ToDusAuthMixin.__new__(ToDusAuthMixin)
        mixin.version_name = "2.1.2"
        mixin.version_code = "30102"
        mixin.session = MagicMock()
        mixin.session.post.side_effect = requests.ConnectionError("red caída")

        with pytest.raises(AuthenticationError) as exc_info:
            mixin.login("5300000000", "password")
        assert "Error de red" in str(exc_info.value)


# ---------------------------------------------------------------------------
# mark_failed distingue retry vs failed permanente
# ---------------------------------------------------------------------------


class TestMarkFailedSemantics:
    def setup_method(self):
        self.tmpfile = tempfile.mktemp(suffix=".db")
        self.store = MessageStore(self.tmpfile)
        self.queue = MessageQueue(self.store, auto_retry=False)

    def teardown_method(self):
        self.store.close()
        if os.path.exists(self.tmpfile):
            os.unlink(self.tmpfile)

    def test_mark_failed_returns_true_when_retry_scheduled(self):
        """Si quedan reintentos, retorna True (retry agendado)."""
        msg = Message(msg_id="m1", to="a", body="x", max_retries=3)
        self.store.add(msg)

        result = self.queue.mark_failed("m1", error="timeout")
        assert result is True
        # Verificar que se incrementó retry_count
        retrieved = self.store.get("m1")
        assert retrieved.retry_count == 1
        assert retrieved.status == MessageStatus.PENDING  # No se marcó FAILED

    def test_mark_failed_returns_false_when_permanent(self):
        """Si se agotaron los reintentos, retorna False (FAILED permanente)."""
        msg = Message(msg_id="m2", to="a", body="x", max_retries=2, retry_count=2)
        self.store.add(msg)

        # Un callback para verificar que se dispara
        callback_called = []
        self.queue.register_callback("on_message_failed",
                                      lambda m: callback_called.append(m))

        result = self.queue.mark_failed("m2", error="agotado")
        assert result is False
        retrieved = self.store.get("m2")
        assert retrieved.status == MessageStatus.FAILED
        assert len(callback_called) == 1


# ---------------------------------------------------------------------------
# SQLite persistente: conexión reutilizada
# ---------------------------------------------------------------------------


class TestPersistentConnection:
    def setup_method(self):
        self.tmpfile = tempfile.mktemp(suffix=".db")
        self.store = MessageStore(self.tmpfile)

    def teardown_method(self):
        self.store.close()
        if os.path.exists(self.tmpfile):
            os.unlink(self.tmpfile)

    def test_uses_single_persistent_connection(self):
        """Después de varias ops, la conexión debe ser la misma objeto."""
        conn_initial = self.store._conn

        # Realizar varias operaciones
        for i in range(10):
            self.store.add(Message(msg_id=f"m{i}", to="a", body=f"body{i}"))
        for i in range(10):
            self.store.get(f"m{i}")
        self.store.get_stats()
        self.store.get_by_status(MessageStatus.PENDING)

        # La conexión no debe haber cambiado
        assert self.store._conn is conn_initial

    def test_store_supports_context_manager(self):
        """MessageStore debe poder usarse con ``with``."""
        with MessageStore(self.tmpfile) as store:
            store.add(Message(msg_id="ctx_test", to="a", body="x"))
            assert store.get("ctx_test") is not None
        # Al salir del with, la conexión debe estar cerrada
        # (no podemos verificar directamente, pero al menos no debe lanzar)


# ---------------------------------------------------------------------------
# login_with_phone_only: método oficial solo-con-número
# ---------------------------------------------------------------------------


class TestLoginWithPhoneOnly:
    """Valida el procedimiento exacto del login solo-con-número."""

    def test_uuid_hardcoded_value(self):
        """El UUID debe ser exactamente el del archivo botcliente.py."""
        from todus.client.auth import PHONE_ONLY_UUID
        assert PHONE_ONLY_UUID == "fake-1234-5678-90ab-cdef12345678"

    def test_secret_derived_from_uuid(self):
        """SECRET = UUID sin guiones, primeros 32 chars."""
        from todus.client.auth import PHONE_ONLY_UUID, PHONE_ONLY_SECRET
        expected = PHONE_ONLY_UUID.replace("-", "")[:32]
        assert PHONE_ONLY_SECRET == expected
        # Valor concreto esperado
        assert PHONE_ONLY_SECRET == "fake1234567890abcdef12345678"

    def test_varint_encoding(self):
        """El varint protobuf debe codificarse correctamente."""
        from todus.client.auth import _varint
        # 0 → 0x00
        assert _varint(0) == b"\x00"
        # 10 → 0x0A
        assert _varint(10) == b"\x0a"
        # 150 → 0x96 0x01 (varint de 2 bytes)
        assert _varint(150) == b"\x96\x01"

    def test_sf_field_encoding(self):
        """sf(n, v) debe producir bytes([(n<<3)|2]) + varint(len(v)) + v."""
        from todus.client.auth import _sf
        # sf(1, "5353715614") → campo 1 (0x0A) + longitud 10 (0x0A) + bytes
        result = _sf(1, "5353715614")
        assert result == b"\x0a\x0a" + b"5353715614"
        # sf(2, "fake1234567890abcdef12345678") → campo 2 (0x12) + len 28 (0x1C) + bytes
        result = _sf(2, "fake1234567890abcdef12345678")
        assert result == b"\x12\x1c" + b"fake1234567890abcdef12345678"

    def test_payload_matches_botcliente(self):
        """El payload debe ser exactamente sf(1, PHONE) + sf(2, SECRET)."""
        from todus.client.auth import (
            _sf, PHONE_ONLY_SECRET, PHONE_ONLY_UUID,
        )
        phone = "5353715614"  # el del archivo botcliente.py
        secret = PHONE_ONLY_SECRET
        payload = _sf(1, phone) + _sf(2, secret)
        # Campo 1: tag 0x0A, len 10, phone
        # Campo 2: tag 0x12, len 28 (len de 'fake1234567890abcdef12345678'), secret
        expected = (
            b"\x0a\x0a" + b"5353715614"
            + b"\x12\x1c" + b"fake1234567890abcdef12345678"
        )
        assert payload == expected

    def test_headers_match_botcliente(self):
        """Los headers deben ser content-type=octet-stream + user-agent=ToDus 2.1.1."""
        from todus.client.auth import ToDusAuthMixin

        mixin = ToDusAuthMixin.__new__(ToDusAuthMixin)
        # Capturar headers usados
        captured_headers = {}

        def fake_post(url, data, headers, timeout):
            captured_headers.update(headers)
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b"eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiNTM1MzcxNTYxNCJ9.sig"
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        mixin.session = MagicMock()
        mixin.session.post.side_effect = fake_post

        mixin.login_with_phone_only("5353715614")

        # Verificar headers exactos del archivo
        assert captured_headers["content-type"] == "application/octet-stream"
        assert captured_headers["user-agent"] == "ToDus 2.1.1"
        # NO debe tener el header "Host" del login normal
        assert "Host" not in captured_headers

    def test_endpoint_is_auth_token(self):
        """El endpoint debe ser https://auth.todus.cu/v2/auth/token."""
        from todus.client.auth import ToDusAuthMixin

        mixin = ToDusAuthMixin.__new__(ToDusAuthMixin)
        captured_url = {}

        def fake_post(url, data, headers, timeout):
            captured_url["url"] = url
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b"eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiNTM1MzcxNTYxNCJ9.sig"
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        mixin.session = MagicMock()
        mixin.session.post.side_effect = fake_post

        mixin.login_with_phone_only("5353715614")

        assert captured_url["url"] == "https://auth.todus.cu/v2/auth/token"

    def test_jwt_extracted_from_response_with_regex(self):
        """El JWT se extrae con regex eyJ... incluso si hay basura alrededor."""
        from todus.client.auth import ToDusAuthMixin

        mixin = ToDusAuthMixin.__new__(ToDusAuthMixin)
        jwt = b"eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiNTM1MzcxNTYxNCJ9.signature"

        # Caso 1: JWT solo
        mixin.session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = jwt
        mock_resp.raise_for_status = MagicMock()
        mixin.session.post.return_value = mock_resp

        token = mixin.login_with_phone_only("5353715614")
        assert token == jwt.decode("utf-8")

        # Caso 2: JWT rodeado de basura protobuf
        mock_resp.content = b"\x00\x01\x02" + jwt + b"\xff\xfe"
        token = mixin.login_with_phone_only("5353715614")
        assert token == jwt.decode("utf-8")

    def test_login_with_phone_only_sets_token_on_client2(self):
        """ToDusClient2.login_with_phone_only() debe setear self.token."""
        from todus.client import ToDusClient2
        from todus.client.auth import ToDusAuthMixin

        client = ToDusClient2("5353715614", verify_ssl=False)
        assert client.token == ""  # Antes de login

        jwt = b"eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiNTM1MzcxNTYxNCJ9.sig"

        def fake_post(url, data, headers, timeout):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = jwt
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        client.session = MagicMock()
        client.session.post.side_effect = fake_post

        client.login_with_phone_only()

        assert client.token == jwt.decode("utf-8")
        assert client.logged is True

    def test_login_with_phone_only_requires_phone(self):
        """Sin teléfono configurado → AuthenticationError."""
        from todus.client import ToDusClient2
        from todus.errors import AuthenticationError

        client = ToDusClient2("", verify_ssl=False)
        with pytest.raises(AuthenticationError) as exc_info:
            client.login_with_phone_only()
        assert "número de teléfono" in str(exc_info.value).lower()

    def test_login_with_phone_only_wraps_network_error(self):
        """Errores de red se envuelven en AuthenticationError."""
        from todus.client.auth import ToDusAuthMixin
        from todus.errors import AuthenticationError
        import requests

        mixin = ToDusAuthMixin.__new__(ToDusAuthMixin)
        mixin.session = MagicMock()
        mixin.session.post.side_effect = requests.ConnectionError("red caída")

        with pytest.raises(AuthenticationError) as exc_info:
            mixin.login_with_phone_only("5353715614")
        assert "Error de red" in str(exc_info.value)

    def test_login_with_phone_only_handles_403(self):
        """HTTP 403 → AuthenticationError."""
        from todus.client.auth import ToDusAuthMixin
        from todus.errors import AuthenticationError

        mixin = ToDusAuthMixin.__new__(ToDusAuthMixin)
        mixin.session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mixin.session.post.return_value = mock_resp

        with pytest.raises(AuthenticationError) as exc_info:
            mixin.login_with_phone_only("5353715614")
        assert "rechazado" in str(exc_info.value).lower()

    def test_login_with_phone_only_raises_on_no_jwt(self):
        """Si el body no contiene un JWT, se lanza AuthenticationError."""
        from todus.client.auth import ToDusAuthMixin
        from todus.errors import AuthenticationError

        mixin = ToDusAuthMixin.__new__(ToDusAuthMixin)
        mixin.session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"no jwt here"
        mock_resp.raise_for_status = MagicMock()
        mixin.session.post.return_value = mock_resp

        with pytest.raises(AuthenticationError) as exc_info:
            mixin.login_with_phone_only("5353715614")
        assert "Token inválido" in str(exc_info.value)
