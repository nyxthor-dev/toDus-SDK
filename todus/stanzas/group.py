"""Generadores de stanzas XML para chat de grupos en ToDus."""

import hashlib
from .. import util


def _generate_msg_id() -> str:
    """Genera msg_id en formato hex 32 chars como usa ToDus oficial."""
    return hashlib.md5(util.generate_token(16).encode()).hexdigest()


def group_message(to: str, body: str, msg_id: str = "", reply_to_id: str = "") -> str:
    """Mensaje de texto para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    body_esc = util.escape_xml(body)
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""
    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<b>{body_esc}</b>"
        f"</m>"
    )


def group_file_message(to: str, url: str, file_name: str, file_size: int,
                       caption: str = "", msg_id: str = "", reply_to_id: str = "") -> str:
    """Archivo para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    fid = _generate_msg_id()
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)
    body_tag = f"<b>{util.escape_xml(caption)}</b>" if caption else "<b/>"
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""

    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<file xmlns='file:n' i='{fid}' mi='{mid}' n='{name_esc}' "
        f"url='{url_esc}' s='{file_size}' h=''/>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"{body_tag}"
        f"</m>"
    )


def group_image_message(to: str, url: str, file_name: str, file_size: int,
                        width: int, height: int, thumbnail: str = "",
                        caption: str = "", msg_id: str = "", reply_to_id: str = "") -> str:
    """Imagen para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    fid = _generate_msg_id()
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)
    tnail = thumbnail if thumbnail else "U6688O?Hr=xu^-w2sp-;,^VZnm-;_3xHMyt5"
    body_tag = f"<b>{util.escape_xml(caption)}</b>" if caption else "<b/>"
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""

    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<image xmlns='image:n' i='{fid}' mi='{mid}' url='{url_esc}' "
        f"n='{name_esc}' s='{file_size}' h='' w='{width}' he='{height}' "
        f"tnail='{tnail}'/>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"{body_tag}"
        f"</m>"
    )


def group_video_message(to: str, url: str, video_id: str, file_name: str,
                        file_size: int, duration: int, width: int, height: int,
                        thumbnail: str, caption: str = "", msg_id: str = "", reply_to_id: str = "") -> str:
    """Video para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)
    body_tag = f"<b>{util.escape_xml(caption)}</b>" if caption else "<b/>"
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""

    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<video xmlns='video:n' i='{video_id}' mi='{mid}' url='{url_esc}' "
        f"s='{file_size}' h='' d='{duration}' n='{name_esc}' "
        f"w='{width}' he='{height}' tnail='{thumbnail}'/>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"{body_tag}"
        f"</m>"
    )


def group_sticker_message(to: str, sticker_id: str, sticker_name: str,
                          sticker_pack: str, sticker_hash: str,
                          msg_id: str = "", reply_to_id: str = "") -> str:
    """Sticker para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(sticker_name)
    pack_esc = util.escape_xml(sticker_pack)
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""

    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<sticker xmlns='sticker:n' i='{sticker_id}' mi='{mid}' "
        f"n='{name_esc}' f='{pack_esc}' url='' s='0' h='{sticker_hash}' json=''/>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<b/>"
        f"</m>"
    )


def group_contact_message(to: str, contact_id: str, contact_name: str,
                          contact_phone: str, msg_id: str = "", reply_to_id: str = "") -> str:
    """Contacto para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(contact_name)
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""

    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<contact xmlns='contact:n' i='{contact_id}' mi='{mid}' "
        f"n='{name_esc}' num='{contact_phone}'/>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<b/>"
        f"</m>"
    )


def group_edit_message(to: str, new_body: str, original_msg_id: str,
                       edit_id: str = "", reply_to_id: str = "") -> str:
    """Editar mensaje en grupo."""
    eid = edit_id or _generate_msg_id()
    body_esc = util.escape_xml(new_body)
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""

    return (
        f"<m to='{to}' t='gc' i='{original_msg_id}' xmlns='jc'>"
        f"<edited xmlns='edited:n' i='{eid}' mi='{original_msg_id}'/>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<b>{body_esc}</b>"
        f"</m>"
    )


def group_delete_message(to: str, message_id: str, msg_id: str = "",
                         body: str = "", media_xml: str = "", reply_to_id: str = "") -> str:
    """Eliminar mensaje en grupo."""
    mid = msg_id or message_id
    did = _generate_msg_id()
    body_xml = f"<b>{util.escape_xml(body)}</b>" if body or not media_xml else "<b/>"
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""
    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"{media_xml}"
        f"<deleted xmlns='deleted:n' i='{did}' mi='{message_id}'/>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"{body_xml}"
        f"</m>"
    )


