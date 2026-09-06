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


def _match_balanced_tag(stanza: str, tag: str) -> str:
    """Encuentra el contenido de la primera etiqueta ``<tag>`` balanceada.

    ``re.search(r'<tag>(.*?)</tag>')`` falla cuando el contenido contiene
    etiquetas ``<tag>`` anidadas, porque el non-greedy captura hasta el
    primer ``</tag>`` (que cierra el anidado, no el exterior).

    Esta función cuenta niveles: empieza después del primer ``<tag ...>``,
    y va avanzando hasta que depth llega a 0. Retorna todo lo que está
    entre el ``<tag>`` de apertura y el ``</tag>`` que lo cierra
    balanceadamente (incluyendo los tags anidados en el medio).

    Maneja:
    - Tags self-closing al inicio del contenido (p.ej. ``<k xmlns='x8'/>``).
    - Tags anidados del mismo nombre (``<b>texto <b>x</b> fin</b>``).
    - Atributos en el tag de apertura (``<b class='x'>...</b>``).
    """
    open_pat = re.compile(rf"<{tag}\b[^>]*>")
    close_pat = re.compile(rf"</{tag}>")
    # Localizar el primer <tag ...>
    open_match = open_pat.search(stanza)
    if not open_match:
        return ""
    start = open_match.end()
    depth = 1
    i = start
    while i < len(stanza):
        next_open = open_pat.search(stanza, i)
        next_close = close_pat.search(stanza, i)
        if not next_close:
            # No cerró — stanza truncada, devolver lo que hay
            return stanza[start:]
        if next_open and next_open.start() < next_close.start():
            # Hay un <tag> antes del </tag>: profundidad aumenta, avanzar.
            depth += 1
            i = next_open.end()
        else:
            # Hay un </tag>: profundidad baja.
            depth -= 1
            if depth == 0:
                # Encontramos el cierre balanceado: devolver todo el contenido
                # desde start hasta este cierre.
                return stanza[start:next_close.start()]
            # Era el cierre de un tag anidado: avanzar.
            i = next_close.end()
    return stanza[start:]


