"""Generadores de stanzas XML para chat privado en ToDus.

Alineado con el protocolo oficial v2.1.2:
- Las respuestas se implementan con la extensión ``resend`` (no existe
  ninguna extensión ``reply:n``).
- Botones: atributos ``btn_t``, ``btn_cmd``, ``btn_msg_c``, ``btn_d``,
  ``btn_size`` (sin ``btn_color`` ni ``btn_row``).
"""

import hashlib
from .. import util


def _generate_msg_id() -> str:
    """Genera msg_id en formato hex 32 chars como usa ToDus oficial."""
    return hashlib.md5(util.generate_token(16).encode()).hexdigest()


def _reply_xml(reply_to_id: str) -> str:
    """Extensión de respuesta apuntando al mensaje original (resend)."""
    if not reply_to_id:
        return ""
    return f"<resend xmlns='resend:n' mi='{reply_to_id}'/>"


def message(to: str, body: str, msg_id: str = "", msg_type: str = "c", reply_to_id: str = "") -> str:
    """Stanza <m> de ToDus para chat privado."""
    mid = msg_id or _generate_msg_id()
    body_esc = util.escape_xml(body)
    reply = _reply_xml(reply_to_id)
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<b>{body_esc}</b>"
        f"</m>"
    )


def edit_message(to: str, new_body: str, original_msg_id: str, edit_id: str = "", reply_to_id: str = "") -> str:
    """Edita un mensaje existente en chat privado."""
    eid = edit_id or _generate_msg_id()
    body_esc = util.escape_xml(new_body)
    reply = _reply_xml(reply_to_id)
    return (
        f"<m to='{to}' t='c' i='{original_msg_id}' xmlns='jc'>"
        f"<edited xmlns='edited:n' i='{eid}' mi='{original_msg_id}'/>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<b>{body_esc}</b>"
        f"</m>"
    )


def file_message(to: str, url: str, file_type: int, caption: str = "", msg_id: str = "", msg_type: str = "c",
                 file_name: str = "", file_size: int = 0, reply_to_id: str = "") -> str:
    """Stanza con archivo adjunto para chat privado."""
    mid = msg_id or _generate_msg_id()
    fid = _generate_msg_id()
    cap_esc = util.escape_xml(caption)
    name_esc = util.escape_xml(file_name)
    reply = _reply_xml(reply_to_id)
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<b>{cap_esc}</b>"
        f"<file xmlns='file:n' i='{fid}' mi='{mid}' n='{name_esc}' url='{util.escape_xml(url)}' s='{file_size}' h=''/>"
        f"</m>"
    )


def image_message(to: str, url: str, file_name: str, file_size: int, width: int = 0, height: int = 0,
                  thumbnail: str = "", caption: str = "", msg_id: str = "", msg_type: str = "c",
                  reply_to_id: str = "") -> str:
    """Stanza con imagen adjunta para chat privado."""
    mid = msg_id or _generate_msg_id()
    fid = _generate_msg_id()
    cap_esc = util.escape_xml(caption)
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)

    tnail = thumbnail if thumbnail else "U6688O?Hr=xu^-w2sp-;,^VZnm-;_3xHMyt5"

    wh_attrs = ""
    if width > 0:
        wh_attrs += f" w='{width}'"
    if height > 0:
        wh_attrs += f" he='{height}'"

    reply = _reply_xml(reply_to_id)

    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<image xmlns='image:n' i='{fid}' mi='{mid}' url='{url_esc}' n='{name_esc}' s='{file_size}'"
        f"h=''{wh_attrs} tnail='{tnail}'/>"
        f"<b>{cap_esc}</b>"
        f"</m>"
    )


def image_message_simple(to: str, url: str, file_name: str, file_size: int,
                         msg_id: str = "", msg_type: str = "c", reply_to_id: str = "") -> str:
    """Versión simple sin metadata para chat privado."""
    mid = msg_id or _generate_msg_id()
    fid = _generate_msg_id()
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)
    reply = _reply_xml(reply_to_id)

    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<image xmlns='image:n' i='{fid}' mi='{mid}' url='{url_esc}' n='{name_esc}' s='{file_size}' h=''/>"
        f"<b/>"
        f"</m>"
    )


def button_message(to: str, text: str, buttons: list[dict], msg_id: str = "", msg_type: str = "c",
                   reply_to_id: str = "") -> str:
    """Envía mensaje con botones interactivos (extensión ``button:n``).

    Cada botón es un dict con:
        - text: texto del botón (attr ``btn_t``)
        - command: comando (attr ``btn_cmd``): ``cmd_type_send``,
          ``cmd_open_web``, ``cmd_copy_to_clipboard``, ``cmd_add_shortcut``,
          ``cmd_open_app_screen``
        - data: valor asociado (attr ``btn_msg_c``): texto a enviar, URL, etc.
        - description: descripción opcional (attr ``btn_d``)
        - size: ``0.82`` (full) o ``0.4`` (mid)
    """
    mid = msg_id or _generate_msg_id()
    text_esc = util.escape_xml(text)
    reply = _reply_xml(reply_to_id)

    buttons_xml = ""
    for btn in buttons:
        btn_text = util.escape_xml(btn.get("text", ""))
        btn_cmd = btn.get("command", "cmd_type_send")
        btn_msg = util.escape_xml(btn.get("data", ""))
        btn_size = btn.get("size", "0.82")
        btn_d = util.escape_xml(btn.get("description", ""))
        desc_attr = f" btn_d='{btn_d}'" if btn_d else ""

        buttons_xml += (
            f"<button xmlns='button:n' btn_t='{btn_text}' btn_cmd='{btn_cmd}' "
            f"btn_msg_c='{btn_msg}'{desc_attr} btn_size='{btn_size}'/>"
        )

    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<b>{text_esc}</b>"
        f"{buttons_xml}"
        f"</m>"
    )


