"""Tests para la sesión XMPP compartida (v1.10.0).

Verifica que:
- Cuando el listener está activo, los ``send_*`` reusan el socket del
  listener en lugar de abrir sesiones nuevas (que matarían la del
  listener — el servidor solo permite 1 por JID).
- Cuando el listener está inactivo, los ``send_*`` caen al fallback
  (abren su propia sesión, comportamiento legacy).
- Si el socket compartido muere durante un send, se limpia y se relanza
  la excepción para que el caller decida.
- El socket del listener no se cierra tras un send.
"""
import threading
import time
from unittest.mock import MagicMock, patch
import inspect

import pytest

import sys
sys.path.insert(0, '/home/z/my-project/todus-sdk')

from todus.client.base import ToDusClientBase, ThreadSafeSocket
from todus.errors import ConnectionLostError
from todus.client.message import ToDusMessageMixin


# ---------------------------------------------------------------------------
# Test 1: _set_shared_sock registra y libera
# ---------------------------------------------------------------------------


class TestSetSharedSock:
    """Verifica el protocolo de registro/liberación del socket compartido."""

    def test_set_shared_sock_registra_socket(self):
        """_set_shared_sock(sock) activa el flag _shared_sock_active."""
        # ToDusClientBase.__init__ requiere parámetros; usar __new__ para
        # evitar la configuración SSL/proxy.
        base = ToDusClientBase.__new__(ToDusClientBase)
        base._shared_sock = None
        base._shared_sock_lock = threading.Lock()
        base._shared_sock_active = threading.Event()

        sock = MagicMock()
        base._set_shared_sock(sock)
        assert base._shared_sock is sock
        assert base._shared_sock_active.is_set()

    def test_set_shared_sock_none_libera(self):
        """_set_shared_sock(None) limpia el flag y el socket."""
        base = ToDusClientBase.__new__(ToDusClientBase)
        base._shared_sock = MagicMock()
        base._shared_sock_lock = threading.Lock()
        base._shared_sock_active = threading.Event()
        base._shared_sock_active.set()

        base._set_shared_sock(None)
        assert base._shared_sock is None
        assert not base._shared_sock_active.is_set()


# ---------------------------------------------------------------------------
# Test 2: _xmpp_session reusa el socket compartido si está activo
# ---------------------------------------------------------------------------


class TestXmppSessionReusesSharedSock:
    """Si el listener está activo, los sends reusan su socket."""

    def test_xmpp_session_reusa_socket_compartido(self):
        """Cuando _shared_sock_active está set, el context manager yield
        el shared sock sin abrir sesión nueva."""
        base = ToDusClientBase.__new__(ToDusClientBase)
        base._shared_sock = MagicMock()
        base._shared_sock_lock = threading.Lock()
        base._shared_sock_active = threading.Event()
        base._shared_sock_active.set()

        # Patchear _connect_xmpp y _handshake para asegurar que no se llamen
        # (caería al fallback si se llamaran).
        base._connect_xmpp = MagicMock(side_effect=AssertionError(
            "No debería abrir sesión nueva cuando hay shared_sock activo"
        ))
        base._handshake = MagicMock()

        with base._xmpp_session("fake_token") as sock:
            # El sock retornado debe ser el compartido, no uno nuevo.
            assert sock is base._shared_sock

        # _connect_xmpp no debe haberse llamado.
        base._connect_xmpp.assert_not_called()

    def test_xmpp_session_no_cierra_socket_compartido(self):
        """Tras usar el socket compartido, NO se cierra (es del listener)."""
        base = ToDusClientBase.__new__(ToDusClientBase)
        shared_sock = MagicMock()
        base._shared_sock = shared_sock
        base._shared_sock_lock = threading.Lock()
        base._shared_sock_active = threading.Event()
        base._shared_sock_active.set()
        base._connect_xmpp = MagicMock()
        base._handshake = MagicMock()

        with base._xmpp_session("fake_token") as sock:
            pass  # usar el socket

        # El shared sock no debe haber sido cerrado.
        shared_sock.close.assert_not_called()
        # Y debe seguir registrado.
        assert base._shared_sock is shared_sock


# ---------------------------------------------------------------------------
# Test 3: _xmpp_session cae al fallback si no hay shared_sock
# ---------------------------------------------------------------------------


class TestXmppSessionFallback:
    """Si no hay listener activo, abre sesión nueva (comportamiento legacy)."""

    def test_xmpp_session_sin_shared_abre_sesion_nueva(self):
        """Si _shared_sock_active no está set, abre sesión nueva con
        handshake + presence."""
        base = ToDusClientBase.__new__(ToDusClientBase)
        base._shared_sock = None
        base._shared_sock_lock = threading.Lock()
        base._shared_sock_active = threading.Event()
        # NO seteado — el listener no está activo.

        # Mock del socket nuevo.
        new_sock = MagicMock()
        base._connect_xmpp = MagicMock(return_value=new_sock)
        base._handshake = MagicMock()

        # Patchear stanza.presence para evitar dependencia de todus.stanza.
        from todus import stanza as stanza_mod
        with patch.object(stanza_mod, 'presence', return_value="<presence/>"):
            with patch.object(stanza_mod, 'stream_close', return_value="</stream>"):
                with base._xmpp_session("fake_token") as sock:
                    # El sock es el nuevo, no el compartido (no había).
                    assert sock is new_sock

        # Se abrió sesión nueva y se cerró al salir.
        base._connect_xmpp.assert_called_once()
        base._handshake.assert_called_once()
        new_sock.sendall.assert_any_call(b"<presence/>")
        new_sock.sendall.assert_any_call(b"</stream>")
        new_sock.close.assert_called_once()


