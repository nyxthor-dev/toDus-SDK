"""Generadores de stanzas XML para chat de grupos en ToDus."""

import hashlib
from .. import util


def _generate_msg_id() -> str:
    """Genera msg_id en formato hex 32 chars como usa ToDus oficial."""
    return hashlib.md5(util.generate_token(16).encode()).hexdigest()


def group_message(to: str, body: str, msg_id: str = "") -> str:
    """Mensaje de texto para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    body_esc = util.escape_xml(body)
    return (
        f"<m xml:lang='en' o='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"<b>{body_esc}</b>"
        f"</m>"
    )


def group_file_message(to: str, url: str, file_name: str, file_size: int, 
                       caption: str = "", msg_id: str = "") -> str:
    """Archivo para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    fid = _generate_msg_id()
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)
    
    return (
        f"<m xml:lang='en' o='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<file xmlns='file:n' i='{fid}' mi='{mid}' n='{name_esc}' "
        f"url='{url_esc}' s='{file_size}' h=''/>"
        f"<k xmlns='x8'/>"
        f"<b/>"
        f"</m>"
    )


def group_image_message(to: str, url: str, file_name: str, file_size: int,
                        width: int, height: int, thumbnail: str = "", 
                        caption: str = "", msg_id: str = "") -> str:
    """Imagen para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    fid = _generate_msg_id()
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)
    tnail = thumbnail if thumbnail else "U6688O?Hr=xu^-w2sp-;,^VZnm-;_3xHMyt5"
    
    return (
        f"<m xml:lang='en' o='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<image xmlns='image:n' i='{fid}' mi='{mid}' url='{url_esc}' "
        f"n='{name_esc}' s='{file_size}' h='' w='{width}' he='{height}' "
        f"tnail='{tnail}'/>"
        f"<k xmlns='x8'/>"
        f"<b/>"
        f"</m>"
    )


def group_video_message(to: str, url: str, video_id: str, file_name: str, 
                        file_size: int, duration: int, width: int, height: int, 
                        thumbnail: str, caption: str = "", msg_id: str = "") -> str:
    """Video para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)
    
    return (
        f"<m xml:lang='en' o='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<video xmlns='video:n' i='{video_id}' mi='{mid}' url='{url_esc}' "
        f"s='{file_size}' h='' d='{duration}' n='{name_esc}' "
        f"w='{width}' he='{height}' tnail='{thumbnail}'/>"
        f"<k xmlns='x8'/>"
        f"<b/>"
        f"</m>"
    )


def group_sticker_message(to: str, sticker_id: str, sticker_name: str, 
                          sticker_pack: str, sticker_hash: str, 
                          msg_id: str = "") -> str:
    """Sticker para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(sticker_name)
    pack_esc = util.escape_xml(sticker_pack)
    
    return (
        f"<m xml:lang='en' o='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<sticker xmlns='sticker:n' i='{sticker_id}' mi='{mid}' "
        f"n='{name_esc}' f='{pack_esc}' url='' s='0' h='{sticker_hash}' json=''/>"
        f"<k xmlns='x8'/>"
        f"<b/>"
        f"</m>"
    )


def group_contact_message(to: str, contact_id: str, contact_name: str, 
                          contact_phone: str, msg_id: str = "") -> str:
    """Contacto para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(contact_name)
    
    return (
        f"<m xml:lang='en' o='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<contact xmlns='contact:n' i='{contact_id}' mi='{mid}' "
        f"n='{name_esc}' num='{contact_phone}'/>"
        f"<k xmlns='x8'/>"
        f"<b/>"
        f"</m>"
    )


def group_edit_message(to: str, new_body: str, original_msg_id: str, 
                       edit_id: str = "") -> str:
    """Editar mensaje en grupo."""
    eid = edit_id or _generate_msg_id()
    body_esc = util.escape_xml(new_body)
    
    return (
        f"<m xml:lang='en' o='{to}' t='gc' i='{original_msg_id}' xmlns='jc'>"
        f"<edited xmlns='edited:n' i='{eid}' mi='{original_msg_id}'/>"
        f"<k xmlns='x8'/>"
        f"<b>{body_esc}</b>"
        f"</m>"
    )


def group_delete_message(to: str, message_id: str, msg_id: str = "", body: str = "", media_xml: str = "") -> str:
    """Eliminar mensaje en grupo."""
    mid = msg_id or message_id
    did = _generate_msg_id()
    body_xml = f"<b>{util.escape_xml(body)}</b>" if body or not media_xml else "<b/>"
    return (
        f"<m xml:lang='en' o='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"{media_xml}"
        f"<deleted xmlns='deleted:n' i='{did}' mi='{message_id}'/>"
        f"<k xmlns='x8'/>"
        f"{body_xml}"
        f"</m>"
    )


def group_location_message(to: str, lat: float, lon: float, zoom: float = 11.0, text: str = "", msg_id: str = "") -> str:
    """Stanza con ubicación adjunta para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    lid = _generate_msg_id()
    text_esc = util.escape_xml(text)
    return (
        f"<m xml:lang='en' o='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<location xmlns='location:n' i='{lid}' mi='{mid}' lat='{lat}' lon='{lon}' z='{zoom}' t='{text_esc}'/>"
        f"<k xmlns='x8'/>"
        f"<b/>"
        f"</m>"
    )


def group_event_message(to: str, event_id: str, title: str, start: int, end: int, all_day: bool, ics_data: str, msg_id: str = "") -> str:
    """Stanza con evento/calendario adjunto para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    eid = event_id or _generate_msg_id()
    ad_str = "true" if all_day else "false"
    title_esc = util.escape_xml(title)
    ics_esc = util.escape_xml(ics_data)
    return (
        f"<m xml:lang='en' o='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<event xmlns='event:n' i='{eid}' mi='{mid}' ti='{title_esc}' s='{start}' e='{end}' ad='{ad_str}'>"
        f"<ics>{ics_esc}</ics>"
        f"</event>"
        f"<k xmlns='x8'/>"
        f"<b/>"
        f"</m>"
    )
