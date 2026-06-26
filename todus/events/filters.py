"""Filtros reutilizables para `EventBus`.

Provee un `Filter` ligero y `build_filter` para convertir kwargs declarativos
en una función que evalúa si un evento (dict) cumple las condiciones.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass
class Filter:
    """Representa un filtro simple sobre eventos.

    Los atributos opcionales son chequeados contra el diccionario `event`.
    - `from_phone`: compara con `event.get('from')` o `event.get('sender_phone')`.
    - `contains_keyword`: busca substring en `event.get('body','')`.
    - `msg_type`: compara `event.get('type')`.
    - `is_group`: compara `event.get('is_group')`.
    - `group_id`: compara `event.get('group_id')`.
    - `regex`: pattern aplicado sobre `body`.
    - `custom`: callable `event -> bool` para condiciones avanzadas.
    """

    from_phone: Optional[str] = None
    contains_keyword: Optional[str] = None
    msg_type: Optional[str] = None
    is_group: Optional[bool] = None
    group_id: Optional[str] = None
    regex: Optional[str] = None
    custom: Optional[Callable[[Dict[str, Any]], bool]] = None

    def matches(self, event: Dict[str, Any]) -> bool:
        if self.from_phone is not None:
            phone = event.get("from") or event.get("sender_phone") or ""
            if self.from_phone != phone:
                return False

        if self.contains_keyword is not None:
            body = (event.get("body") or "")
            if self.contains_keyword not in body:
                return False

        if self.msg_type is not None:
            if event.get("type") != self.msg_type:
                return False

        if self.is_group is not None:
            if bool(event.get("is_group")) != bool(self.is_group):
                return False

        if self.group_id is not None:
            if event.get("group_id") != self.group_id:
                return False

        if self.regex is not None:
            body = (event.get("body") or "")
            try:
                if not re.search(self.regex, body):
                    return False
            except re.error:
                return False

        if self.custom is not None:
            try:
                if not self.custom(event):
                    return False
            except Exception:
                return False

        return True


def build_filter(**kwargs) -> Callable[[Dict[str, Any]], bool]:
    """Crea una función filtro a partir de kwargs declarativos.

    Uso: `build_filter(from_phone='53...', contains_keyword='hola')`
    """
    f = Filter(
        from_phone=kwargs.get("from_phone"),
        contains_keyword=kwargs.get("contains_keyword"),
        msg_type=kwargs.get("msg_type"),
        is_group=kwargs.get("is_group"),
        group_id=kwargs.get("group_id"),
        regex=kwargs.get("regex"),
        custom=kwargs.get("custom"),
    )

    return f.matches