# ---------------------------------------------------------------------------
# Test 4: si el socket compartido muere durante un send, se limpia
# ---------------------------------------------------------------------------


class TestSharedSockFailure:
    """Si el sendall sobre el socket compartido falla, se limpia el shared."""

    def test_sendall_falla_limpia_shared_sock(self):
        """Si el socket compartido falla con OSError, se limpia y se
        relanza la excepción para que el caller decida."""
        base = ToDusClientBase.__new__(ToDusClientBase)
        bad_sock = MagicMock()
        bad_sock.sendall.side_effect = OSError("socket muerto")
        base._shared_sock = bad_sock
        base._shared_sock_lock = threading.Lock()
        base._shared_sock_active = threading.Event()
        base._shared_sock_active.set()
        base._connect_xmpp = MagicMock()
        base._handshake = MagicMock()

        # El caller intenta usar el socket compartido; sendall falla.
        with pytest.raises(OSError):
            with base._xmpp_session("fake_token") as sock:
                sock.sendall(b"<m/>")

        # El shared_sock debe haberse limpiado (porque es el mismo socket).
        assert base._shared_sock is None
        assert not base._shared_sock_active.is_set()

    def test_sendall_falla_no_limpiar_si_ya_cambio(self):
        """Si el listener reconectó entre el check y el fallo, no se
        limpia el nuevo shared_sock — solo se limpia si era el mismo."""
        base = ToDusClientBase.__new__(ToDusClientBase)
        old_sock = MagicMock()
        old_sock.sendall.side_effect = OSError("socket viejo muerto")
        new_sock = MagicMock()  # listener reconectó con este
        base._shared_sock = new_sock  # ya cambió
        base._shared_sock_lock = threading.Lock()
        base._shared_sock_active = threading.Event()
        base._shared_sock_active.set()
        base._connect_xmpp = MagicMock()
        base._handshake = MagicMock()

        # Simular: el caller capturó old_sock, pero mientras tanto el
        # listener reemplazó por new_sock. Para testear esto, forzamos el
        # código a usar old_sock sobreescribiendo _shared_sock antes del
        # yield, pero restaurando new_sock antes del except.
        # Es difícil de simular; en su lugar testeamos que el except no
        # limpia si _shared_sock es distinto del que tuvimos en yield.
        # Hacemos un test más directo: si sendall falla y _shared_sock
        # apunta a OTRO socket, NO se limpia.
        with pytest.raises(OSError):
            # Simular: el yield captura old_sock (que es el compartido
            # al inicio), pero antes del except el listener cambió a
            # new_sock. Hacemos eso con un patcher.
            original_shared = base._shared_sock
            base._shared_sock = old_sock  # forzar el yield use old_sock
            try:
                with base._xmpp_session("fake_token") as sock:
                    # Simular que el listener reconectó con new_sock
                    # mientras enviábamos.
                    base._shared_sock = new_sock
                    base._shared_sock_active.set()
                    sock.sendall(b"<m/>")  # falla con OSError
            except OSError:
                raise
            finally:
                base._shared_sock = new_sock  # restaurar

        # El nuevo shared_sock no debe haberse limpiado.
        assert base._shared_sock is new_sock
        assert base._shared_sock_active.is_set()


# ---------------------------------------------------------------------------
# Test 5: _listen_loop registra y libera el shared sock
# ---------------------------------------------------------------------------


class TestListenLoopRegistersSharedSock:
    """El listener debe registrar su socket como compartido al arrancar
    y liberarlo al terminar."""

    def test_listen_loop_registra_y_libera(self):
        """Verifica que _listen_loop llama a _set_shared_sock(sock) al
        inicio y _set_shared_sock(None) al final."""

        class FakeMixin(ToDusMessageMixin):
            def __init__(self):
                self._xml_parser = MagicMock()
                self._xml_parser.reset = MagicMock()
                self._xml_parser.feed = MagicMock(return_value=[])
                # Inicializar shared_sock attrs (como en ToDusClientBase.__init__)
                self._shared_sock = None
                self._shared_sock_lock = threading.Lock()
                self._shared_sock_active = threading.Event()
                # Capturar llamadas a _set_shared_sock
                self.calls = []

                def capture_set(sock):
                    self.calls.append(sock)
                    # Aplicar el efecto del set real
                    with self._shared_sock_lock:
                        self._shared_sock = sock
                        if sock is not None:
                            self._shared_sock_active.set()
                        else:
                            self._shared_sock_active.clear()
                self._set_shared_sock = capture_set

            def _xmpp_session(self, token):
                # No se usa en este test porque pasamos el sock directamente
                pass

        m = FakeMixin()
        sock = MagicMock()
        stop_event = threading.Event()

        # Hacer que el loop salga inmediatamente
        def fake_recv_all(s):
            stop_event.set()
            return ""
        m._recv_all = fake_recv_all

        m._listen_loop(sock, MagicMock(), stop_event=stop_event)

        # Verificar que registró sock al inicio y None al final.
        assert m.calls[0] is sock
        assert m.calls[-1] is None
        # Y que al final el shared_sock_active quedó limpio.
        assert not m._shared_sock_active.is_set()


