"""Master class that combines all ElkM1 pieces together."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .areas import Areas
from .connection import Connection
from .counters import Counters
from .keypads import Keypads
from .lights import Lights
from .message import MessageEncode, MsgHandler, ua_encode
from .notify import Notifier
from .outputs import Outputs
from .panel import Panel
from .settings import Settings
from .tasks import Tasks
from .thermostats import Thermostats
from .users import Users
from .util import url_scheme_is_secure
from .zones import Zones

LOG = logging.getLogger(__name__)


class Elk:
    """Represents all the components on an Elk panel."""

    def __init__(
        self, config: dict[str, Any], loop: asyncio.AbstractEventLoop | None = None
    ) -> None:
        """Initialize a new Elk instance."""
        self._config = config
        if not loop:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        self._loop = loop

        self._notifier = Notifier()
        self._connection = Connection(config["url"], self._notifier)
        self._logged_in = False

        # Setup for all the types of elements tracked
        if "element_list" in config:
            self.element_list = config["element_list"]
        else:
            self.element_list = [
                "panel",
                "zones",
                "lights",
                "areas",
                "tasks",
                "keypads",
                "outputs",
                "thermostats",
                "counters",
                "settings",
                "users",
            ]

        self._notifier.attach("connected", self._connected)
        self._notifier.attach("disconnected", self._disconnected)
        self._notifier.attach("login", self._login_status)
        self._notifier.attach("IE", self._call_sync_handlers)
        self._notifier.attach("VN", self._got_first_message)

        self.areas = Areas(self._connection, self._notifier)
        self.counters = Counters(self._connection, self._notifier)
        self.keypads = Keypads(self._connection, self._notifier)
        self.lights = Lights(self._connection, self._notifier)
        self.outputs = Outputs(self._connection, self._notifier)
        self.panel = Panel(self._connection, self._notifier)
        self.settings = Settings(self._connection, self._notifier)
        self.tasks = Tasks(self._connection, self._notifier)
        self.thermostats = Thermostats(self._connection, self._notifier)
        self.users = Users(self._connection, self._notifier)
        self.zones = Zones(self._connection, self._notifier)

    def _login_status(self, succeeded: bool) -> None:
        self._logged_in = succeeded
        if not succeeded:
            self._connection.disconnect()
            LOG.error("Invalid username or password.")

    def _got_first_message(self, **kwargs: dict[str, Any]) -> None:
        if not self._logged_in:
            self._notifier.notify("login", {"succeeded": True})

    def _connected(self) -> None:
        if url_scheme_is_secure(self._config["url"]):
            self._connection.send_raw(self._config["userid"])
            self._connection.send_raw(self._config["password"])
        self._call_sync_handlers()

    def _disconnected(self) -> None:
        self._logged_in = False

    def _sync_complete(self, **_: dict[str, Any]) -> None:
        self._notifier.notify("sync_complete", {})

        # Remove so that other apps can send UA and not trigger sync_complete
        self._notifier.detach("UA", self._sync_complete)

    def _call_sync_handlers(self) -> None:
        """Invoke the synchronization handlers."""

        LOG.debug("Synchronizing panel...")
        self.add_handler("UA", self._sync_complete)
        for element in self.element_list:
            getattr(self, element).sync()
        self.send(ua_encode(0))  # Used to mark end of sync

    @property
    def connection(self) -> Connection:
        """Return the connection instance."""
        return self._connection

    def run(self) -> None:
        """Enter the asyncio loop."""
        self._loop.run_forever()

    def add_handler(self, msg_type: str, handler: MsgHandler) -> None:
        """Helper to connection add_handler."""
        self._notifier.attach(msg_type, handler)

    def remove_handler(self, msg_type: str, handler: MsgHandler) -> None:
        """Helper to connection remove_handler."""
        self._notifier.detach(msg_type, handler)

    def connect(self) -> None:
        """Helper to connection connect."""
        asyncio.ensure_future(self._connection.connect())

    def disconnect(self) -> None:
        """Helper to connection disconnect."""
        self._connection.disconnect()

    def is_connected(self) -> bool:
        """Helper to connection is_connected."""
        return self._connection.is_connected()

    def send(self, msg: MessageEncode) -> None:
        """Helper to connection send."""
        self._connection.send(msg)
