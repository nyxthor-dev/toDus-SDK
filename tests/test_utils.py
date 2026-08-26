import pytest
from todus.util import (
    normalize_phone, build_jid, parse_jid, escape_xml, unescape_xml,
    jwt_decode_payload, timestamp_ms, format_size, generate_token,
    generate_blurhash, sanitize_filename,
)
from todus.types import FileType


class TestNormalizePhone:
    def test_8_digits_adds_53(self):
        assert normalize_phone("54123456") == "5354123456"

    def test_full_10_digits(self):
        assert normalize_phone("5354123456") == "5354123456"

    def test_with_plus_prefix(self):
        assert normalize_phone("+5354123456") == "5354123456"

    def test_with_spaces(self):
        assert normalize_phone("53 5412 3456") == "5354123456"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            normalize_phone("123")


class TestBuildJid:
    def test_basic(self):
        assert build_jid("54123456") == "5354123456@im.todus.cu"

    def test_full_number(self):
        assert build_jid("5354123456") == "5354123456@im.todus.cu"


class TestParseJid:
    def test_simple(self):
        phone, resource = parse_jid("5354123456@im.todus.cu")
        assert phone == "5354123456"
        assert resource == ""

    def test_with_resource(self):
        phone, resource = parse_jid("5354123456@im.todus.cu/todusandroid")
        assert phone == "5354123456"
        assert resource == "todusandroid"


class TestEscapeUnescapeXml:
    def test_escape(self):
        assert escape_xml("a<b&c>d'e") == "a&lt;b&amp;c&gt;d&apos;e"

    def test_unescape(self):
        assert unescape_xml("a&lt;b&amp;c&gt;d&apos;e") == "a<b&c>d'e"

    def test_roundtrip(self):
        original = "<hola> & 'mundo'"
        assert unescape_xml(escape_xml(original)) == original


class TestJwtDecodePayload:
    def test_valid_jwt(self):
        token = "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiNTMxMjM0NTY3OCJ9.signature"
        result = jwt_decode_payload(token)
        assert result["user"] == "5312345678"

    def test_invalid_jwt(self):
        assert jwt_decode_payload("not.a.jwt") == {}

    def test_empty_string(self):
        assert jwt_decode_payload("") == {}


class TestTimestampMs:
    def test_returns_int(self):
        assert isinstance(timestamp_ms(), int)

    def test_positive(self):
        assert timestamp_ms() > 0


class TestFormatSize:
    def test_bytes(self):
        assert "B" in format_size(500)

    def test_kilobytes(self):
        assert "KB" in format_size(2048)

    def test_megabytes(self):
        assert "MB" in format_size(5 * 1024 * 1024)

    def test_gigabytes(self):
        assert "GB" in format_size(2 * 1024 * 1024 * 1024)

    def test_terabytes(self):
        assert "TB" in format_size(5000 * 1024 * 1024 * 1024)


class TestGenerateToken:
    def test_length(self):
        assert len(generate_token(16)) == 16

    def test_default_length(self):
        assert len(generate_token()) == 8

    def test_alphanumeric(self):
        token = generate_token(100)
        assert token.isalnum()

    def test_uniqueness(self):
        tokens = {generate_token(32) for _ in range(100)}
        assert len(tokens) == 100


class TestGenerateBlurhash:
    def test_returns_string(self):
        result = generate_blurhash(800, 600)
        assert isinstance(result, str)

    def test_deterministic(self):
        assert generate_blurhash(800, 600) == generate_blurhash(800, 600)

    def test_different_dims_different_hash(self):
        assert generate_blurhash(100, 100) != generate_blurhash(200, 200)


class TestSanitizeFilename:
    def test_basic(self):
        assert sanitize_filename("foto.jpg", FileType.PICTURE) == "foto.jpg"

    def test_empty_uses_default(self):
        result = sanitize_filename("", FileType.PICTURE)
        assert result == "photo.jpg"

    def test_special_chars_cleaned(self):
        result = sanitize_filename("mi/foto*?.jpg", FileType.PICTURE)
        assert "/" not in result
        assert "*" not in result
        assert "?" not in result

    def test_no_extension_adds_default(self):
        result = sanitize_filename("video_sin_ext", FileType.VIDEO)
        assert result.endswith(".mp4")

    def test_long_name_truncated(self):
        long_name = "a" * 100 + ".jpg"
        result = sanitize_filename(long_name, FileType.PICTURE)
        assert len(result) < 60
