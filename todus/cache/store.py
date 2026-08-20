"""Message Queue & History Manager para toDus-API."""

import sqlite3
import json
import logging
import threading
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Callable
from datetime import datetime
from enum import StrEnum

logger = logging.getLogger("todus.cache")


class MessageStatus(StrEnum):
    """Estados de un mensaje en la cola."""
    PENDING = "pending"          # Esperando envío
    SENT = "sent"                # Enviado al servidor
    DELIVERED = "delivered"      # Entregado al destinatario
    READ = "read"                # Leído por el destinatario
    FAILED = "failed"            # Falló en envío
    CANCELLED = "cancelled"      # Cancelado por usuario


@dataclass
class Message:
    """Representa un mensaje en la queue."""
    msg_id: str
    to: str
    body: str
    msg_type: str = "text"
    status: MessageStatus = MessageStatus.PENDING
    created_at: float = None
    sent_at: Optional[float] = None
    delivered_at: Optional[float] = None
    read_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    last_error: str = ""
    metadata: dict = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict:
        """Convierte a dict para almacenamiento."""
        data = asdict(self)
        data["status"] = str(self.status)
        data["metadata"] = json.dumps(self.metadata)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Crea desde dict."""
        data = data.copy()
        data["status"] = MessageStatus(data["status"])
        if isinstance(data["metadata"], str):
            data["metadata"] = json.loads(data["metadata"])
        return cls(**data)


class MessageStore:
    """Almacenamiento persistente de mensajes."""

    def __init__(self, db_path: str = None):
        """Inicializa la BD. Si db_path es None, usa ':memory:'."""
        if db_path is None:
            db_path = str(Path.home() / ".todus" / "messages.db")
        
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self):
        """Crea tablas si no existen."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    msg_id TEXT PRIMARY KEY,
                    "to" TEXT NOT NULL,
                    body TEXT NOT NULL,
                    msg_type TEXT DEFAULT 'text',
                    status TEXT DEFAULT 'pending',
                    created_at REAL NOT NULL,
                    sent_at REAL,
                    delivered_at REAL,
                    read_at REAL,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    last_error TEXT DEFAULT '',
                    metadata TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON messages(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_to ON messages("to")
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON messages(created_at)
            """)
            conn.commit()

    def add(self, msg: Message) -> bool:
        """Agrega un mensaje a la BD."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO messages 
                        (msg_id, "to", body, msg_type, status, created_at, sent_at, 
                         delivered_at, read_at, retry_count, max_retries, last_error, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        msg.msg_id, msg.to, msg.body, msg.msg_type, str(msg.status),
                        msg.created_at, msg.sent_at, msg.delivered_at, msg.read_at,
                        msg.retry_count, msg.max_retries, msg.last_error, 
                        json.dumps(msg.metadata) if msg.metadata else '{}'
                    ))
                    conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error al agregar mensaje: {e}")
                return False

    def get(self, msg_id: str) -> Optional[Message]:
        """Obtiene un mensaje por ID."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(
                        "SELECT * FROM messages WHERE msg_id = ?",
                        (msg_id,)
                    )
                    row = cursor.fetchone()
                    return Message.from_dict(dict(row)) if row else None
            except Exception as e:
                logger.error(f"Error al obtener mensaje: {e}")
                return None

    def get_by_status(self, status: MessageStatus, limit: int = 100) -> List[Message]:
        """Obtiene mensajes por estado."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(
                        "SELECT * FROM messages WHERE status = ? ORDER BY created_at ASC LIMIT ?",
                        (str(status), limit)
                    )
                    return [Message.from_dict(dict(row)) for row in cursor.fetchall()]
            except Exception as e:
                logger.error(f"Error al obtener por estado: {e}")
                return []

    def update_status(self, msg_id: str, new_status: MessageStatus, error: str = "") -> bool:
        """Actualiza estado de un mensaje."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    if new_status == MessageStatus.SENT:
                        conn.execute(
                            "UPDATE messages SET status = ?, sent_at = ? WHERE msg_id = ?",
                            (str(new_status), time.time(), msg_id)
                        )
                    elif new_status == MessageStatus.DELIVERED:
                        conn.execute(
                            "UPDATE messages SET status = ?, delivered_at = ? WHERE msg_id = ?",
                            (str(new_status), time.time(), msg_id)
                        )
                    elif new_status == MessageStatus.READ:
                        conn.execute(
                            "UPDATE messages SET status = ?, read_at = ? WHERE msg_id = ?",
                            (str(new_status), time.time(), msg_id)
                        )
                    elif new_status == MessageStatus.FAILED:
                        conn.execute(
                            "UPDATE messages SET status = ?, last_error = ? WHERE msg_id = ?",
                            (str(new_status), error, msg_id)
                        )
                    else:
                        conn.execute(
                            "UPDATE messages SET status = ? WHERE msg_id = ?",
                            (str(new_status), msg_id)
                        )
                    conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error al actualizar estado: {e}")
                return False

    def increment_retry(self, msg_id: str) -> bool:
        """Incrementa contador de reintentos."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "UPDATE messages SET retry_count = retry_count + 1 WHERE msg_id = ?",
                        (msg_id,)
                    )
                    conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error al incrementar reintentos: {e}")
                return False

    def delete(self, msg_id: str) -> bool:
        """Elimina un mensaje de la BD."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM messages WHERE msg_id = ?", (msg_id,))
                    conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error al eliminar mensaje: {e}")
                return False

    def get_stats(self) -> dict:
        """Obtiene estadísticas de mensajes."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT status, COUNT(*) as count FROM messages GROUP BY status
                    """)
                    stats = {row[0]: row[1] for row in cursor.fetchall()}
                    return stats
            except Exception as e:
                logger.error(f"Error al obtener stats: {e}")
                return {}

    def clear_old(self, days: int = 30) -> int:
        """Elimina mensajes más antiguos que N días (solo READ y DELIVERED)."""
        with self._lock:
            try:
                cutoff_time = time.time() - (days * 86400)
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        DELETE FROM messages 
                        WHERE created_at < ? AND status IN (?, ?)
                    """, (cutoff_time, str(MessageStatus.READ), str(MessageStatus.DELIVERED)))
                    conn.commit()
                    return cursor.rowcount
            except Exception as e:
                logger.error(f"Error al limpiar: {e}")
                return 0