def group_location_message(to: str, lat: float, lon: float, zoom: float = 11.0,
                           text: str = "", msg_id: str = "", reply_to_id: str = "") -> str:
    """Stanza con ubicación adjunta para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    lid = _generate_msg_id()
    text_esc = util.escape_xml(text)
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""
    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<location xmlns='location:n' i='{lid}' mi='{mid}' lat='{lat}' lon='{lon}' z='{zoom}' t='{text_esc}'/>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<b/>"
        f"</m>"
    )


def group_event_message(to: str, event_id: str, title: str, start: int, end: int,
                        all_day: bool, ics_data: str, msg_id: str = "", reply_to_id: str = "") -> str:
    """Stanza con evento/calendario adjunto para grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    eid = event_id or _generate_msg_id()
    ad_str = "true" if all_day else "false"
    title_esc = util.escape_xml(title)
    ics_esc = util.escape_xml(ics_data)
    reply_xml = f"<reply xmlns='reply:n' mi='{reply_to_id}'/>" if reply_to_id else ""
    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<event xmlns='event:n' i='{eid}' mi='{mid}' ti='{title_esc}' s='{start}' e='{end}' ad='{ad_str}'>"
        f"<ics>{ics_esc}</ics>"
        f"</event>"
        f"<k xmlns='x8'/>"
        f"{reply_xml}"
        f"<b/>"
        f"</m>"
    )


def group_update_name(to: str, name: str, msg_id: str = "") -> str:
    """Stanza para actualizar el nombre del grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    v_hash = _generate_msg_id()
    name_esc = util.escape_xml(name)
    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<x xmlns='x10'><v>{v_hash}</v><g4>{name_esc}</g4></x>"
        f"</m>"
    )


def group_update_subject(to: str, subject: str, msg_id: str = "") -> str:
    """Stanza para actualizar el asunto/descripción del grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    v_hash = _generate_msg_id()
    subject_esc = util.escape_xml(subject)
    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<x xmlns='x10'><v>{v_hash}</v><subject>{subject_esc}</subject></x>"
        f"</m>"
    )


def group_update_avatar(to: str, avatar_url: str, msg_id: str = "") -> str:
    """Stanza para actualizar el avatar del grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    v_hash = _generate_msg_id()
    url_esc = util.escape_xml(avatar_url)
    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<x xmlns='x10'><v>{v_hash}</v><g3>{url_esc}</g3></x>"
        f"</m>"
    )


def group_update_avatar_thumbnail(to: str, thumbnail_url: str, msg_id: str = "") -> str:
    """Stanza para actualizar la miniatura del avatar del grupo MUC Light."""
    mid = msg_id or _generate_msg_id()
    v_hash = _generate_msg_id()
    url_esc = util.escape_xml(thumbnail_url)
    return (
        f"<m to='{to}' t='gc' i='{mid}' xmlns='jc'>"
        f"<x xmlns='x10'><v>{v_hash}</v><picture_thumbnail_url>{url_esc}</picture_thumbnail_url></x>"
        f"</m>"
    )


def group_leave_iq(to: str, msg_id: str = "") -> str:
    """Stanza IQ para salir formalmente de un grupo (x13)."""
    mid = msg_id or _generate_msg_id()
    return (
        f"<iq to='{to}' type='set' id='{mid}'>"
        f"<query xmlns='x13'/>"
        f"</iq>"
    )


def group_get_link_iq(to: str, msg_id: str = "") -> str:
    """Stanza IQ para solicitar el enlace de invitación de un grupo (x14)."""
    mid = msg_id or _generate_msg_id()
    return (
        f"<iq to='{to}' type='get' id='{mid}'>"
        f"<query xmlns='x14'/>"
        f"</iq>"
    )


def group_set_link_iq(to: str, msg_id: str = "") -> str:
    """Stanza IQ para revocar y generar un nuevo enlace de invitación (x14)."""
    mid = msg_id or _generate_msg_id()
    return (
        f"<iq to='{to}' type='set' id='{mid}'>"
        f"<query xmlns='x14'/>"
        f"</iq>"
    )


def group_get_members_iq(to: str, msg_id: str = "") -> str:
    """Stanza IQ para solicitar la lista de miembros de un grupo (x11)."""
    mid = msg_id or _generate_msg_id()
    return (
        f"<iq to='{to}' type='get' id='{mid}'>"
        f"<query xmlns='x11'/>"
        f"</iq>"
    )


def group_set_members_iq(to: str, affiliations: dict[str, str], msg_id: str = "") -> str:
    """
    Stanza IQ para modificar roles, añadir o expulsar miembros (x11).
    affiliations: dict de {numero_telefono: rol}
                  ej: {"5350000000": "participant", "5351111111": "none"}
    """
    mid = msg_id or _generate_msg_id()
    users_xml = ""
    for phone, role in affiliations.items():
        user_jid = f"{phone}@im.todus.cu"
        users_xml += f"<user affiliation='{role}'>{user_jid}</user>"
        
    return (
        f"<iq to='{to}' type='set' id='{mid}'>"
        f"<query xmlns='x11'>{users_xml}</query>"
        f"</iq>"
    )
