"""Parser de stanzas XMPP/ToDus."""

import re
from . import util


def _attr(stanza: str, name: str) -> str:
    """Extrae atributo de stanza. Soporta comillas simples y dobles."""
    for quote in ("'", '"'):
        pattern = rf"\b{name}={quote}([^{quote}]*){quote}"
        match = re.search(pattern, stanza)
        if match:
            return match.group(1)
    return ""


def parse_todus_message(stanza: str) -> dict:
    """Parsea stanza <m> de ToDus."""
    # Extraer tag de apertura <m ...> para leer atributos propios del mensaje
    m_open_match = re.search(r"<m\b[^>]*>", stanza)
    m_tag = m_open_match.group(0) if m_open_match else ""

    result = {
        "from": _attr(m_tag, "f"),
        "to": _attr(m_tag, "o"),
        "id": _attr(m_tag, "i"),
        "type": _attr(m_tag, "t"),
        "original_id": _attr(m_tag, "mi"),
        "body": "",
        "url": "",
        "file_name": "",
        "file_size": 0,
        "file_id": "",
        "file_hash": "",
        "message_file_id": "",
        "contact_id": "",
        "contact_name": "",
        "contact_phone": "",
        "sticker_id": "",
        "sticker_name": "",
        "sticker_pack": "",
        "sticker_hash": "",
        "video_id": "",
        "video_url": "",
        "video_name": "",
        "video_size": 0,
        "video_duration": 0,
        "video_width": 0,
        "video_height": 0,
        "video_thumbnail": "",
        "image_width": 0,
        "image_height": 0,
        "image_thumbnail": "",
        "has_key": "<k" in stanza,
        "offline_ts": "",
        "edited": "",
        "deleted": "",
        "chat_state": "",
        "receipt": "",
        "receipt_type": "",
        "location_id": "",
        "location_lat": 0.0,
        "location_lon": 0.0,
        "location_zoom": 0.0,
        "location_text": "",
        "event_id": "",
        "event_title": "",
        "event_start": 0,
        "event_end": 0,
        "event_all_day": False,
        "event_ics": "",
        "has_format": False,
        "buttons": [],
        "raw": stanza,
        "is_group": False,
        "group_id": "",
        "sender_phone": "",
    }

    # Detectar si es mensaje de grupo
    msg_type = _attr(m_tag, "t")
    result["is_group"] = msg_type == "gc"

    if result["is_group"]:
        # Extraer ID del grupo del JID 'from' o 'to'
        from_jid = result.get("from", "")
        if "@muclight.im.todus.cu" in from_jid:
            parts = from_jid.split("/", 1)
            result["group_id"] = parts[0].split("@")[0] if parts else ""
            if len(parts) > 1:
                result["sender_phone"] = parts[1].split("@")[0]

    # Body
    match = re.search(r"<b>(.*?)</b>", stanza, re.DOTALL)
    if match:
        result["body"] = util.unescape_xml(match.group(1)).strip()
        if "<linkInfo" in stanza:
            result["has_format"] = True

    # Botones interactivos
    button_pattern = r"<button\s+btn_t='([^']*)'\s+btn_cmd='([^']*)'\s+btn_msg_c='([^']*)'\s+btn_size='([^']*)'/?>"
    for btn_match in re.finditer(button_pattern, stanza):
        result["buttons"].append({
            "text": util.unescape_xml(btn_match.group(1)),
            "command": btn_match.group(2),
            "data": util.unescape_xml(btn_match.group(3)),
            "size": btn_match.group(4)
        })

    # URL de archivo (formato antiguo <u>)
    match = re.search(r"<u>(.*?)</u>", stanza, re.DOTALL)
    if match:
        result["url"] = util.unescape_xml(match.group(1)).strip()

    # Archivo adjunto (formato nuevo <file>)
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

    # Imagen adjunta (formato </tr>)
    image_match = re.search(r"<image\b[^>]*>", stanza)
    if image_match:
        image_tag = image_match.group(0)
        result["file_id"] = _attr(image_tag, "i")
        result["message_file_id"] = _attr(image_tag, "mi")
        result["file_name"] = util.unescape_xml(_attr(image_tag, "n")) or "image.jpg"
        result["url"] = _attr(image_tag, "url")
        try:
            result["file_size"] = int(_attr(image_tag, "s"))
        except ValueError:
            result["file_size"] = 0
        result["file_hash"] = _attr(image_tag, "h")
        try:
            result["image_width"] = int(_attr(image_tag, "w"))
        except ValueError:
            result["image_width"] = 0
        try:
            result["image_height"] = int(_attr(image_tag, "he"))
        except ValueError:
            result["image_height"] = 0
        result["image_thumbnail"] = _attr(image_tag, "tnail")

    # Contacto adjunto (formato <contact>)
    contact_match = re.search(r"<contact\b[^>]*>", stanza)
    if contact_match:
        contact_tag = contact_match.group(0)
        result["contact_id"] = _attr(contact_tag, "i")
        result["contact_name"] = util.unescape_xml(_attr(contact_tag, "n"))
        result["contact_phone"] = _attr(contact_tag, "num")
        result["message_file_id"] = _attr(contact_tag, "mi")

    # Sticker adjunto (formato <sticker>)
    sticker_match = re.search(r"<sticker\b[^>]*>", stanza)
    if sticker_match:
        sticker_tag = sticker_match.group(0)
        result["sticker_id"] = _attr(sticker_tag, "i")
        result["sticker_name"] = util.unescape_xml(_attr(sticker_tag, "n"))
        result["sticker_pack"] = util.unescape_xml(_attr(sticker_tag, "f"))
        result["sticker_hash"] = _attr(sticker_tag, "h")
        result["message_file_id"] = _attr(sticker_tag, "mi")

    # Video adjunto (formato <video>)
    video_match = re.search(r"<video\b[^>]*>", stanza)
    if video_match:
        video_tag = video_match.group(0)
        result["video_id"] = _attr(video_tag, "i")
        result["message_file_id"] = _attr(video_tag, "mi")
        result["video_name"] = util.unescape_xml(_attr(video_tag, "n"))
        result["video_url"] = _attr(video_tag, "url")
        try:
            result["video_size"] = int(_attr(video_tag, "s"))
        except ValueError:
            result["video_size"] = 0
        try:
            result["video_duration"] = int(_attr(video_tag, "d"))
        except ValueError:
            result["video_duration"] = 0
        try:
            result["video_width"] = int(_attr(video_tag, "w"))
        except ValueError:
            result["video_width"] = 0
        try:
            result["video_height"] = int(_attr(video_tag, "he"))
        except ValueError:
            result["video_height"] = 0
        result["video_thumbnail"] = _attr(video_tag, "tnail")
        result["file_hash"] = _attr(video_tag, "h")

    # Offline timestamp
    match = re.search(r"<todus_offline\s+ts='([^']+)'", stanza)
    if not match:
        match = re.search(r'<todus_offline\s+ts="([^"]+)"', stanza)
    if match:
        result["offline_ts"] = match.group(1)

    # Edited
    edited_match = re.search(r"<edited\b[^>]*>", stanza)
    if edited_match:
        edited_tag = edited_match.group(0)
        result["edited"] = _attr(edited_tag, "i")

    # Deleted
    deleted_match = re.search(r"<deleted\b[^>]*>", stanza)
    if deleted_match:
        deleted_tag = deleted_match.group(0)
        result["deleted"] = _attr(deleted_tag, "mi") or _attr(deleted_tag, "i")

    # Ubicación adjunta (location)
    location_match = re.search(r"<location\b[^>]*>", stanza)
    if location_match:
        loc_tag = location_match.group(0)
        result["location_id"] = _attr(loc_tag, "i")
        result["message_file_id"] = _attr(loc_tag, "mi")
        try:
            result["location_lat"] = float(_attr(loc_tag, "lat"))
        except ValueError:
            result["location_lat"] = 0.0
        try:
            result["location_lon"] = float(_attr(loc_tag, "lon"))
        except ValueError:
            result["location_lon"] = 0.0
        try:
            result["location_zoom"] = float(_attr(loc_tag, "z"))
        except ValueError:
            result["location_zoom"] = 0.0
        result["location_text"] = util.unescape_xml(_attr(loc_tag, "t"))

    # Evento adjunto (event)
    event_match = re.search(r"<event\b[^>]*>", stanza)
    if event_match:
        event_tag = event_match.group(0)
        result["event_id"] = _attr(event_tag, "i")
        result["message_file_id"] = _attr(event_tag, "mi")
        result["event_title"] = util.unescape_xml(_attr(event_tag, "ti"))
        try:
            result["event_start"] = int(_attr(event_tag, "s"))
        except ValueError:
            result["event_start"] = 0
        try:
            result["event_end"] = int(_attr(event_tag, "e"))
        except ValueError:
            result["event_end"] = 0
        result["event_all_day"] = _attr(event_tag, "ad").lower() == "true"
        
        ics_match = re.search(r"<ics>(.*?)</ics>", stanza, re.DOTALL)
        if ics_match:
            result["event_ics"] = ics_match.group(1).strip()

    # Estado de chat (csp/csc)
    if "<csp xmlns='uc1'/>" in stanza:
        result["chat_state"] = "composing"
    elif "<csc xmlns='uc1'/>" in stanza:
        result["chat_state"] = "paused"

    # Recibos de entrega (dd) o lectura (rd)
    receipt_match = re.search(r"<dd\b[^>]*>", stanza)
    if receipt_match:
        receipt_tag = receipt_match.group(0)
        result["receipt"] = _attr(receipt_tag, "i")
        result["receipt_type"] = "delivered"
    else:
        read_match = re.search(r"<rd\b[^>]*>", stanza)
        if read_match:
            read_tag = read_match.group(0)
            result["receipt"] = _attr(read_tag, "i")
            result["receipt_type"] = "read"

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
    if _attr(stanza, "put"):
        result["upload_url"] = _attr(stanza, "put").replace("amp;", "")
        result["download_url"] = _attr(stanza, "get").replace("amp;", "")

    # Download URL
    if _attr(stanza, "du"):
        result["real_url"] = _attr(stanza, "du").replace("amp;", "")

    return result


def parse_tdack(stanza: str) -> dict:
    """Parsea stanza <tdack> de ToDus (acknowledgment)."""
    return {
        "type": "tdack",
        "message_id": _attr(stanza, "mi"),
        "raw": stanza,
    }


def extract_all_stanzas(xml: str) -> dict:
    """Extrae todas las stanzas de un chunk XML."""
    return {
        "messages": re.findall(r"<m\b.*?</m>", xml, re.DOTALL),
        "presences": re.findall(r"<p\b.*?</p>", xml, re.DOTALL),
        "iqs": re.findall(r"<iq\b.*?</iq>", xml, re.DOTALL),
        "tdacks": re.findall(r"<tdack\b[^>]*?/>", xml),
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
            (r"<tdack\b[^>]*?/>", parse_tdack),
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

        # Limpiar buffer hasta el final de la última stanza procesada
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

        # Evitar crecimiento infinito de basura no-XML
        if len(self._buffer) > 20000:
            if "<" not in self._buffer:
                self._buffer = ""
            else:
                last_tag = self._buffer.rfind("<")
                if last_tag > 0:
                    self._buffer = self._buffer[last_tag:]

        return stanzas

    def reset(self):
        """Limpia el buffer."""
        self._buffer = ""