def parse_todus_message(stanza: str) -> dict:
    """Parsea stanza <m> de ToDus."""
    # Extraer tag de apertura <m ...> para leer atributos propios del mensaje
    m_open_match = re.search(r"<m\b[^>]*>", stanza)
    m_tag = m_open_match.group(0) if m_open_match else ""

    # Fix v1.10.2: aceptar tanto ``o=`` (protocolo toDus) como ``to=`` (legacy).
    to_val = _attr(m_tag, "o") or _attr(m_tag, "to")
    result = {
        "from": _attr(m_tag, "f"),
        "to": to_val,
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
        "voice_url": "",
        "voice_name": "",
        "voice_size": 0,
        "voice_duration": 0,
        "voice_wave": "",
        "gif_url": "",
        "gif_name": "",
        "gif_size": 0,
        "gif_width": 0,
        "gif_height": 0,
        "gif_thumbnail": "",
        "stream_guid": "",
        "stream_url": "",
        "stream_duration": 0,
        "stream_codec": "",
        "reaction_id": "",
        "reaction_msg_id": "",
        "reaction_code": "",
        "mentions": [],
        "forward_id": "",
        "forward_owner": "",
        "call_state": "",
        "call_id": "",
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
        "reply_to": "",      # ID del mensaje al que se responde (via resend)
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
    # Fix v1.9.1: manejar <b> anidados y CDATA correctamente.
    # Antes, ``re.search(r"<b>(.*?)</b>", stanza, re.DOTALL)`` cortaba en el
    # primer ``</b>`` que encontraba — incorrecto si el body contenía
    # ``<b>negrita</b>`` anidado. Ahora contamos niveles para emparejar
    # el ``</b>`` de cierre correcto. También limpiamos CDATA.
    body_match = _match_balanced_tag(stanza, "b")
    if body_match:
        raw_body = body_match
        # Strip CDATA wrappers si están presentes (raro pero posible).
        raw_body = re.sub(
            r"<!\[CDATA\[(.*?)\]\]>", r"\1", raw_body, flags=re.DOTALL
        )
        result["body"] = util.unescape_xml(raw_body).strip()
        if "<linkInfo" in stanza:
            result["has_format"] = True

    # Botones interactivos
    button_pattern = (
        r"<button\s+[^>]*?btn_t='([^']*)'\s+btn_cmd='([^']*)'"
        r"\s+btn_msg_c='([^']*)'[^>]*?btn_size='([^']*)'[^>]*/?>"
    )
    for btn_match in re.finditer(button_pattern, stanza):
        result["buttons"].append({
            "text": util.unescape_xml(btn_match.group(1)),
            "command": btn_match.group(2),
            "data": util.unescape_xml(btn_match.group(3)),
            "size": btn_match.group(4)
        })

    # Descripción de botones (btn_d)
    btn_d_match = re.search(r"btn_d='([^']*)'", stanza)
    if btn_d_match and result["buttons"]:
        result["buttons"][-1]["description"] = util.unescape_xml(btn_d_match.group(1))

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

    # Imagen adjunta (formato <image>)
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

    # Nota de voz (voice:n) — attrs: i, mi, url, s, h, d, n, ws
    voice_match = re.search(r"<voice\b[^>]*>", stanza)
    if voice_match:
        voice_tag = voice_match.group(0)
        result["voice_url"] = _attr(voice_tag, "url")
        result["voice_name"] = util.unescape_xml(_attr(voice_tag, "n"))
        result["message_file_id"] = _attr(voice_tag, "mi")
        try:
            result["voice_size"] = int(_attr(voice_tag, "s"))
        except ValueError:
            result["voice_size"] = 0
        try:
            result["voice_duration"] = int(_attr(voice_tag, "d"))
        except ValueError:
            result["voice_duration"] = 0
        result["voice_wave"] = _attr(voice_tag, "ws")
        result["url"] = result["url"] or result["voice_url"]

    # GIF (gif:n) — attrs: i, mi, url, n, s, h, w, he, tnail
    gif_match = re.search(r"<gif\b[^>]*>", stanza)
    if gif_match:
        gif_tag = gif_match.group(0)
        result["gif_url"] = _attr(gif_tag, "url")
        result["gif_name"] = util.unescape_xml(_attr(gif_tag, "n"))
        result["message_file_id"] = _attr(gif_tag, "mi")
        try:
            result["gif_size"] = int(_attr(gif_tag, "s"))
        except ValueError:
            result["gif_size"] = 0
        try:
            result["gif_width"] = int(_attr(gif_tag, "w"))
        except ValueError:
            result["gif_width"] = 0
        try:
            result["gif_height"] = int(_attr(gif_tag, "he"))
        except ValueError:
            result["gif_height"] = 0
        result["gif_thumbnail"] = _attr(gif_tag, "tnail")
        result["url"] = result["url"] or result["gif_url"]

    # Video en stream (streamvideo:n) — attrs: gu, su, du, ec
    stream_match = re.search(r"<streamvideo\b[^>]*>", stanza)
    if stream_match:
        stream_tag = stream_match.group(0)
        result["stream_guid"] = _attr(stream_tag, "gu")
        result["stream_url"] = _attr(stream_tag, "su")
        try:
            result["stream_duration"] = int(_attr(stream_tag, "du"))
        except ValueError:
            result["stream_duration"] = 0
        result["stream_codec"] = _attr(stream_tag, "ec")

    # Reacción (reaction:n) — attrs: i, mi, mir, rc, ca
    reaction_match = re.search(r"<reaction\b[^>]*>", stanza)
    if reaction_match:
        reaction_tag = reaction_match.group(0)
        result["reaction_id"] = _attr(reaction_tag, "i")
        result["reaction_msg_id"] = _attr(reaction_tag, "mi") or _attr(reaction_tag, "mir")
        result["reaction_code"] = _attr(reaction_tag, "rc")

    # Menciones (mention:n) — attrs: o, l, ui (puede haber varias)
    for mention_match in re.finditer(r"<mention\b[^>]*>", stanza):
        mention_tag = mention_match.group(0)
        try:
            offset = int(_attr(mention_tag, "o"))
        except ValueError:
            offset = 0
        try:
            length = int(_attr(mention_tag, "l"))
        except ValueError:
            length = 0
        result["mentions"].append({
            "offset": offset,
            "length": length,
            "user_id": _attr(mention_tag, "ui"),
        })

    # Reenvío / respuesta (resend:n) — attrs: i, mi, uowner
    resend_match = re.search(r"<resend\b[^>]*>", stanza)
    if resend_match:
        resend_tag = resend_match.group(0)
        result["forward_id"] = _attr(resend_tag, "mi")
        result["forward_owner"] = _attr(resend_tag, "uowner")
        result["reply_to"] = result["forward_id"]

    # Señalización de llamada (tcall:n) — attrs: i, mi, st, cid
    tcall_match = re.search(r"<tcall\b[^>]*>", stanza)
    if tcall_match:
        tcall_tag = tcall_match.group(0)
        result["call_state"] = _attr(tcall_tag, "st")
        result["call_id"] = _attr(tcall_tag, "cid")

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

    # Estado de chat (XEP-0085 ofuscado de toDus).
    # Fix v1.10.2: INVERTIDO respecto a v1.8.0. Alineado con ElJoker63:
    # csp=composing, csc=paused, csa=active, csi=inactive, csg=gone.
    if "<csp xmlns='uc1'/>" in stanza:
        result["chat_state"] = "composing"
    elif "<csc xmlns='uc1'/>" in stanza:
        result["chat_state"] = "paused"
    elif "<csa xmlns='uc1'/>" in stanza:
        result["chat_state"] = "active"
    elif "<csi xmlns='uc1'/>" in stanza:
        result["chat_state"] = "inactive"
    elif "<csg xmlns='uc1'/>" in stanza:
        result["chat_state"] = "gone"

    # Recibos según el protocolo de toDus (v1.10.2, alineado con ElJoker63):
    # dd = delivery (entregado), rd = read (leído/displayed)
    # INVERTIDO respecto a v1.8.0 (que decía rd=delivered, dd=read).
    delivery_match = re.search(r"<dd\b[^>]*>", stanza)
    if delivery_match:
        receipt_tag = delivery_match.group(0)
        result["receipt"] = _attr(receipt_tag, "i")
        result["receipt_type"] = "delivered"
    else:
        read_match = re.search(r"<rd\b[^>]*>", stanza)
        if read_match:
            read_tag = read_match.group(0)
            result["receipt"] = _attr(read_tag, "i")
            result["receipt_type"] = "read"

    # ACK (ak; tdack se mantiene
    # por compatibilidad con versiones anteriores del SDK)
    ack_match = re.search(r"<ak\b[^>]*>", stanza)
    if ack_match:
        result["ack"] = _attr(ack_match.group(0), "i")

    return result


def parse_presence(stanza: str) -> dict:
    """Parsea stanza ``<p>`` (o ``<presence>`` legacy) de presencia."""
    # Fix v1.10.2: aceptar tanto ``o=`` (protocolo toDus) como ``to=``
    # (legacy/estándar XMPP) para el atributo de destino.
    to_val = _attr(stanza, "o") or _attr(stanza, "to")
    result = {
        "from": _attr(stanza, "f"),
        "to": to_val,
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
    # Fix v1.10.2: aceptar ``o=`` (toDus) o ``to=`` (legacy), ``i=`` o ``id=``, ``t=`` o ``type=``.
    to_val = _attr(stanza, "o") or _attr(stanza, "to")
    id_val = _attr(stanza, "i") or _attr(stanza, "id")
    type_val = _attr(stanza, "t") or _attr(stanza, "type")
    result = {
        "from": _attr(stanza, "f"),
        "to": to_val,
        "id": id_val,
        "type": type_val,
        "error": "",
        "raw": stanza,
    }

    if "<error" in stanza:
        match = re.search(r"<error[^>]*>(.*?)</error>", stanza, re.DOTALL)
        if match:
            result["error"] = match.group(1)

    # Extraer query interno si existe (útil para canales)
    query_match = re.search(r"<query[^>]*>(.*?)</query>", stanza, re.DOTALL)
    if query_match:
        result["query"] = query_match.group(1)
    else:
        # En caso de que el query no tenga hijos (e.g. <query .../>) pero tenga atributos
        query_self_closing = re.search(r"<query([^>]*?)/>", stanza)
        if query_self_closing:
            result["query_attrs"] = query_self_closing.group(1)

    # Upload URLs
    if _attr(stanza, "put"):
        result["upload_url"] = _attr(stanza, "put").replace("amp;", "")
        result["download_url"] = _attr(stanza, "get").replace("amp;", "")

    # Download URL
    if _attr(stanza, "du"):
        result["real_url"] = _attr(stanza, "du").replace("amp;", "")

    return result


def parse_tdack(stanza: str) -> dict:
    """Parsea stanza <tdack> (legado del SDK)."""
    return {
        "type": "tdack",
        "message_id": _attr(stanza, "mi"),
        "raw": stanza,
    }


def parse_ack(stanza: str) -> dict:
    """Parsea stanza <ak> (ACK del protocolo oficial)."""
    return {
        "type": "ack",
        "message_id": _attr(stanza, "i") or _attr(stanza, "mi"),
        "raw": stanza,
    }


def extract_all_stanzas(xml: str) -> dict:
    """Extrae todas las stanzas de un chunk XML."""
    return {
        "messages": re.findall(r"<m\b.*?</m>", xml, re.DOTALL),
        "presences": re.findall(r"<p\b.*?</p>", xml, re.DOTALL),
        "iqs": re.findall(r"<iq\b.*?</iq>", xml, re.DOTALL),
        "tdacks": re.findall(r"<tdack\b[^>]*?/>", xml),
        "acks": re.findall(r"<ak\b[^>]*?/>", xml),
        "streams": re.findall(r"<\?xml[^?]*\?><stream:stream[^>]*/?>", xml),
        "unknown": [],
    }


class IncrementalParser:
    """Parser incremental que maneja stanzas fragmentadas por TCP.

    Fix v1.9.1 — reescritura del algoritmo para resolver 5 bugs a la vez:

    - Bug #2: antes ``feed()`` emitía la misma stanza dos veces si llegaba en
      feeds separados (``seen_ids`` era local a cada llamada). Ahora el set
      de IDs vistos persiste en ``self._seen_ids`` entre llamadas.
    - Bug #3: antes el ``<?xml ...?><stream:stream ...>`` inicial se quedaba
      pegado al buffer para siempre porque el cleanup solo disparaba con
      ``len(buffer) > 20000``. Ahora se descarta de forma determinista
      al inicio de cada feed.
    - Bug #4: antes ``<m ... />`` (self-closing) no se parseaba porque el
      patrón exigía ``</m>``. Ahora se intenta primero el patrón con
      cierre y luego el self-closing.
    - Bug #5: antes ``<![CDATA[...]]>`` dentro de ``<b>`` corrompía el body.
      Ahora ``_strip_cdata`` lo limpia antes de unescape.
    - Bug #6: antes ``<b>`` anidados se rompían por el non-greedy regex.
      Ahora ``parse_todus_message`` cuenta niveles para emparejar
      correctamente el ``</b>`` de cierre.

    Además, el algoritmo ahora es O(n) por chunk en vez de O(n²) sobre el
    buffer acumulado: solo se procesa el nuevo chunk y se conserva el
    fragmento final incompleto.
    """

    # Patrones en orden de preferencia. Los self-closing van después de
    # los de cierre completo para que un ``<m>...</m>`` no sea capturado por
    # el self-closing ``<m ... />``.
    _PATTERNS = [
        # Stanzas con tag de cierre explícito (non-greedy con DOTALL).
        (r"<m\b[^>]*>.*?</m>", parse_todus_message),
        (r"<p\b[^>]*>.*?</p>", parse_presence),
        (r"<iq\b[^>]*>.*?</iq>", parse_iq),
        # Stanzas self-closing (deben ir después de las de cierre completo).
        (r"<ak\b[^>]*/>", parse_ack),
        (r"<tdack\b[^>]*/>", parse_tdack),
        # Caso raro: <m .../> sin cierre y sin self-closing slash (malformed
        # pero posible). Lo capturamos como último recurso.
        (r"<m\b[^>]*/>", parse_todus_message),
    ]

    def __init__(self):
        self._buffer = ""
        # Persiste entre llamadas a feed() para evitar reemitir stanzas
        # duplicadas que lleguen en chunks separados (reenvío del servidor).
        self._seen_ids: set[str] = set()

    def feed(self, chunk: str) -> list[dict]:
        """Alimenta con nuevo chunk y retorna stanzas completas parseadas."""
        if not chunk:
            return []

        self._buffer += chunk

        # Descartar headers XMPP iniciales que el servidor envía al abrir
        # stream y que no son stanzas parseables. Antes se quedaban pegados
        # al buffer indefinidamente.
        self._strip_stream_headers()

        stanzas: list[dict] = []
        # Encontrar todas las stanzas completas en el buffer actual.
        # Procesamos por orden de aparición (por offset) para respetar el
        # orden de llegada.
        # ``seen_here`` trackea IDs ya añadidos en ESTA feed para evitar
        # añadir el mismo ID dos veces dentro del mismo feed (caso de
        # stanzas duplicadas en el mismo chunk). ``self._seen_ids`` trackea
        # IDs vistos en feeds anteriores (reenvío del servidor).
        seen_here: set[str] = set()
        candidates: list[tuple[int, int, dict]] = []  # (start, end, parsed)

        for pattern, parser_fn in self._PATTERNS:
            for match in re.finditer(pattern, self._buffer, re.DOTALL):
                stanza_str = match.group(0)
                try:
                    parsed = parser_fn(stanza_str)
                except Exception:
                    continue
                msg_id = parsed.get("id", "")
                # Deduplicar: si ya emitimos esta stanza en feeds previas
                # o dentro de esta misma feed, saltar.
                if msg_id and (msg_id in self._seen_ids or msg_id in seen_here):
                    continue
                if msg_id:
                    seen_here.add(msg_id)
                candidates.append((match.start(), match.end(), parsed))

        # Ordenar por offset de aparición para respetar orden de llegada.
        candidates.sort(key=lambda c: c[0])

        # Eliminar candidatos solapados (un <m> completo solapa con un
        # <m/> self-closing si el regex atrapa el mismo tramo de ambas
        # formas). Nos quedamos con el más largo.
        non_overlapping: list[tuple[int, int, dict]] = []
        last_end = -1
        for start, end, parsed in candidates:
            if start < last_end:
                # Solapa con el anterior: el anterior ya se aceptó.
                # Si el nuevo es más largo, reemplazarlo.
                if non_overlapping and end > non_overlapping[-1][1]:
                    non_overlapping[-1] = (start, end, parsed)
                continue
            non_overlapping.append((start, end, parsed))
            last_end = end

        for start, end, parsed in non_overlapping:
            msg_id = parsed.get("id", "")
            if msg_id:
                # Persistir el ID visto para futuras feeds (reenvío del
                # servidor no se reemitirá).
                self._seen_ids.add(msg_id)
            stanzas.append(parsed)

        # Truncar el buffer hasta el final de la última stanza procesada.
        # El resto (fragmento incompleto) se conserva para el siguiente feed.
        if non_overlapping:
            last_end = max(c[1] for c in non_overlapping)
            self._buffer = self._buffer[last_end:]
        # Si no hubo stanzas pero el buffer crece sin contener "<" (basura
        # no-XML), vaciarlo para evitar crecimiento infinito.
        if not non_overlapping and len(self._buffer) > 20000:
            if "<" not in self._buffer:
                self._buffer = ""
            else:
                # Conservar desde el último "<" (posible inicio de stanza).
                last_tag = self._buffer.rfind("<")
                if last_tag > 0:
                    self._buffer = self._buffer[last_tag:]

        # Limitar la memoria del set de IDs vistos.
        if len(self._seen_ids) > 50000:
            # Reset simple: el servidor no debería reenviar mensajes tan viejos.
            self._seen_ids.clear()

        return stanzas

    def _strip_stream_headers(self) -> None:
        """Elimina ``<?xml ...?>`` y ``<stream:stream ...>`` del inicio del
        buffer. Estos headers no son stanzas parseables y antes se quedaban
        pegados al buffer consumiendo memoria.
        """
        # Quitar <?xml version='1.0'?> opcional al inicio
        if self._buffer.startswith("<?xml"):
            end = self._buffer.find("?>")
            if end >= 0:
                self._buffer = self._buffer[end + 2:]
        # Quitar <stream:stream ...> (con o sin self-closing)
        # Solo si está al inicio, sin stanzas antes.
        if self._buffer.lstrip().startswith("<stream:stream"):
            stripped = self._buffer.lstrip()
            # Buscar el final del tag (> o />)
            idx = stripped.find(">")
            if idx >= 0:
                # ¿Self-closing (termina en />)?
                if stripped[:idx].endswith("/"):
                    self._buffer = stripped[idx + 1:]
                else:
                    self._buffer = stripped[idx + 1:]

    def reset(self):
        """Limpia el buffer y el historial de IDs vistos."""
        self._buffer = ""
        self._seen_ids.clear()
