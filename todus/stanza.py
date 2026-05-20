"""Constructor de stanzas XMPP/ToDus."""

import hashlib
from . import util


def _generate_msg_id() -> str:
    """Genera msg_id en formato hex 32 chars como usa ToDus oficial."""
    return hashlib.md5(util.generate_token(16).encode()).hexdigest()


def message(to: str, body: str, msg_id: str = "", msg_type: str = "c") -> str:
    """Stanza <m> de ToDus (mensaje de chat)."""
    mid = msg_id or _generate_msg_id()
    body_esc = util.escape_xml(body)
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"<b>{body_esc}</b>"
        f"</m>"
    )


def edit_message(to: str, new_body: str, original_msg_id: str, msg_id: str = "", msg_type: str = "c") -> str:
    mid = msg_id or _generate_msg_id()
    body_esc = util.escape_xml(new_body)
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' mi='{original_msg_id}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"<b>{body_esc}</b>"
        f"</m>"
    )


def file_message(to: str, url: str, file_type: int, caption: str = "", msg_id: str = "", msg_type: str = "c", file_name: str = "", file_size: int = 0) -> str:
    """Stanza <m> de ToDus con archivo adjunto (formato nuevo <file>)."""
    mid = msg_id or _generate_msg_id()
    fid = _generate_msg_id()
    cap_esc = util.escape_xml(caption)
    name_esc = util.escape_xml(file_name)
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"<b>{cap_esc}</b>"
        f"<file xmlns='file:n' i='{fid}' mi='{mid}' n='{name_esc}' url='{util.escape_xml(url)}' s='{file_size}' h=''/>"
        f"</m>"
    )


def image_message(to: str, url: str, file_name: str, file_size: int, width: int = 0, height: int = 0, thumbnail: str = "", caption: str = "", msg_id: str = "", msg_type: str = "c") -> str:
    """Stanza <m> de ToDus con imagen adjunta.

    FORMATO EXACTO capturado de ToDus oficial:
    <m ... i='MSG_ID'>
      <k xmlns='x8'/>
      <image xmlns='image:n' i='FILE_ID' mi='MSG_ID' url='...' n='...' s='...' h='' w='...' he='...' tnail='...'/>
      <b/>   <-- body vacío AL FINAL
    </m>

    CRÍTICO:
    - mi (en <image>) debe ser IGUAL al i del <m> (msg_id)
    - i (en <image>) es un ID de archivo diferente (32 hex)
    - <b/> va al final, no al principio
    - tnail debe ser un BlurHash real (no genérico)
    """
    mid = msg_id or _generate_msg_id()
    fid = _generate_msg_id()  # ID del archivo, diferente del msg_id
    cap_esc = util.escape_xml(caption)
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)

    # BlurHash real o placeholder
    tnail = thumbnail if thumbnail else "U6688O?Hr=xu^-w2sp-;,^VZnm-;_3xHMyt5"

    # Construir atributos opcionales de dimensiones
    wh_attrs = ""
    if width > 0:
        wh_attrs += f" w='{width}'"
    if height > 0:
        wh_attrs += f" he='{height}'"

    # ORDEN EXACTO: <k> → <image> → <b/>
    # mi='{mid}' es IGUAL al i='{mid}' del mensaje
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"<image xmlns='image:n' i='{fid}' mi='{mid}' url='{url_esc}' n='{name_esc}' s='{file_size}' h=''{wh_attrs} tnail='{tnail}'/>"
        f"<b>{cap_esc}</b>"
        f"</m>"
    )


def image_message_simple(to: str, url: str, file_name: str, file_size: int, msg_id: str = "", msg_type: str = "c") -> str:
    """Versión simple sin metadata (fallback)."""
    mid = msg_id or _generate_msg_id()
    fid = _generate_msg_id()
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)

    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"<image xmlns='image:n' i='{fid}' mi='{mid}' url='{url_esc}' n='{name_esc}' s='{file_size}' h=''/>"
        f"<b/>"
        f"</m>"
    )


def button_message(to: str, text: str, buttons: list[dict], msg_id: str = "", msg_type: str = "c") -> str:
    """Stanza <m> de ToDus con botones interactivos."""
    mid = msg_id or _generate_msg_id()
    text_esc = util.escape_xml(text)

    buttons_xml = ""
    for btn in buttons:
        btn_text = util.escape_xml(btn.get("text", ""))
        btn_cmd = btn.get("command", "cmd_type_send")
        btn_msg = util.escape_xml(btn.get("data", ""))
        btn_size = btn.get("size", "0.82")
        buttons_xml += f"<button xmlns='button:n' btn_t='{btn_text}' btn_cmd='{btn_cmd}' btn_msg_c='{btn_msg}' btn_size='{btn_size}'/>"

    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"<b>{text_esc}</b>"
        f"{buttons_xml}"
        f"</m>"
    )


def contact_message(to: str, contact_id: str, contact_name: str, contact_phone: str, msg_id: str = "", msg_type: str = "c") -> str:
    """Stanza <m> de ToDus con contacto adjunto (vCard)."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(contact_name)
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"<contact xmlns='contact:n' i='{contact_id}' mi='{mid}' n='{name_esc}' num='{contact_phone}'/>"
        f"<b/>"
        f"</m>"
    )


def sticker_message(to: str, sticker_id: str, sticker_name: str, sticker_pack: str, sticker_hash: str, msg_id: str = "", msg_type: str = "c") -> str:
    """Stanza <m> de ToDus con sticker adjunto."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(sticker_name)
    pack_esc = util.escape_xml(sticker_pack)
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}' xmlns='jc'>"
        f"<k xmlns='x8'/>"
        f"<sticker xmlns='sticker:n' i='{sticker_id}' mi='{mid}' n='{name_esc}' f='{pack_esc}' url='' s='0' h='{sticker_hash}' json=''/>"
        f"<b/>"
        f"</m>"
    )


