"""Event system for toDus: EventBus + filters.

API:
- EventBus: register handlers, dispatch events.
- build_filter / Filter: helpers to create filter callables.
"""
from .bus import EventBus
from .filters import build_filter, Filter

__all__ = ["EventBus", "build_filter", "Filter"]
