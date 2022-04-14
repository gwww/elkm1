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
from .outputs import Outputs
from .panel import Panel
from .settings import Settings
from .tasks import Tasks
from .thermostats import Thermostats
from .users import Users
from .zones import Zones

LOG = logging.getLogger(__name__)


class Elk:
    """Represents all the components on an Elk panel."""

    def __init__(
        self, config: dict[str, Any], loop: asyncio.AbstractEventLoop | None = None
    ) -> None:
        """Initialize a new Elk instance."""
        self._config = config
        self.loop = loop if loop else asyncio.get_event_loop()

        self._connection: Connection = Connection(config)

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

        self.add_handler("connected", self._connected)
        self.add_handler("login", self._login_status)
        self.add_handler("IE", self._call_sync_handlers)

        self.areas: Areas = Areas(self._connection)
        self.counters: Counters = Counters(self._connection)
        self.keypads: Keypads = Keypads(self._connection)
        self.lights: Lights = Lights(self._connection)
        self.outputs: Outputs = Outputs(self._connection)
        self.panel: Panel = Panel(self._connection)
        self.settings: Settings = Settings(self._connection)
        self.tasks: Tasks = Tasks(self._connection)
        self.thermostats: Thermostats = Thermostats(self._connection)
        self.users: Users = Users(self._connection)
        self.zones: Zones = Zones(self._connection)

    def _login_status(self, succeeded: bool) -> None:
        if not succeeded:
            self._connection.disconnect()
            LOG.error("Invalid username or password.")

    def _connected(self) -> None:
        self._call_sync_handlers()

    def _sync_complete(self, **_: dict[str, Any]) -> None:
        self._connection.msg_decode.call_handlers("sync_complete", {})

        # Remove so that other apps can send UA and not trigger sync_complete
        self.remove_handler("UA", self._sync_complete)

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
        self.loop.run_forever()

    def add_handler(self, msg_type: str, handler: MsgHandler) -> None:
        """Helper to connection add_handler."""
        self._connection.msg_decode.add_handler(msg_type, handler)

    def remove_handler(self, msg_type: str, handler: MsgHandler) -> None:
        """Helper to connection remove_handler."""
        self._connection.msg_decode.remove_handler(msg_type, handler)

    def is_connected(self) -> bool:
        """Helper to connection is_connected."""
        return self._connection.is_connected()

    def connect(self) -> None:
        """Helper to connection connect."""
        asyncio.ensure_future(self._connection.connect())

    def send(self, msg: MessageEncode) -> None:
        """Helper to connection send."""
        self._connection.send(msg)

    def pause(self) -> None:
        """Helper to connection pause."""
        self._connection.pause()

    def resume(self) -> None:
        """Helper to connection resume."""
        self._connection.resume()

    def disconnect(self) -> None:
        """Helper to connection disconnect."""
        self._connection.disconnect()