def video_message(to: str, url: str, video_id: str, file_name: str, file_size: int, duration: int, width: int, height: int, thumbnail: str, msg_id: str = "", msg_type: str = "c", info_text: str = "") -> str:
    """Stanza <m> de ToDus con video adjunto."""
    mid = msg_id or _generate_msg_id()
    name_esc = util.escape_xml(file_name)
    url_esc = util.escape_xml(url)
    info_esc = util.escape_xml(info_text)
    return (
        f"<m to='{to}' t='{msg_type}' i='{mid}'>"
        f"<k xmlns='x8'/>"
        f"<video xmlns='video:n' i='{video_id}' mi='{mid}' url='{url_esc}' n='{name_esc}' s='{file_size}' h='' d='{duration}' w='{width}' he='{height}' tnail='{thumbnail}'/>"
        f"<b>{info_esc}</b>"
        f"</m>"
    )


def presence(status: str = "Online", priority: int = 5, show: str = "", caps: bool = True) -> str:
    """Stanza <presence> con capabilities."""
    cap = ""
    if caps:
        cap = (
            "<c ver='foVtX1ZDcopvf5CM63LcnVayPRs=' "
            "node='http://www.process-one.net/en/ejabberd/' "
            "hash='sha-1' xmlns='http://jabber.org/protocol/caps'/>"
        )
    show_tag = f"<show>{show}</show>" if show else ""
    return (
        f"<presence xmlns='jc'>"
        f"<status>{util.escape_xml(status)}</status>"
        f"{show_tag}"
        f"<priority>{priority}</priority>"
        f"{cap}"
        f"</presence>"
    )


def iq(type_: str, iq_id: str, payload: str = "", to: str = "") -> str:
    """Stanza IQ genérica."""
    to_attr = f" to='{to}'" if to else ""
    return f"<iq i='{iq_id}' t='{type_}'{to_attr}>{payload}</iq>"


def ping(ping_id: str) -> str:
    """XMPP ping (urn:xmpp:ping)."""
    return f"<iq i='{ping_id}' t='get'><ping xmlns='urn:xmpp:ping'/></iq>"


def chat_state(to: str, state: str) -> str:
    """XEP-0085 chat state notification."""
    return (
        f"<message to='{to}' t='chat' xmlns='jc'>"
        f"<{state} xmlns='http://jabber.org/protocol/chatstates'/>"
        f"</message>"
    )


def receipt(to: str, msg_id: str) -> str:
    """Delivery receipt (XEP-0184)."""
    return (
        f"<message to='{to}' t='chat' xmlns='jc'>"
        f"<received xmlns='urn:xmpp:receipts' id='{msg_id}'/>"
        f"</message>"
    )


def read_receipt(to: str, msg_id: str) -> str:
    """Read receipt (XEP-0333)."""
    return (
        f"<message to='{to}' t='chat' xmlns='jc'>"
        f"<read xmlns='urn:xmpp:read-receipts' id='{msg_id}'/>"
        f"</message>"
    )


def ack(msg_id: str, to: str = "") -> str:
    """ACK de mensaje recibido (tdack)."""
    return f"<tdack xmlns='x8' mi='{msg_id}'/>"


def keepalive() -> str:
    """Keepalive: espacio en blanco (ToDus espera cada 60s)."""
    return " "


def stream_open(host: str = "im.todus.cu") -> str:
    """Stream header inicial."""
    return f"<stream:stream xmlns='jc' o='{host}' xmlns:stream='x1' v='1.0'>"


def stream_restart(host: str = "im.todus.cu") -> str:
    """Stream header post-auth."""
    return f"<stream:stream xmlns='jc' o='{host}' xmlns:stream='x1' v='1.0'>"


def stream_close() -> str:
    """Cierre graceful del stream."""
    return "</stream:stream>"


def sasl_auth(authstr: bytes) -> str:
    """SASL PLAIN auth."""
    return b"<ah xmlns='ah:ns' e='PLAIN'>" + authstr + b"</ah>"


def bind(iq_id: str) -> str:
    """Resource bind."""
    return f"<iq i='{iq_id}' t='set'><b1 xmlns='x4'></b1></iq>"


def mam_query(query_id: str, since: str = "", before: str = "", limit: int = 50) -> str:
    """Query de Message Archive Management (MAM)."""
    filters = ""
    if since:
        filters += f"<start>{since}</start>"
    if before:
        filters += f"<end>{before}</end>"
    return (
        f"<iq i='{query_id}' t='set'>"
        f"<query xmlns='todus:mam'>{filters}"
        f"<set xmlns='http://jabber.org/protocol/rsm'><max>{limit}</max></set>"
        f"</query></iq>"
    )


def upload_query(iq_id: str, size: int, file_type: int, persistent: bool = False) -> str:
    """Reserva URL de subida."""
    persist = "true" if persistent else "false"
    return (
        f"<iq i='{iq_id}-3' t='get'>"
        f"<query xmlns='todus:purl' type='{file_type}' "
        f"persistent='{persist}' size='{size}' room=''></query>"
        f"</iq>"
    )


def download_query(iq_id: str, url: str) -> str:
    """Resuelve URL real de descarga."""
    return (
        f"<iq i='{iq_id}-2' t='get'>"
        f"<query xmlns='todus:gurl' url='{url}'></query>"
        f"</iq>"
    )
