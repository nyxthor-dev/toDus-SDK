"""Tests para el soporte de proxy en ToDus."""

import pytest
import socks
from todus.client.base import ToDusClientBase
from todus.client import ToDusClient2


class TestProxySupport:
    def test_parse_socks5_proxy_basic(self):
        client = ToDusClientBase()
        proxy_type, host, port, username, password = client._parse_proxy("socks5://127.0.0.1:1080")
        assert proxy_type == socks.SOCKS5
        assert host == "127.0.0.1"
        assert port == 1080
        assert username is None
        assert password is None

    def test_parse_socks5_proxy_auth(self):
        client = ToDusClientBase()
        proxy_type, host, port, username, password = client._parse_proxy("socks5://user:pass@127.0.0.1:1080")
        assert proxy_type == socks.SOCKS5
        assert host == "127.0.0.1"
        assert port == 1080
        assert username == "user"
        assert password == "pass"

    def test_parse_http_proxy_default_port(self):
        client = ToDusClientBase()
        proxy_type, host, port, username, password = client._parse_proxy("http://proxy.example.com")
        assert proxy_type == socks.HTTP
        assert host == "proxy.example.com"
        assert port == 8080
        assert username is None
        assert password is None

    def test_parse_socks5h_proxy(self):
        client = ToDusClientBase()
        proxy_type, host, port, username, password = client._parse_proxy("socks5h://127.0.0.1")
        assert proxy_type == socks.SOCKS5
        assert host == "127.0.0.1"
        assert port == 1080

    def test_parse_unsupported_scheme(self):
        client = ToDusClientBase()
        with pytest.raises(ValueError):
            client._parse_proxy("ftp://127.0.0.1")

    def test_client_init_with_proxy(self):
        proxy_url = "socks5://127.0.0.1:1080"
        client = ToDusClientBase(proxy=proxy_url)
        assert client.proxy == proxy_url
        assert client.session.proxies == {
            "http": proxy_url,
            "https": proxy_url,
        }

    def test_client2_init_with_proxy(self):
        proxy_url = "http://127.0.0.1:8080"
        client = ToDusClient2(phone_number="5312345678", password="pass", proxy=proxy_url)
        assert client.proxy == proxy_url
        assert client.session.proxies == {
            "http": proxy_url,
            "https": proxy_url,
        }

    def test_upload_file_uses_session(self, monkeypatch):
        client = ToDusClient2(phone_number="5312345678", password="pass", proxy="http://127.0.0.1:8080")
        client._token = "mock_token"

        def mock_reserve(*args, **kwargs):
            return "https://upload.todus.cu/put", "https://download.todus.cu/get"
        monkeypatch.setattr(client, "reserve_upload_url", mock_reserve)

        called_args = []
        class MockResponse:
            def raise_for_status(self):
                pass
        
        def mock_put(url, *args, **kwargs):
            called_args.append(url)
            return MockResponse()
            
        monkeypatch.setattr(client.session, "put", mock_put)

        down_url = client.upload_file(b"test data", file_name="test.txt")
        
        assert down_url == "https://download.todus.cu/get"
        assert len(called_args) == 1
        assert called_args[0] == "https://upload.todus.cu/put"
        assert client.session.proxies == {
            "http": "http://127.0.0.1:8080",
            "https": "http://127.0.0.1:8080",
        }

    def test_upload_avatar_uses_session(self, monkeypatch):
        client = ToDusClient2(phone_number="5312345678", password="pass", proxy="http://127.0.0.1:8080")
        client._token = "mock_token"

        urls = [
            ("https://upload.todus.cu/put_main", "https://download.todus.cu/get_main"),
            ("https://upload.todus.cu/put_thumb", "https://download.todus.cu/get_thumb")
        ]
        url_idx = 0
        def mock_reserve(self_obj, token, size, file_type, file_name=""):
            nonlocal url_idx
            val = urls[url_idx]
            url_idx += 1
            return val
        monkeypatch.setattr("todus.client.file.ToDusFileMixin.reserve_upload_url", mock_reserve)

        called_urls = []
        class MockResponse:
            def raise_for_status(self):
                pass
        
        def mock_put(url, *args, **kwargs):
            called_urls.append(url)
            return MockResponse()
            
        monkeypatch.setattr(client.session, "put", mock_put)

        profile_url, thumb_url = client.upload_avatar(b"main_image", b"thumb_image")
        
        assert profile_url == "https://download.todus.cu/get_main"
        assert thumb_url == "https://download.todus.cu/get_thumb"
        assert len(called_urls) == 2
        assert called_urls[0] == "https://upload.todus.cu/put_main"
        assert called_urls[1] == "https://upload.todus.cu/put_thumb"
        assert client.session.proxies == {
            "http": "http://127.0.0.1:8080",
            "https": "http://127.0.0.1:8080",
        }