def contact_message(to: str, contact_id: str, contact_name: str, contact_phone: str,
                    msg_id: str = "", msg_type: str = "c", reply_to_id: str = "") -> str:
    """Stanza con contacto adjunto."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(contact_name)
    reply = _reply_xml(reply_to_id)
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<contact xmlns='contact:n' i='{contact_id}' mi='{mid}' n='{name_esc}'"
        f"num='{util.escape_xml(contact_phone)}'/>"
        f"<b/>"
        f"</m>"
    )


def sticker_message(to: str, sticker_id: str, sticker_name: str, sticker_pack: str, sticker_hash: str,
                    msg_id: str = "", msg_type: str = "c", reply_to_id: str = "") -> str:
    """Stanza con sticker adjunto."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(sticker_name)
    pack_esc = util.escape_xml(sticker_pack)
    reply = _reply_xml(reply_to_id)
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<sticker xmlns='sticker:n' i='{sticker_id}' mi='{mid}' n='{name_esc}' f='{pack_esc}' url='' s='0'"
        f"h='{util.escape_xml(sticker_hash)}' json=''/>"
        f"<b/>"
        f"</m>"
    )


def video_message(to: str, url: str, video_id: str, file_name: str, file_size: int, duration: int,
                  width: int, height: int, thumbnail: str, msg_id: str = "", msg_type: str = "c",
                  info_text: str = "", reply_to_id: str = "") -> str:
    """Stanza con video adjunto."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)
    body_tag = "<b/>" if not info_text else f"<b>{util.escape_xml(info_text)}</b>"
    reply = _reply_xml(reply_to_id)

    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<video xmlns='video:n' i='{video_id}' mi='{mid}' url='{url_esc}' s='{file_size}' h='' d='{duration}'"
        f"n='{name_esc}' w='{width}' he='{height}' tnail='{thumbnail}'/>"
        f"{body_tag}"
        f"</m>"
    )


def voice_message(to: str, url: str, file_name: str, file_size: int, duration: int,
                  wave_sample: str, msg_id: str = "", msg_type: str = "c",
                  caption: str = "", reply_to_id: str = "") -> str:
    """Stanza con nota de voz (extensión ``voice:n``).

    ``wave_sample`` (attr ``ws``) es la forma de onda para dibujar la
    burbuja de audio (lista de amplitudes separadas por coma).
    """
    mid = msg_id or _generate_msg_id()
    fid = _generate_msg_id()
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)
    body_tag = f"<b>{util.escape_xml(caption)}</b>" if caption else "<b/>"
    reply = _reply_xml(reply_to_id)

    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<voice xmlns='voice:n' i='{fid}' mi='{mid}' url='{url_esc}' s='{file_size}' "
        f"h='' d='{duration}' n='{name_esc}' ws='{util.escape_xml(wave_sample)}'/>"
        f"{body_tag}"
        f"</m>"
    )


def gif_message(to: str, url: str, file_name: str, file_size: int, width: int = 0, height: int = 0,
                thumbnail: str = "", caption: str = "", msg_id: str = "", msg_type: str = "c",
                reply_to_id: str = "") -> str:
    """Stanza con GIF adjunto (extensión ``gif:n``)."""
    mid = msg_id or _generate_msg_id()
    fid = _generate_msg_id()
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)
    body_tag = f"<b>{util.escape_xml(caption)}</b>" if caption else "<b/>"
    reply = _reply_xml(reply_to_id)

    wh_attrs = ""
    if width > 0:
        wh_attrs += f" w='{width}'"
    if height > 0:
        wh_attrs += f" he='{height}'"

    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<gif xmlns='gif:n' i='{fid}' mi='{mid}' url='{url_esc}' n='{name_esc}' "
        f"s='{file_size}' h=''{wh_attrs} tnail='{thumbnail}'/>"
        f"{body_tag}"
        f"</m>"
    )


def stream_video_message(to: str, guid: str, stream_url: str, duration: int = 0,
                         extra_codec: str = "", msg_id: str = "", msg_type: str = "c") -> str:
    """Stanza de video en stream (extensión ``streamvideo:n``).

    Atributos: ``gu`` (guid), ``su`` (stream url), ``du`` (duración),
    ``ec`` (extra codec).
    """
    mid = msg_id or _generate_msg_id()
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"<streamvideo xmlns='streamvideo:n' gu='{guid}' su='{util.escape_xml(stream_url)}' "
        f"du='{duration}' ec='{util.escape_xml(extra_codec)}'/>"
        f"</m>"
    )


def reaction_message(to: str, reacted_msg_id: str, reaction_code: str, reaction_id: str = "",
                     ca: str = "", msg_id: str = "", msg_type: str = "c") -> str:
    """Stanza de reacción a un mensaje (extensión ``reaction:n``).

    Atributos: ``i`` (id de la reacción), ``mi`` (id del mensaje que se
    reacciona), ``mir`` (id del mensaje de reacción original), ``rc``
    (código del emoji), ``ca`` (atributo adicional).
    """
    rid = reaction_id or _generate_msg_id()
    return (
        f"<m to='{to}' t='{msg_type}' i='{msg_id or rid}' xmlns='jc'>"
        f"<reaction xmlns='reaction:n' i='{rid}' mi='{reacted_msg_id}' "
        f"mir='{reacted_msg_id}' rc='{util.escape_xml(reaction_code)}' ca='{ca}'/>"
        f"</m>"
    )


def forward_message(to: str, original_msg_id: str, original_owner: str = "",
                    msg_id: str = "", msg_type: str = "c", body: str = "") -> str:
    """Reenvía (forward) un mensaje (extensión ``resend:n``).

    Atributos: ``i`` (id del reenvío), ``mi`` (id del mensaje original),
    ``uowner`` (JID del dueño original del mensaje).
    """
    mid = msg_id or _generate_msg_id()
    body_tag = f"<b>{util.escape_xml(body)}</b>" if body else "<b/>"
    owner_attr = f" uowner='{original_owner}'" if original_owner else ""
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"<resend xmlns='resend:n' i='{mid}' mi='{original_msg_id}'{owner_attr}/>"
        f"{body_tag}"
        f"</m>"
    )


def tcall_message(to: str, call_state: str, call_id: str, msg_id: str = "",
                  msg_type: str = "c") -> str:
    """Señalización de llamada (extensión ``tcall:n``).

    Atributos: ``i`` (id), ``mi`` (id del mensaje), ``st`` (estado de la
    llamada: p.ej. ``ringing``, ``accept``, ``end``), ``cid`` (call id).
    """
    mid = msg_id or _generate_msg_id()
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<tcall xmlns='tcall:n' i='{mid}' mi='{mid}' st='{util.escape_xml(call_state)}' cid='{call_id}'/>"
        f"</m>"
    )


def mention_extension(offset: int, length: int, user_id: str) -> str:
    """Extensión de mención (``mention:n``) para incluir dentro de un <m>.

    Atributos: ``o`` (offset en el texto), ``l`` (longitud de la mención),
    ``ui`` (user id / JID del mencionado).
    """
    return f"<mention xmlns='mention:n' o='{offset}' l='{length}' ui='{user_id}'/>"


def delete_message(to: str, message_id: str, msg_id: str = "", msg_type: str = "c",
                   body: str = "", media_xml: str = "", reply_to_id: str = "") -> str:
    """Eliminar mensaje."""
    mid = msg_id or message_id
    did = _generate_msg_id()
    body_xml = f"<b>{util.escape_xml(body)}</b>" if body or not media_xml else "<b/>"
    reply = _reply_xml(reply_to_id)
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"{media_xml}"
        f"<deleted xmlns='deleted:n' i='{did}' mi='{message_id}'/>"
        f"{body_xml}"
        f"</m>"
    )


def location_message(to: str, lat: float, lon: float, zoom: float = 11.0, text: str = "",
                     msg_id: str = "", reply_to_id: str = "") -> str:
    """Stanza con ubicación adjunta para chat privado."""
    mid = msg_id or _generate_msg_id()
    lid = _generate_msg_id()
    text_esc = util.escape_xml(text)
    reply = _reply_xml(reply_to_id)
    return (
        f"<m to='{to}' t='c' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<location xmlns='location:n' i='{lid}' mi='{mid}' lat='{lat}' lon='{lon}' z='{zoom}' t='{text_esc}'/>"
        f"<b/>"
        f"</m>"
    )


def event_message(to: str, event_id: str, title: str, start: int, end: int,
                  all_day: bool, ics_data: str, msg_id: str = "", reply_to_id: str = "") -> str:
    """Stanza con evento/calendario adjunto para chat privado."""
    mid = msg_id or _generate_msg_id()
    eid = event_id or _generate_msg_id()
    ad_str = "true" if all_day else "false"
    title_esc = util.escape_xml(title)
    ics_esc = util.escape_xml(ics_data)
    reply = _reply_xml(reply_to_id)
    return (
        f"<m to='{to}' t='c' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply}"
        f"<event xmlns='event:n' i='{eid}' mi='{mid}' ti='{title_esc}' s='{start}' e='{end}' ad='{ad_str}'>"
        f"<ics>{ics_esc}</ics>"
        f"</event>"
        f"<b/>"
        f"</m>"
    )