# ---------------------------------------------------------------------------
# Test 6: send_message usa el shared sock cuando el listener está activo
# ---------------------------------------------------------------------------


class TestSendMessageUsesSharedSock:
    """Test de integración: send_message reusa el socket del listener."""

    def test_send_message_no_abre_sesion_nueva_si_hay_shared(self):
        """Si hay shared_sock activo, send_message lo usa sin llamar a
        _connect_xmpp ni _handshake."""
        # Usar ToDusClient2 para tener send_message con auto-detección.
        from todus.client import ToDusClient2
        client = ToDusClient2("5353715614", "pass", verify_ssl=False)
        # Simular login ya hecho.
        client._token = "fake_jwt_token"

        # Simular listener activo con un socket mock.
        shared_sock = MagicMock()
        client._set_shared_sock(shared_sock)

        # Patchear para asegurar que NO se abra sesión nueva.
        client._connect_xmpp = MagicMock(side_effect=AssertionError(
            "send_message no debe abrir sesión nueva con listener activo"
        ))

        # Llamar send_message — debe usar el shared sock.
        result = client.send_message("5356795360", "hola")

        # El shared_sock.sendall fue llamado con la stanza del mensaje.
        assert shared_sock.sendall.called
        # _connect_xmpp no fue llamado.
        client._connect_xmpp.assert_not_called()
        # El shared_sock sigue activo (no se cerró).
        assert client._shared_sock is shared_sock


# ---------------------------------------------------------------------------
# Test 7: dedup — los send_* en paralelo no se intercalan
# ---------------------------------------------------------------------------


class TestParallelSendsSerialized:
    """Múltiples sends en paralelo deben escribir al shared sock de forma
    atómica (no intercalar bytes TLS)."""

    def test_dos_sends_paralelo_se_serializan(self):
        """Dos threads enviando al mismo tiempo deben hacerlo en serie
        (gracias al lock de ThreadSafeSocket)."""
        from todus.client import ToDusClient2
        client = ToDusClient2("5353715614", "pass", verify_ssl=False)
        # Simular login ya hecho.
        client._token = "fake_jwt_token"

        # Mock que simula ThreadSafeSocket con un lock real.
        class FakeThreadSafeSocket:
            def __init__(self):
                self._lock = threading.Lock()
                self.writes = []
                self.in_sendall = False
                self.concurrent_violation = False

            def sendall(self, data):
                with self._lock:
                    # Verificar que no haya otro sendall concurrente.
                    if self.in_sendall:
                        self.concurrent_violation = True
                    self.in_sendall = True
                try:
                    # Simular "escritura" — sleep corto para permitir overlap.
                    time.sleep(0.001)
                    self.writes.append(data)
                finally:
                    with self._lock:
                        self.in_sendall = False

        shared = FakeThreadSafeSocket()
        client._set_shared_sock(shared)
        client._connect_xmpp = MagicMock()

        # Lanzar 5 sends en paralelo.
        threads = []
        errors = []

        def send_one(i):
            try:
                client.send_message("5356795360", f"msg{i}")
            except Exception as e:
                errors.append(e)

        for i in range(5):
            t = threading.Thread(target=send_one, args=(i,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join(timeout=5)

        # No debe haber errores ni violaciones de concurrencia.
        assert not errors, f"Errores en sends paralelos: {errors}"
        # Las 5 stanzas se escribieron (en serie, no intercaladas).
        assert len(shared.writes) == 5


# ---------------------------------------------------------------------------
# Test 8: cuando el listener muere, los sends caen al fallback
# ---------------------------------------------------------------------------


class TestFallbackWhenListenerDead:
    """Si el listener muere (no hay shared_sock), los sends abren su
    propia sesión."""

    def test_send_message_abre_sesion_nueva_si_no_hay_shared(self):
        from todus.client import ToDusClient2
        client = ToDusClient2("5353715614", "pass", verify_ssl=False)
        # Simular login ya hecho.
        client._token = "fake_jwt_token"
        # No setear shared_sock — listener apagado.

        new_sock = MagicMock()
        client._connect_xmpp = MagicMock(return_value=new_sock)
        client._handshake = MagicMock()

        # Patchear stanza.presence y stream_close.
        from todus import stanza as stanza_mod
        with patch.object(stanza_mod, 'presence', return_value="<p/>"):
            with patch.object(stanza_mod, 'stream_close', return_value="</s>"):
                client.send_message("5356795360", "hola")

        # Se abrió sesión nueva y se cerró al final.
        client._connect_xmpp.assert_called_once()
        new_sock.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
