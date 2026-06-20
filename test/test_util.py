"""Tests para todus.util."""

import pytest
from todus.util import (
    normalize_phone,
    build_jid,
    escape_xml,
    unescape_xml,
    format_size,
    generate_token,
    jwt_decode_payload,
    timestamp_ms,
    parse_jid,
    get_image_dimensions,
    sanitize_filename,
)


class TestNormalizePhone:
    def test_ten_digits(self):
        assert normalize_phone("5312345678") == "5312345678"

    def test_eight_digits(self):
        assert normalize_phone("12345678") == "5312345678"

    def test_with_plus(self):
        assert normalize_phone("+5312345678") == "5312345678"

    def test_with_spaces(self):
        assert normalize_phone("53 1234 5678") == "5312345678"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            normalize_phone("123")

    def test_invalid_short(self):
        with pytest.raises(ValueError):
            normalize_phone("abc")


class TestBuildJid:
    def test_basic(self):
        assert build_jid("5312345678") == "5312345678@im.todus.cu"

    def test_with_prefix(self):
        assert build_jid("12345678") == "5312345678@im.todus.cu"


class TestParseJid:
    def test_basic(self):
        phone, resource = parse_jid("5312345678@im.todus.cu")
        assert phone == "5312345678"
        assert resource == ""

    def test_with_resource(self):
        phone, resource = parse_jid("5312345678@im.todus.cu/android")
        assert phone == "5312345678"
        assert resource == "android"


class TestEscapeXml:
    def test_ampersand(self):
        assert escape_xml("a&b") == "a&amp;b"

    def test_lt_gt(self):
        assert escape_xml("<tag>") == "&lt;tag&gt;"

    def test_apostrophe(self):
        assert escape_xml("it's") == "it&apos;s"

    def test_no_change(self):
        assert escape_xml("hello world") == "hello world"

    def test_roundtrip(self):
        original = "a<b&c'd"
        assert unescape_xml(escape_xml(original)) == original


class TestUnescapeXml:
    def test_entities(self):
        assert unescape_xml("&lt;tag&gt;") == "<tag>"

    def test_ampersand(self):
        assert unescape_xml("a&amp;b") == "a&b"

    def test_apostrophe(self):
        assert unescape_xml("it&apos;s") == "it's"


class TestFormatSize:
    def test_bytes(self):
        assert format_size(512) == "512.0 B"

    def test_kilobytes(self):
        assert format_size(1024) == "1.0 KB"

    def test_megabytes(self):
        assert format_size(1024 * 1024) == "1.0 MB"

    def test_gigabytes(self):
        assert format_size(1024 ** 3) == "1.0 GB"

    def test_zero(self):
        assert format_size(0) == "0.0 B"


class TestGenerateToken:
    def test_default_length(self):
        token = generate_token()
        assert len(token) == 8
        assert token.isalnum()

    def test_custom_length(self):
        token = generate_token(16)
        assert len(token) == 16

    def test_uniqueness(self):
        tokens = {generate_token() for _ in range(100)}
        assert len(tokens) == 100  # probabilísticamente siempre pasa


class TestJwtDecodePayload:
    def test_empty_token(self):
        assert jwt_decode_payload("") == {}

    def test_no_dots(self):
        assert jwt_decode_payload("nodots") == {}

    def test_one_dot(self):
        # Solo header, sin payload
        assert jwt_decode_payload("header.") == {}


class TestTimestampMs:
    def test_is_int(self):
        ts = timestamp_ms()
        assert isinstance(ts, int)

    def test_reasonable_value(self):
        ts = timestamp_ms()
        # Debe ser un timestamp en milisegundos razonable (post-2020)
        assert ts > 1_577_836_800_000


class TestSanitizeFilename:
    def test_basic(self):
        result = sanitize_filename("photo.jpg")
        assert result == "photo.jpg"

    def test_spaces(self):
        result = sanitize_filename("my photo.jpg")
        assert result == "my_photo.jpg"

    def test_special_chars(self):
        result = sanitize_filename('file<name>.txt')
        assert result == "file_name_.txt"

    def test_empty_with_type(self):
        from todus.types import FileType
        result = sanitize_filename("", FileType.PICTURE)
        assert result == "photo.jpg"

    def test_no_extension_with_type(self):
        from todus.types import FileType
        result = sanitize_filename("myfile", FileType.VIDEO)
        assert result == "myfile.mp4"

    def test_long_name_truncated(self):
        long_name = "a" * 60 + ".txt"
        result = sanitize_filename(long_name)
        assert len(result) <= 54  # 47 + "..." + ".txt"

    def test_path_basename(self):
        result = sanitize_filename("/some/path/to/file.pdf")
        assert result == "file.pdf"
