import os
import re
import time
import logging
from typing import Callable
import requests
from .. import util, stanza
from ..types import FileType
from ..errors import ConnectionLostError, TokenExpiredError, UploadError

logger = logging.getLogger("todus")


class _ProgressReader:
    def __init__(self, data: bytes, progress_callback: Callable[[int, int], None]) -> None:
        self.data = data
        self.total = len(data)
        self.offset = 0
        self.progress_callback = progress_callback

    def read(self, size: int = -1) -> bytes:
        if self.offset >= self.total:
            return b""

        if size is None or size < 0:
            chunk = self.data[self.offset:]
            self.offset = self.total
        else:
            end = min(self.offset + size, self.total)
            chunk = self.data[self.offset:end]
            self.offset = end

        if chunk and self.progress_callback:
            self.progress_callback(self.offset, self.total)

        return chunk


class ToDusFileMixin:
    """Mixin que contiene los métodos de subida y descarga de archivos de ToDus."""

    # --- Archivos ---

    def reserve_upload_url(self, token: str, size: int, file_type: FileType, file_name: str = "") -> tuple[str, str]:
        phone, authstr = self._authstr_from_token(token)
        sid = util.generate_token(5)
        up_url = down_url = ""

        # Sanitizar nombre del archivo
        sanitized_name = util.sanitize_filename(file_name, int(file_type))

        with self._xmpp_session(token) as sock:
            sock.send(stanza.upload_query(sid, size, int(file_type), file_name=sanitized_name).encode())
            while True:
                response = self._recv_all(sock)
                if response is None:
                    raise ConnectionLostError()
                if response == "":
                    continue
                if "i='" + sid + "-3'" in response and "put='" in response:
                    put_match = re.search(r"put=['\"]([^'\"]+)['\"]", response)
                    get_match = re.search(r"get=['\"]([^'\"]+)['\"]", response)
                    if put_match and get_match:
                        up_url = put_match.group(1).replace("amp;", "")
                        down_url = get_match.group(1)
                    break
                if "<not-authorized/>" in response:
                    raise TokenExpiredError()

        return up_url, down_url

    def get_real_download_url(self, token: str, url: str) -> str:
        _, authstr = self._authstr_from_token(token)
        sid = util.generate_token(5)

        with self._xmpp_session(token) as sock:
            sock.send(stanza.download_query(sid, url).encode())
            while True:
                response = self._recv_all(sock)
                if response is None:
                    raise ConnectionLostError()
                if response == "":
                    continue
                if "i='" + sid + "-2'" in response and "du='" in response:
                    match = re.match(".*du='(.*)' stat.*", response)
                    if match:
                        return match.group(1).replace("amp;", "")
                    break
                if "<not-authorized/>" in response:
                    raise TokenExpiredError()

        return ""

    def upload_file(self, token: str, data: bytes, file_type: FileType = FileType.FILE, progress_callback: Callable[[int, int], None] = None, file_name: str = "") -> str:
        up_url, down_url = self.reserve_upload_url(token, len(data), file_type, file_name=file_name)
        upload_data = _ProgressReader(data, progress_callback) if progress_callback else data
        resp = requests.put(
            up_url,
            data=upload_data,
            headers={"Content-Length": str(len(data))},
            timeout=60,
        )
        resp.raise_for_status()
        if progress_callback:
            progress_callback(len(data), len(data))
        return down_url

    def download_file(self, token: str, url: str, path: str) -> int:
        real_url = self.get_real_download_url(token, url)
        headers = {
            "User-Agent": "ToDus " + self.version_name + " HTTP-Download",
            "Authorization": "Bearer " + token,
        }
        temp_path = path + ".part"
        size = -1
        with open(temp_path, "ab") as f:
            pos = f.tell()
            while pos < size or size == -1:
                if pos:
                    headers["Range"] = "bytes=" + str(pos) + "-"
                try:
                    with self.session.get(real_url, headers=headers, stream=True, timeout=60) as resp:
                        resp.raise_for_status()
                        size = pos + int(resp.headers.get("Content-Length", 0))
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                except Exception:
                    time.sleep(5)
                pos = f.tell()
        os.rename(temp_path, path)
        return size

    def download_file_to_folder(self, token: str, url: str, folder: str, filename: str = "") -> tuple[int, str]:
        headers = {
            "User-Agent": "ToDus " + self.version_name + " HTTP-Download",
            "Authorization": "Bearer " + token,
        }

        os.makedirs(folder, exist_ok=True)

        if not filename:
            filename = os.path.basename(url.split("?")[0]) or "download"

        final_path = os.path.join(folder, filename)
        temp_path = final_path + ".part"

        if os.path.exists(temp_path):
            os.remove(temp_path)

        try:
            test_resp = self.session.head(url, headers=headers, timeout=15, allow_redirects=True)
            if test_resp.status_code in (200, 206, 401, 403, 302, 301):
                real_url = url
            else:
                real_url = self.get_real_download_url(token, url)
                if not real_url:
                    raise UploadError("No se pudo resolver URL de descarga")
        except Exception:
            real_url = self.get_real_download_url(token, url)
            if not real_url:
                raise UploadError("No se pudo obtener URL de descarga")

        size = -1
        downloaded = 0
        start_time = time.time()
        last_progress = 0

        with open(temp_path, "wb") as f:
            with self.session.get(real_url, headers=headers, stream=True, timeout=300) as resp:
                if resp.status_code not in (200, 206):
                    raise UploadError(f"HTTP {resp.status_code}: {resp.text[:100]}")

                size = int(resp.headers.get("Content-Length", 0))

                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if downloaded - last_progress >= (500 * 1024):
                            elapsed = time.time() - start_time
                            speed = downloaded / elapsed if elapsed > 0 else 0
                            logger.info("Descargando %s / %s @ %s/s",
                                        util.format_size(downloaded),
                                        util.format_size(size),
                                        util.format_size(int(speed)))
                            last_progress = downloaded

        os.rename(temp_path, final_path)
        logger.info("Descarga completa: %s", util.format_size(downloaded))
        return downloaded, final_path
