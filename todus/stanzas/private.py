"""Generadores de stanzas XML para chat privado en ToDus."""

import hashlib
from .. import util


def _generate_msg_id() -> str:
    """Genera msg_id en formato hex 32 chars como usa ToDus oficial."""
    return hashlib.md5(util.generate_token(16).encode()).hexdigest()


def message(to: str, body: str, msg_id: str = "", msg_type: str = "c", reply_to_id: str = "") -> str:
    """Stanza <m> de ToDus para chat privado."""
    mid = msg_id or _generate_msg_id()
    body_esc = util.escape_xml(body)
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<b>{body_esc}</b>"
        f"</m>"
    )


def edit_message(to: str, new_body: str, original_msg_id: str, edit_id: str = "", reply_to_id: str = "") -> str:
    """Edita un mensaje existente en chat privado."""
    eid = edit_id or _generate_msg_id()
    body_esc = util.escape_xml(new_body)
    # La edición también puede tener reply? En la app no lo he visto, pero lo dejamos por si acaso.
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""
    return (
        f"<m to='{to}' t='c' i='{original_msg_id}' xmlns='jc'>"
        f"<edited xmlns='edited:n' i='{eid}' mi='{original_msg_id}'/>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
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
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
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

    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""

    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<image xmlns='image:n' i='{fid}' mi='{mid}' url='{url_esc}' n='{name_esc}' s='{file_size}' h=''{wh_attrs} tnail='{tnail}'/>"
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
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""

    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<image xmlns='image:n' i='{fid}' mi='{mid}' url='{url_esc}' n='{name_esc}' s='{file_size}' h=''/>"
        f"<b/>"
        f"</m>"
    )


# stanzas/private.py

def button_message(to: str, text: str, buttons: list[dict], msg_id: str = "", msg_type: str = "c", reply_to_id: str = "") -> str:
    """
    Envía mensaje con botones interactivos.
    
    Cada botón es un dict con:
        - text: texto del botón
        - command: 'cmd_type_send', 'cmd_type_url', 'cmd_type_copy', 'cmd_type_call', 'cmd_type_reply', 'cmd_type_share'
        - data: valor asociado (texto a enviar, URL, texto a copiar, número de teléfono, etc.)
        - size: '0.82' (full) o '0.5' (half)
        - color: 'primary', 'secondary', 'danger', 'success' (opcional)
        - row: True si debe empezar una nueva fila (opcional)
    """
    mid = msg_id or _generate_msg_id()
    text_esc = util.escape_xml(text)
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""

    buttons_xml = ""
    for i, btn in enumerate(buttons):
        btn_text = util.escape_xml(btn.get("text", ""))
        btn_cmd = btn.get("command", "cmd_type_send")
        btn_msg = util.escape_xml(btn.get("data", ""))
        btn_size = btn.get("size", "0.82")
        btn_color = btn.get("color", "")  # primary, secondary, danger, success
        btn_row = " true" if btn.get("row", False) else ""
        
        color_attr = f" btn_color='{btn_color}'" if btn_color else ""
        row_attr = f" btn_row='{btn_row.strip()}'" if btn_row else ""
        
        buttons_xml += f"<button xmlns='button:n' btn_t='{btn_text}' btn_cmd='{btn_cmd}' btn_msg_c='{btn_msg}' btn_size='{btn_size}'{color_attr}{row_attr}/>"

    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<b>{text_esc}</b>"
        f"{buttons_xml}"
        f"</m>"
    )


def contact_message(to: str, contact_id: str, contact_name: str, contact_phone: str,
                    msg_id: str = "", msg_type: str = "c", reply_to_id: str = "") -> str:
    """Stanza con contacto adjunto."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(contact_name)
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<contact xmlns='contact:n' i='{contact_id}' mi='{mid}' n='{name_esc}' num='{contact_phone}'/>"
        f"<b/>"
        f"</m>"
    )


def sticker_message(to: str, sticker_id: str, sticker_name: str, sticker_pack: str, sticker_hash: str,
                    msg_id: str = "", msg_type: str = "c", reply_to_id: str = "") -> str:
    """Stanza con sticker adjunto."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(sticker_name)
    pack_esc = util.escape_xml(sticker_pack)
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<sticker xmlns='sticker:n' i='{sticker_id}' mi='{mid}' n='{name_esc}' f='{pack_esc}' url='' s='0' h='{sticker_hash}' json=''/>"
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
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""

    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<video xmlns='video:n' i='{video_id}' mi='{mid}' url='{url_esc}' s='{file_size}' h='' d='{duration}' n='{name_esc}' w='{width}' he='{height}' tnail='{thumbnail}'/>"
        f"{body_tag}"
        f"</m>"
    )


def delete_message(to: str, message_id: str, msg_id: str = "", msg_type: str = "c",
                   body: str = "", media_xml: str = "", reply_to_id: str = "") -> str:
    """Eliminar mensaje."""
    mid = msg_id or message_id
    did = _generate_msg_id()
    body_xml = f"<b>{util.escape_xml(body)}</b>" if body or not media_xml else "<b/>"
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
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
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""
    return (
        f"<m to='{to}' t='c' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
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
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""
    return (
        f"<m to='{to}' t='c' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<event xmlns='event:n' i='{eid}' mi='{mid}' ti='{title_esc}' s='{start}' e='{end}' ad='{ad_str}'>"
        f"<ics>{ics_esc}</ics>"
        f"</event>"
        f"<b/>"
        f"</m>"
    )