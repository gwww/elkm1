from collections.abc import Callable
import logging
from typing import Any

EventHandler = Callable[..., None]
LOG = logging.getLogger(__name__)


class EventHandling:
    """Register and dispatch for events."""

    def __init__(self) -> None:
        """Initialize a new event instance."""
        self._handlers: dict[str, list[EventHandler]] = {}

    def add_handler(self, event_type: str, handler: EventHandler) -> None:
        """Add callback for handlers."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def remove_handler(self, event_type: str, handler: EventHandler) -> None:
        """Remove callback for handlers."""
        if event_type not in self._handlers:
            return
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def call_handlers(self, event: str, event_parameters: dict[str, Any]) -> None:
        """Call the message handlers."""
        # Copy the handlers list as add/remove could be called when invoking the handlers
        handlers = list(self._handlers.get(event, []))
        for handler in handlers:
            try:
                handler(**event_parameters)
            except Exception as exc:
                LOG.exception(exc)
