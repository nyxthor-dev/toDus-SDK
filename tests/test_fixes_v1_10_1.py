"""Tests para los bugs detectados en la suite de integración v1.10.0.

Bug #16: Falta wrapper ToDusClient2.send_delivery_receipt(to_phone, msg_id)
Bug #17: LSP violation en ToDusClient2.get_real_download_url
         (no acepta token como primer arg; la base la llama con (token, url))
Bug #17b: Igual LSP en download_file y download_file_to_folder
"""
import inspect
import pytest

import sys
sys.path.insert(0, '/home/z/my-project/todus-sdk')

from todus.client import ToDusClient2


# ---------------------------------------------------------------------------
# Bug #16: ToDusClient2.send_delivery_receipt
# ---------------------------------------------------------------------------


class TestSendDeliveryReceiptWrapper:
    """En v1.10.0, send_read_receipt tenía wrapper pero
    send_delivery_receipt no. El caller tenía que usar la firma del mixin
    base (token, to_jid, msg_id) que no encaja con la API pública de
    ToDusClient2."""

    def test_send_delivery_receipt_existe_en_ToDusClient2(self):
        """El método debe existir en ToDusClient2 con la firma
        (to_phone, msg_id) — igual que send_read_receipt."""
        assert hasattr(ToDusClient2, 'send_delivery_receipt'), (
            "ToDusClient2 debe tener send_delivery_receipt"
        )

    def test_send_delivery_receipt_firma_to_phone_msg_id(self):
        """La firma debe ser (to_phone, msg_id) — no (token, to_jid, msg_id)."""
        sig = inspect.signature(ToDusClient2.send_delivery_receipt)
        params = list(sig.parameters.keys())
        # Excluir 'self'
        params = [p for p in params if p != 'self']
        assert params == ['to_phone', 'msg_id'], (
            f"Firma esperada (to_phone, msg_id), obtuvo {params}"
        )

    def test_send_delivery_receipt_paralelo_a_send_read_receipt(self):
        """La firma debe ser idéntica a send_read_receipt (que ya funcionaba)."""
        sig_d = inspect.signature(ToDusClient2.send_delivery_receipt)
        sig_r = inspect.signature(ToDusClient2.send_read_receipt)
        # Solo deben diferir en el nombre del método, no en params.
        assert sig_d.parameters == sig_r.parameters, (
            f"send_delivery_receipt params {sig_d.parameters} != "
            f"send_read_receipt params {sig_r.parameters}"
        )


# ---------------------------------------------------------------------------
# Bug #17: LSP en get_real_download_url
# ---------------------------------------------------------------------------


class TestGetRealDownloadUrlLSP:
    """ToDusClient2.get_real_download_url no aceptaba `token` como
    primer arg, pero la base (ToDusFileMixin) internamente la llama con
    (token, url) — TypeError en runtime."""

    def test_get_real_download_url_acepta_token_opcional(self):
        """Verifica que el método acepta tanto (url) como (token, url).
        En v1.10.0 solo aceptaba (url) — TypeError cuando la base llamaba
        con (token, url)."""
        client = ToDusClient2("5353448202", "", verify_ssl=False)
        client._token = "fake_token"
        # Patchear super().get_real_download_url para no hacer la llamada real.
        from todus.client.file import ToDusFileMixin
        original = ToDusFileMixin.get_real_download_url
        ToDusFileMixin.get_real_download_url = lambda self_obj, t, u: "OK"
        try:
            # 1) Llamada estilo ToDusClient2: (url)
            r = client.get_real_download_url("https://todus.cu/abc")
            assert r == "OK"
            # 2) Llamada estilo base: (token, url)
            r = client.get_real_download_url("fake_token", "https://todus.cu/abc")
            assert r == "OK"
            # 3) Llamada con kwargs
            r = client.get_real_download_url(url="https://todus.cu/abc",
                                            token="fake_token")
            assert r == "OK"
        finally:
            ToDusFileMixin.get_real_download_url = original

    def test_get_real_download_url_llamada_interna_funciona(self):
        """Simula la llamada interna que hace download_file_to_folder
        (de la base): self.get_real_download_url(token, url).
        En v1.10.0, eso rompía con TypeError."""
        client = ToDusClient2("5353448202", "", verify_ssl=False)
        client._token = "fake_token"  # simular login

        # Patchear super().get_real_download_url para capturar los args.
        # El método de la base es un-bound function: (self, token, url).
        from todus.client.file import ToDusFileMixin
        captured_args = []

        def fake_get_real(self_obj, token, url):
            captured_args.append((self_obj, token, url))
            return "https://resolved.url/fake"

        # Re-bind a la clase base — se accede como método de instancia.
        original = ToDusFileMixin.get_real_download_url
        ToDusFileMixin.get_real_download_url = fake_get_real
        try:
            # Llamar como lo haría la base: self.get_real_download_url(token, url)
            result = client.get_real_download_url("fake_token", "https://todus.cu/abc")
            assert result == "https://resolved.url/fake"
            assert len(captured_args) == 1
            # Args: (self_obj, token, url)
            self_obj, token, url = captured_args[0]
            assert token == "fake_token"
            assert url == "https://todus.cu/abc"
        finally:
            ToDusFileMixin.get_real_download_url = original


# ---------------------------------------------------------------------------
# Bug #17b: LSP en download_file y download_file_to_folder
# ---------------------------------------------------------------------------


class TestDownloadMethodsLSP:
    """download_file y download_file_to_folder también deben aceptar
    token opcional para LSP con la base."""

    def test_download_file_acepta_token(self):
        sig = inspect.signature(ToDusClient2.download_file)
        assert 'token' in sig.parameters

    def test_download_file_to_folder_acepta_token(self):
        sig = inspect.signature(ToDusClient2.download_file_to_folder)
        assert 'token' in sig.parameters

    def test_download_file_to_folder_llamada_interna_funciona(self):
        """Simula la llamada interna: la base llama
        self.get_real_download_url(token, url). En v1.10.0 rompía con
        TypeError: takes 2 positional arguments but 3 were given."""
        client = ToDusClient2("5353448202", "", verify_ssl=False)
        client._token = "fake_token"

        # Patchear super().download_file_to_folder para capturar
        # y NO hacer la descarga real.
        from todus.client.file import ToDusFileMixin
        captured = []

        def fake_dl(self_obj, token, url, folder, filename=""):
            captured.append((token, url, folder, filename))
            return (1024, "/tmp/fake.png")

        original = ToDusFileMixin.download_file_to_folder
        ToDusFileMixin.download_file_to_folder = fake_dl
        try:
            result = client.download_file_to_folder(
                "https://todus.cu/x", "/tmp", "test.png"
            )
            assert result == (1024, "/tmp/fake.png")
            assert len(captured) == 1
            # Verificar que el token llegó bien a la base.
            assert captured[0][0] == "fake_token"
            assert captured[0][1] == "https://todus.cu/x"
            assert captured[0][2] == "/tmp"
            assert captured[0][3] == "test.png"
        finally:
            ToDusFileMixin.download_file_to_folder = original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
