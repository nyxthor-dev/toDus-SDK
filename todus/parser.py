"""Parser de stanzas XMPP/ToDus."""

import re
from . import util
from .errors import ParseError


def _attr(stanza: str, name: str) -> str:
    """Extrae atributo de stanza. Soporta comillas simples y dobles."""
    for quote in ("'", '"'):
        pattern = rf"{name}={quote}([^{quote}]+){quote}"
        match = re.search(pattern, stanza)
        if match:
            return match.group(1)
    return ""


def parse_todus_message(stanza: str) -> dict:
    """Parsea stanza <m> de ToDus."""
    result = {
        "from": _attr(stanza, "f"),
        "to": _attr(stanza, "o"),
        "id": _attr(stanza, "i"),
        "type": _attr(stanza, "t"),
        "body": "",
        "url": "",
        "file_name": "",
        "file_size": 0,
        "file_id": "",
        "file_hash": "",
        "message_file_id": "",
        "has_key": "<k" in stanza,
        "offline_ts": "",
        "edited": "",
        "deleted": "",
        "raw": stanza,
    }

    # Body
    match = re.search(r"<b>(.*?)</b>", stanza, re.DOTALL)
    if match:
        result["body"] = util.unescape_xml(match.group(1)).strip()

    # URL de archivo (formato antiguo <u>)
    match = re.search(r"<u>(.*?)</u>", stanza, re.DOTALL)
    if match:
        result["url"] = util.unescape_xml(match.group(1)).strip()

    # Archivo adjunto (formato nuevo <file>) — robusto ante orden de atributos
    file_match = re.search(r"<file\b[^>]*>", stanza)
    if file_match:
        file_tag = file_match.group(0)
        result["file_id"] = _attr(file_tag, "i")
        result["message_file_id"] = _attr(file_tag, "mi")
        result["file_name"] = util.unescape_xml(_attr(file_tag, "n"))
        result["url"] = _attr(file_tag, "url")
        try:
            result["file_size"] = int(_attr(file_tag, "s"))
        except ValueError:
            result["file_size"] = 0
        result["file_hash"] = _attr(file_tag, "h")

    # Offline timestamp
    match = re.search(r"<todus_offline\s+ts='([^']+)'", stanza)
    if not match:
        match = re.search(r'<todus_offline\s+ts="([^"]+)"', stanza)
    if match:
        result["offline_ts"] = match.group(1)

    # Edited
    match = re.search(r"<edited\s+xmlns='edited:n'\s+i='([^']+)'", stanza)
    if not match:
        match = re.search(r'<edited\s+xmlns="edited:n"\s+i="([^"]+)"', stanza)
    if match:
        result["edited"] = match.group(1)

    # Deleted
    match = re.search(r"<deleted\s+xmlns='deleted:n'\s+i='([^']+)'", stanza)
    if not match:
        match = re.search(r'<deleted\s+xmlns="deleted:n"\s+i="([^"]+)"', stanza)
    if match:
        result["deleted"] = match.group(1)

    return result


def parse_presence(stanza: str) -> dict:
    """Parsea stanza <p> de presencia."""
    result = {
        "from": _attr(stanza, "f"),
        "to": _attr(stanza, "o"),
        "id": _attr(stanza, "i"),
        "status": "",
        "show": "",
        "priority": "",
        "raw": stanza,
    }

    match = re.search(r"<status>(.*?)</status>", stanza, re.DOTALL)
    if match:
        result["status"] = util.unescape_xml(match.group(1))

    match = re.search(r"<show>(.*?)</show>", stanza, re.DOTALL)
    if match:
        result["show"] = match.group(1)

    match = re.search(r"<priority>(\d+)</priority>", stanza)
    if match:
        result["priority"] = int(match.group(1))

    return result


def parse_iq(stanza: str) -> dict:
    """Parsea stanza IQ."""
    result = {
        "from": _attr(stanza, "f"),
        "to": _attr(stanza, "o"),
        "id": _attr(stanza, "i"),
        "type": _attr(stanza, "t"),
        "error": "",
        "raw": stanza,
    }

    if "<error" in stanza:
        match = re.search(r"<error[^>]*>(.*?)</error>", stanza, re.DOTALL)
        if match:
            result["error"] = match.group(1)

    # Upload URLs — robusto ante orden de atributos
    if _attr(stanza, "put"):
        result["upload_url"] = _attr(stanza, "put").replace("amp;", "")
        result["download_url"] = _attr(stanza, "get").replace("amp;", "")

    # Download URL
    if _attr(stanza, "du"):
        result["real_url"] = _attr(stanza, "du").replace("amp;", "")

    return result


def extract_all_stanzas(xml: str) -> dict:
    """Extrae todas las stanzas de un chunk XML."""
    return {
        "messages": re.findall(r"<m\b.*?</m>", xml, re.DOTALL),
        "presences": re.findall(r"<p\b.*?</p>", xml, re.DOTALL),
        "iqs": re.findall(r"<iq\b.*?</iq>", xml, re.DOTALL),
        "streams": re.findall(r"<\?xml[^?]*\?><stream:stream[^>]*/?>", xml),
        "unknown": [],
    }


class IncrementalParser:
    """Parser incremental que maneja stanzas fragmentadas por TCP."""

    def __init__(self):
        self._buffer = ""

    def feed(self, chunk: str) -> list[dict]:
        """Alimenta con nuevo chunk y retorna stanzas completas parseadas."""
        if not chunk:
            return []

        self._buffer += chunk
        stanzas = []
        seen_raw = set()

        patterns = [
            (r"<m\b.*?</m>", parse_todus_message),
            (r"<p\b.*?</p>", parse_presence),
            (r"<iq\b.*?</iq>", parse_iq),
        ]

        for pattern, parser_fn in patterns:
            for match in re.finditer(pattern, self._buffer, re.DOTALL):
                stanza_str = match.group(0)
                if stanza_str in seen_raw:
                    continue
                seen_raw.add(stanza_str)
                try:
                    parsed = parser_fn(stanza_str)
                    stanzas.append(parsed)
                except Exception:
                    pass

        # Limpiar buffer
        if stanzas:
            last_end = 0
            for s in stanzas:
                raw = s.get("raw", "")
                idx = self._buffer.find(raw)
                if idx >= 0:
                    end = idx + len(raw)
                    if end > last_end:
                        last_end = end
            self._buffer = self._buffer[last_end:]

        if len(self._buffer) > 10000 and "<" not in self._buffer:
            self._buffer = ""

        return stanzas

    def reset(self):
        """Limpia el buffer."""
        self._buffer = ""
