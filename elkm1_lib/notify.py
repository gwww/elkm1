"""Observer for notifying when messages received or events occur."""

import logging
from collections.abc import Callable
from typing import Any

NotifyHandler = Callable[..., None]
LOG = logging.getLogger(__name__)


class Notifier:
    """Register and notify on events."""

    def __init__(self) -> None:
        """Initialize a new notify instance."""
        self._observers: dict[str, list[NotifyHandler]] = {}

    def attach(self, notify_type: str, handler: NotifyHandler) -> None:
        """Add observer."""
        if notify_type not in self._observers:
            self._observers[notify_type] = []

        if handler not in self._observers[notify_type]:
            self._observers[notify_type].append(handler)

    def detach(self, notify_type: str, handler: NotifyHandler) -> None:
        """Remove observer."""
        if notify_type not in self._observers:
            return
        if handler in self._observers[notify_type]:
            self._observers[notify_type].remove(handler)

    def notify(self, notify_type: str, notify_parameters: dict[str, Any]) -> None:
        """Call the observers."""
        # Dup obervers list; add/remove could be called when invoking the observers
        observers = list(self._observers.get(notify_type, []))
        for observer in observers:
            try:
                observer(**notify_parameters)
            except Exception as exc:  # pylint: disable=broad-except
                LOG.exception(exc)
