"""Parser de stanzas XMPP/ToDus."""

import re
from . import util
from .errors import ParseError


def _attr(stanza: str, name: str) -> str:
    """Extrae atributo de stanza."""
    match = re.search(rf"{name}='([^']+)'", stanza)
    return match.group(1) if match else ""


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

    # Archivo adjunto (formato nuevo <file>)
    # <file xmlns='file:n' i='file-id' mi='msg-id' n='nombre.docx' url='https://...' s='10210' h='hash'/>
    file_match = re.search(
        r"<file\s+xmlns='file:n'\s+"
        r"i='([^']*)'\s+"
        r"mi='([^']*)'\s+"
        r"n='([^']*)'\s+"
        r"url='([^']*)'\s+"
        r"s='([^']*)'\s+"
        r"h='([^']*)'",
        stanza,
    )
    if file_match:
        result["file_id"] = file_match.group(1)
        result["message_file_id"] = file_match.group(2)
        result["file_name"] = util.unescape_xml(file_match.group(3))
        result["url"] = file_match.group(4)
        try:
            result["file_size"] = int(file_match.group(5))
        except ValueError:
            result["file_size"] = 0
        result["file_hash"] = file_match.group(6)

    # Offline timestamp
    match = re.search(r"<todus_offline\s+ts='([^']+)'", stanza)
    if match:
        result["offline_ts"] = match.group(1)

    # Edited
    match = re.search(r"<edited\s+xmlns='edited:n'\s+i='([^']+)'", stanza)
    if match:
        result["edited"] = match.group(1)

    # Deleted
    match = re.search(r"<deleted\s+xmlns='deleted:n'\s+i='([^']+)'", stanza)
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

    # Upload URLs
    if "put='" in stanza:
        match = re.match(r".*put='(.*)' get='(.*)' stat.*", stanza)
        if match:
            result["upload_url"] = match.group(1).replace("amp;", "")
            result["download_url"] = match.group(2)

    # Download URL
    if "du='" in stanza:
        match = re.match(".*du='(.*)' stat.*", stanza)
        if match:
            result["real_url"] = match.group(1).replace("amp;", "")

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

        patterns = [
            (r"<m\b.*?</m>", parse_todus_message),
            (r"<p\b.*?</p>", parse_presence),
            (r"<iq\b.*?</iq>", parse_iq),
        ]

        for pattern, parser_fn in patterns:
            for match in re.finditer(pattern, self._buffer, re.DOTALL):
                stanza_str = match.group(0)
                # Evitar duplicados
                if stanza_str not in [s.get("raw", "") for s in stanzas]:
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
